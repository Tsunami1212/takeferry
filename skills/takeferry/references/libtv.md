# LibTV native MCP

Connect the official remote server over OAuth in the writer's Hermes profile. The authenticated tool descriptions are the source for parameter names and the actions the current account can take. [Official LibTV connector](https://github.com/liblib-ai/marketplace)

1. Read the user's selected project or create one when requested. Inspect its workflow and native node IDs. Use model discovery and the model detail tool to check the inputs for this particular job.
2. Build the source references and a dedicated destination video node on that canvas. Use the service's preparation mode when it exposes one. Include potentially chargeable intermediate image generation in the review. Read the native graph to check the destination, model, prompt and reference links.
3. Reserve the reviewed take with `takeferry_libtv_claim` after the writer approves. The response contains `dispatch`. A true value grants one dispatch in the TakeFerry ledger. A false value means the reservation already exists. Retrieve the original task rather than issuing another generation.
4. Use the official LibTV MCP action for the approved video node. Use the account, project and model from that review and pass an idempotency key if the tool provides one. Record its actual task ID with `takeferry_receipt` using `{"task_id":"<returned ID>"}`. If the first request had an uncertain outcome, inspect the original canvas and task before recording a recovered receipt.
5. Query the original task. Once it succeeds, read the native result node and inspect its media. Pass the observed canvas ID, node ID, task ID and asset ID to `takeferry_libtv_finish`. An optional local original can be included from the TakeFerry state directory's `media/` folder. A take with only a remote asset still appears in the cut list.

Hermes makes the official remote call directly with the writer's OAuth session. TakeFerry records the readback supplied by that session as `reported_native_readback`. A local reservation can prevent a duplicate in this workflow. Other clients of the same LibTV account have their own controls.
