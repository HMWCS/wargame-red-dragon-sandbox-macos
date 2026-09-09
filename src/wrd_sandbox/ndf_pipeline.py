from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def unpack_edat_to_workspace(target_file: Path, workspace_root: Path) -> Path:
    workspace = workspace_root / "workspace"
    subprocess.run(
        [sys.executable, "-m", "wgrd_cons_parsers.edat", str(target_file), "-o", str(workspace)],
        check=True,
    )
    return workspace


def repack_workspace_to_file(workspace: Path, target_name: str, output_root: Path) -> Path:
    rebuilt_root = output_root / "rebuilt"
    xml_path = workspace / f"{target_name}.xml"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "wgrd_cons_parsers.edat",
            "-p",
            str(xml_path),
            "-o",
            str(rebuilt_root),
        ],
        check=True,
    )
    return rebuilt_root / target_name
