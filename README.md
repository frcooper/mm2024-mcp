# MediaMonkey 2024 MCP

Python-based Model Context Protocol (MCP) server that proxies MediaMonkey 2024 / MediaMonkey 5 via the official COM automation surface. The MCP tools expose playback control, volume/seek management, queue inspection, and a safe wrapper around the `runJSCode` bridge described in MediaMonkey's documentation.

## References

- [Controlling MM5 from External Applications](https://mediamonkey.com/wiki/Controlling_MM5_from_External_Applications)
- [SDBApplication automation reference](https://mediamonkey.com/wiki/SDBApplication)
- [SDBPlayer / SDBSongData object model](https://mediamonkey.com/wiki/SDBPlayer)

## Requirements

- Windows host with MediaMonkey 5+/2024 installed.
- Python 3.11+ (the MCP SDK requires 3.10+, we target 3.11).
- `pywin32` (installed automatically via `pyproject.toml`).
- `modelcontextprotocol` Python SDK 1.2.0+.

> **Note:** MediaMonkey automatically launches when the COM `SongsDB5.SDBApplication` object is created. The MCP server keeps `ShutdownAfterDisconnect = False` so MediaMonkey is not force-closed when the server exits.

## Setup

```pwsh
uv venv
uv pip install -e .
```

If you do not use `uv`, replace with `python -m venv` and `pip install -e .`.

## Running the MCP server

```pwsh
uv run mm2024-mcp
```

Or execute directly:

```pwsh
python -m mm2024_mcp.server
```

The server speaks MCP over stdio. Configure your MCP host (Claude for Desktop, VS Code MCP client, etc.) to launch the `mm2024-mcp` console command or `python -m mm2024_mcp.server` within this repository.

## Using VS Code as your MCP host

Visual Studio Code 1.102+ with GitHub Copilot supports MCP servers natively (see the [VS Code "Use MCP servers" guide](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)). This repository includes a ready-to-use workspace configuration under `.vscode/mcp.json`.

1. Install the latest VS Code and sign in to Copilot.
2. Enable the MCP gallery (`chat.mcp.gallery.enabled`) or open the Command Palette and run **MCP: Open Workspace Folder Configuration**.
3. Inspect `.vscode/mcp.json`, update the path if your repository resides somewhere other than `${workspaceFolder}`, and tweak `env` entries (for example, override `MM2024_COM_PROGID`).
4. Open the Chat view (Ctrl+Alt+I), pick the `mm2024` server in the Tools picker, and approve the trust prompt the first time VS Code launches the server.
5. While developing MediaMonkey plugins, invoke MCP tools directly from chat (for example, `#get_playback_state`, `#list_now_playing`, or `#run_javascript`) to validate COM behavior without leaving the editor.

Tips:

- VS Code caches tool metadata. Use the **MCP: Reset Cached Tools** command after adding new MCP tools in `server.py`.
- Enable **MCP: Reset Trust** if you change the server command and VS Code refuses to restart it.
- Development mode is already configured in `.vscode/mcp.json` so editing `src/**/*.py` automatically restarts the MCP server that VS Code launched.

## Available tools

| Tool | Description |
| --- | --- |
| `get_playback_state` | Returns `SDBPlayer` status plus metadata from `CurrentSong`. |
| `control_playback` | Dispatches `Play`, `Pause`, `Stop`, `Next`, `Previous`, `toggle`, or `stop_after_current`. |
| `set_volume` | Sets the `SDBPlayer.Volume` property (0-100). |
| `seek` | Sets `SDBPlayer.PlaybackTime` (milliseconds). |
| `list_now_playing` | Reads the `CurrentSongList` queue (first N entries). |
| `run_javascript` | Invokes `SDBApplication.runJSCode` per the MediaMonkey wiki for advanced automations. |

All tool results are serialized using Pydantic models defined under `src/mm2024_mcp/models.py`.

## Plugin development workflow

1. Launch MediaMonkey 2024 normally so its COM automation layer is warmed up.
2. Open this repository in VS Code, enable the bundled `mm2024` MCP server (Chat → Tools → Servers), and keep the MCP chat panel docked next to your add-on source files.
3. While editing your MediaMonkey plug-in, use chat prompts such as `Run list_now_playing to confirm the testing playlist` or `Call run_javascript with the playlist enumerator snippet` to validate behavior live.
4. After iterating on COM changes inside `media_monkey_client.py`, run `uv run mm2024-mcp` in a terminal if you need to debug outside of VS Code's agent view.

## Troubleshooting

- If the MCP host reports `pywin32 is not available`, ensure you're installing dependencies within a Windows Python environment.
- If the COM automation object cannot be created, confirm MediaMonkey is installed and that the `SongsDB5.SDBApplication` ProgID exists. Override via `MM2024_COM_PROGID` if needed.
- `run_javascript` wraps payloads so `runJSCode_callback` returns JSON. For raw scripts that manage callbacks themselves, pass `expect_callback=False` to avoid double-wrapping.