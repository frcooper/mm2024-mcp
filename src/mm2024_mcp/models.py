"""Pydantic models shared by MCP tools."""

from __future__ import annotations

from typing import Optional

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
