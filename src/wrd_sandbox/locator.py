from __future__ import annotations

import re
from pathlib import Path


DEFAULT_GAME_ROOT = Path(
    Path.home() / "Library/Application Support/Steam/steamapps/common/Wargame Red Dragon"
)

REVISION_PATTERN = re.compile(rb"SVNREVISION####0*(\d{6,})####SVNREVISION")


def extract_revision_from_binary(binary_path: Path) -> str:
    match = REVISION_PATTERN.search(binary_path.read_bytes())
    if not match:
        raise RuntimeError(f"Could not find SVN revision in {binary_path}")
    return match.group(1).decode("ascii")


def find_active_ndf_path(game_root: Path) -> tuple[str, Path]:
    candidates = sorted(
        (
            path.parent.name,
            path,
        )
        for path in (game_root / "Data" / "WarGame" / "PC").glob("*/NDF_MacOS.dat")
    )
    binary_path = game_root / "WarGame3"
    if binary_path.is_file():
        try:
            revision = extract_revision_from_binary(binary_path)
            preferred = (
                game_root / "Data" / "WarGame" / "PC" / revision / "NDF_MacOS.dat"
            )
            if preferred.is_file():
                return revision, preferred
        except RuntimeError:
            pass

    if not candidates:
        raise RuntimeError(f"Could not find NDF_MacOS.dat under {game_root}")
    return candidates[-1]
