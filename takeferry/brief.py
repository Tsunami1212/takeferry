"""Validate an immutable shot brief before it can be shown for approval."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import PurePosixPath


class TakeError(ValueError):
    """A problem the writer or their agent can act on."""


def text(value, field, limit=1024):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise TakeError(f"{field} must contain 1 to {limit} characters.")
    if any(ord(c) < 32 and c not in "\n\t\r" for c in value):
        raise TakeError(f"{field} contains a control character.")
    return value


def identifier(value, field):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,159}", value):
        raise TakeError(f"{field} must be a stable identifier of up to 160 characters.")
    return value


def note_path(value):
    value = text(value, "reference file", 512)
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value or value.startswith("-"):
        raise TakeError("Use a relative path inside the configured media directory.")
    return value


def keys(obj, required, optional=()):
    if not isinstance(obj, dict):
        raise TakeError("Expected an object.")
    missing = set(required) - obj.keys()
    extra = obj.keys() - set(required) - set(optional)
    if missing:
        raise TakeError("Missing fields: " + ", ".join(sorted(missing)))
    if extra:
        raise TakeError("Unknown fields: " + ", ".join(sorted(extra)))


def digest(obj):
    data = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(data.encode()).hexdigest()


def validate(brief):
    keys(brief, ("shot", "provider", "account", "canvas", "node", "model", "prompt",
                 "duration", "ratio", "camera", "sound", "references", "cues"),
         ("parent", "team", "resolution", "differences", "quote"))
    for name in ("shot", "account", "canvas", "node"):
        identifier(brief[name], name)
    if brief["provider"] not in ("libtv", "pippit"):
        raise TakeError("Choose libtv or pippit.")
    text(brief["model"], "model", 160)
    text(brief["prompt"], "the final provider prompt", 16000)
    for name in ("camera", "sound"):
        text(brief[name], name)
    duration = brief["duration"]
    if type(duration) is not int or not 1 <= duration <= 600:
        raise TakeError("duration must be an integer between 1 and 600 seconds.")
    if not isinstance(brief["ratio"], str) or not re.fullmatch(r"[1-9][0-9]{0,2}:[1-9][0-9]{0,2}", brief["ratio"]):
        raise TakeError("Use an explicit aspect ratio such as 9:16.")
    if brief["provider"] == "pippit":
        if not isinstance(brief.get("team"), str) or not re.fullmatch(r"[0-9]{1,32}", brief["team"]):
            raise TakeError("Set the Pippit team ID as a string. Use 0 for personal space.")
    for key in ("resolution", "quote"):
        if key in brief:
            text(brief[key], key, 256)
    if "parent" in brief:
        identifier(brief["parent"], "parent")
    refs = brief["references"]
    if not isinstance(refs, list) or len(refs) > 24:
        raise TakeError("references must be a list of at most 24 entries.")
    seen = set()
    for ref in refs:
        keys(ref, ("node", "role", "kind"), ("file",))
        identifier(ref["node"], "reference node")
        text(ref["role"], "reference role", 240)
        if ref["kind"] not in ("image", "video", "audio"):
            raise TakeError("Reference kind must be image, video or audio.")
        if ref["node"] in seen or ref["node"] == brief["node"]:
            raise TakeError("Give each reference its own source node.")
        seen.add(ref["node"])
        if "file" in ref:
            note_path(ref["file"])
        elif brief["provider"] == "pippit":
            raise TakeError("Each Pippit reference needs an approved local file for the generation CLI.")
    cues = brief["cues"]
    if not isinstance(cues, list) or len(cues) > 32:
        raise TakeError("cues must be a list of at most 32 timed directions.")
    for cue in cues:
        keys(cue, ("at", "action"))
        at = cue["at"]
        if type(at) not in (int, float) or not math.isfinite(at) or not 0 <= at <= duration:
            raise TakeError("Place the action cue within the duration of the shot.")
        text(cue["action"], "action cue", 512)
    differences = brief.get("differences", [])
    if not isinstance(differences, list) or len(differences) > 24:
        raise TakeError("differences must be a list of creative changes the writer should review.")
    for item in differences:
        text(item, "difference", 512)
    return brief
