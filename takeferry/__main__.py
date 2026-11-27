"""Command line entry points."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

from . import __version__
from .canvases import MODES, ROUTES, catalog
from .demo import rehearse
from .skillpack import export_skill
from .server import serve
from .studio import Studio


def hermes_config(providers=None, tapnow_site="media", rhtv_site="ai"):
    # JSON quoted scalars are also valid YAML scalars.
    executable = json.dumps(sys.executable)
    artifact = Path(sys.argv[0]).resolve()
    packed = artifact.is_file() and artifact.suffix.lower() == ".pyz"
    args = [str(artifact), "serve"] if packed else ["-m", "takeferry", "serve"]
    directory = json.dumps(str(artifact.parent if packed else Path(__file__).resolve().parents[1]))
    fragment = f"""mcp_servers:
  takeferry:
    command: {executable}
    args: {json.dumps(args)}
    cwd: {directory}
    timeout: 240
"""
    emitted = {"takeferry"}
    for key in providers or ["libtv"]:
        route = ROUTES[key]
        if route.connector in emitted:
            continue
        emitted.add(route.connector)
        if key == "comfy-local":
            fragment += '  comfy_local:\n    command: "comfy-mcp"\n    args: []\n    timeout: 180\n'
            continue
        url = route.endpoint
        if key == "tapnow" and tapnow_site == "ai":
            url = "https://mcp.tapnow.ai/api/agent-gateway/mcp/general/mcp"
        if key == "rhtv" and rhtv_site == "cn":
            url = "https://www.runninghub.cn/canvas-api/v1/mcp"
        fragment += f"  {route.connector}:\n    url: {json.dumps(url)}\n    timeout: 180\n"
        if key != "excalidraw":
            fragment += "    auth: oauth\n"
        if key == "canva":
            fragment += ('    oauth:\n      client_id: "${CANVA_CLIENT_ID}"\n'
                         '      client_secret: "${CANVA_CLIENT_SECRET}"\n      redirect_port: 27890\n')
    return fragment


def main(argv=None):
    parser = argparse.ArgumentParser(prog="takeferry", description="Direct a shot on the writer's own video canvases.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("serve", help="Start the stdio MCP server.")
    config = sub.add_parser("config", help="Print Hermes MCP settings for the platforms you select.")
    config.add_argument("--provider", nargs="+", action="extend", choices=list(ROUTES),
                        help="Default: local tools and LibTV. Choose one or more routes.")
    config.add_argument("--tapnow-site", choices=("ai", "media", "tv"), default="media")
    config.add_argument("--rhtv-site", choices=("ai", "cn"), default="ai")
    listing = sub.add_parser("catalog", help="Show supported canvases and the evidence each route can record.")
    listing.add_argument("--provider", choices=list(ROUTES))
    listing.add_argument("--mode", choices=list(MODES))
    listing.add_argument("--json", action="store_true")
    skill = sub.add_parser("skill", help="Export the directing skill, upstream guides and licenses as a ZIP.")
    skill.add_argument("--output", required=True, type=Path)
    board = sub.add_parser("board", help="Build a storyboard from a shot list and optional recorded takes.")
    board.add_argument("--shots", required=True, type=Path, help="JSON array of shot IDs and beats.")
    board.add_argument("--state", type=Path, help="Directory containing any takes to include.")
    board.add_argument("--format", choices=("canvas", "cards", "mermaid"), default="canvas")
    board.add_argument("--output", required=True, type=Path, help="New file for the editable board.")
    demo = sub.add_parser("demo", help="Rehearse one shot, two fixture canvases, a revision and a cut list offline.")
    demo.add_argument("--output", type=Path, help="An empty output directory. The default is a new temporary directory.")
    demo.add_argument("--canvas-tour", action="store_true", help="Also rehearse the external video connectors using synthetic receipts.")
    demo.add_argument("--json", action="store_true", help="Print the rehearsal summary as JSON.")
    options = parser.parse_args(argv)
    try:
        if options.command == "config":
            print(hermes_config(options.provider, options.tapnow_site, options.rhtv_site), end="")
        elif options.command == "catalog":
            data = catalog(options.provider, options.mode)
            if options.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                for route in data["routes"]:
                    print(f'{route["id"]:12} {route["name"]} ({route["mode"]})\n             {route["workflow"]}')
        elif options.command == "skill":
            print(export_skill(options.output))
        elif options.command == "board":
            shots = json.loads(options.shots.read_text(encoding="utf-8"))
            doc = Studio(options.state).storyboard(shots, options.format)["document"]
            body = doc if isinstance(doc, str) else json.dumps(doc, indent=2, ensure_ascii=False)
            options.output.parent.mkdir(parents=True, exist_ok=True)
            with options.output.open("x", encoding="utf-8") as stream:
                stream.write(body + "\n")
            print(options.output)
        elif options.command == "serve":
            serve(Studio())
        else:
            path = options.output or Path(tempfile.mkdtemp(prefix="takeferry-rehearsal-"))
            result = rehearse(path, canvas_tour=options.canvas_tour)
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
                if options.canvas_tour:
                    print("Canvas tour: eight external video routes, one shared storyboard, synthetic readbacks.")
                print("Editable shot board: rain-at-the-door.canvas")
                print("Canvas snapshots, take receipts and skill draft:", result["output"])
        return 0
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"TakeFerry: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
