"""Operations shared by the command line, the offline example and MCP."""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from .brief import TakeError, digest, identifier, keys, note_path, text, validate
from .canvases import HOST_RENDERERS, ROUTES, catalog
from .ledger import Ledger, fingerprint, inside
from .pippit import EDIT, MEDIA, READ, Pippit
from .storyboard import storyboard


class Studio:
    def __init__(self, directory=None, pippit=None):
        state = directory or os.environ.get("TAKEFERRY_STATE_DIR") or (Path.home() / ".takeferry")
        self.ledger = Ledger(state)
        self.pippit = pippit or Pippit(os.environ.get("TAKEFERRY_MEDIA_DIR", self.ledger.media))

    def prepare(self, take, brief):
        validate(brief)
        identifier(take, "take")
        existing = self.ledger.existing(take)
        if existing:
            if existing["brief"] != brief:
                raise TakeError("This take ID already has a different brief. Give the revision a new ID.")
            return existing
        inputs = {}
        if brief["provider"] == "pippit":
            self.pippit.inspect_target(brief)
            self.pippit.validate_model(brief)
            inputs = {"files": self.pippit.reference_files(brief),
                      "native_sources": self.pippit.reference_bindings(brief)}
        return self.ledger.prepare(take, brief, inputs)

    canvas_catalog = staticmethod(catalog)

    def storyboard(self, shots, format="canvas"):
        return storyboard(self.ledger, shots, format)

    def remote_claim(self, take, provider, approval, current):
        if provider not in HOST_RENDERERS:
            raise TakeError("Use the dedicated tools for this provider.")
        row = self.ledger.get(take)
        if row["brief"]["provider"] != provider or digest(row["brief"].get("remote")) != digest(current):
            raise TakeError("The remote tool, arguments or current snapshot differ from the reviewed plan.")
        acquired, row = self.ledger.claim(take, approval, provider)
        return {"dispatch": acquired, "remote": row["brief"]["remote"] if acquired else None, "take": row}

    def remote_finish(self, take, provider, account, task_id, asset, team=None, canvas=None, node=None, file=None):
        if provider not in HOST_RENDERERS:
            raise TakeError("Use the dedicated result tools for this provider.")
        row = self.ledger.get(take)
        brief = row["brief"]
        if (brief["provider"], brief["account"], brief.get("team"), row["receipt"]) != (
                provider, account, team, {"task_id": task_id}):
            raise TakeError("The readback must match the reviewed provider, account, team and original task.")
        mode = ROUTES[provider].mode
        evidence = {"node": "reported_native_readback", "workflow": "reported_workflow_output",
                    "canvas": "reported_canvas_asset", "asset": "reported_job_asset"}
        result = {"asset": identifier(asset, "asset"), "evidence": evidence[mode]}
        for field, observed in (("canvas", canvas), ("node", node)):
            if field in brief and brief[field] != observed:
                raise TakeError(f"The reported {field} differs from the approved target.")
            if observed is not None:
                if mode == "asset":
                    raise TakeError("Use the media asset receipt for this route.")
                result[field] = identifier(observed, field)
        if mode == "canvas" and canvas is None:
            raise TakeError("Read the media from the provider canvas before marking the take ready.")
        return self._finish_original(take, result, file)

    def libtv_claim(self, take, approval):
        dispatch, row = self.ledger.claim(take, approval, "libtv")
        return {"dispatch": dispatch, "take": row}

    def receipt(self, take, receipt):
        row = self.ledger.get(take)
        names = ("thread_id", "run_id") if row["brief"]["provider"] == "pippit" else ("task_id",)
        keys(receipt, names)
        for name in names:
            identifier(receipt[name], name)
        return self.ledger.submitted(take, receipt)

    def libtv_finish(self, take, task_id, canvas, node, asset, file=None):
        row = self.ledger.get(take)
        b = row["brief"]
        if (b["provider"], b["canvas"], b["node"], row["receipt"]) != ("libtv", canvas, node, {"task_id": task_id}):
            raise TakeError("Native readback must match the original provider, task, canvas and node.")
        result = {"asset": identifier(asset, "asset"), "evidence": "reported_native_readback"}
        return self._finish_original(take, result, file)

    def _finish_original(self, take, result, file):
        if file is not None:
            relative = note_path(file)
            src = inside(self.ledger.media, relative)
            if not src.is_file() or src.suffix.lower() not in (".mp4", ".mov", ".webm", ".mkv"):
                raise TakeError("Place the returned local original in the state media directory.")
            result.update(file=relative, sha256=fingerprint(src))
        return self.ledger.finish_native(take, result)

    def pippit_models(self, account, team, model=None):
        self.pippit.check(account, team)
        if model:
            return self.pippit.model(model, team)
        return self.pippit.native(["model", "list", "--type", "video"], team)

    def pippit_create(self, account, team, title):
        self.pippit.check(account, team)
        return self.pippit.native(["canvas", "create", "--title", text(title, "title", 50), "--wait"], team)

    def pippit_upload(self, account, team, file):
        self.pippit.check(account, team)
        path = inside(self.pippit.media_root, note_path(file))
        if not path.is_file() or not any(path.suffix.lower() in types for types in MEDIA.values()):
            raise TakeError("Choose a supported image, audio or video file under TAKEFERRY_MEDIA_DIR.")
        return self.pippit.upload(path, team)

    def canvas_read(self, account, team, canvas, operation, values):
        if operation not in READ:
            raise TakeError("Use get_snapshot, get_asset or get_permissions.")
        self.pippit.check(account, team)
        return self.pippit.canvas(operation, canvas, team, values)

    def canvas_edit(self, account, team, canvas, operation, values):
        if operation not in EDIT:
            raise TakeError("Choose one of the documented native canvas edits.")
        self.pippit.check(account, team)
        return self.pippit.canvas(operation, canvas, team, values)

    def pippit_submit(self, take, approval):
        row = self.ledger.get(take)
        b = row["brief"]
        if b["provider"] != "pippit" or row["approval"] != approval:
            raise TakeError("Use the approval from the exact Pippit plan the writer reviewed.")
        if row["state"] != "planned":
            return {"dispatched": False, "take": row}
        self.pippit.inspect_target(b)
        use_reference_mode = self.pippit.validate_model(b)
        if self.pippit.reference_bindings(b) != row["inputs"]["native_sources"]:
            raise TakeError("A source node now points to different media. Review the take again.")
        with tempfile.TemporaryDirectory() as staging:
            args = self.pippit.generation_args(b, row["inputs"]["files"], Path(staging), use_reference_mode)
            self.pippit.check(b["account"], b["team"])
            acquired, row = self.ledger.claim(take, approval, "pippit")
            if not acquired:
                return {"dispatched": False, "take": row}
            # A timeout can follow a successful charge. Keep the reservation on error.
            try:
                result = self.pippit.native(args, b["team"])
                ids = {k: identifier(result.get(k), k) for k in ("thread_id", "run_id")}
                row = self.ledger.submitted(take, ids)
            except (TakeError, OSError) as exc:
                raise TakeError("Submission status is uncertain. Look up the original task in Pippit, then record its two receipt IDs.") from exc
            return {"dispatched": True, "take": row}

    def pippit_collect(self, take, video_index=0):
        row = self.ledger.get(take)
        b = row["brief"]
        if b["provider"] != "pippit" or not row["receipt"]:
            raise TakeError("Record the Pippit receipt first.")
        if row["state"] != "submitted":
            return row
        if type(video_index) is not int or video_index < 0:
            raise TakeError("video_index must be a nonnegative integer.")
        self.pippit.check(b["account"], b["team"])
        target = self.ledger.media / "renders" / digest(take)[:24]
        target.mkdir(parents=True, exist_ok=True)
        ids = row["receipt"]
        # Isolate concurrent collectors. Only the file accepted by the ledger survives.
        with tempfile.TemporaryDirectory(dir=target) as attempt:
            directory = Path(attempt).resolve()
            result = self.pippit.native(["query-result", "--thread-id", ids["thread_id"],
                                        "--run-id", ids["run_id"], "--download-dir", str(directory)], b["team"])
            if any(result.get(k) != v for k, v in ids.items()):
                raise TakeError("The query returned a different thread or run.")
            if result.get("status") != "succeeded" or result.get("completed") is not True:
                return {"take": row, "platform_status": result.get("status", "unknown")}
            clips = result.get("videos", [])
            if not isinstance(clips, list) or video_index >= len(clips) or not isinstance(clips[video_index], dict):
                raise TakeError("No such downloaded video. Query this receipt again.")
            output = clips[video_index].get("output_path")
            if not isinstance(output, str) or not output:
                raise TakeError("The provider completed the run but has not delivered a local file.")
            path = (directory / output).resolve()
            if (directory not in path.parents or not path.is_file() or path.stat().st_size == 0
                    or path.suffix.lower() not in (".mp4", ".mov", ".webm", ".mkv")):
                raise TakeError("The original file could not be verified in this task's download directory.")
            checksum = fingerprint(path)
            with tempfile.NamedTemporaryFile(dir=target, suffix=path.suffix.lower(), delete=False) as saved:
                original = Path(saved.name)
            try:
                os.replace(path, original)
                download = {"file": str(original.relative_to(self.ledger.media)), "sha256": checksum}
                acquired, row = self.ledger.step(take, "submitted", "collected", download=download)
            except BaseException:
                original.unlink(missing_ok=True)
                raise
            if not acquired:
                original.unlink(missing_ok=True)
            return row

    def pippit_bind(self, take, retry_edit=False, recovered_upload=None):
        row = self.ledger.get(take)
        b = row["brief"]
        if b["provider"] != "pippit" or not row["download"]:
            raise TakeError("Collect the video from its original Pippit receipt first.")
        if row["state"] == "ready":
            return row
        self.pippit.check(b["account"], b["team"])
        if recovered_upload is not None:
            asset = identifier(recovered_upload, "recovered asset")
            if row["state"] != "uploading":
                raise TakeError("Recover an existing asset only after an interrupted upload.")
            self.pippit.media_identity(asset, b["team"])
            _, row = self.ledger.step(take, "uploading", "uploaded", upload={"asset": asset})
        if row["state"] == "collected":
            path = inside(self.ledger.media, row["download"]["file"])
            if not path.is_file() or fingerprint(path) != row["download"]["sha256"]:
                raise TakeError("The collected original has changed.")
            acquired, row = self.ledger.step(take, "collected", "uploading")
            if acquired:
                result = self.pippit.upload(path, b["team"])
                asset = identifier(result.get("pippit_asset_id"), "uploaded Pippit asset")
                _, row = self.ledger.step(take, "uploading", "uploaded", upload={"asset": asset})
        if row["state"] == "uploading":
            raise TakeError("An upload is in progress or its receipt was lost. Recover the existing Pippit asset ID.")
        if row["state"] not in ("uploaded", "binding"):
            return row
        asset = row["upload"]["asset"]
        cloud = self.pippit.media_identity(asset, b["team"])
        content = self.pippit.inspect_target(b, allow_bound=True)
        bound = str(content.get("pippitAssetId") or "")
        if bound and bound != asset:
            raise TakeError("The target node now holds different media. Review the native canvas before continuing.")
        acquired, row = self.ledger.step(take, "uploaded", "binding")
        if row["state"] == "ready":
            return row
        if bound != asset or str(content.get("assetId", "")) != cloud:
            if not acquired and retry_edit is not True:
                raise TakeError("Writeback is unconfirmed. Inspect the native node, then set retry_edit to repeat only the binding.")
            self.pippit.canvas("update_node_data", b["canvas"], b["team"],
                               {"id": b["node"], "patch": {"pippitAssetId": asset}})
        content = self.pippit.inspect_target(b, allow_bound=True)
        if str(content.get("pippitAssetId", "")) != asset or str(content.get("assetId", "")) != cloud:
            raise TakeError("Canvas readback does not yet show both media IDs on the intended video node.")
        result = {"asset": asset, "cloud_asset": cloud, "file": row["download"]["file"],
                  "sha256": row["download"]["sha256"], "evidence": "native_node_readback"}
        return self.ledger.step(take, "binding", "ready", result=result)[1]

    def lesson(self, take, name, when, steps):
        row = self.ledger.get(take)
        selected = self.ledger.list(row["shot"])["selection"]
        if not selected or selected["take_id"] != take:
            raise TakeError("Choose the take that taught this workflow before drafting a skill.")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
            raise TakeError("Use a short hyphenated English skill name.")
        text(when, "when to apply this lesson", 400)
        if "\n" in when or not isinstance(steps, list) or not 1 <= len(steps) <= 16:
            raise TakeError("Provide a one-line description and one to sixteen reusable steps.")
        body = ["---", "name: " + name, "description: " + json.dumps(when, ensure_ascii=False),
                "---", "", "# " + name.replace("-", " ").title(), ""]
        for i, step in enumerate(steps, 1):
            body.append(f"{i}. {text(step, 'step', 1200)}")
        return {"name": name, "content": "\n".join(body) + "\n",
                "next": "Review the draft with the writer. Save it with Hermes skill_manage in the active profile."}
