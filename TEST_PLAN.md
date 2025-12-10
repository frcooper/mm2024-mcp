# MediaMonkey MCP Test Plan

This document lists the manual and semi-automated checks we run before shipping changes to the MediaMonkey 2024 MCP server. The coverage focuses on the COM wrapper (`MediaMonkeyClient`) and the FastMCP tools surfaced in `server.py`.

## Prerequisites

1. Windows host with MediaMonkey 5/2024 installed and launched at least once (so the COM server is registered).
2. Python 3.11+ with project dependencies installed (`uv pip install -e .`).
3. MediaMonkey has access to a handful of local files so that playback and menus behave normally.
4. VS Code, Claude Desktop, or another MCP host configured to run `uv run mm2024-mcp` from this repository.

## Smoke tests

1. **Server boot**
   - Command: `uv run mm2024-mcp` (or `python -m mm2024_mcp.server`).
   - Expected: MediaMonkey starts if it was not already running; the MCP host lists the tools without error.

2. **Playback state + transport**
   - Call `get_playback_state`; verify JSON includes `track` metadata when a song is active.
   - Trigger `control_playback` with `next`, `previous`, and `stop_after_current`; confirm return payload reflects the toggled flags.
   - Run `set_volume` at 10 and 90 to ensure clamping works and volume changes inside MediaMonkey.
   - Use `seek` with a mid-song offset and confirm `playback_time_ms` updates accordingly.

3. **Queue inspection**
   - Start playback of a playlist and invoke `list_now_playing` with `limit=5`; verify the list aligns with the Now Playing pane.

4. **JavaScript bridge**
   - Call `run_javascript` with a simple snippet (e.g., `return app.player.getSongTitle();`).
   - Repeat with `expect_callback=False` while passing a script that already handles `runJSCode_callback` to confirm double-wrapping is avoided.

## Menu automation

1. **Basic invocation**
   - Run `invoke_menu_item` with `scope="Menu_Tools"` and `path=["Options..."]`; MediaMonkey’s Options dialog should appear.
   - Dismiss the dialog to reset state.

2. **Nested path**
   - Use `scope="Menu_File"`, `path=["Add/Rescan files to the Library..."]` and verify the scan dialog opens.

3. **Matching strategies**
   - Choose a caption with accelerator keys (`&Play`). Call `invoke_menu_item` with `path=["Play"]` and `match_strategy="startswith"`; tool should still resolve the `&Play` item.

4. **Disabled handling**
   - Pause playback so that `Menu_Play -> Stop` becomes disabled, then call `invoke_menu_item` with `allow_disabled=True` and confirm that the tool succeeds (MediaMonkey may still reject the action but the tool should not crash). Repeat with `allow_disabled=False` and ensure it raises an error.

5. **Error messaging**
   - Supply an invalid scope (e.g., `Menu_Foo`) and confirm the MCP tool returns a descriptive failure that surfaces in the host UI.

## Configuration helper

1. **String write**
   - Call `set_config_value` with `section="MMPlayer"`, `key="TestString"`, `value="hello"`, `value_type="string"`, `persist_mode="flush"`.
   - Inspect `%appdata%\MediaMonkey\MediaMonkey.ini` to confirm the new key/value pair exists.

2. **Integer write**
   - Use `value_type="int"` on a known numeric key (e.g., `NowPlaying\VisibleColumns`). Confirm the returned payload reports the previous integer.

3. **Boolean write**
   - Toggle `Options\PartyModeEnabled` (or another boolean) with `value=True` and `persist_mode="apply"`; verify MediaMonkey reflects the change immediately or after a quick UI refresh.

4. **Type safety**
   - Attempt to submit a non-numeric string with `value_type="int"`; expect the tool to raise a validation error before touching MediaMonkey.

5. **Unknown keys**
   - Write to a throwaway section/key and ensure the tool reports `previous_value=None` but still succeeds.

## Regression checks

1. Re-run `get_playback_state` and `list_now_playing` after the menu/config tests to ensure recent additions did not corrupt the COM session.
2. Restart the MCP server (Ctrl+C and `uv run mm2024-mcp` again) and repeat a menu invocation plus a config write to confirm the singleton client caches behave after reconnects.
3. If time permits, run `ruff check` / `mypy` (if configured) to keep static analysis happy.

Document any deviations or newly discovered menu scopes inside `README.md` (tool table) and `.github/copilot-instructions.md` so future contributors have the latest compatibility notes.
