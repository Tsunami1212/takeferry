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
| `ready` | The returned media was associated with the intended node. | Compare, select, branch or export the take. |

The LibTV path uses its official remote MCP in the Hermes session. On success, the caller records observed native readback against the reserved take. The Pippit bridge performs the query, upload, native binding and readback itself. [LibTV directions](../skills/takeferry/references/libtv.md) · [Pippit directions](../skills/takeferry/references/pippit.md)

## Contributing another provider

Implement native canvas discovery, source-node mapping, a draft video node, model and cost inspection, one authorized submit, receipt recovery and node readback. Send the same shot to both providers using their own native IDs. Include a synthetic contract test for a missing media result and a duplicate submit. Publish the official interface you used and the date of any real-account check. Mark generation-only connections separately until a writer can open the target canvas and find the clip on the intended node.
