# TakeFerry

TakeFerry lets a screenwriter direct a shot in Hermes and open the resulting workflow on the video platform's own canvas. It connects to LibTV's official MCP server and provides an MCP bridge for Pippit's native canvas tools.

> Use A for An's face and B for the light. Five seconds, vertical. A key turns behind her at two seconds. Keep the rain. Give me one locked shot first.

Hermes helps choose a model, writes the prompt and connects the references. You see the account, creative changes and cost before you approve a generation. You can then try the same shot on another platform or change one camera move. Each take keeps its parent and its original canvas node.

[简体中文](README.zh-CN.md) · [Connect Hermes](docs/setup.md) · [What has been tested](docs/verification.md)

![Two illustrated takes of An at a doorway, one locked and one pushing in](examples/rainy-door/preview.gif)

*These five-second storyboards come with the offline example. The two columns show the camera choices.*

## Try the rainy-door scene

With Python 3.9 or later, download `takeferry.pyz` from the [release](https://github.com/Tsunami1212/takeferry/releases/tag/v0.1.0-alpha.1) and run it.

```sh
python3 takeferry.pyz demo --output rainy-door-demo
```

Or run the same example from source.

```sh
git clone https://github.com/Tsunami1212/takeferry.git
cd takeferry
python3 -m takeferry demo --output rainy-door-demo
```

Open `rainy-door-demo/rain-at-the-door.zip`. The original is five seconds long. In `cut-list.csv`, the writer chose seconds 1.0 to 4.5 of the slower push. Next to the ZIP, `canvases.json` shows the reference links and resulting media nodes on two simulated canvases. `takes.json` records the four takes. `branch-camera-movement/SKILL.md` is a draft of the method the writer wanted to keep.

The rehearsal runs offline with bundled media and costs zero credits. It needs neither Hermes nor a platform login.

## Use your own canvas

Install the directing skill in your Hermes profile. Run `python3 -m takeferry config` (or `python3 takeferry.pyz config`) to print the MCP entries for the local tool and LibTV. Then authorize the platform you want to use. Pippit also needs its official CLI and Canvas SDK entry on the host running the bridge. [Setup and credentials](docs/setup.md)

Start by pasting a scene into Hermes. Pick a shot from the proposed breakdown. The first run is one take on one platform. For a comparison, say “try that same shot on the other platform.” For a revision, say “keep her face and the light, but slow the push on the take I chose.”

| Provider | Where the work happens | How the result is checked |
| --- | --- | --- |
| LibTV | Hermes uses the official remote MCP to prepare and run a native canvas node. | Hermes reads the task and node on LibTV, then records their IDs and the observed media asset in TakeFerry. |
| Pippit / 小云雀 | TakeFerry's local MCP calls Pippit's official media CLI and Canvas SDK in the selected account and team space. | The bridge collects the original run, attaches its media to the intended node, and reads both media IDs back from Pippit. |

Live generation uses credits on the selected platform. When a platform doesn't quote a price, the skill asks you to approve a stated number of generations at an unknown price. The language model you configure in Hermes has its own billing.

When you want to keep a method, ask Hermes to save it as a private skill. For example, it can remember to reuse the approved face and light references before branching a camera move. Your next project can use that method with its own cast and material. [Directing skill](skills/takeferry/SKILL.md)

## Release status

This is a source preview. The offline rehearsal covers both provider paths, and the local MCP server has been exercised with the official Python MCP client. The public checkout has not been used for a paid generation on either platform. [Verification details](docs/verification.md)

Run the tests with `python3 -m unittest discover -s tests -v`. The core, the MCP server and the example use the Python standard library. [Contributor guide](CONTRIBUTING.md) · [Adapter notes](docs/adapters.md) · [Apache-2.0 license](LICENSE)
