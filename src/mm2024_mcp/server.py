"""Entry point for the MediaMonkey 2024 MCP server."""

from __future__ import annotations

import logging
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .media_monkey_client import MediaMonkeyClient, MediaMonkeyUnavailableError

LOGGER = logging.getLogger(__name__)

mcp = FastMCP("mm2024-mcp")
_client: MediaMonkeyClient | None = None


def _get_client() -> MediaMonkeyClient:
    global _client
    if _client is None:
        _client = MediaMonkeyClient()
    return _client


def _serialize_state(state) -> dict:
    return state.model_dump()


@mcp.tool()
async def get_playback_state() -> dict:
    """Return MediaMonkey's current playback state and track metadata."""

    try:
        state = _get_client().get_playback_state()
    except MediaMonkeyUnavailableError as exc:
        raise RuntimeError(str(exc)) from exc
    return _serialize_state(state)


@mcp.tool()
async def control_playback(
    action: Literal["play", "pause", "toggle", "stop", "next", "previous", "stop_after_current"]
) -> dict:
    """Execute a playback command via MediaMonkey's SDBPlayer API."""

    try:
        state = _get_client().control_playback(action)
    except MediaMonkeyUnavailableError as exc:
        raise RuntimeError(str(exc)) from exc
    return _serialize_state(state)


@mcp.tool()
async def set_volume(level: Annotated[int, Field(ge=0, le=100)]) -> dict:
    """Set MediaMonkey's master output level (0-100)."""

    try:
        state = _get_client().set_volume(level)
    except MediaMonkeyUnavailableError as exc:
        raise RuntimeError(str(exc)) from exc
    return _serialize_state(state)


@mcp.tool()
async def seek(playback_time_ms: Annotated[int, Field(ge=0)]) -> dict:
    """Seek within the active track. Playback time is expressed in milliseconds."""

    try:
        state = _get_client().seek(playback_time_ms)
    except MediaMonkeyUnavailableError as exc:
        raise RuntimeError(str(exc)) from exc
    return _serialize_state(state)


@mcp.tool()
async def list_now_playing(limit: Annotated[int, Field(ge=1, le=100)] = 25) -> list[dict]:
    """Return up to ``limit`` tracks from MediaMonkey's Now Playing queue."""

    try:
        tracks = _get_client().now_playing(limit)
    except MediaMonkeyUnavailableError as exc:
        raise RuntimeError(str(exc)) from exc
    return [track.model_dump() for track in tracks]


@mcp.tool()
async def run_javascript(code: str, expect_callback: bool = True) -> str:
    """Invoke MediaMonkey's ``runJSCode`` bridge for advanced automations."""

    try:
        return _get_client().run_js(code, expect_callback=expect_callback)
    except MediaMonkeyUnavailableError as exc:
        raise RuntimeError(str(exc)) from exc


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    mcp.run(transport="stdio")


if __name__ == "__main__":  # pragma: no cover
    main()
