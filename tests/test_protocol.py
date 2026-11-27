import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProtocolTests(unittest.TestCase):
    def test_stdio_lifecycle_discovery_and_tool_errors(self):
        with tempfile.TemporaryDirectory() as temp:
            messages = [
                {"id": 1, "method": "tools/list"},
                {"id": 2, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
                {"method": "notifications/initialized"},
                {"id": 3, "method": "tools/list"},
                {"id": 4, "method": "tools/call", "params": {"name": "takeferry_compare", "arguments": {"shot": "sample/01"}}},
                {"id": 5, "method": "tools/call", "params": {"name": "takeferry_take", "arguments": {"take": "missing"}}},
                {"id": 6, "method": "ping"},
            ]
            payload = "{bad\n" + "\n".join(json.dumps(dict(x, jsonrpc="2.0")) for x in messages) + "\n"
            result = subprocess.run([sys.executable, "-m", "takeferry", "serve"], cwd=ROOT,
                                    env=dict(os.environ, TAKEFERRY_STATE_DIR=temp),
                                    input=payload, capture_output=True, text=True, check=True)
            responses = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(len(responses), 7)
            self.assertEqual(responses[0]["error"]["code"], -32700)
            self.assertEqual(responses[1]["error"]["code"], -32002)
            self.assertEqual(responses[2]["result"]["protocolVersion"], "2025-11-25")
            names = {x["name"] for x in responses[3]["result"]["tools"]}
            self.assertIn("takeferry_pippit_bind", names)
            self.assertIn("takeferry_libtv_claim", names)
            self.assertEqual(responses[4]["result"]["structuredContent"], {"takes": [], "selection": None})
            self.assertTrue(responses[5]["result"]["isError"])
            self.assertEqual(responses[6]["result"], {})

    def test_packaged_application_runs_outside_the_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / "takeferry.pyz"
            subprocess.run([sys.executable, str(ROOT / "scripts/build_release.py"), str(app)], cwd=temp,
                           capture_output=True, check=True)
            target = Path(temp) / "out"
            data = subprocess.check_output([sys.executable, str(app), "demo", "--output", str(target), "--json"],
                                           cwd=temp, text=True)
            self.assertEqual(json.loads(data)["selected"]["take_id"], "pippit-slow-push")
            config = subprocess.check_output([sys.executable, str(app), "config"], cwd=temp, text=True)
            self.assertIn(str(app), config)
            with zipfile.ZipFile(app) as archive:
                self.assertIn("LICENSE", archive.namelist())
                self.assertIsNone(archive.testzip())
