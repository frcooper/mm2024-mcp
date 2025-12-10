# MediaMonkey 2024 MCP – Agent Guide

## Repository Snapshot
- Python MCP server (`pyproject.toml`) that exposes MediaMonkey 5/2024 via COM. Code lives under `src/mm2024_mcp/`.
- `README.md` documents setup (Python 3.11+, `uv`/`pip install -e .`), runtime instructions (`uv run mm2024-mcp`), tool catalog, and upstream wiki links.
- `src/mm2024_mcp/media_monkey_client.py` encapsulates all COM interactions: it instantiates `SongsDB5.SDBApplication`, keeps `ShutdownAfterDisconnect=False`, and exposes helpers for playback, queue inspection, and `runJSCode` execution. Reuse this wrapper instead of touching COM objects directly.
- `src/mm2024_mcp/models.py` defines the Pydantic `TrackInfo` and `PlaybackState` models shared by tools.
- `src/mm2024_mcp/server.py` wires the MCP tools using `mcp.server.fastmcp.FastMCP`. Add new tooling here (decorate with `@mcp.tool()`), keep return values JSON-serializable (prefer `model_dump()` on Pydantic models).

## External Protocol Facts
- MediaMonkey’s supported automation entry point is `SongsDB5.SDBApplication` (see [wiki](https://mediamonkey.com/wiki/Controlling_MM5_from_External_Applications)). It allows direct access to `SDBPlayer`, `SDBSongList`, `SDBSongData`, etc.
- `SDBApplication.runJSCode` can execute arbitrary JavaScript inside the MediaMonkey UI. Our `run_javascript` tool wraps scripts so results are funneled through `runJSCode_callback` and encoded as JSON. When tooling already calls `runJSCode_callback`, pass `expect_callback=False` to avoid double wrapping.

## Implementation Conventions
- Treat `MediaMonkeyClient` as the single source of truth for COM access. Add new MediaMonkey operations there, expose them via thin MCP wrappers, and keep COM-specific error handling localized.
- When reading COM fields, use the `_safe_str`/`_safe_int` helpers already provided to normalize values; they guard against missing properties reported in the wiki’s support matrix.
- Keep MCP tools async (the FastMCP decorator accepts `async def`). Blocking COM calls may run synchronously inside those coroutines, but avoid spawning extra threads unless you understand COM apartment requirements.
- All tool responses should be human-readable JSON blobs. Use the existing Pydantic models or add new ones to `models.py` for clarity.
- Avoid stdout logging—the MCP stdio transport expects JSON-RPC over stdout only. Use the `logging` module (stderr) if you need diagnostics.

## Workflows
- Install dependencies with `uv venv && uv pip install -e .` (or `python -m venv` + `pip install -e .`).
- Run the server via `uv run mm2024-mcp` or `python -m mm2024_mcp.server`. Configure MCP hosts (Claude Desktop, VS Code MCP client, etc.) to launch the same command.
- MediaMonkey must be installed on the same Windows machine. The server auto-launches it; if COM activation fails, surface actionable errors instead of silent failures.
- VS Code + GitHub Copilot can start this server using the workspace `.vscode/mcp.json` file. Use the MCP: Open Workspace Folder Configuration command to review/edit the entry and enable the `mm2024` tools from the Chat tool picker (see [docs](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)).

## Collaboration Notes
- Be cautious with disruptive actions (volume jumps, queue clears). Mention them in PR summaries and consider confirmation flags in tool schemas.
- When adding new automation capabilities, cite the relevant wiki section inside docstrings or README so future agents know which MediaMonkey API they rely on.
- Update this file whenever the project structure, workflows, or tool semantics change. This is the primary onboarding reference for subsequent agents.
