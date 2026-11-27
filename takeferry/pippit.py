"""MCP-facing operations for Pippit's official media CLI and Canvas SDK entry."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from .brief import TakeError, identifier, note_path, text
from .ledger import fingerprint, inside


READ = {"get_snapshot", "get_asset", "get_permissions"}
EDIT = {"create_biz_node", "update_node_data", "move_nodes", "align_nodes",
        "xyq.generation.update_prompt"}
MEDIA = {"image": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"},
         "video": {".mp4", ".webm", ".mov", ".mkv"},
         "audio": {".mp3", ".wav"}}


def run_json(command):
    try:
        proc = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
                              timeout=180, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TakeError("Could not finish the official CLI call. Inspect the existing task before retrying a write.") from exc
    try:
        answer = json.loads(proc.stdout)
    except (ValueError, UnicodeError) as exc:
        raise TakeError("The official CLI returned no usable JSON. Check its login and installed version.") from exc
    if not isinstance(answer, dict):
        raise TakeError("The official CLI returned an unexpected response.")
    if proc.returncode or answer.get("ok") is False or answer.get("error_message") or answer.get("error"):
        # Provider error text and URLs can contain account details.
        raise TakeError("The official CLI reported an error. Inspect the task in the original account.")
    return answer


class Pippit:
    def __init__(self, media_root, runner=run_json):
        self.media_root = Path(media_root).resolve()
        self.run = runner
        self.binary = os.environ.get("TAKEFERRY_PIPPIT_CLI", "pippit-tool-cli")
        self.node = os.environ.get("TAKEFERRY_NODE", "node")
        self.entry = os.environ.get("TAKEFERRY_PIPPIT_CANVAS_ENTRY", "")

    def account(self):
        status = self.run([self.binary, "status"])
        uid = status.get("uid")
        if status.get("logged_in") is not True or type(uid) not in (int, str) or not str(uid).strip():
            raise TakeError("Log in with the official Pippit CLI on this host and check its account ID.")
        return {"account": str(uid)}

    def check(self, account, team):
        if not isinstance(team, str) or not team.isascii() or not team.isdigit() or len(team) > 32:
            raise TakeError("Use the actual team ID. Personal space is 0.")
        if self.account()["account"] != account:
            raise TakeError("The signed-in Pippit account differs from the one selected for this shot.")

    def native(self, args, team):
        return self.run([self.binary, *args, "--team-id", team])

    def sdk(self, args):
        if not self.entry or not Path(self.entry).is_absolute():
            raise TakeError("Set TAKEFERRY_PIPPIT_CANVAS_ENTRY to the official Canvas scripts/run.js on this host.")
        return self.run([self.node, self.entry, "canvas", "command", *args])

    def catalog(self, name=None):
        if name is None:
            return self.sdk(["list"])
        identifier(name, "command")
        return self.sdk(["schema", name])

    def canvas(self, name, canvas, team, values):
        identifier(canvas, "canvas")
        if name not in READ | EDIT or not isinstance(values, dict):
            raise TakeError("Choose a supported canvas operation and its JSON input.")
        return self.sdk(["run", name, "--canvas-id", canvas, "--team-id", team,
                         "--input", json.dumps(values, ensure_ascii=False, allow_nan=False)])

    def get_node(self, canvas, node, team):
        raw = self.canvas("get_asset", canvas, team, {"assetId": identifier(node, "node")})
        envelope = raw.get("data")
        payload = envelope.get("asset") if isinstance(envelope, dict) else None
        if not isinstance(payload, dict) or str(payload.get("pippitAssetId", "")) != node:
            raise TakeError("Canvas readback did not identify the requested native node.")
        return payload

    def reference_files(self, brief):
        files = {}
        for ref in brief["references"]:
            rel = note_path(ref["file"])
            path = inside(self.media_root, rel)
            if not path.is_file() or path.suffix.lower() not in MEDIA[ref["kind"]]:
                raise TakeError(f"Resolve the {ref['kind']} reference under the media directory: {rel}")
            files[rel] = fingerprint(path)
        return files

    def reference_bindings(self, brief):
        bindings = {}
        for ref in brief["references"]:
            node = self.get_node(brief["canvas"], ref["node"], brief["team"])
            content = node.get("content") or {}
            if not isinstance(content, dict):
                raise TakeError("The reference node did not return readable media content.")
            asset, cloud = content.get("pippitAssetId"), content.get("assetId")
            if node.get("type") != "biz/" + ref["kind"] or not asset or not cloud:
                raise TakeError("A reference node has no verified media binding for its requested kind.")
            bindings[ref["node"]] = {"asset": str(asset), "cloud_asset": str(cloud)}
        return bindings

    def inspect_target(self, brief, allow_bound=False):
        self.check(brief["account"], brief["team"])
        node = self.get_node(brief["canvas"], brief["node"], brief["team"])
        if node.get("type") != "biz/video":
            raise TakeError("Select a native video node for this take.")
        content = node.get("content")
        if not isinstance(content, dict):
            raise TakeError("The target node did not contain native video data.")
        if content.get("pippitAssetId") and not allow_bound:
            raise TakeError("This video node already holds media. Create a fresh branch for the take.")
        generation = content.get("generation") or {}
        if not isinstance(generation, dict) or generation.get("prompt") != brief["prompt"] or generation.get("model") != brief["model"]:
            raise TakeError("The provider prompt or model differs from the reviewed native node.")
        for setting in ("ratio", "duration", "resolution"):
            saved = generation.get(setting)
            if saved is not None and setting in brief and str(saved) != str(brief[setting]):
                raise TakeError(f"The native node has a different {setting}.")
        linked = generation.get("references", [])
        if not isinstance(linked, list) or any(not isinstance(r, dict) for r in linked):
            raise TakeError("The native node returned an unreadable reference list.")
        refs = [str(r.get("sourceNodeId")) for r in linked]
        if refs != [r["node"] for r in brief["references"]]:
            raise TakeError("The native node references differ from the reviewed brief. Read the canvas again.")
        return content

    def model(self, name, team):
        return self.native(["model", "describe", text(name, "model", 160), "--type", "video"], team)

    def validate_model(self, brief):
        answer = self.model(brief["model"], brief["team"])
        model = answer.get("model", answer)
        if not isinstance(model, dict) or model.get("key") != brief["model"]:
            raise TakeError("Model discovery returned a different video model.")
        for field in ("duration", "ratio", "resolution"):
            dimension = model.get(field) or {}
            if not isinstance(dimension, dict):
                raise TakeError(f"The model returned an unreadable {field} constraint.")
            if field not in brief:
                if dimension.get("required_field"):
                    raise TakeError(f"The model requires an explicit {field}.")
                continue
            value = brief[field]
            options = dimension.get("options")
            if isinstance(options, list):
                accepted = value in options
            elif field == "duration" and all(type(dimension.get(k)) in (int, float) for k in ("min", "max")):
                lo, hi, step = dimension["min"], dimension["max"], dimension.get("step", 1)
                accepted = lo <= value <= hi and type(step) in (int, float) and step > 0 and (value - lo) % step == 0
            else:
                accepted = False
            if not accepted:
                raise TakeError(f"The current model does not confirm the requested {field}. Review its schema.")

        refs = brief["references"]
        modes = model.get("creation_modes") or []
        limits = model.get("material_limits") or {}
        if not isinstance(modes, list) or not isinstance(limits, dict):
            raise TakeError("Unable to read the current model's reference constraints.")
        reference_mode = next((m for m in modes if isinstance(m, dict)
                               and m.get("key") == "reference_generation" and m.get("enabled") is not False), None)
        if refs and modes and reference_mode is None:
            raise TakeError("This model does not offer ordinary reference generation. Review the transfer.")
        for kind in MEDIA:
            limit = limits.get(kind + "_total_limit")
            if type(limit) is int and sum(r["kind"] == kind for r in refs) > limit:
                raise TakeError(f"The selected model cannot accept this many {kind} references.")
        if type(limits.get("total_limit")) is int and len(refs) > limits["total_limit"]:
            raise TakeError("The reference count exceeds the model's total limit.")
        max_image = limits.get("max_image_size_bytes")
        for ref in refs:
            if ref["kind"] == "image" and type(max_image) is int:
                if inside(self.media_root, ref["file"]).stat().st_size > max_image:
                    raise TakeError("A reference image exceeds this model's file limit.")
        return bool(refs and reference_mode and reference_mode.get("task_type") == "reference")

    def generation_args(self, brief, inputs, staging, use_reference_mode=False):
        args = ["generate-video", "--model", brief["model"], "--prompt", brief["prompt"],
                "--duration", str(brief["duration"]), "--ratio", brief["ratio"]]
        if use_reference_mode:
            args.extend(["--task-type", "reference"])
        if brief.get("resolution"):
            args.extend(["--resolution", brief["resolution"]])
        for i, ref in enumerate(brief["references"]):
            src = inside(self.media_root, ref["file"])
            dest = staging / f"reference-{i + 1}{src.suffix.lower()}"
            shutil.copyfile(src, dest)
            if fingerprint(dest) != inputs.get(ref["file"]):
                raise TakeError("A reference changed after review. Prepare a new take.")
            args.extend(["--" + ref["kind"], str(dest)])
        return args

    def upload(self, path, team):
        return self.native(["canvas", "upload", "--path", str(path)], team)

    def media_identity(self, asset, team):
        asset = identifier(asset, "Pippit media asset")
        answer = self.native(["canvas", "get", "--asset-id", asset], team)
        rows = answer.get("assets", [])
        if not isinstance(rows, list):
            raise TakeError("Could not read the uploaded video asset.")
        for row in rows:
            if not isinstance(row, dict):
                continue
            if str(row.get("PippitAssetID", row.get("pippit_asset_id", ""))) != asset:
                continue
            video = row.get("Video") or row.get("video") or {}
            if not isinstance(video, dict):
                continue
            cloud = video.get("asset_id") or video.get("AssetID")
            if isinstance(cloud, (str, int)) and str(cloud):
                return str(cloud)
        raise TakeError("The uploaded video is still missing its cloud media identity. Query it again later.")
