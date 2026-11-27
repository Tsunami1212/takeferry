# Shoot through another MCP server

Use the tools exposed in this Hermes session. `takeferry_canvas_catalog` describes the published contract for each route. Check what the signed-in server offers today. Keep the platform account, team, reference duties, timing and intended output visible to the writer. For a comparison, get permission to send the selected references to the second platform.

## Review one run

1. Read the account and destination. Inspect the model or node catalog. Put the prompt, references and supported settings on the selected graph when the route exposes one. Include any paid intermediate work in the review. One TakeFerry approval covers one video submission.
2. Call `takeferry_prepare` with a new take ID, the shared shot ID and the selected parent for a revision. Its `remote` field identifies the `server` from the TakeFerry configuration. `tool` is the exact upstream tool exposed to Hermes. `arguments` are the final non-secret inputs to that tool. `snapshot` contains the observed `account`, the same `team` if present, `video_outputs: 1`, source asset identities and relevant graph settings. Use stable asset IDs. Keep tokens, expiring signed URLs and raw media outside the ledger. If a tool cannot run from safe, stable inputs, explain the limitation before spending.
3. Show the writer the platform, model, reference roles, settings, expected count and price or unknown price. After consent, reread the inputs and call `takeferry_remote_claim` with the approval and current remote plan. A changed reference, argument or graph needs a new review. Submit the returned call once when `dispatch` is true. On a previous claim, look up the original job.
4. Record the actual job identifier as `task_id` with `takeferry_receipt`. Poll that job to completion. Call `takeferry_remote_finish` with the same account, team if used, task ID and stable output identity. Supply only the canvas or node evidence described below. If the original job or output cannot be identified, keep the take pending. An optional local original goes under the private state media directory.
5. Compare or select this take under the original shot. A retry uses the existing receipt. A creative change gets a fresh take ID.

The Python service reserves the take and checks reported identities. Hermes makes the upstream call and reads the evidence from the signed-in server.

## Magnific Spaces

Read `spaces_state` and `spaces_node_types_search`. Create a new target node for this take and wire its reference inputs with `spaces_add_connection`. Read the selected nodes, then use `simulate_spaces` on the intended run. Review the reachable graph for extra outputs or paid stages. After approval, submit through `spaces_run`, follow `spaces_run_status` and retrieve the video asset from the same node using `spaces_get_nodes`. Use the Space and node IDs in the brief and at finish. For character and camera work, see the [bundled production skills](skill-library.md). [Provider's Spaces tool reference](https://docs.magnific.com/modelcontextprotocol)

## Comfy Cloud and ComfyUI Local

On Cloud, search templates and node schemas before wiring the video graph. Save a distinct workflow with the provider, obtain its workflow ID and canvas link, and identify its output node. Reserve the approved run, then execute the saved graph. With its prompt ID, inspect the job's outputs and match the chosen node. Return the saved graph link separately. The recorded evidence is a workflow job output. Use the [Comfy node guide](upstream/comfy/search-nodes/guide.md) and [Cloud tools](https://github.com/Comfy-Org/docs/blob/main/agent-tools/mcp.mdx).

For `comfy-local`, use the writer's existing ComfyUI instance and `comfy-mcp` executable. Read `server_info`, validate against the local nodes and models, and keep a reopenable workflow file with a stable identifier. Record its identity, output node and a digest of the exact graph in the review. Run the validated graph with `run_workflow` and collect from the same job with `fetch_outputs`. Set the account field to an agreed non-secret label for that local instance. Local GPU compute and metered partner nodes have different costs. Review partner charges before passing the provider's spending flag. [Local MCP tools](https://github.com/Comfy-Org/comfy-mcp)

## TapNow and RunningHub rhTV

Use the site and account the writer uses in the browser. On TapNow, identify the team chosen during OAuth, list recent canvases, inspect video models and obtain the Tapies estimate. Use the single video operation for a one-take approval. On rhTV, discover the account's current canvas, media and generation schemas after authorization. Use the provider's own reference IDs.

Set `canvas` in the brief if the tool accepts a chosen destination. If the provider assigns the canvas when it returns the video, leave that field absent and tell the writer. At finish, identify the completed asset on the returned canvas. A canvas URL alone provides no media identity. A result that can only be found in a task response remains pending on this route. [TapNow connector](https://docs.tapnow.media/en/docs/mcp/use-tapnow-in-other-agents) · [rhTV connector](https://rhtv.runninghub.ai/projects/mcp)

## Figma Weave, Runway and Krea

These ledger routes track a completed media asset in the original account. Omit canvas and node from the brief and the finish call. Check what the chosen video model actually accepts, and record the job and asset IDs from the provider's response. The result can be compared against a native canvas take. If your client returns only a temporary download URL, keep looking for a stable output identity.

For Weave, check the active workspace, inspect the published tool's inputs and review its Weave credit cost. Some clients also expose graph-authoring tools. Use Figma's authoring guide and inspect the actual tool list before attempting a graph edit. The public guidance and rollout differ by client. [Weave running guide](https://help.weavy.ai/en/articles/16202764-running-weave-tools-and-models-from-external-agents-mcp) · [Figma's graph-authoring skill](https://github.com/figma/mcp-server-guide/blob/5e4790847aedd4312fff65a11f7695c9c9382be0/skills/figma-weave-workflows/SKILL.md)

Runway and Krea expose their own authorized media tools. Use their live catalogs to choose a model and upload only the approved references. When the writer needs editable native nodes, use a node or workflow route. [Runway connector](https://help.runwayml.com/hc/en-us/articles/51931843164691-Connecting-to-Runway-MCP) · [Krea MCP](https://www.krea.ai/mcp)
