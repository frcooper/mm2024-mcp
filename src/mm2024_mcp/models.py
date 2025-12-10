"""Pydantic models shared by MCP tools."""

from __future__ import annotations

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


class TrackInfo(BaseModel):
    """Subset of MediaMonkey's `SDBSongData` fields that are useful to MCP tools."""

    title: Optional[str] = Field(None, description="Track title (SDBSongData.Title)")
    artist: Optional[str] = Field(None, description="Performer (SDBSongData.ArtistName)")
    album: Optional[str] = Field(None, description="Album (SDBSongData.AlbumName)")
    album_artist: Optional[str] = Field(None, description="Album artist (SDBSongData.AlbumArtistName)")
    genre: Optional[str] = Field(None, description="Genre tag")
    year: Optional[int] = Field(None, description="Release year")
    track_number: Optional[int] = Field(None, description="Track number within the album")
    duration_ms: Optional[int] = Field(None, description="Song length reported by MediaMonkey (milliseconds)")
    path: Optional[str] = Field(None, description="Absolute path to the media file on disk")
    rating: Optional[int] = Field(None, description="MediaMonkey star rating (0-100 scale)")
    song_id: Optional[int] = Field(None, description="Internal MediaMonkey track identifier")


class PlaybackState(BaseModel):
    """Snapshot of MediaMonkey's player state."""

    is_playing: bool = Field(..., description="True when audio is actively playing")
    is_paused: bool = Field(..., description="True when playback is paused")
    shuffle: bool = Field(..., description="Player shuffle flag (SDBPlayer.isShuffle)")
    repeat: bool = Field(..., description="Player repeat flag (SDBPlayer.isRepeat)")
    stop_after_current: bool = Field(..., description="Whether playback will stop after the current track")
    volume: int = Field(..., ge=0, le=100, description="Current output level (SDBPlayer.Volume)")
    playback_time_ms: int = Field(..., ge=0, description="Current position within the active track (milliseconds)")
    track_length_ms: Optional[int] = Field(None, description="Length of the active track (milliseconds)")
    current_index: Optional[int] = Field(None, description="Index of the active track in Now Playing (0-based)")
    now_playing_size: Optional[int] = Field(None, description="Number of entries in the Now Playing queue")
    track: Optional[TrackInfo] = Field(None, description="Metadata for the active track")


class MenuInvocationResult(BaseModel):
    """Details about an invoked MediaMonkey menu item."""

    scope: str = Field(..., description="Name of the `SDB.UI` menu collection used as the root")
    requested_path: List[str] = Field(..., min_length=1, description="Menu captions requested by the caller")
    matched_path: List[Optional[str]] = Field(..., description="Actual captions resolved within MediaMonkey")
    caption: Optional[str] = Field(None, description="Caption of the final menu item that was triggered")
    enabled: bool = Field(..., description="Whether MediaMonkey reported the menu item as enabled prior to invocation")
    executed: bool = Field(..., description="True once at least one invocation strategy succeeded")


class ConfigValue(BaseModel):
    """Result of reading or mutating MediaMonkey's INI configuration."""

    section: str = Field(..., description="INI section that was accessed")
    key: str = Field(..., description="INI key that was read or mutated")
    value_type: Literal["string", "int", "bool"] = Field(..., description="Underlying INI storage type")
    value: Union[str, int, bool, None] = Field(..., description="Value after the mutation completes")
    previous_value: Union[str, int, bool, None] = Field(
        None, description="Previously stored value, if it could be read before the mutation"
    )
    applied: bool = Field(False, description="True when the change was flushed or applied immediately")
