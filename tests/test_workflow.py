import copy
import csv
import io
import shutil
import tempfile
import unittest
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from takeferry.brief import TakeError, validate
from takeferry.demo import DATA, SHOT, RehearsalCLI, rehearse, sample_brief
from takeferry.pippit import Pippit
from takeferry.studio import Studio
from takeferry.tools import dispatch


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.refs = self.root / "input"
        self.refs.mkdir()
        shutil.copyfile(DATA / "identity.png", self.refs / "identity.png")
        self.cli = RehearsalCLI()
        self.provider = Pippit(self.refs, self.cli)
        self.provider.entry = str(self.root / "fixture.js")
        self.app = Studio(self.root / "state", self.provider)
        self.lib = sample_brief("libtv", "c1", "v1", [], "locked")

    def pippit(self, take="one"):
        refs = [{"node": "face", "kind": "image", "role": "identity", "file": "identity.png"}]
        brief = sample_brief("pippit", "native-canvas", "native-video", refs, "push")
        self.cli.nodes["face"] = {"type": "biz/image", "pippitAssetId": "face",
                                  "content": {"pippitAssetId": "portrait", "assetId": "portrait-cloud"}}
        self.cli.nodes["native-video"] = {"type": "biz/video", "pippitAssetId": "native-video",
            "content": {"generation": {"model": brief["model"], "prompt": brief["prompt"],
                                       "references": [{"sourceNodeId": "face"}]}}}
        return self.app.prepare(take, brief)

    def submitted(self):
        row = self.pippit()
        return self.app.pippit_submit("one", row["approval"])["take"]

    def collected(self):
        self.submitted()
        return self.app.pippit_collect("one")

    def lib_ready(self, name="base", file=None):
        row = self.app.prepare(name, self.lib)
        self.app.libtv_claim(name, row["approval"])
        self.app.receipt(name, {"task_id": "task-1"})
        return self.app.libtv_finish(name, "task-1", "c1", "v1", "asset-1", file)

    def test_duration_and_action_time_are_independent(self):
        self.assertEqual(validate(self.lib)["duration"], 5)
        self.assertEqual(self.lib["cues"][0]["at"], 2)
        self.lib["cues"][0]["at"] = 6
        with self.assertRaisesRegex(TakeError, "within"):
            self.app.prepare("bad", self.lib)

    def test_prepare_retries_are_stable_and_modified_briefs_need_new_id(self):
        row = self.app.prepare("take-1", self.lib)
        self.assertEqual(self.app.prepare("take-1", self.lib), row)
        with self.assertRaisesRegex(TakeError, "different brief"):
            self.app.prepare("take-1", dict(self.lib, camera="pan"))

    def test_only_one_concurrent_claim_can_dispatch(self):
        row = self.app.prepare("take-1", self.lib)
        with ThreadPoolExecutor(max_workers=6) as pool:
            claims = list(pool.map(lambda _: self.app.libtv_claim("take-1", row["approval"]), range(12)))
        self.assertEqual(sum(x["dispatch"] for x in claims), 1)
        self.assertFalse(Studio(self.root / "state").libtv_claim("take-1", row["approval"])["dispatch"])

    def test_receipt_must_match_take_and_cannot_be_replaced(self):
        self.lib_ready()
        self.assertEqual(self.app.receipt("base", {"task_id": "task-1"})["state"], "ready")
        for receipt in [{"task_id": "other"}, {"run_id": "wrong-kind"}]:
            with self.assertRaises(TakeError):
                self.app.receipt("base", receipt)
        for ids in [("wrong", "c1", "v1"), ("task-1", "wrong", "v1"), ("task-1", "c1", "wrong")]:
            with self.assertRaisesRegex(TakeError, "readback"):
                self.app.libtv_finish("base", *ids, "asset-1")

    def test_revision_and_selection_survive_a_platform_change(self):
        self.lib_ready()
        self.app.ledger.choose("base", 1, 4)
        row = self.app.prepare("rev", dict(self.lib, parent="base", node="v2"))
        self.assertEqual(row["brief"]["parent"], "base")
        self.assertEqual(self.app.ledger.list(SHOT)["selection"]["take_id"], "base")
        with self.assertRaisesRegex(TakeError, "same shot"):
            self.app.prepare("other", dict(self.lib, shot="scene/03", parent="base"))
        with self.assertRaises(TakeError):
            self.app.ledger.choose("base", 3, 2)

    def test_export_cut_list_for_an_online_only_asset(self):
        self.lib_ready()
        self.app.ledger.choose("base", 1, 4.25)
        path = self.root / "online.zip"
        self.app.ledger.export(path, [SHOT])
        with zipfile.ZipFile(path) as z:
            self.assertEqual(z.namelist(), ["cut-list.csv"])
            row = next(csv.DictReader(io.StringIO(z.read("cut-list.csv").decode("utf-8-sig"))))
            self.assertEqual((row["asset"], row["in_seconds"], row["out_seconds"], row["file"]),
                             ("asset-1", "1.0", "4.25", ""))
        with self.assertRaises(TakeError):
            self.app.ledger.export(path, [SHOT])

    def test_native_original_can_be_added_after_playback_and_remote_readback(self):
        self.lib_ready()
        shutil.copyfile(DATA / "locked.mp4", self.app.ledger.media / "original.mp4")
        current = self.app.libtv_finish("base", "task-1", "c1", "v1", "asset-1", "original.mp4")
        replay = self.app.libtv_finish("base", "task-1", "c1", "v1", "asset-1")
        self.assertEqual(current["result"], replay["result"])
        self.assertIn("sha256", current["result"])

    def test_export_fails_cleanly_for_changed_or_missing_original(self):
        original = self.app.ledger.media / "base.mp4"
        shutil.copyfile(DATA / "locked.mp4", original)
        self.lib_ready(file="base.mp4")
        self.app.ledger.choose("base", 0, 5)
        original.write_bytes(b"changed")
        for missing in (False, True):
            if missing:
                original.unlink()
            dest = self.root / "bad.zip"
            with self.assertRaises(TakeError):
                self.app.ledger.export(dest, [SHOT])
            self.assertFalse(dest.exists())

    def test_prepare_confirm_and_repeat_do_not_spend_twice(self):
        row = self.pippit()
        self.assertEqual(self.cli.charges, 0)
        with self.assertRaises(TakeError):
            self.app.pippit_submit("one", "outdated")
        self.assertTrue(self.app.pippit_submit("one", row["approval"])["dispatched"])
        self.assertFalse(self.app.pippit_submit("one", row["approval"])["dispatched"])
        self.assertEqual(self.cli.charges, 1)

    def test_changed_file_account_links_and_model_keep_take_unsubmitted(self):
        row = self.pippit()
        original = (self.refs / "identity.png").read_bytes()
        (self.refs / "identity.png").write_bytes(b"different")
        with self.assertRaisesRegex(TakeError, "reference changed"):
            self.app.pippit_submit("one", row["approval"])
        (self.refs / "identity.png").write_bytes(original)
        with patch.object(self.provider, "account", return_value={"account": "different"}):
            with self.assertRaisesRegex(TakeError, "account differs"):
                self.app.pippit_submit("one", row["approval"])
        native = self.cli.nodes["native-video"]["content"]["generation"]
        for key, value in [("references", []), ("model", "different"), ("prompt", "someone edited this")]:
            with patch.dict(native, {key: value}), self.assertRaises(TakeError):
                self.app.pippit_submit("one", row["approval"])
        self.assertEqual((self.cli.charges, self.app.ledger.get("one")["state"]), (0, "planned"))

    def test_replaced_native_source_is_caught_even_when_its_node_id_stays_the_same(self):
        row = self.pippit()
        self.cli.nodes["face"]["content"]["assetId"] = "different-portrait"
        with self.assertRaisesRegex(TakeError, "different media"):
            self.app.pippit_submit("one", row["approval"])
        self.assertEqual(self.cli.charges, 0)

    def test_two_plans_cannot_claim_the_same_native_video_slot(self):
        row = self.pippit()
        with self.assertRaisesRegex(TakeError, "already uses"):
            self.app.prepare("two", row["brief"])

    def test_model_removed_before_confirm_requires_review(self):
        row = self.pippit()
        with patch.object(self.provider, "model", return_value={"model": {"key": "fixture-video", "ratio": {"options": ["1:1"]}}}):
            with self.assertRaises(TakeError):
                self.app.pippit_submit("one", row["approval"])
        self.assertEqual(self.cli.charges, 0)

    def test_lost_submission_receipt_can_be_recovered_without_resubmitting(self):
        row = self.pippit()
        def lost(cmd):
            answer = self.cli(cmd)
            if cmd[1] == "generate-video":
                raise TakeError("lost after upstream accepted")
            return answer
        with patch.object(self.provider, "run", side_effect=lost):
            with self.assertRaisesRegex(TakeError, "uncertain"):
                self.app.pippit_submit("one", row["approval"])
        self.assertFalse(self.app.pippit_submit("one", row["approval"])["dispatched"])
        self.app.receipt("one", {"thread_id": "fixture-thread", "run_id": "fixture-run-1"})
        self.assertEqual(self.app.pippit_collect("one")["state"], "collected")
        self.assertEqual(self.cli.charges, 1)

    def test_matching_successful_query_and_actual_download_are_required(self):
        row = self.submitted()
        for change, holds in [({"status": "failed", "completed": True}, True),
                              ({"run_id": "unrelated"}, False),
                              ({"status": "succeeded", "completed": True, "videos": []}, False)]:
            query = dict(row["receipt"])
            query.update(change)
            with patch.object(self.provider, "native", return_value=query):
                if holds:
                    self.assertEqual(self.app.pippit_collect("one")["platform_status"], "failed")
                else:
                    with self.assertRaises(TakeError):
                        self.app.pippit_collect("one")
            self.assertEqual(self.app.ledger.get("one")["state"], "submitted")

    def test_parallel_collectors_keep_the_same_immutable_original(self):
        self.submitted()
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.app.pippit_collect("one"), range(4)))
        self.assertEqual(len({r["download"]["file"] for r in results}), 1)
        self.assertEqual(len(list(self.app.ledger.media.rglob("*.mp4"))), 1)

    def test_explicitly_unsupported_reference_mode_does_not_issue_a_paid_call(self):
        row = self.pippit()
        model = self.provider.model(row["brief"]["model"], "0")
        model["model"]["creation_modes"] = [{"key": "first_last_frame", "enabled": True}]
        with patch.object(self.provider, "model", return_value=model), self.assertRaisesRegex(TakeError, "reference generation"):
            self.app.pippit_submit("one", row["approval"])
        self.assertEqual(self.cli.charges, 0)

    def test_media_must_be_attached_and_read_back_on_exact_node(self):
        row = self.collected()
        self.assertEqual(row["state"], "collected")
        with self.assertRaises(TakeError):
            self.app.ledger.choose("one", 0, 5)
        with patch.object(self.provider, "canvas", wraps=self.provider.canvas) as spy:
            result = self.app.pippit_bind("one")
            operations = [call.args[0] for call in spy.call_args_list]
            self.assertIn("update_node_data", operations)
            self.assertEqual(operations[-1], "get_asset")
        self.assertEqual(result["state"], "ready")
        content = self.cli.nodes["native-video"]["content"]
        self.assertEqual(result["result"]["asset"], content["pippitAssetId"])
        self.assertEqual(result["result"]["cloud_asset"], content["assetId"])
        self.assertEqual(self.app.prepare("one", result["brief"]), result)
        self.assertEqual(self.app.pippit_bind("one"), result)

    def test_unacknowledged_node_write_is_read_back_without_new_charge(self):
        self.collected()
        original = self.provider.canvas
        def uncertain(operation, *args):
            answer = original(operation, *args)
            if operation == "update_node_data":
                raise TakeError("lost write acknowledgement")
            return answer
        with patch.object(self.provider, "canvas", side_effect=uncertain), self.assertRaises(TakeError):
            self.app.pippit_bind("one")
        self.assertEqual(self.app.ledger.get("one")["state"], "binding")
        self.assertEqual(self.app.pippit_bind("one")["state"], "ready")
        self.assertEqual(self.cli.charges, 1)

    def test_conflicting_native_media_is_preserved(self):
        self.collected()
        self.cli.nodes["native-video"]["content"]["pippitAssetId"] = "writers-new-media"
        with self.assertRaisesRegex(TakeError, "different media"):
            self.app.pippit_bind("one")
        self.assertEqual(self.cli.nodes["native-video"]["content"]["pippitAssetId"], "writers-new-media")

    def test_skill_draft_is_scoped_to_a_selected_take(self):
        self.lib_ready()
        args = ("base", "reuse-lights", "Reuse the light on a new camera branch.", ["Read the light node back."])
        with self.assertRaises(TakeError):
            self.app.lesson(*args)
        self.app.ledger.choose("base", 0, 5)
        content = self.app.lesson(*args)["content"]
        self.assertIn("name: reuse-lights", content)
        self.assertNotIn("fixture-writer", content)

    def test_rehearsal_packs_the_selected_original_and_saves_the_method(self):
        root = self.root / "rehearsal"
        summary = rehearse(root)
        self.assertEqual((summary["fixture"], summary["platform_credits"], len(summary["takes"])), (True, 0, 4))
        with zipfile.ZipFile(summary["archive"]) as z:
            self.assertEqual(z.read("shot-001.mp4"), (DATA / "slow-push.mp4").read_bytes())
        self.assertTrue((root / "branch-camera-movement" / "SKILL.md").is_file())
        with self.assertRaises(TakeError):
            rehearse(root)

    def test_schema_rejects_extra_fields_and_ambiguous_types(self):
        with self.assertRaisesRegex(TakeError, "Unknown field"):
            dispatch(self.app, "takeferry_prepare", {"take": "a", "brief": dict(self.lib, executable="unexpected")})
        bad = copy.deepcopy(self.lib)
        bad["duration"] = True
        with self.assertRaises(TakeError):
            dispatch(self.app, "takeferry_prepare", {"take": "a", "brief": bad})
