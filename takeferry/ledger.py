"""A local shot ledger. A claim is committed before a provider can spend credits."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sqlite3
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path

from .brief import TakeError, digest, identifier, validate


def inside(root, relative):
    root = Path(root).resolve()
    result = (root / relative).resolve()
    if result == root or root not in result.parents:
        raise TakeError("The file is outside the configured media directory.")
    return result


def fingerprint(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class Ledger:
    def __init__(self, directory):
        self.directory = Path(directory).expanduser().resolve()
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.media = self.directory / "media"
        self.media.mkdir(exist_ok=True, mode=0o700)
        self.path = self.directory / "takes.sqlite3"
        with self.transaction() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS takes (
                id TEXT PRIMARY KEY, shot TEXT NOT NULL, approval TEXT NOT NULL,
                brief TEXT NOT NULL, inputs TEXT NOT NULL, state TEXT NOT NULL,
                receipt TEXT, download TEXT, upload TEXT, result TEXT)""")
            db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS pippit_destination ON takes (
                json_extract(brief, '$.account'), json_extract(brief, '$.team'),
                json_extract(brief, '$.canvas'), json_extract(brief, '$.node')
            ) WHERE json_extract(brief, '$.provider') = 'pippit'""")
            db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS magnific_destination ON takes (
                json_extract(brief, '$.account'), coalesce(json_extract(brief, '$.team'), ''),
                json_extract(brief, '$.canvas'), json_extract(brief, '$.node')
            ) WHERE json_extract(brief, '$.provider') = 'magnific'""")
            db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS external_task ON takes (
                json_extract(brief, '$.provider'), json_extract(brief, '$.account'),
                coalesce(json_extract(brief, '$.team'), ''), json_extract(receipt, '$.task_id')
            ) WHERE receipt IS NOT NULL AND json_extract(brief, '$.provider') NOT IN ('libtv', 'pippit')""")
            db.execute("""CREATE TABLE IF NOT EXISTS selections (
                shot TEXT PRIMARY KEY, take_id TEXT NOT NULL REFERENCES takes(id),
                start REAL NOT NULL, stop REAL NOT NULL)""")

    @contextmanager
    def transaction(self, write=True):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _row(db, take):
        row = db.execute("SELECT * FROM takes WHERE id=?", (take,)).fetchone()
        if row is None:
            raise TakeError(f"Unknown take {take}.")
        result = dict(row)
        for key in ("brief", "inputs", "receipt", "download", "upload", "result"):
            if result[key] is not None:
                result[key] = json.loads(result[key])
        brief = result["brief"]
        result["cost_review"] = {"provider": brief["provider"], "account": brief["account"],
                                 "team": brief.get("team"), "video_generations": 1,
                                 "quote": brief.get("quote", "Unknown. The platform has not quoted this take.")}
        return result

    def existing(self, take):
        with self.transaction(False) as db:
            if db.execute("SELECT 1 FROM takes WHERE id=?", (take,)).fetchone():
                return self._row(db, take)
            return None

    def get(self, take):
        with self.transaction(False) as db:
            return self._row(db, take)

    def list(self, shot):
        with self.transaction(False) as db:
            rows = db.execute("SELECT id FROM takes WHERE shot=? ORDER BY rowid", (shot,))
            selected = db.execute("SELECT take_id,start,stop FROM selections WHERE shot=?", (shot,)).fetchone()
            return {"takes": [self._row(db, r["id"]) for r in rows],
                    "selection": dict(selected) if selected else None}

    def prepare(self, take, brief, inputs=None):
        identifier(take, "take")
        validate(brief)
        inputs = inputs or {}
        approval = digest({"take": take, "brief": brief, "inputs": inputs})
        with self.transaction() as db:
            if "parent" in brief:
                parent = self._row(db, brief["parent"])
                if parent["shot"] != brief["shot"] or parent["state"] != "ready":
                    raise TakeError("Choose a finished parent from the same shot.")
            try:
                db.execute("""INSERT INTO takes (id,shot,approval,brief,inputs,state)
                            VALUES (?,?,?,?,?,'planned') ON CONFLICT(id) DO NOTHING""",
                           (take, brief["shot"], approval, json.dumps(brief), json.dumps(inputs)))
            except sqlite3.IntegrityError as exc:
                raise TakeError("Another take already uses this video node. Create a fresh video node for the revision.") from exc
            row = self._row(db, take)
            if row["approval"] != approval:
                raise TakeError("This take ID already has a different brief. Give the revision a new ID.")
            return row

    def claim(self, take, approval, provider):
        with self.transaction() as db:
            row = self._row(db, take)
            if row["brief"]["provider"] != provider or row["approval"] != approval:
                raise TakeError("The provider or approval does not match the reviewed take.")
            acquired = row["state"] == "planned"
            if acquired:
                db.execute("UPDATE takes SET state='submitting' WHERE id=?", (take,))
            return acquired, self._row(db, take)

    def step(self, take, expected, state, **fields):
        """Compare and set a checkpoint. Two processes cannot both acquire a step."""
        if any(k not in ("receipt", "upload", "download", "result") for k in fields):
            raise TakeError("Unknown checkpoint.")
        assignments = ["state=?"] + [k + "=?" for k in fields]
        with self.transaction() as db:
            params = [state] + [json.dumps(v) for v in fields.values()] + [take, expected]
            cursor = db.execute("UPDATE takes SET " + ",".join(assignments) +
                                " WHERE id=? AND state=?", params)
            return bool(cursor.rowcount), self._row(db, take)

    def submitted(self, take, receipt):
        row = self.get(take)
        if row["receipt"] is not None:
            if row["receipt"] != receipt:
                raise TakeError("This take is already bound to another receipt.")
            return row
        try:
            changed, row = self.step(take, "submitting", "submitted", receipt=receipt)
        except sqlite3.IntegrityError as exc:
            raise TakeError("That provider task is already bound to another take in this account.") from exc
        if not changed and row["receipt"] != receipt:
            raise TakeError("Record a receipt only after claiming its reviewed take.")
        return row

    def finish_native(self, take, result):
        with self.transaction() as db:
            row = self._row(db, take)
            existing = row["result"]
            if row["state"] == "ready":
                existing_binding = {k: v for k, v in existing.items() if k not in ("file", "sha256")}
                new_binding = {k: v for k, v in result.items() if k not in ("file", "sha256")}
                if existing_binding != new_binding:
                    raise TakeError("A different asset or destination is already attached to this take.")
                if "file" not in result or existing == result:
                    return row
                if existing.get("file"):
                    raise TakeError("This take already records another local original.")
            elif row["state"] != "submitted":
                raise TakeError("Record the original submission receipt first.")
            db.execute("UPDATE takes SET state='ready', result=? WHERE id=?", (json.dumps(result), take))
            return self._row(db, take)

    def choose(self, take, start, stop):
        with self.transaction() as db:
            row = self._row(db, take)
            if row["state"] != "ready":
                raise TakeError("Choose a take after its result has been read back.")
            if not (type(start) in (int, float) and type(stop) in (int, float)
                    and 0 <= start < stop <= row["brief"]["duration"]):
                raise TakeError("Set an in point and a later out point within the shot.")
            db.execute("INSERT OR REPLACE INTO selections VALUES (?,?,?,?)",
                       (row["shot"], take, start, stop))
            return {"shot": row["shot"], "take": take, "in": start, "out": stop}

    def export(self, destination, shots):
        """Write selected originals and a UTF-8 CSV in the supplied shot order."""
        if not shots or len(set(shots)) != len(shots):
            raise TakeError("List each shot in cut order once.")
        with self.transaction(False) as db:
            entries = []
            for shot in shots:
                pick = db.execute("SELECT * FROM selections WHERE shot=?", (shot,)).fetchone()
                if not pick:
                    raise TakeError(f"Select a take for {shot} before exporting.")
                entries.append((self._row(db, pick["take_id"]), pick["start"], pick["stop"]))
        dest = Path(destination).expanduser()
        if dest.exists():
            raise TakeError("Choose a new archive filename.")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as tmp:
            temporary = Path(tmp.name)
        try:
            sheet = io.StringIO(newline="")
            writer = csv.writer(sheet)
            writer.writerow(("shot", "take", "provider", "canvas", "node", "asset", "in_seconds", "out_seconds", "file"))
            with zipfile.ZipFile(temporary, "w") as archive:
                for index, (row, start, stop) in enumerate(entries, 1):
                    b, result = row["brief"], row["result"]
                    clip = ""
                    if result.get("file"):
                        src = inside(self.media, result["file"])
                        if not src.is_file():
                            raise TakeError(f"Restore the original file for {row['id']} before exporting.")
                        if result.get("sha256") and fingerprint(src) != result["sha256"]:
                            raise TakeError(f"The original for {row['id']} changed after collection.")
                        clip = f"shot-{index:03d}{src.suffix.lower()}"
                        archive.write(src, clip)
                    cells = [row["shot"], row["id"], b["provider"], result.get("canvas", b.get("canvas", "")),
                             result.get("node", b.get("node", "")),
                             result["asset"], start, stop, clip]
                    writer.writerow(["'" + c if isinstance(c, str) and c.lstrip().startswith(("=", "+", "-", "@")) else c for c in cells])
                archive.writestr("cut-list.csv", sheet.getvalue().encode("utf-8-sig"))
            os.link(temporary, dest)
        finally:
            temporary.unlink(missing_ok=True)
        return {"archive": str(dest), "shots": len(entries)}
