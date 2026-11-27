# Sources and licenses

TakeFerry's original code, writing, original storyboards and generated rehearsal media are distributed under the [Apache License 2.0](LICENSE). Copyright 2026 TakeFerry contributors. The source for the bundled picture sequences, rain and key sound is [make_storyboards.py](examples/rainy-door/make_storyboards.py).

Hermes Agent is a separate program under its upstream MIT license. LibTV supplies its official Remote MCP. Pippit supplies the native media CLI and Canvas SDK used by the optional bridge. These programs are obtained from their publishers. Platform access, service terms and billing follow the respective account. [Hermes license](https://github.com/NousResearch/hermes-agent/blob/main/LICENSE) · [LibTV connector](https://github.com/liblib-ai/marketplace) · [Pippit CLI](https://github.com/Pippit-dev/cli)

Eight third-party skill guides, their supporting references and their upstream MIT license texts ship under `skills/takeferry/references/upstream/`. The original publishers are Comfy-Org, Freepik/Magnific and Obsidian. The checked-in manifest maps each redistributed file to its source path, Git commit and SHA-256. The Figma and Miro guides are accessed from their publishers. [Bundled skill index](skills/takeferry/references/skill-library.md) · [Manifest](skills/takeferry/references/upstream/index.json)

The bridge was written against Pippit's published [canvas contract](https://github.com/Pippit-dev/cli/blob/2d4f74b63341f8d1c7f1c8b9206672b0a0b951d9/skills/xyq-nest-skill/commands/canvas.md). Tool and parameter names describe the respective interfaces. Provider names identify the services with which the adapters communicate.
