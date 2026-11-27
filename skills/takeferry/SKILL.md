---
name: takeferry
description: Help a screenwriter build a storyboard, try the same shot on different AI video platforms and revise a selected take. Use connected native canvases, saved ComfyUI workflows, media tools and review boards.
---

# TakeFerry

Work in the writer's language. Start with English when they have no preference. Use the writer's own Hermes profile and the connected account they chose.

Ask for a scene, or use the one already in the conversation. Offer a short shot list tied to lines from the script. Let the writer pick a shot. The first audition is one take on one platform unless they ask for more.

## Choose where the work belongs

Call `takeferry_canvas_catalog` and inspect the tools available to this Hermes session. If the writer wants to plan a shot or send a team an editable board, use [storyboards](references/storyboards.md). A planning board can be built before any video is generated.

For video, use the requested platform and check what it can return. LibTV, Pippit and Magnific Spaces can identify media on a target node. Comfy Cloud and ComfyUI Local can identify a saved graph and its job output. TapNow and rhTV can return a canvas and an asset. Runway, Krea and Weave can supply a generated asset. Describe the evidence the writer can open. Choose reference and camera methods from the [canvas skill library](references/skill-library.md).

## Build the shot

1. Read the chosen project and its existing nodes. Identify reference images by native ID. Give each a job, such as character identity, light, opening frame or costume. Ask about a reference only when its role or destination is ambiguous.
2. Keep the shot duration, timed action, camera and sound as separate decisions. “Five seconds, she turns at two” means five seconds of video. A request to keep rain and a file containing recorded rain are separate inputs.
3. Inspect the account's current model list and the selected model's input contract. Choose a model that accepts the required inputs. If a direction can only go in prose, tell the writer. Show any reference or setting the target cannot accept.
4. For a native graph, build the workflow on the platform's own canvas. Reuse approved source nodes and branch a fresh video node for a new take. Connect native references and write the final prompt. If the writer supplied a verbatim prompt, keep it. Read back the target and its connections.
5. Call `takeferry_prepare` with one stable take ID. Show the writer the platform and account, model, final prompt, reference roles, actual parameters, unit count and quoted cost. Mark unavailable prices as unknown. A changed plan gets a new ID. Checking a price does not change the plan.
6. Obtain the writer's consent for the displayed paid run. Follow the provider guide to submit once. The approval digest binds a review to its contents. Hermes is responsible for getting consent. If a write times out, recover using the original receipt or the native canvas.
7. Give the writer the returned canvas link when available and identify the result node. A successful task, a downloaded clip and a bound result have different receipts. Check the native node, saved workflow output, canvas asset or job output that the chosen route supports.

Use the dedicated [LibTV](references/libtv.md) or [Pippit](references/pippit.md) procedure for those providers. Use [remote shoots](references/remote-shoots.md) for the other video connectors. Hermes may add a server prefix to the tool names. Use the names actually exposed in the active session.

## Compare and revise

“Try it on the other platform” keeps the shot ID, timing, references and camera. Get permission for any reference the second platform will receive. Resolve fresh target-side node IDs, record differences and ask before spending that platform's credits. “Try a push instead” keeps the provider and changes the camera. Give a revision its own take ID and set `parent` to the finished take the writer selected. Use `takeferry_compare` to resolve titles or version letters that could refer to more than one take.

Record the writer's choice with `takeferry_select`. The in and out points travel in the cut list. `takeferry_export` packs each available full-length original alongside that list. Keep the originals on their native canvases.

## Remember a method

When the writer wants to reuse a method, ask which project or model it applies to if that is unclear. Use `takeferry_skill_draft` on the selected take. Remove cast names, account IDs, private media and anything specific to this one job. Use Hermes's native `skill_manage` to create or update a separate private skill with the reviewed steps. In a new session, use `skill_view` and apply it to new material. Check current provider capabilities again. Leave one-shot notes in the shot record and keep personal preferences in the appropriate Hermes profile.
