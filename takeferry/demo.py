"""Run the directing workflow against two fictional, in-memory provider canvases."""
from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path

from .brief import TakeError
from .pippit import Pippit
from .studio import Studio
from .tools import dispatch

DATA = Path(__file__).with_name("data") / "rainy-door"
SHOT = "rain-at-the-door/02"


def sample_brief(provider, canvas, node, refs, camera, parent=None):
    direction = {"locked": "Keep the camera locked.", "push": "Push slowly toward An.",
                 "slow-push": "Push at half the previous speed."}[camera]
    brief = {"shot": SHOT, "provider": provider, "account": "fixture-writer",
             "canvas": canvas, "node": node, "model": "fixture-video", "duration": 5, "ratio": "9:16",
             "prompt": "Five seconds, portrait. An passes the door with a letter. A key turns. "
                       "She looks back at two seconds. Use A for her face and B only for the light. Keep the rain. " + direction,
             "camera": camera, "sound": "Rain through a steel window. A key at two seconds.",
             "cues": [{"at": 2, "action": "An turns at the sound of a key."}],
             "references": refs, "quote": "Offline storyboards. Zero platform credits."}
    if provider == "pippit":
        brief["team"] = "0"
    if parent:
        brief["parent"] = parent
    return brief


class RehearsalCLI:
    """Only the public contract shapes used in the rehearsal. Never opens a socket."""
    def __init__(self, assets=DATA):
        self.assets = assets
        self.nodes = {}
        self.uploads = {}
        self.runs = {}
        self.charges = 0
        self.log = []

    def __call__(self, cmd):
        cmd = list(cmd)
        self.log.append(cmd)
        def value(flag):
            return cmd[cmd.index(flag) + 1]
        if cmd[1] == "status":
            return {"logged_in": True, "uid": "fixture-writer"}
        if cmd[1:3] == ["model", "describe"]:
            return {"model": {"key": "fixture-video", "ratio": {"options": ["9:16"]},
                              "duration": {"min": 4, "max": 10, "step": 1}}}
        if cmd[1:3] == ["model", "list"]:
            return {"models": [{"key": "fixture-video", "kind": "video"}]}
        if cmd[1:3] == ["canvas", "create"]:
            return {"canvas_asset_id": "fixture-pippit-canvas", "state": "ready"}
        if cmd[1:3] == ["canvas", "upload"]:
            asset = "fixture-media-" + str(len(self.uploads) + 1)
            kind = "Video" if Path(value("--path")).suffix.lower() == ".mp4" else "Image"
            self.uploads[asset] = {"PippitAssetID": asset, kind: {"asset_id": "cloud-" + asset}}
            return {"state": "ready", "pippit_asset_id": asset}
        if cmd[1:3] == ["canvas", "get"]:
            return {"assets": [self.uploads[value("--asset-id")]]}
        if cmd[2:5] == ["canvas", "command", "run"]:
            op = cmd[5]
            values = json.loads(value("--input"))
            if op == "create_biz_node":
                node = "fixture-node-" + str(len(self.nodes) + 1)
                data = deepcopy(values.get("initialData", {}))
                if "pippitAssetId" in data:
                    data["assetId"] = "cloud-" + data["pippitAssetId"]
                if values.get("references"):
                    data.setdefault("generation", {})["references"] = [{"sourceNodeId": r} for r in values["references"]]
                self.nodes[node] = {"type": "biz/" + values["nodeKind"], "pippitAssetId": node, "content": data}
                return {"ok": True, "data": {"id": node}, "allocated_asset_ids": [node]}
            if op == "get_snapshot":
                return {"ok": True, "data": {"document": {"assets": deepcopy(self.nodes)}}}
            if op == "get_asset":
                return {"ok": True, "data": {"asset": deepcopy(self.nodes[values["assetId"]])}}
            if op == "update_node_data":
                patch = values["patch"]
                self.nodes[values["id"]]["content"].update(deepcopy(patch))
                if "pippitAssetId" in patch:
                    self.nodes[values["id"]]["content"]["assetId"] = "cloud-" + patch["pippitAssetId"]
                return {"ok": True}
        if cmd[1] == "generate-video":
            self.charges += 1
            key = "fixture-run-" + str(self.charges)
            prompt = value("--prompt")
            self.runs[key] = "slow-push" if "half the previous" in prompt else ("push" if "Push slowly" in prompt else "locked")
            return {"thread_id": "fixture-thread", "run_id": key}
        if cmd[1] == "query-result":
            target = Path(value("--download-dir")) / "take.mp4"
            shutil.copyfile(self.assets / (self.runs[value("--run-id")] + ".mp4"), target)
            return {"status": "succeeded", "completed": True, "thread_id": value("--thread-id"), "run_id": value("--run-id"),
                    "videos": [{"output_path": str(target)}]}
        raise TakeError("Unsupported rehearsal command. Check the sample workflow.")


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def rehearse_remote_canvases(studio, assets):
    """Exercise the host handoff with synthetic receipts and one shared storyboard."""
    from .canvases import HOST_RENDERERS, ROUTES, SUBMIT_TOOLS
    shutil.copyfile(assets / "slow-push.mp4", studio.ledger.media / "remote-fixture.mp4")
    baseline = studio.ledger.get("pippit-slow-push")["brief"]
    for provider in HOST_RENDERERS:
        mode = ROUTES[provider].mode
        canvas, node = "fixture-" + provider + "-board", "fixture-output"
        take = provider + "-fixture"
        brief = {key: baseline[key] for key in ("shot", "duration", "ratio", "camera", "sound", "cues", "prompt")}
        brief.update(provider=provider, account="fixture-writer", model="fixture-video", parent="pippit-slow-push",
                     references=[{"node": "fixture-face", "kind": "image", "role": "identity"},
                                 {"node": "fixture-light", "kind": "image", "role": "lighting only"}],
                     differences=["Synthetic contract rehearsal using the same bundled storyboard."],
                     quote="Offline fixture, zero platform credits.",
                     remote={"server": ROUTES[provider].connector, "tool": SUBMIT_TOOLS.get(provider, ("fixture_video",))[0],
                             "arguments": {"shot": SHOT, "count": 1}, "snapshot": {"account": "fixture-writer",
                             "video_outputs": 1, "model": "fixture-video", "references": ["fixture-face", "fixture-light"]}})
        if mode in ("node", "workflow"):
            brief.update(canvas=canvas, node=node)
        row = studio.prepare(take, brief)
        if not studio.remote_claim(take, provider, row["approval"], brief["remote"])["dispatch"]:
            raise TakeError("Expected an unused fixture take.")
        job = "fixture-" + provider + "-job"
        studio.receipt(take, {"task_id": job})
        studio.remote_finish(take, provider, "fixture-writer", job, "fixture-" + provider + "-asset",
                             canvas=canvas if mode != "asset" else None,
                             node=node if mode in ("node", "workflow") else None, file="remote-fixture.mp4")


def rehearse(output, canvas_tour=False):
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise TakeError("Choose a new or empty directory for the rehearsal.")
    output.mkdir(parents=True, exist_ok=True)
    from importlib.resources import files
    assets = output / "storyboards"
    assets.mkdir()
    bundled = files("takeferry").joinpath("data").joinpath("rainy-door")
    for name in ("identity.png", "lighting.png", "locked.mp4", "push.mp4", "slow-push.mp4"):
        (assets / name).write_bytes(bundled.joinpath(name).read_bytes())
    runner = RehearsalCLI(assets)
    remote = Pippit(assets, runner=runner)
    remote.entry = str(output / "fixture-canvas-entry.js")
    studio = Studio(output / "state", pippit=remote)

    def act(tool, **args):
        return dispatch(studio, "takeferry_" + tool, args)

    lib_refs = [{"node": "fixture-face", "role": "identity", "kind": "image"},
                {"node": "fixture-light", "role": "lighting only", "kind": "image"}]
    lib_brief = sample_brief("libtv", "fixture-libtv-canvas", "fixture-locked", lib_refs, "locked")
    lib_graph = {"canvas": lib_brief["canvas"], "nodes": [*lib_refs, {"id": lib_brief["node"],
                 "prompt": lib_brief["prompt"], "model": lib_brief["model"]}],
                 "edges": [{"source": r["node"], "target": lib_brief["node"]} for r in lib_refs]}
    row = act("prepare", take="libtv-locked", brief=lib_brief)
    claimed = act("libtv_claim", take=row["id"], approval=row["approval"])
    if not claimed["dispatch"]:
        raise TakeError("Expected a new rehearsal canvas.")
    act("receipt", take=row["id"], receipt={"task_id": "fixture-libtv-job"})
    lib_graph["nodes"][-1]["asset"] = "fixture-libtv-film"
    shutil.copyfile(assets / "locked.mp4", studio.ledger.media / "locked.mp4")
    act("libtv_finish", take=row["id"], task_id="fixture-libtv-job", canvas=lib_graph["canvas"],
        node=lib_graph["nodes"][-1]["id"], asset=lib_graph["nodes"][-1]["asset"], file="locked.mp4")
    act("select", take=row["id"], start=0, stop=5)
    account, team = "fixture-writer", "0"
    canvas = act("pippit_create_canvas", account=account, team=team, title="Rain at the door")["canvas_asset_id"]
    refs = []
    def create(kind, data, references):
        result = act("pippit_edit", account=account, team=team, canvas=canvas, operation="create_biz_node",
                     values={"nodeKind": kind, "initialData": data, "references": references})
        return result["data"]["id"]
    for file, role in [("identity.png", "identity"), ("lighting.png", "lighting only")]:
        asset = act("pippit_upload_reference", account=account, team=team, file=file)["pippit_asset_id"]
        node = create("image", {"pippitAssetId": asset}, [])
        refs.append({"node": node, "file": file, "kind": "image", "role": role})
    for camera, parent in [("locked", "libtv-locked"), ("push", "pippit-locked"), ("slow-push", "pippit-push")]:
        brief = sample_brief("pippit", canvas, "draft", refs, camera, parent)
        brief["node"] = create("video", {"nodeName": camera, "generation": {"model": brief["model"],
                               "prompt": brief["prompt"], "ratio": brief["ratio"], "duration": 5}},
                               [ref["node"] for ref in refs])
        take = "pippit-" + camera
        row = act("prepare", take=take, brief=brief)
        act("pippit_submit", take=take, approval=row["approval"])
        act("pippit_collect", take=take)
        act("pippit_bind", take=take)
    act("select", take="pippit-slow-push", start=1, stop=4.5)
    skill = act("skill_draft", take="pippit-slow-push", name="branch-camera-movement",
                when="Compare camera movement while keeping the character and lighting consistent.",
                steps=["Reuse the approved character and lighting references.",
                       "Fork the video node and change only the camera direction.",
                       "Read both reference links back on the native canvas before running the new take."])
    lessons = output / "branch-camera-movement"
    lessons.mkdir()
    (lessons / "SKILL.md").write_text(skill["content"], encoding="utf-8")
    result = studio.ledger.export(output / "rain-at-the-door.zip", [SHOT])
    if canvas_tour:
        rehearse_remote_canvases(studio, assets)
    comparison = act("compare", shot=SHOT)
    write_json(output / "takes.json", comparison)
    shot_list = json.loads(bundled.joinpath("shot-list.json").read_text(encoding="utf-8"))
    write_json(output / "shot-list.json", shot_list)
    write_json(output / "rain-at-the-door.canvas", studio.storyboard(shot_list)["document"])
    write_json(output / "canvases.json", {"fixture": True, "libtv": lib_graph, "pippit":
               act("pippit_read", account=account, team=team, canvas=canvas, operation="get_snapshot", values={})["data"]["document"]})
    return {"fixture": True, "platform_credits": 0, "takes": [r["id"] for r in comparison["takes"]],
            "selected": comparison["selection"], "archive": result["archive"], "output": str(output)}
