# TakeFerry

TakeFerry is an open-source agent for screenwriters who want to try the same shot on different AI video platforms. Paste a scene into your own Hermes and choose a shot from the breakdown. TakeFerry uses MCP to build the workflow for that shot on your LibTV or Pippit canvas.

> Use image A for her face and image B just for the light. Five seconds, vertical. Have her turn at two seconds when the key clicks. Keep the sound of the rain. Start with a locked shot on LibTV.

On LibTV, TakeFerry picks a model that accepts both images, writes the prompt, and connects A and B to a video node. You can open the canvas and edit what it built. You see the account, model, final prompt and quoted cost before you approve one take with your LibTV credits. If LibTV hasn't quoted a price, TakeFerry says so.

After watching it, you can say, “Try the same locked shot on Pippit.” TakeFerry rebuilds the shot on your Pippit canvas with the references you approve. It explains any differences and asks before using your Pippit credits. Or stay on LibTV and say, “Keep this one. Try a slow push-in.” The new take gets its own node.

Tell Hermes when a method is worth keeping. “Next time I change the camera move, reuse the face and lighting references I approved.” TakeFerry drafts the steps for your own Hermes to save as a private skill. [Directing skill](skills/takeferry/SKILL.md)

## Try the rainy-door scene

Try the scene offline on two simulated canvases. The rehearsal uses bundled storyboards and costs zero credits. With Python 3.9 or later, download `takeferry.pyz` from the [release](https://github.com/Tsunami1212/takeferry/releases/tag/v0.1.0-alpha.1) and run it.

```sh
python3 takeferry.pyz demo --output rainy-door-demo
```

Or run it from source.

```sh
git clone https://github.com/Tsunami1212/takeferry.git
cd takeferry
python3 -m takeferry demo --output rainy-door-demo
```

![Two storyboard takes of An at the door, with a locked camera on the left and a push-in on the right](examples/rainy-door/preview.gif)

Open `rainy-door-demo/rain-at-the-door.zip` for the five-second original. In `cut-list.csv`, the writer kept seconds 1.0 to 4.5 of the slower push-in. Beside the ZIP are both simulated canvas layouts (`canvases.json`), four take records (`takes.json`), and the skill draft (`branch-camera-movement/SKILL.md`).

## Connect your own canvas

Install the directing skill in your Hermes profile. Run `python3 -m takeferry config` or `python3 takeferry.pyz config` to print the Model Context Protocol (MCP) settings, then authorize the platform you want to use. Your Hermes language model has its own billing. [Setup and credentials](docs/setup.md)

- **LibTV** provides the official remote MCP server. Hermes builds and runs the shot there, then reads the result back from its canvas node.
- **Pippit (小云雀)** uses TakeFerry's MCP bridge to its official media CLI and Canvas SDK. The bridge attaches the returned video to the intended node and checks its media IDs on Pippit.

This alpha has been tested with the offline rehearsal and the official Python MCP client. Paid renders on both platforms and saving a skill in a real Hermes profile still need testing. [Verification details](docs/verification.md)

The core, MCP server and example use the Python standard library. Run the tests with `python3 -m unittest discover -s tests -v`. [Contributor guide](CONTRIBUTING.md) · [Adapter notes](docs/adapters.md) · [Apache-2.0 license](LICENSE) · [中文使用指南](README.zh-CN.md)
