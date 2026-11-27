import copy
import csv
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from takeferry.__main__ import hermes_config
from takeferry.brief import TakeError
from takeferry.canvases import HOST_RENDERERS, ROUTES, SUBMIT_TOOLS
from takeferry.demo import SHOT, rehearse, sample_brief
from takeferry.skillpack import export_skill
from takeferry.studio import Studio
from takeferry.tools import dispatch


ROOT = Path(__file__).resolve().parents[1]


class CanvasTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.studio = Studio(self.root / "state")

    def brief(self, provider):
        mode = ROUTES[provider].mode
        brief = sample_brief(provider, "canvas-1", "node-1", [], "locked")
        brief.update(account="owner", team="workspace", remote={"server": ROUTES[provider].connector,
                     "tool": SUBMIT_TOOLS.get(provider, ("submit_video",))[0], "arguments": {"count": 1},
                     "snapshot": {"account": "owner", "team": "workspace", "video_outputs": 1, "reference": "asset-A"}})
        if mode not in ("node", "workflow"):
            brief.pop("node")
        if mode == "asset":
            brief.pop("canvas")
        return brief

    def submitted(self, provider, name="a", job="task", brief=None):
        brief = brief or self.brief(provider)
        row = dispatch(self.studio, "takeferry_prepare", {"take": name, "brief": brief})
        claim = {"take": name, "provider": provider, "approval": row["approval"], "current": brief["remote"]}
        self.assertTrue(dispatch(self.studio, "takeferry_remote_claim", claim)["dispatch"])
        self.studio.receipt(name, {"task_id": job})
        return brief

    def test_filters_and_configuration_use_only_selected_servers(self):
        self.assertEqual(len(dispatch(self.studio, "takeferry_canvas_catalog", {})["routes"]), len(ROUTES))
        self.assertEqual({r["id"] for r in self.studio.canvas_catalog(mode="board")["routes"]},
                         {"figjam", "miro", "canva", "excalidraw"})
        config = hermes_config(["figjam", "weave", "pippit", "json-canvas", "comfy-local", "tapnow", "rhtv", "canva", "excalidraw"], "ai", "cn")
        self.assertEqual(config.count("  figma:\n"), 1)
        self.assertEqual(config.count("  takeferry:\n"), 1)
        self.assertIn('command: "comfy-mcp"', config)
        self.assertIn("mcp.tapnow.ai", config)
        self.assertIn("www.runninghub.cn", config)
        self.assertIn("${CANVA_CLIENT_SECRET}", config)
        self.assertNotIn("libtv:", config)
        self.assertNotIn("auth:", config.split("  excalidraw:")[1])
        self.assertIn("mcp.tapnow.media", hermes_config(["tapnow"], "tv"))
        self.assertIn("mcp.liblib.tv", hermes_config())

    def test_graph_change_and_concurrent_dispatch(self):
        brief = self.brief("magnific")
        row = self.studio.prepare("a", brief)
        changed = copy.deepcopy(brief["remote"])
        changed["snapshot"]["reference"] = "asset-B"
        with self.assertRaises(TakeError):
            self.studio.remote_claim("a", "magnific", row["approval"], changed)
        with ThreadPoolExecutor(max_workers=4) as pool:
            claims = list(pool.map(lambda _: self.studio.remote_claim("a", "magnific", row["approval"], brief["remote"]), range(8)))
        self.assertEqual(sum(x["dispatch"] for x in claims), 1)
        self.assertTrue(all(x["remote"] is None for x in claims if not x["dispatch"]))
        with self.assertRaises(TakeError):
            self.studio.prepare("another", brief)

    def test_every_external_route_records_its_own_evidence(self):
        for provider in HOST_RENDERERS:
            with self.subTest(provider=provider):
                brief = self.submitted(provider, provider, "task-" + provider)
                args = dict(take=provider, provider=provider, account="owner", team="workspace",
                            task_id="task-" + provider, asset="video")
                for field in ("canvas", "node"):
                    if field in brief:
                        args[field] = brief[field]
                result = dispatch(self.studio, "takeferry_remote_finish", args)
                evidence = {"node": "reported_native_readback", "workflow": "reported_workflow_output",
                            "canvas": "reported_canvas_asset", "asset": "reported_job_asset"}
                self.assertEqual(result["result"]["evidence"], evidence[ROUTES[provider].mode])
                self.assertEqual(result["state"], "ready")

    def test_approval_binds_the_connector_account_and_single_output(self):
        for change in ("server", "tool", "account", "team", "video_outputs"):
            brief = self.brief("magnific")
            remote = brief["remote"]
            if change in ("server", "tool"):
                remote[change] = "unrelated"
            else:
                remote["snapshot"][change] = 2 if change == "video_outputs" else "another"
            with self.subTest(change=change), self.assertRaises(TakeError):
                self.studio.prepare("one", brief)
        brief = self.brief("magnific")
        brief["remote"]["tool"] = "mcp__magnific__spaces_run"
        self.assertEqual(self.studio.prepare("one", brief)["state"], "planned")

    def test_provider_assigned_canvas_and_exports(self):
        brief = self.brief("tapnow")
        brief.pop("canvas")
        self.submitted("tapnow", brief=brief)
        args = dict(take="a", provider="tapnow", account="owner", team="workspace", task_id="task", asset="video")
        with self.assertRaises(TakeError):
            self.studio.remote_finish(**args)
        self.studio.remote_finish(**args, canvas="returned-canvas")
        with self.assertRaises(TakeError):
            self.studio.remote_finish(**args, canvas="different")
        self.studio.ledger.choose("a", 0, 3)
        archive = self.root / "board.zip"
        self.studio.ledger.export(archive, [SHOT])
        with zipfile.ZipFile(archive) as z:
            line = next(csv.DictReader(io.StringIO(z.read("cut-list.csv").decode("utf-8-sig"))))
        self.assertEqual((line["canvas"], line["node"]), ("returned-canvas", ""))

    def test_identity_checks_and_unique_task_recovery(self):
        self.submitted("runway")
        args = dict(take="a", provider="runway", account="owner", team="workspace", task_id="task", asset="video")
        for change in [dict(provider="krea"), dict(account="other"), dict(team="other"), dict(task_id="unrelated"), dict(node="guess")]:
            with self.subTest(change=change), self.assertRaises(TakeError):
                self.studio.remote_finish(**dict(args, **change))
        b = self.brief("runway")
        row = self.studio.prepare("b", b)
        self.studio.remote_claim("b", "runway", row["approval"], b["remote"])
        with self.assertRaisesRegex(TakeError, "another take"):
            self.studio.receipt("b", {"task_id": "task"})
        self.assertEqual(self.studio.ledger.get("b")["state"], "submitting")
        self.studio.receipt("b", {"task_id": "second-job"})
        self.assertEqual(self.studio.remote_finish(**args)["state"], "ready")

    def test_planning_boards_cannot_be_submitted_as_video(self):
        for provider in ("miro", "figjam", "canva", "excalidraw", "json-canvas"):
            with self.subTest(provider=provider), self.assertRaises(TakeError):
                self.studio.prepare("bad", dict(self.brief("runway"), provider=provider))
        with self.assertRaises(TakeError):
            self.studio.prepare("bad", dict(self.brief("krea"), canvas="guess"))
        with self.assertRaises(TakeError):
            self.studio.prepare("bad", dict(self.brief("comfy"), node=None))
        with self.assertRaises(TakeError):
            self.studio.prepare("bad", dict(self.brief("comfy"), remote={"tool": "run"}))

    def test_empty_scene_board_escapes_mermaid_and_preserves_ids(self):
        shots = [{"shot": "01", "beat": 'Open the door. "] <tag>', "references": [{"name": "A", "role": "Face"}]},
                 {"shot": "02", "beat": "An looks back."}]
        canvas = self.studio.storyboard(shots)["document"]
        self.assertEqual(len(canvas["nodes"]), 3)
        ids = {n["id"] for n in canvas["nodes"]}
        self.assertTrue(all(e["fromNode"] in ids and e["toNode"] in ids for e in canvas["edges"]))
        changed = copy.deepcopy(shots)
        changed[0]["beat"] = "Walk toward the door."
        self.assertEqual(ids, {n["id"] for n in self.studio.storyboard(changed)["document"]["nodes"]})
        mermaid = self.studio.storyboard(shots, "mermaid")["document"]
        self.assertNotIn("<tag>", mermaid)
        self.assertIn("#60;tag#62;", mermaid)
        with self.assertRaises(TakeError):
            self.studio.storyboard([shots[0], shots[0]])

    def test_tour_joins_revisions_and_preserves_private_fields(self):
        result = rehearse(self.root / "tour", canvas_tour=True)
        self.assertEqual((result["platform_credits"], len(result["takes"])), (0, 12))
        out = self.root / "tour"
        board = json.loads((out / "rain-at-the-door.canvas").read_text())
        self.assertEqual((len(board["nodes"]), len(board["edges"])), (15, 14))
        self.assertIn("Selected 1 to 4.5 seconds", str(board))
        self.assertNotIn("fixture-writer", str(board))
        state = Studio(out / "state")
        self.assertEqual(len(state.canvas_catalog()["routes"]), 15)
        self.assertEqual(state.ledger.get("comfy-fixture")["result"]["evidence"], "reported_workflow_output")

    def test_skill_bundle_matches_all_pinned_sources(self):
        one, two = self.root / "one.zip", self.root / "two.zip"
        export_skill(one)
        export_skill(two)
        self.assertEqual(one.read_bytes(), two.read_bytes())
        with self.assertRaises(TakeError):
            export_skill(one)
        with zipfile.ZipFile(one) as z:
            names = z.namelist()
            self.assertEqual(sum(n.endswith("/guide.md") for n in names), 8)
            self.assertEqual(sum(n.endswith("/SKILL.md") for n in names), 1)
            prefix = "takeferry/references/upstream/"
            manifest = json.loads(z.read(prefix + "index.json"))
            for publisher in manifest.values():
                self.assertEqual(publisher["license"], "MIT")
                self.assertEqual(len(publisher["commit"]), 40)
                for item in publisher["files"]:
                    self.assertEqual(hashlib.sha256(z.read(prefix+item["local"])).hexdigest(), item["sha256"])
            self.assertIn("takeferry/LICENSE", names)

    def test_release_app_exports_skill_and_board_outside_checkout(self):
        app, out = self.root / "takeferry.pyz", self.root / "output.canvas"
        def run(*args):
            return subprocess.check_output([sys.executable, str(app), *map(str, args)], cwd=self.root,
                                           env=dict(os.environ, TAKEFERRY_STATE_DIR=str(self.root/"private")), text=True)
        subprocess.run([sys.executable, str(ROOT/"scripts/build_release.py"), str(app)], check=True, capture_output=True)
        run("skill", "--output", self.root/"public.zip")
        with zipfile.ZipFile(self.root/"public.zip") as z:
            self.assertIsNone(z.testzip())
            self.assertIn("takeferry/references/upstream/obsidian/json-canvas/references/EXAMPLES.md", z.namelist())
        run("board", "--shots", ROOT/"takeferry/data/rainy-door/shot-list.json", "--output", out)
        self.assertEqual(len(json.loads(out.read_text())["nodes"]), 3)
        self.assertEqual(len(json.loads(run("catalog", "--json"))["routes"]), 15)
