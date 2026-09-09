from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


BACKUP_SUFFIX = ".pre-wrd-sandbox"
STATE_NAME = ".wrd-sandbox-state.json"


def backup_path_for(target_file: Path) -> Path:
    return target_file.with_name(target_file.name + BACKUP_SUFFIX)


def state_path_for(target_file: Path) -> Path:
    return target_file.with_name(STATE_NAME)


def create_backup(target_file: Path) -> Path:
    backup_file = backup_path_for(target_file)
    if not backup_file.exists():
        shutil.copy2(target_file, backup_file)
    return backup_file


def delete_backup(target_file: Path) -> Path:
    backup_file = backup_path_for(target_file)
    if backup_file.exists():
        backup_file.unlink()
    return backup_file


def rebuild_backup(target_file: Path) -> Path:
    backup_file = delete_backup(target_file)
    shutil.copy2(target_file, backup_file)
    return backup_file


def restore_backup(target_file: Path) -> Path:
    backup_file = backup_path_for(target_file)
    shutil.copy2(backup_file, target_file)
    return backup_file


def save_state(target_file: Path, payload: dict[str, Any]) -> Path:
    state_file = state_path_for(target_file)
    state_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return state_file


def load_state(target_file: Path) -> dict[str, Any] | None:
    state_file = state_path_for(target_file)
    if not state_file.exists():
        return None
    return json.loads(state_file.read_text(encoding="utf-8"))
