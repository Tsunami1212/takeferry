"""Command line entry points."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

from . import __version__
from .brief import TakeError
from .demo import rehearse
from .server import serve
from .studio import Studio


def hermes_config():
    # JSON quoted scalars are also valid YAML scalars.
    executable = json.dumps(sys.executable)
    artifact = Path(sys.argv[0]).resolve()
    packed = artifact.is_file() and artifact.suffix.lower() == ".pyz"
    args = [str(artifact), "serve"] if packed else ["-m", "takeferry", "serve"]
    directory = json.dumps(str(artifact.parent if packed else Path(__file__).resolve().parents[1]))
    return f"""mcp_servers:
  takeferry:
    command: {executable}
    args: {json.dumps(args)}
    cwd: {directory}
    timeout: 240
  libtv:
    url: "https://mcp.liblib.tv/mcp"
    auth: oauth
    timeout: 180
"""


def main(argv=None):
    parser = argparse.ArgumentParser(prog="takeferry", description="Direct a shot on the writer's own video canvases.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("serve", help="Start the stdio MCP server.")
    sub.add_parser("config", help="Print a Hermes MCP configuration fragment with this checkout's paths.")
    demo = sub.add_parser("demo", help="Rehearse one shot, two fixture canvases, a revision and a cut list offline.")
    demo.add_argument("--output", type=Path, help="An empty output directory. The default is a new temporary directory.")
    demo.add_argument("--json", action="store_true", help="Print the rehearsal summary as JSON.")
    options = parser.parse_args(argv)
    try:
        if options.command == "config":
            print(hermes_config(), end="")
        elif options.command == "serve":
            serve(Studio())
        else:
            path = options.output or Path(tempfile.mkdtemp(prefix="takeferry-rehearsal-"))
            result = rehearse(path)
            if options.json:
                print(json.dumps(result, indent=2))
            else:
                print("Rain at the door | offline rehearsal | 0 platform credits")
                print("Shot 02: portrait, five seconds. An turns at two seconds.")
                print("LibTV fixture: locked camera. Face and light have separate source nodes.")
                print("Pippit fixture: same shot, then a push and a slower revision.")
                print("Each Pippit take was bound to its intended canvas node and read back.")
                print("Selected pippit-slow-push, 1.0 to 4.5 seconds.")
                print("Cut list and original:", result["archive"])
                print("Canvas snapshots, take receipts and skill draft:", result["output"])
        return 0
    except (TakeError, OSError, sqlite3.Error) as exc:
        print(f"TakeFerry: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
