"""Published connector contracts. Remote tools are called in the writer's Hermes session."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Route:
    name: str
    mode: str
    connector: str
    endpoint: str
    guide: str
    source: str
    tools: tuple
    workflow: str


FIGMA = "https://mcp.figma.com/mcp"
ROUTES = {
    "libtv": Route("LibTV", "node", "libtv", "https://mcp.liblib.tv/mcp", "libtv.md",
        "https://github.com/liblib-ai/marketplace", (),
        "Discover the official graph tools. Prepare the native target, then check the task and its media on that node."),
    "pippit": Route("Pippit / Xiaoyunque", "node", "takeferry", "", "pippit.md",
        "https://github.com/Pippit-dev/cli/blob/main/skills/xyq-nest-skill/commands/canvas.md",
        ("takeferry_pippit_catalog", "takeferry_pippit_submit", "takeferry_pippit_collect", "takeferry_pippit_bind"),
        "Use the local bridge with the account's official CLI and Canvas SDK. Bind the collected video to the reviewed node."),
    "magnific": Route("Magnific Spaces (Freepik)", "node", "magnific", "https://mcp.magnific.com/mcp",
        "remote-shoots.md", "https://docs.magnific.com/modelcontextprotocol",
        ("spaces_state", "spaces_node_types_search", "spaces_create_node", "spaces_add_connection", "simulate_spaces",
         "spaces_run", "spaces_run_status", "spaces_get_nodes"),
        "Build the shot in an editable Space. Estimate its run, inspect the finished run and reread the chosen video node."),
    "comfy": Route("Comfy Cloud", "workflow", "comfy", "https://cloud.comfy.org/mcp", "remote-shoots.md",
        "https://github.com/Comfy-Org/docs/blob/main/agent-tools/mcp.mdx",
        ("search_templates", "get_template_schema", "search_nodes", "get_node", "save_workflow",
         "get_workflow_canvas_url", "run_saved_workflow", "get_job_status"),
        "Save a graph the writer can reopen. Match the completed prompt to its output node and media in job history."),
    "comfy-local": Route("ComfyUI Local", "workflow", "comfy_local", "", "remote-shoots.md",
        "https://github.com/Comfy-Org/comfy-mcp", ("server_info", "validate_workflow", "run_workflow", "fetch_outputs"),
        "Open a saved workflow on the writer's ComfyUI instance. Validate it against installed nodes. Local compute and metered partner nodes have different costs."),
    "tapnow": Route("TapNow", "canvas", "tapnow", "https://mcp.tapnow.media/api/agent-gateway/mcp/general/mcp",
        "remote-shoots.md", "https://docs.tapnow.media/en/docs/mcp/use-tapnow-in-other-agents", (),
        "Discover recent canvases, model inputs, Tapies estimates, video submission and result lookup. Read the asset on its canvas."),
    "rhtv": Route("RunningHub rhTV", "canvas", "rhtv", "https://www.runninghub.ai/canvas-api/v1/mcp",
        "remote-shoots.md", "https://rhtv.runninghub.ai/projects/mcp", (),
        "Discover the official canvas, reference and generation tools for the authorized site. Find the returned asset on the destination canvas."),
    "weave": Route("Figma Weave", "asset", "figma", FIGMA, "remote-shoots.md",
        "https://help.weavy.ai/en/articles/16202764-running-weave-tools-and-models-from-external-agents-mcp",
        ("weave_list_tools", "weave_run_tool", "weave_run_model"),
        "Inspect the active workspace and the published tool or model inputs. Record a completed Weave output. Graph editing depends on the tools exposed to this account."),
    "runway": Route("Runway", "asset", "runway", "https://mcp.runwayml.com/mcp", "remote-shoots.md",
        "https://help.runwayml.com/hc/en-us/articles/51931843164691-Connecting-to-Runway-MCP", (),
        "Inspect current models and reference support. Record the completed generation from the connected Runway account."),
    "krea": Route("Krea", "asset", "krea", "https://api.krea.ai/mcp", "remote-shoots.md",
        "https://www.krea.ai/mcp", (),
        "Inspect the available video tools. Keep the job and asset identity returned by the connected Krea account."),
    "figjam": Route("FigJam", "board", "figma", FIGMA, "storyboards.md",
        "https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/",
        ("generate_diagram",), "Send the storyboard's Mermaid diagram to FigJam. Read the file or diagram back and keep its link."),
    "miro": Route("Miro", "board", "miro", "https://mcp.miro.com/", "storyboards.md",
        "https://developers.miro.com/docs/miro-mcp-tools",
        ("canvas_get_canvas_composer_skill", "canvas_read_as_svg", "canvas_create_from_svg", "canvas_update_from_svg"),
        "Use the live Canvas Composer instructions to place shot cards on a board, then read back the affected area."),
    "canva": Route("Canva", "board", "canva", "https://api.canva.com/connect/v1/mcp", "storyboards.md",
        "https://www.canva.dev/docs/apps/mcp/tools/",
        ("start-editing-transaction", "perform-editing-operations", "commit-editing-transaction"),
        "Lay out a shot per page in an editable design. Review the transaction before committing the writer's changes."),
    "excalidraw": Route("Excalidraw", "board", "excalidraw", "https://mcp.excalidraw.com/mcp", "storyboards.md",
        "https://github.com/excalidraw/excalidraw-mcp", ("read_me", "create_view"),
        "Use the server's element schema to draw an editable shot map in an MCP Apps viewer. Keep its checkpoint for revisions."),
    "json-canvas": Route("Obsidian / JSON Canvas", "file", "takeferry", "", "storyboards.md",
        "https://jsoncanvas.org/spec/1.0/", ("takeferry_storyboard",),
        "Export local, editable shot cards with reference and revision edges. Open the .canvas file in Obsidian."),
}

# These native submission tools have published names. Other servers expose their
# generation schemas after sign-in and must be inspected in the Hermes session.
SUBMIT_TOOLS = {
    "magnific": ("spaces_run",),
    "comfy": ("run_saved_workflow", "submit_workflow"),
    "comfy-local": ("run_workflow",),
    "weave": ("weave_run_tool", "weave_run_model"),
}

MODES = {
    "node": "Media read back on the reviewed native node.",
    "workflow": "Media on a job output from the saved workflow.",
    "canvas": "A completed media asset found on the provider canvas.",
    "asset": "A completed provider media asset.",
    "board": "Editable storyboard or review items.",
    "file": "A portable JSON Canvas storyboard.",
}
RENDERERS = tuple(key for key, route in ROUTES.items() if route.mode in ("node", "workflow", "canvas", "asset"))
HOST_RENDERERS = tuple(key for key in RENDERERS if key not in ("libtv", "pippit"))


def catalog(provider=None, mode=None):
    return {"routes": [dict(asdict(route), id=key, evidence=MODES[route.mode])
                       for key, route in ROUTES.items()
                       if (provider is None or key == provider) and (mode is None or route.mode == mode)]}
