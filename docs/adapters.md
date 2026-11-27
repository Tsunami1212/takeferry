# Adapter contract

A shot ID survives a platform change. A native canvas ID, reference node ID and destination video node belong to one provider and account. Pippit also binds operations to one team space. Keep native IDs as strings.

## Plan and submission

`takeferry_prepare` accepts a stable take ID and a brief. Use the MCP tool schema for the complete field list. The brief names the shot, provider, account, native target, model, final prompt, camera, sound, duration, ratio, timed cues and reference duties. A revision has the same shot ID and a finished parent take. A cross-platform comparison also identifies differences the writer should review.

A plan is one video submission. Repeated calls with the same ID and contents return the original plan. A change uses a fresh take ID. For Pippit, preparation checks the current model and native video node. The displayed digest includes the reviewed reference files' hashes. The submitter rechecks the account, parameters, native target and staged bytes, then reserves the take in SQLite before sending it to the provider.

| Checkpoint | Meaning | Recovery |
| --- | --- | --- |
| `planned` | The writer can inspect the frozen brief. | Submit only after approval. |
| `submitting` | One caller owns the dispatch. The provider may already have accepted it. | Look up the original task. Record its returned identity with `takeferry_receipt`. |
| `submitted` | The original provider receipt is stored. | Ask this task for its result. |
| `collected` | Pippit returned a matching successful run and a local original. | Bind the file to its native video node. |
| `uploading` / `uploaded` | Canvas upload started or its stable asset ID is known. | Recover an existing upload, or query the known asset until its video identity is available. |
| `binding` | The intended node edit may already have succeeded. | Read back the native asset IDs. Explicitly retry the same edit only after inspecting an unconfirmed write. |
| `ready` | The take has the evidence its route supports, such as media on a node or a completed job asset. | Compare, select, branch or export the take. |

The LibTV path uses its official remote MCP in the Hermes session. On success, the caller records observed native readback against the reserved take. The Pippit bridge performs the query, upload, native binding and readback itself. [LibTV directions](../skills/takeferry/references/libtv.md) · [Pippit directions](../skills/takeferry/references/pippit.md)

## Direct calls from Hermes to another provider

The provider catalog describes the type of result each route can prove. For a hosted or local external connector, a reviewed brief includes `remote.server`, `remote.tool`, `remote.arguments` and `remote.snapshot`. Bind the displayed plan and freshly observed inputs with `takeferry_remote_claim`, then call the official MCP through Hermes once. The returned upstream job becomes `task_id` in `takeferry_receipt`.

`takeferry_remote_finish` checks the account, optional team, task and reviewed destination. It records evidence reported by Hermes. Node and workflow routes require a canvas and node in advance. Canvas-delivery routes can record a provider-assigned canvas at completion, or constrain the run to a known canvas in advance. Asset routes omit canvas and node. Each route can later attach a verified local original for export. Auth sessions, secrets and raw input media belong outside the ledger. [Remote shooting guide](../skills/takeferry/references/remote-shoots.md)

## Contributing another provider

Implement native canvas discovery, source-node mapping, a draft video node, model and cost inspection, one authorized submit, receipt recovery and node readback. Send the same shot to both providers using their own native IDs. Include a synthetic contract test for a missing media result and a duplicate submit. Publish the official interface you used and the date of any real-account check. Mark generation-only connections separately until a writer can open the target canvas and find the clip on the intended node.
