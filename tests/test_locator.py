from pathlib import Path

import pytest

from wrd_sandbox.locator import (
    DEFAULT_GAME_ROOT,
    extract_revision_from_binary,
    find_active_ndf_path,
)


def test_default_root_matches_installed_game():
    assert DEFAULT_GAME_ROOT == Path(
        Path.home() / "Library/Application Support/Steam/steamapps/common/Wargame Red Dragon"
    )


def test_extract_revision_from_binary_reads_embedded_revision(tmp_path: Path):
    binary = tmp_path / "WarGame3"
    binary.write_bytes(b"foo ####SVNREVISION####0510064564####SVNREVISION#### bar")

    assert extract_revision_from_binary(binary) == "510064564"


def test_extract_revision_from_binary_fails_when_missing(tmp_path: Path):
    binary = tmp_path / "WarGame3"
    binary.write_bytes(b"no revision here")

    with pytest.raises(RuntimeError, match="SVN revision"):
        extract_revision_from_binary(binary)


def test_find_active_ndf_prefers_revision_from_binary(tmp_path: Path):
    root = tmp_path / "Wargame Red Dragon"
    binary = root / "WarGame3"
    ndf = root / "Data" / "WarGame" / "PC" / "510064564" / "NDF_MacOS.dat"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_bytes(b"####SVNREVISION####0510064564####SVNREVISION####")
    ndf.parent.mkdir(parents=True, exist_ok=True)
    ndf.write_bytes(b"x")

    revision, resolved = find_active_ndf_path(root)

    assert revision == "510064564"
    assert resolved == ndf


def test_find_active_ndf_falls_back_to_highest_version(tmp_path: Path):
    root = tmp_path / "Wargame Red Dragon"
    binary = root / "WarGame3"
    lower = root / "Data" / "WarGame" / "PC" / "510060540" / "NDF_MacOS.dat"
    higher = root / "Data" / "WarGame" / "PC" / "510064564" / "NDF_MacOS.dat"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_bytes(b"####SVNREVISION####0510063000####SVNREVISION####")
    lower.parent.mkdir(parents=True, exist_ok=True)
    lower.write_bytes(b"a")
    higher.parent.mkdir(parents=True, exist_ok=True)
    higher.write_bytes(b"b")

    revision, resolved = find_active_ndf_path(root)

    assert revision == "510064564"
    assert resolved == higher


def test_find_active_ndf_falls_back_when_binary_is_missing(tmp_path: Path):
    root = tmp_path / "Wargame Red Dragon"
    lower = root / "Data" / "WarGame" / "PC" / "510060540" / "NDF_MacOS.dat"
    higher = root / "Data" / "WarGame" / "PC" / "510064564" / "NDF_MacOS.dat"
    lower.parent.mkdir(parents=True, exist_ok=True)
    lower.write_bytes(b"a")
    higher.parent.mkdir(parents=True, exist_ok=True)
    higher.write_bytes(b"b")

    revision, resolved = find_active_ndf_path(root)

    assert revision == "510064564"
    assert resolved == higher


def test_find_active_ndf_falls_back_when_revision_cannot_be_extracted(tmp_path: Path):
    root = tmp_path / "Wargame Red Dragon"
    binary = root / "WarGame3"
    lower = root / "Data" / "WarGame" / "PC" / "510060540" / "NDF_MacOS.dat"
    higher = root / "Data" / "WarGame" / "PC" / "510064564" / "NDF_MacOS.dat"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_bytes(b"no revision here")
    lower.parent.mkdir(parents=True, exist_ok=True)
    lower.write_bytes(b"a")
    higher.parent.mkdir(parents=True, exist_ok=True)
    higher.write_bytes(b"b")

    revision, resolved = find_active_ndf_path(root)

    assert revision == "510064564"
    assert resolved == higher
