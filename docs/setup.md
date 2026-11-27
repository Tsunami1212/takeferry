# Connect TakeFerry to Hermes

Start the free rehearsal first if you want to see how a shot, a revision and a cut list fit together. Connecting a real platform requires your own account.

## Hermes profile

Use a working Hermes Agent installation with a language model configured. Install the public directing skill into the profile you use for film work.

```sh
hermes skills install Tsunami1212/takeferry/skills/takeferry
```

To get the complete skill without a Git checkout, download the release's `takeferry-skill.zip`, or run `python3 takeferry.pyz skill --output takeferry-skill.zip`. Unzip its `takeferry/` directory into the active Hermes profile's `skills/` directory. The archive includes the reference guides and their licenses.

Hermes can also load the checked-out `skills/takeferry/` directory from its profile's `skills/` folder. Keep private lessons in separate skills so you can update the public package. [Hermes skill installation](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)

From the checkout, run `python3 -m takeferry config`. If you downloaded the portable app, run `python3 takeferry.pyz config` instead. Merge the printed entries under `mcp_servers` in the active Hermes profile's `config.yaml`. Keep its other servers in place. The output uses the actual Python and checkout or application path on your machine.

For other platforms, select only the connectors you want, for example `python3 takeferry.pyz config --provider tapnow magnific comfy figjam`. See the [canvas guide](canvases.md) for local ComfyUI, regional endpoints and Canva's OAuth client settings.

Start a new Hermes session or reload its MCP connections. Ask it to list the TakeFerry tools and read an empty shot using `takeferry_compare`. The result should contain an empty `takes` list and a null selection. [Hermes MCP configuration](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)

## LibTV

Keep the printed `libtv` entry with its official URL and `auth: oauth`. Complete LibTV's OAuth login through Hermes, then ask it to read the selected project and the current video models. Use the account you intend to charge. A successful discovery or login alone does not produce a video. [LibTV official connector](https://github.com/liblib-ai/marketplace)

## Pippit / Xiaoyunque

Use the official Pippit CLI on the machine that runs TakeFerry. Complete its documented login and confirm `pippit-tool-cli status` returns `logged_in` and an account `uid`. The official Canvas setup identifies both the native executable and a matching JavaScript Canvas entry, usually named `scripts/run.js`. These are separate entry points. [Pippit installation](https://github.com/Pippit-dev/cli) · [Canvas entry discovery](https://github.com/Pippit-dev/cli/blob/main/skills/xyq-nest-skill/commands/canvas.md)

Specify these settings in the `env` map of the `takeferry` MCP server. Replace the example paths with your own.

```yaml
env:
  TAKEFERRY_PIPPIT_CLI: "/path/to/pippit-tool-cli"
  TAKEFERRY_PIPPIT_CANVAS_ENTRY: "/path/to/pippit-cli/scripts/run.js"
  TAKEFERRY_MEDIA_DIR: "/path/to/approved-reference-files"
  TAKEFERRY_STATE_DIR: "/path/to/private-takeferry-state"
```

The default CLI command is `pippit-tool-cli`. The default Node command is `node`. Use `TAKEFERRY_NODE` to select a specific Node executable. The default state directory is `~/.takeferry`. If you omit the media directory, the bridge reads references under the state directory's `media/` folder. Reference filenames in a brief are relative to that directory. The bridge checks the reviewed file hashes again before it uploads anything for a generation.

Call `takeferry_pippit_account`, then `takeferry_pippit_models` with the returned account and the intended team ID. Use the string `"0"` for personal space. Once the writer identifies an existing canvas, inspect its native snapshot. Use a fresh video node for each take.

## What leaves the machine

Hermes sends the conversation to the language model you selected. The chosen video provider receives the prompt, parameters and media for its take. Pippit reference files are read from the directory you specified. Generation receipts, selections and cached downloads live under the private state directory. Review private skill drafts before saving them to a Hermes profile.

Local tool access trusts the host. The approval digest identifies an exact plan. User consent comes from the writer's conversation or the approval controls in their Hermes host. Restrict access to the profile and state directory to the people who can operate that account.
