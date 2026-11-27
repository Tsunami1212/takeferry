# What has been tested

These checks cover v0.1.0-alpha.2 on 2026-11-27. The example media are bundled storyboards. Testing used zero platform credits.

| Path | Evidence for this release |
| --- | --- |
| Free rehearsal | The source checkout and the standalone Python app each built four takes on two simulated canvases, recorded a parent revision and exported the selected original with its cut list. The bundled video and audio streams are both five seconds long. |
| MCP transport | The official Python MCP client 1.26.0 initialized the stdio server, negotiated protocol 2025-11-25, discovered 23 tools, read a shot, queried the Magnific route and built an editable storyboard. The standard-library test suite also checks error responses and notifications. |
| LibTV | Anonymous metadata discovery identified the official endpoint and its OAuth authorization server. The rehearsal exercises local reservation, receipt and readback recording. A paid run and native node readback from this public release remain unverified. |
| Pippit | Contract fixtures exercise account and team binding, a native video node, the selected model and references, one submission, collection, media upload and a fresh read of both media IDs. These checks use synthetic command responses. Live accounts, credit deductions and video binding on a real Pippit canvas remain unverified. |
| Expanded canvas tour | The portable app rehearsed all ten video routes. Its twelve synthetic takes include node readbacks, saved-workflow outputs, assets on provider canvases and media-only jobs. The board contains 15 cards and 14 edges. One shared clip stands in for the eight additional runs. |
| Public remote MCP access | Anonymous initialization requests reached the official OAuth challenges for LibTV, Magnific, Comfy Cloud, TapNow, rhTV, Figma, Miro, Canva, Runway and Krea. Both published TapNow endpoints and both rhTV sites were checked. These responses confirm where login starts. Account-specific tools, actual rendering and billing still need authorized testing. |
| Excalidraw | The official Python client initialized the hosted server, listed five tools and called the public `read_me` tool successfully. Interactive rendering and checkpoint edits have not been tested in an MCP Apps viewer. |
| Boards and local software | The local JSON Canvas file, stable card IDs, revision edges, selected edit points and Mermaid output were tested offline. Local ComfyUI execution and authenticated Figma, Miro or Canva board writes still need operator testing. |
| Skill distribution | Eight upstream guides and their supporting files match the pinned SHA-256 manifest. The skill ZIP exports from source, the portable app and the unpacked wheel layout. The upstream MIT texts are included. |
| Hermes skill | The repository ships the English skill and references. The rehearsal creates a separate reusable skill draft from the selected take. Saving and recalling that draft in a real Hermes profile remains unverified for this release. |
| Python and release package | The offline suite ran locally on Python 3.9 and 3.12. GitHub runs it on Linux and macOS and exercises the downloadable application format. [CI runs](https://github.com/Tsunami1212/takeferry/actions/workflows/check.yml) |

## Reproduce the checks

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py dist/takeferry.pyz
python3 dist/takeferry.pyz demo --canvas-tour --output rehearsal
python3 dist/takeferry.pyz skill --output rehearsal-skill.zip
python3 -m zipfile -t rehearsal/rain-at-the-door.zip
```

If the official Python MCP client is already available, run `python3 scripts/verify_mcp_client.py --app dist/takeferry.pyz`. To explore a completed rehearsal conversationally, set the local MCP server's `TAKEFERRY_STATE_DIR` to the rehearsal's `state/` directory and try the [read-only questions](../examples/rainy-door/evaluation.xml) with the default four-take demo. The [canvas tour questions](../examples/rainy-door/canvas-evaluation.xml) use the twelve-take tour.

For a live verification, authorize one take in your own account. Open the result described by that route and compare its task, asset and destination with the recorded receipt. For a node route, also inspect the reference connections and actual result node. Repeat on the second platform for the same shot. Only move a capability into the live-tested column after that check. Leave private media, IDs and receipts in the operator's copy.
