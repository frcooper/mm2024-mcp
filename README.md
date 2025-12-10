# MediaMonkey 2024 MCP

Python-based Model Context Protocol (MCP) server that proxies MediaMonkey 2024 / MediaMonkey 5 via the official COM automation surface. The MCP tools expose playback control, volume/seek management, queue inspection, and a safe wrapper around the `runJSCode` bridge described in MediaMonkey's documentation.

The package is published on [PyPI](https://pypi.org/project/mm2024-mcp/), so you can install it system-wide with `pip install mm2024-mcp` or work directly from a local checkout.

## References

- [Controlling MM5 from External Applications](https://mediamonkey.com/wiki/Controlling_MM5_from_External_Applications)
- [SDBApplication automation reference](https://mediamonkey.com/wiki/SDBApplication)
- [SDBPlayer / SDBSongData object model](https://mediamonkey.com/wiki/SDBPlayer)
- [ISDBUI::Menu Compendium (menu scopes)](https://www.mediamonkey.com/wiki/ISDBUI::Menu_Compendium)
- [SDBIniFile reference (config settings)](https://www.mediamonkey.com/wiki/SDBIniFile)

## Requirements

- Windows host with MediaMonkey 5+/2024 installed.
- Python 3.11+ (the MCP SDK requires 3.10+, we target 3.11).
- `pywin32` (installed automatically via `pyproject.toml`).
- `modelcontextprotocol` Python SDK 1.2.0+.

> **Note:** MediaMonkey automatically launches when the COM `SongsDB5.SDBApplication` object is created. The MCP server keeps `ShutdownAfterDisconnect = False` so MediaMonkey is not force-closed when the server exits.

## Installation

### Install from PyPI

```pwsh
pip install mm2024-mcp
```

This installs the `mm2024-mcp` console entry point plus the MCP tools so any compatible host can launch the server without cloning the repository.

### Local editable install

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
| `invoke_menu_item` | Walks an `SDB.UI` menu/toolbar scope and executes the resolved `SDBMenuItem`. |
| `set_config_value` | Writes MediaMonkey.ini entries through `SDB.IniFile` (string, int, or bool). |

All tool results are serialized using Pydantic models defined under `src/mm2024_mcp/models.py`.

### Menu automation

`invoke_menu_item` uses the menu scopes listed in the [ISDBUI::Menu Compendium](https://www.mediamonkey.com/wiki/ISDBUI::Menu_Compendium). Provide the scope name (for example `Menu_Tools`) and a list of captions to traverse beneath that scope (`["Options..."]`). Captions are normalized by removing ampersands and trailing ellipses, and you can loosen matching via `match_strategy="startswith"` or `match_strategy="contains"`. Some menu trees are generated on demand; if a path fails, open the target menu in MediaMonkey once to warm it up before calling the tool again. Passing `allow_disabled=True` is useful for diagnostic scenarios, but be careful—MediaMonkey may still block execution for items that are disabled in the UI.

### Configuration helpers

`set_config_value` wraps `SDB.IniFile` (see the [SDBIniFile reference](https://www.mediamonkey.com/wiki/SDBIniFile)) so you can modify `MediaMonkey.ini` remotely. Pick a `value_type` (`string`, `int`, or `bool`), supply the new value, and optionally choose `persist_mode="flush"` or `persist_mode="apply"` to force MediaMonkey to write or re-load the ini file immediately. The tool returns the prior value whenever possible so you can confirm that a change was accepted. Some settings only take effect after restarting MediaMonkey—consult the MediaMonkey wiki for per-setting caveats.

## Plugin development workflow

1. Launch MediaMonkey 2024 normally so its COM automation layer is warmed up.
2. Open this repository in VS Code, enable the bundled `mm2024` MCP server (Chat → Tools → Servers), and keep the MCP chat panel docked next to your add-on source files.
3. While editing your MediaMonkey plug-in, use chat prompts such as `Run list_now_playing to confirm the testing playlist` or `Call run_javascript with the playlist enumerator snippet` to validate behavior live.
4. After iterating on COM changes inside `media_monkey_client.py`, run `uv run mm2024-mcp` in a terminal if you need to debug outside of VS Code's agent view.

## Packaging & releases

### Local builds

1. Install the packaging tools (this uses the optional `dev` extra defined in `pyproject.toml`):

    ```pwsh
    uv pip install -e .[dev]
    ```

2. Build the source distribution and wheel:

    ```pwsh
    python -m build --sdist --wheel
    ```

3. Verify the metadata before uploading:

    ```pwsh
    python -m twine check dist/*
    ```

4. Publish to PyPI (requires an API token created in your PyPI account):

    ```pwsh
    $env:TWINE_USERNAME = "__token__"
    $env:TWINE_PASSWORD = "pypi-xxxxxxxxxxxxxxxx"
    python -m twine upload dist/*
    ```

Artifacts are emitted to `dist/` (already ignored by `.gitignore`). Delete the folder between releases if you want a clean rebuild.

### GitHub Actions workflow

- `.github/workflows/publish.yml` runs on manual dispatch, annotated tag pushes that match semantic `vMAJOR.MINOR.PATCH` tags, and `release` events when a GitHub release is published.
- The workflow builds the wheel and sdist, runs `twine check`, uploads the `dist/` contents as a workflow artifact, and optionally pushes to PyPI via `pypa/gh-action-pypi-publish`.
- PyPI publishing uses the [trusted publisher](https://docs.pypi.org/trusted-publishers/) flow, so GitHub Actions exchanges an OIDC token directly with PyPI—no PAT secrets are required.
- Typical release flow: bump the version in `pyproject.toml`, tag the commit (`git tag v0.2.0 && git push origin v0.2.0`), then watch the workflow finish. Only semantic tags (`vMAJOR.MINOR.PATCH`) trigger automatic PyPI uploads, so rerun the workflow via **Actions → Build and Publish → Run workflow** if you need artifacts without pushing a new tag.

## Troubleshooting

- If the MCP host reports `pywin32 is not available`, ensure you're installing dependencies within a Windows Python environment.
- If the COM automation object cannot be created, confirm MediaMonkey is installed and that the `SongsDB5.SDBApplication` ProgID exists. Override via `MM2024_COM_PROGID` if needed.
- `run_javascript` wraps payloads so `runJSCode_callback` returns JSON. For raw scripts that manage callbacks themselves, pass `expect_callback=False` to avoid double-wrapping.
