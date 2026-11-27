"""MCP tool contracts for TakeFerry."""
from __future__ import annotations

import re
from numbers import Real

from .brief import TakeError
from .canvases import HOST_RENDERERS, MODES, RENDERERS, ROUTES


def string(description):
    return {"type": "string", "description": description, "minLength": 1}


def obj(props, *required):
    return {"type": "object", "properties": props, "required": list(required), "additionalProperties": False}


def array(items):
    return {"type": "array", "items": items}


S = string
TAKE = S("Stable take ID. Reuse it on retries.")
ACCOUNT = S("Account ID returned by the provider.")
TEAM = S("Selected provider team or workspace ID. Pippit uses 0 for personal space.")
CANVAS = S("Native platform canvas asset or project ID.")
NODE = S("Native destination node or saved workflow output node ID.")
ARGS = {"type": "object", "description": "Arguments matching the installed Canvas command schema."}
APPROVAL = S("SHA-256 from the exact displayed plan, after the writer approves its cost and contents.")
REMOTE = obj({"server": S("Connector name in the TakeFerry profile."), "tool": S("Exact MCP tool discovered in the connected session."),
              "arguments": {"type": "object", "description": "Final provider arguments for one approved video."},
              "snapshot": {"type": "object", "description": "Stable reviewed account, input IDs and relevant graph settings."}},
             "server", "tool", "arguments", "snapshot")
BOARD_SHOT = obj({"shot": S("Stable scene and shot ID."), "beat": S("Visible action or screenplay beat."),
                  "camera": S("Optional camera direction."),
                  "references": array(obj({"name": S("Writer-facing reference name."), "role": S("Reference duty.")},
                                          "name", "role"))}, "shot", "beat")
REF = obj({"node": S("Native source node or upstream reference asset ID."), "role": S("What this reference contributes."),
           "kind": {"type": "string", "enum": ["image", "video", "audio"]},
           "file": S("Relative file under TAKEFERRY_MEDIA_DIR. Required for Pippit.")}, "node", "role", "kind")
CUE = obj({"at": {"type": "number", "description": "Seconds from the start."}, "action": S("What happens.")}, "at", "action")
BRIEF = obj({
    "shot": S("Stable scene and shot ID shared across platforms."), "provider": {"type": "string", "enum": list(RENDERERS)},
    "account": ACCOUNT, "team": TEAM, "canvas": CANVAS, "node": NODE, "model": S("Exact model returned by provider discovery."),
    "prompt": S("Final provider prompt, including the direction and reference roles."),
    "duration": {"type": "integer", "description": "Full shot length in seconds."},
    "ratio": S("Requested aspect ratio, for example 9:16."), "resolution": S("Optional provider resolution."),
    "camera": S("Camera direction."), "sound": S("Audio direction."), "references": array(REF), "cues": array(CUE),
    "parent": S("Completed parent take from the same shot."), "differences": array(S("A change the writer should see.")),
    "remote": REMOTE, "quote": S("Provider's price with units, or say unknown.")},
    "shot", "provider", "account", "model", "prompt", "duration", "ratio", "camera", "sound", "references", "cues")


def definitions():
    tools = {}
    def add(name, method, description, schema, read=False, external=False):
        tools["takeferry_" + name] = (method, {"name": "takeferry_" + name, "description": description,
            "inputSchema": schema, "annotations": {"readOnlyHint": read, "openWorldHint": external}})
    add("canvas_catalog", "canvas_catalog", "Find a route by provider or evidence. The list describes documented capabilities, not an authenticated tool list.",
        obj({"provider": {"type": "string", "enum": list(ROUTES)}, "mode": {"type": "string", "enum": list(MODES)}}), True)
    add("storyboard", "storyboard", "Build local shot cards, a FigJam Mermaid diagram or an editable JSON Canvas. Includes recorded takes and revisions without uploading media.",
        obj({"shots": array(BOARD_SHOT), "format": {"type": "string", "enum": ["canvas", "mermaid", "cards"]}}, "shots"), True)
    remote_provider = {"type": "string", "enum": list(HOST_RENDERERS)}
    add("remote_claim", "remote_claim", "After consent, reserve one remote MCP generation against its freshly checked plan. Call the returned remote tool only when dispatch is true.",
        obj({"take": TAKE, "provider": remote_provider, "approval": APPROVAL, "current": REMOTE},
            "take", "provider", "approval", "current"))
    add("remote_finish", "remote_finish", "Record the upstream readback for the original task at the evidence level of this provider.",
        obj({"take": TAKE, "provider": remote_provider, "account": ACCOUNT, "team": TEAM, "task_id": S("Original job ID."),
             "asset": S("Stable output asset identity reported by the job."), "canvas": CANVAS, "node": NODE,
             "file": S("Optional verified original in the private state media directory.")},
            "take", "provider", "account", "task_id", "asset"))
    add("prepare", "prepare", "Freeze one take for review. Reuse the take ID on retry. Show the complete brief, quote and one-generation limit.",
        obj({"take": TAKE, "brief": BRIEF}, "take", "brief"), external=True)
    add("take", "ledger.get", "Read a take, its approved target, original receipt and latest checkpoint.", obj({"take": TAKE}, "take"), True)
    add("compare", "ledger.list", "List takes for one shot, their parent versions and the current selection.", obj({"shot": S("Shot ID.")}, "shot"), True)
    add("libtv_claim", "libtv_claim", "Reserve one approved LibTV submission. Only dispatch to official LibTV MCP if dispatch is true.",
        obj({"take": TAKE, "approval": APPROVAL}, "take", "approval"))
    add("receipt", "receipt", "Record an existing native task receipt. Supply task_id for a hosted MCP run, or thread_id and run_id for Pippit.",
        obj({"take": TAKE, "receipt": {"type": "object", "properties": {k: S("Original provider ID.") for k in ("task_id", "thread_id", "run_id")}, "additionalProperties": False}}, "take", "receipt"))
    add("libtv_finish", "libtv_finish", "Record the asset after the official MCP reports task success and readback on the planned canvas and node.",
        obj({"take": TAKE, "task_id": S("Original task ID."), "canvas": CANVAS, "node": NODE,
             "asset": S("Native result asset ID."), "file": S("Optional downloaded original, relative to the state media directory.")},
            "take", "task_id", "canvas", "node", "asset"))
    add("select", "ledger.choose", "Record the writer's chosen take and usable interval in seconds.",
        obj({"take": TAKE, "start": {"type": "number"}, "stop": {"type": "number"}}, "take", "start", "stop"))
    add("export", "export_selection", "Export selected shots in cut order to a ZIP with a CSV and any saved originals.",
        obj({"name": S("New ZIP filename."), "shots": array(S("Shot ID in desired order."))}, "name", "shots"))
    add("skill_draft", "lesson", "Turn a selected take into a reusable skill draft. Save it with the writer's consent in their Hermes profile.",
        obj({"take": TAKE, "name": S("Short skill name."), "when": S("When to apply this method."),
             "steps": array(S("Reusable direction or readback check."))}, "take", "name", "when", "steps"))
    add("pippit_account", "pippit.account", "Read the signed-in official Pippit CLI account ID.", obj({}), True, True)
    add("pippit_models", "pippit_models", "List current video models or describe a model's exact capabilities.",
        obj({"account": ACCOUNT, "team": TEAM, "model": S("Exact model key to describe.")}, "account", "team"), True, True)
    add("pippit_catalog", "pippit.catalog", "Discover native canvas commands or read one full input schema.",
        obj({"name": S("Optional native command name.")}), True)
    add("pippit_create_canvas", "pippit_create", "Create a native canvas when the writer asks for a new canvas. Keep its returned canvas_asset_id.",
        obj({"account": ACCOUNT, "team": TEAM, "title": S("Canvas title.")}, "account", "team", "title"), external=True)
    add("pippit_upload_reference", "pippit_upload", "Upload a writer-selected local reference to the selected space. Use its stable Pippit asset ID.",
        obj({"account": ACCOUNT, "team": TEAM, "file": S("Relative file in the media directory.")}, "account", "team", "file"), external=True)
    for name, method, ops, read in [
        ("pippit_read", "canvas_read", ["get_snapshot", "get_asset", "get_permissions"], True),
        ("pippit_edit", "canvas_edit", ["create_biz_node", "update_node_data", "xyq.generation.update_prompt", "move_nodes", "align_nodes"], False)]:
        add(name, method, "Run a native canvas command against the selected account, space and canvas. Discover its schema first.",
            obj({"account": ACCOUNT, "team": TEAM, "canvas": CANVAS, "operation": {"type": "string", "enum": ops}, "values": ARGS},
                "account", "team", "canvas", "operation", "values"), read, True)
    add("pippit_submit", "pippit_submit", "Submit the approved video once. This spends credits on the chosen Pippit account.",
        obj({"take": TAKE, "approval": APPROVAL}, "take", "approval"), external=True)
    add("pippit_collect", "pippit_collect", "Query the original run and collect its video. This does not resubmit the generation.",
        obj({"take": TAKE, "video_index": {"type": "integer"}}, "take"), external=True)
    add("pippit_bind", "pippit_bind", "Attach the collected video to the intended native node, then verify both native media IDs by reading it back.",
        obj({"take": TAKE, "retry_edit": {"type": "boolean", "description": "Explicitly retry a previously unconfirmed binding after inspecting the node."},
             "recovered_upload": S("Existing asset ID to reconcile an interrupted media upload.")}, "take"), external=True)
    return tools


TOOLS = definitions()


def check(value, schema, path="arguments"):
    kind = schema.get("type")
    types = {"string": str, "integer": int, "boolean": bool, "array": list, "object": dict, "number": Real}
    if not isinstance(value, types[kind]) or (kind in ("integer", "number") and isinstance(value, bool)):
        raise TakeError(f"{path} must be a {kind}.")
    if "enum" in schema and value not in schema["enum"]:
        raise TakeError(f"{path} is not a supported choice.")
    if kind == "string" and len(value) < schema.get("minLength", 0):
        raise TakeError(f"{path} is empty.")
    if kind == "array":
        for i, entry in enumerate(value):
            check(entry, schema["items"], f"{path}[{i}]")
    if kind == "object":
        for key in schema.get("required", []):
            if key not in value:
                raise TakeError(f"Missing {path}.{key}.")
        for key, item in value.items():
            if key in schema.get("properties", {}):
                check(item, schema["properties"][key], path + "." + key)
            elif schema.get("additionalProperties") is False:
                raise TakeError(f"Unknown field {path}.{key}.")


def dispatch(studio, name, arguments):
    if name not in TOOLS:
        raise TakeError("Unknown tool. Use tools/list to see the available operations.")
    method, spec = TOOLS[name]
    check(arguments, spec["inputSchema"])
    if method == "export_selection":
        filename = arguments["name"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}\.zip", filename):
            raise TakeError("Choose a simple ZIP filename.")
        return studio.ledger.export(studio.ledger.directory / "exports" / filename, arguments["shots"])
    fn = studio
    for key in method.split("."):
        fn = getattr(fn, key)
    return fn(**arguments)
