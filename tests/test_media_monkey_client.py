"""Unit tests for internal MediaMonkey helper functions."""

# pylint: disable=protected-access

import types

import mm2024_mcp.media_monkey_client as mmc


def test_normalize_menu_label_strips_accelerators_and_ellipsis() -> None:
    assert mmc._normalize_menu_label("&File...") == "file"
    assert mmc._normalize_menu_label(" Play ") == "play"


def test_caption_matches_strategies() -> None:
    assert mmc._caption_matches("play", "pl", "startswith")
    assert mmc._caption_matches("playback", "back", "contains")
    assert mmc._caption_matches("options", "options", "exact")
    assert not mmc._caption_matches("options", "xyz", "contains")


def test_coerce_ini_input_and_result() -> None:
    assert mmc._coerce_ini_input("yes", "bool") is True
    assert mmc._coerce_ini_input("0", "bool") is False
    assert mmc._coerce_ini_input("7", "int") == 7
    assert mmc._coerce_ini_input(3, "string") == "3"

    assert mmc._coerce_ini_result("true", "bool") is True
    assert mmc._coerce_ini_result("nope", "bool") is False
    assert mmc._coerce_ini_result("9", "int") == 9
    assert mmc._coerce_ini_result(5, "string") == "5"


class _RecordingIni:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def StringValue(self, section: str, key: str, value, flags=None):  # noqa: N802
        # Raise when flags are missing to exercise the retry path.
        if flags is None:
            raise TypeError("flags required")
        self.calls.append((section, key, value, flags))

    def Apply(self) -> None:  # noqa: N802
        self.calls.append(("Apply",))

    def Flush(self) -> None:  # noqa: N802
        self.calls.append(("Flush",))


def test_write_ini_value_prefers_four_arg_and_persists() -> None:
    ini = _RecordingIni()

    mmc._write_ini_value(ini, "StringValue", "Section", "Key", "Value")
    assert ini.calls == [("Section", "Key", "Value", 0)]

    applied = mmc._persist_ini_changes(ini, "apply")
    assert applied is True
    assert ("Apply",) in ini.calls


def test_iterate_menu_children_handles_collections() -> None:
    child = types.SimpleNamespace()

    class _Collection:
        def __init__(self) -> None:
            self.Count = 1

        def Item(self, index):  # noqa: N802
            if index == 0:
                return child
            raise IndexError

    class _Menu:
        def __init__(self) -> None:
            self.SubItems = _Collection()

    menu = _Menu()
    assert list(mmc._iterate_menu_children(menu)) == [child]
