# Pick a canvas for the shot

If you want to move the reference connections after a shoot, choose a native node or a saved workflow. If you want to compare the look of two models, a completed media asset may be enough. For notes before the shoot, start with a board. TakeFerry keeps one shot ID across those decisions.

| Route in `config --provider` | What the writer can open or check | Official interface |
| --- | --- | --- |
| `libtv` | The result on the chosen native video node. Hermes reports its readback. | [LibTV MCP](https://github.com/liblib-ai/marketplace) |
| `pippit` | The video uploaded and bound to the intended Pippit node. The local bridge checks both media IDs. | [Pippit Canvas CLI and SDK](https://github.com/Pippit-dev/cli/blob/main/skills/xyq-nest-skill/commands/canvas.md) |
| `magnific` | A Magnific Space with its input nodes, connections and video node. The connector can estimate and run the workflow. | [Magnific Spaces tools](https://docs.magnific.com/modelcontextprotocol) |
| `comfy` | A reopenable Comfy Cloud graph and the output of a particular node in its generation job. | [Comfy Cloud MCP](https://github.com/Comfy-Org/docs/blob/main/agent-tools/mcp.mdx) |
| `comfy-local` | A workflow file on the writer's ComfyUI instance and the original job's output. The official local MCP and ComfyUI must already be available. | [ComfyUI Local MCP](https://github.com/Comfy-Org/comfy-mcp) |
| `tapnow` | The resulting video on the writer's TapNow canvas. Inspect the model inputs and Tapies estimate before running. | [TapNow connector](https://docs.tapnow.media/en/docs/mcp/use-tapnow-in-other-agents) |
| `rhtv` | The generated asset on the RunningHub rhTV canvas in the authorized account. | [International site](https://rhtv.runninghub.ai/projects/mcp) · [Chinese site](https://rhtv.runninghub.cn/projects/mcp) |
| `weave` | A Figma Weave tool or model output in the active workspace. Only use graph editing when the connected server exposes its authoring tools. | [Weave MCP guide](https://help.weavy.ai/en/articles/16202764-running-weave-tools-and-models-from-external-agents-mcp) · [Figma's authoring skill](https://github.com/figma/mcp-server-guide/blob/5e4790847aedd4312fff65a11f7695c9c9382be0/skills/figma-weave-workflows/SKILL.md) |
| `runway`, `krea` | The original generation job and its finished video. These ledger entries identify the media asset. | [Runway MCP](https://help.runwayml.com/hc/en-us/articles/51931843164691-Connecting-to-Runway-MCP) · [Krea MCP](https://www.krea.ai/mcp) |
| `figjam` | An editable shot diagram made from Mermaid. Uses the same Figma connection as Weave. | [Figma MCP tools](https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/) |
| `miro` | Editable cards and connections in the selected Miro board area. Use the current Canvas Composer tool family. | [Miro MCP tools](https://developers.miro.com/docs/miro-mcp-tools) |
| `canva` | An editable shot deck. Preview and commit changes through Canva's editing transaction. | [Canva MCP editing tools](https://www.canva.dev/docs/apps/mcp/tools/) |
| `excalidraw` | A diagram and checkpoint in a client with an MCP Apps viewer. | [Excalidraw MCP](https://github.com/excalidraw/excalidraw-mcp) |
| `json-canvas` | A local `.canvas` file containing shots, reference duties, revision edges and selected edit points. | [JSON Canvas 1.0](https://jsoncanvas.org/spec/1.0/) |

## Connect the platforms you use

```sh
python3 -m takeferry catalog
python3 -m takeferry config --provider magnific comfy miro
python3 -m takeferry config --provider tapnow rhtv --tapnow-site ai --rhtv-site cn
```

Paste the printed entries into the active Hermes profile and complete each selected provider's authorization. The local TakeFerry server appears once in every configuration. The default command still prints the local server and LibTV. Pippit uses that local server. FigJam and Weave share one Figma entry. The commands print configuration and leave account settings and installed software in your hands. [Hermes setup](setup.md)

Choose the TapNow site you actually use. The `.tv` site shares the `.media` connector. rhTV has separate international and Chinese URLs. Use the same site for authorization and canvas lookup. [TapNow site map](https://docs.tapnow.media/en/docs/mcp/add-a-custom-connector)

For Canva's developer MCP, register your app and a matching redirect URL in Canva. The printed profile uses `CANVA_CLIENT_ID` and `CANVA_CLIENT_SECRET` from the Hermes environment. Its default callback is `http://localhost:27890/callback`. Use the port you registered. Excalidraw needs an MCP Apps viewer to show an interactive board. A local ComfyUI setup needs the official `comfy-mcp` executable on the Hermes host's path. Partner nodes can incur charges on a locally run graph. [Canva setup](https://www.canva.dev/docs/apps/quickstart/) · [Hermes OAuth settings](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) · [Local Comfy prerequisites](https://github.com/Comfy-Org/comfy-mcp)

## Make a board before your first render

```sh
python3 -m takeferry board --shots takeferry/data/rainy-door/shot-list.json --output rain.canvas
```

Open the file in Obsidian or a JSON Canvas editor. To include recorded takes, pass `--state PATH` for the private state directory used on that shoot. For FigJam use `--format mermaid --output rain.mmd`. For a review deck use `--format cards --output rain.json`. In Hermes, call `takeferry_storyboard` with the same shot list and the format you need. The tool returns a local document. Sharing it with a connected board is a separate action.

The publisher guides for Comfy Cloud, Magnific and Obsidian ship in the package. Export the complete directing skill with `python3 -m takeferry skill --output takeferry-skill.zip`. [Upstream skill library](../skills/takeferry/references/skill-library.md) · [Verification status](verification.md)
