"""Thin wrapper around MediaMonkey's COM automation surface."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from .models import PlaybackState, TrackInfo

try:  # pragma: no cover - platform-specific import guard
    import pythoncom  # type: ignore
    import win32com.client  # type: ignore
    from pywintypes import com_error  # type: ignore
except Exception:  # pragma: no cover - raised later when actually used
    pythoncom = None  # type: ignore
    win32com = None  # type: ignore
    com_error = Exception  # type: ignore[misc, assignment]

LOGGER = logging.getLogger(__name__)

_MEDIA_MONKEY_PROG_ID = os.environ.get("MM2024_COM_PROGID", "SongsDB5.SDBApplication")


class MediaMonkeyUnavailableError(RuntimeError):
    """Raised when MediaMonkey is missing or cannot be automated."""


@dataclass
class _RawPlaybackState:
    """Internal helper that mirrors :class:`PlaybackState` but stores native COM values."""

    is_playing: bool
    is_paused: bool
    shuffle: bool
    repeat: bool
    stop_after_current: bool
    volume: int
    playback_time_ms: int
    track_length_ms: Optional[int]
    current_index: Optional[int]
    now_playing_size: Optional[int]
    track: Optional[TrackInfo]

    def to_model(self) -> PlaybackState:
        return PlaybackState(**asdict(self))


class MediaMonkeyClient:
    """Encapsulates MediaMonkey automation usage patterns used by MCP tools."""

    def __init__(self, keep_alive: bool = True) -> None:
        if win32com is None:
            raise MediaMonkeyUnavailableError(
                "pywin32 is not available. Install pywin32 and run on Windows."
            )
        # Initialize COM apartment for the current thread.
        pythoncom.CoInitialize()
        try:
            self._sdb = win32com.client.Dispatch(_MEDIA_MONKEY_PROG_ID)
        except com_error as exc:  # pragma: no cover - depends on local install
            raise MediaMonkeyUnavailableError(
                f"Unable to create COM object '{_MEDIA_MONKEY_PROG_ID}'. "
                "Verify that MediaMonkey 5/2024 is installed."
            ) from exc

        if keep_alive:
            try:
                self._sdb.ShutdownAfterDisconnect = False
            except Exception:  # pragma: no cover - property missing on older builds
                LOGGER.debug("ShutdownAfterDisconnect not exposed by current build")

        self._player = self._sdb.Player

    # ------------------------------------------------------------------
    # Public surface consumed by MCP tools
    # ------------------------------------------------------------------
    def get_playback_state(self) -> PlaybackState:
        """Return a :class:`PlaybackState` snapshot."""

        raw_state = self._collect_playback_state()
        return raw_state.to_model()

    def control_playback(self, action: str) -> PlaybackState:
        """Dispatch common player actions (play, pause, stop, etc.)."""

        action = action.lower()
        player = self._player

        if action == "play":
            player.Play()
        elif action == "pause":
            player.Pause()
        elif action == "toggle":
            if bool(getattr(player, "isPlaying", False)):
                player.Pause()
            else:
                player.Play()
        elif action == "stop":
            player.Stop()
        elif action == "next":
            player.Next()
        elif action == "previous":
            player.Previous()
        elif action == "stop_after_current":
            player.StopAfterCurrent = not bool(getattr(player, "StopAfterCurrent", False))
        else:  # pragma: no cover - defensive path validated earlier
            raise ValueError(f"Unsupported playback action: {action}")

        return self.get_playback_state()

    def set_volume(self, level: int) -> PlaybackState:
        """Clamp and set master volume (0-100)."""

        level = max(0, min(100, int(level)))
        self._player.Volume = level
        return self.get_playback_state()

    def seek(self, playback_time_ms: int) -> PlaybackState:
        """Jump to a position within the active track (milliseconds)."""

        playback_time_ms = max(0, int(playback_time_ms))
        self._player.PlaybackTime = playback_time_ms
        return self.get_playback_state()

    def now_playing(self, limit: int = 25) -> List[TrackInfo]:
        """Return the first ``limit`` entries from the Now Playing queue."""

        song_list = getattr(self._player, "CurrentSongList", None)
        if song_list is None:
            return []

        count = int(getattr(song_list, "Count", 0))
        if count <= 0:
            return []

        safe_limit = max(0, min(limit, count))
        tracks: List[TrackInfo] = []
        for index in range(safe_limit):
            try:
                song = song_list.Item(index)
            except Exception as exc:  # pragma: no cover - COM quirks
                LOGGER.warning("Failed to read Now Playing index %s: %s", index, exc)
                continue
            track = self._song_to_track(song)
            if track:
                tracks.append(track)
        return tracks

    def run_js(self, code: str, expect_callback: bool = True) -> str:
        """Execute MediaMonkey's ``SDBApplication.runJSCode`` helper."""

        if not code.strip():
            raise ValueError("JavaScript payload cannot be empty")

        wrapped = code
        if expect_callback and "runJSCode_callback" not in code:
            wrapped = (
                "(() => {"
                "  try {"
                f"    const result = (async () => {{ {code} }})();"
                "    if (result && typeof result.then === 'function') {"
                "      result.then("
                "        value => runJSCode_callback(JSON.stringify({ok: true, data: value})),"
                "        err => runJSCode_callback(JSON.stringify({ok: false, error: err && err.message ? err.message : String(err)}))"
                "      );"
                "    } else {"
                "      runJSCode_callback(JSON.stringify({ok: true, data: result}));"
                "    }"
                "  } catch (error) {"
                "    runJSCode_callback(JSON.stringify({ok: false, error: error && error.message ? error.message : String(error)}));"
                "  }"
                "})();"
            )

        result = self._sdb.runJSCode(wrapped, True)
        if not expect_callback:
            return str(result)

        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            LOGGER.warning("runJSCode returned non-JSON data: %s", result)
            return str(result)

        if not parsed.get("ok", False):
            raise RuntimeError(parsed.get("error", "Unknown MediaMonkey JS error"))
        data = parsed.get("data")
        return json.dumps(data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _collect_playback_state(self) -> _RawPlaybackState:
        player = self._player
        song = getattr(player, "CurrentSong", None)
        track = self._song_to_track(song)

        now_playing = getattr(player, "CurrentSongList", None)
        now_playing_size = int(getattr(now_playing, "Count", 0)) if now_playing else None

        return _RawPlaybackState(
            is_playing=bool(getattr(player, "isPlaying", False)),
            is_paused=bool(getattr(player, "isPaused", False)),
            shuffle=bool(getattr(player, "isShuffle", False)),
            repeat=bool(getattr(player, "isRepeat", False)),
            stop_after_current=bool(getattr(player, "StopAfterCurrent", False)),
            volume=int(getattr(player, "Volume", 0)),
            playback_time_ms=int(getattr(player, "PlaybackTime", 0)),
            track_length_ms=int(getattr(song, "SongLength", 0)) if track else None,
            current_index=int(getattr(player, "CurrentSongIndex", -1)),
            now_playing_size=now_playing_size,
            track=track,
        )

    @staticmethod
    def _song_to_track(song: Any) -> Optional[TrackInfo]:
        if song is None:
            return None
        try:
            return TrackInfo(
                title=_safe_str(song, "Title"),
                artist=_safe_str(song, "ArtistName"),
                album=_safe_str(song, "AlbumName"),
                album_artist=_safe_str(song, "AlbumArtistName"),
                genre=_safe_str(song, "Genre"),
                year=_safe_int(song, "Year"),
                track_number=_safe_int(song, "TrackOrder"),
                duration_ms=_safe_int(song, "SongLength"),
                path=_safe_str(song, "Path"),
                rating=_safe_int(song, "Rating"),
                song_id=_safe_int(song, "SongID"),
            )
        except Exception as exc:  # pragma: no cover - COM edge cases
            LOGGER.warning("Unable to parse SDBSongData: %s", exc)
            return None


def _safe_str(obj: Any, attr: str) -> Optional[str]:
    try:
        value = getattr(obj, attr)
    except Exception:
        return None
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_int(obj: Any, attr: str) -> Optional[int]:
    try:
        value = getattr(obj, attr)
    except Exception:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
