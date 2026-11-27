# What has been tested

This page covers the public TakeFerry source preview dated 2026-11-27. Testing the rehearsal uses no platform credits.

| Path | Evidence for this release |
| --- | --- |
| Free rehearsal | The source checkout and the standalone Python app each built four takes on two simulated canvases, recorded a parent revision and exported the selected original with its cut list. The bundled video and audio streams are both five seconds long. |
| MCP transport | The official Python MCP client 1.26.0 initialized the stdio server, negotiated protocol 2025-11-25, discovered 19 tools and read a shot. The standard-library test suite also checks error responses and notifications. |
| LibTV | Anonymous metadata discovery identified the official endpoint and its OAuth authorization server. The rehearsal exercises local reservation, receipt and readback recording. A paid run and native node readback from this public release remain unverified. |
| Pippit | Contract fixtures exercise account and team binding, a native video node, the selected model and references, one submission, collection, media upload and a fresh read of both media IDs. These checks use synthetic command responses. Live accounts, credit deductions and video binding on a real Pippit canvas remain unverified. |
| Hermes skill | The repository ships the English skill and references. The rehearsal creates a separate reusable skill draft from the selected take. Saving and recalling that draft in a real Hermes profile remains unverified for this release. |
| Python and release package | The offline suite ran locally on Python 3.9 and 3.12. GitHub runs it on Linux and macOS and exercises the downloadable application format. [CI runs](https://github.com/Tsunami1212/takeferry/actions/workflows/check.yml) |

## Reproduce the checks

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py dist/takeferry.pyz
python3 dist/takeferry.pyz demo --output rehearsal
python3 -m zipfile -t rehearsal/rain-at-the-door.zip
```

If the official Python MCP client is already available, run `python3 scripts/verify_mcp_client.py --app dist/takeferry.pyz`. To explore a completed rehearsal conversationally, set the local MCP server's `TAKEFERRY_STATE_DIR` to the rehearsal's `state/` directory and try the [read-only questions](../examples/rainy-door/evaluation.xml).

For a live verification, authorize one take in your own account. Open the provider's original canvas, check the reference links and the actual result node, and compare the receipt to the task in that account. Repeat on the second platform for the same shot. Only move a capability into the live-tested column after that check. Leave private media, IDs and receipts in the operator's copy.
