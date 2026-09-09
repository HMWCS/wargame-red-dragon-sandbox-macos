from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from wrd_sandbox.backup import (
    backup_path_for,
    delete_backup,
    load_state,
    rebuild_backup,
    restore_backup,
    save_state,
)
from wrd_sandbox.locator import DEFAULT_GAME_ROOT, find_active_ndf_path
from wrd_sandbox.ndf_pipeline import repack_workspace_to_file, unpack_edat_to_workspace
from wrd_sandbox.patch_all import ScanSummary, apply_all_patches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wrd-sandbox")
    parser.add_argument("command", choices=("on", "off", "status"))
    parser.add_argument("--game-root", default=str(DEFAULT_GAME_ROOT))
    parser.add_argument("--max-packs-99", action="store_true")
    args = parser.parse_args(argv)

    try:
        game_root = Path(args.game_root).expanduser()
        revision, target_file = find_active_ndf_path(game_root)
        state = load_state(target_file)

        if args.command == "status":
            return _print_status(game_root, revision, target_file, state)
        if args.command == "on":
            return _turn_on(game_root, revision, target_file, state, args.max_packs_99)
        return _turn_off(game_root, revision, target_file, state)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _print_status(game_root: Path, revision: str, target_file: Path, state: dict | None) -> int:
    backup_exists = backup_path_for(target_file).exists()
    status = state["status"] if state else ("enabled" if backup_exists else "disabled")
    max_packs_99 = _state_max_packs_99(state)
    print(f"game_root: {game_root}")
    print(f"revision: {revision}")
    print(f"target_file: {target_file}")
    print(f"backup_exists: {'yes' if backup_exists else 'no'}")
    print(f"status: {status}")
    print(f"max_packs_99: {'yes' if max_packs_99 else 'no'}")
    return 0


def _turn_on(
    game_root: Path,
    revision: str,
    target_file: Path,
    state: dict | None,
    max_packs_99: bool,
) -> int:
    backup_file = backup_path_for(target_file)
    backup_exists = backup_file.exists()
    state_status = _state_status(state)

    if state_status == "enabled" and not backup_exists:
        raise RuntimeError(f"Backup file does not exist: {backup_file}")

    if backup_exists and state_status != "disabled":
        if state_status == "enabled" and _state_max_packs_99(state) == max_packs_99:
            print("status: enabled")
            return 0
        source_file = backup_file
    else:
        backup_file = rebuild_backup(target_file)
        source_file = backup_file

    with tempfile.TemporaryDirectory(prefix="wrd-sandbox-") as temp_dir:
        temp_root = Path(temp_dir)
        workspace_input = _workspace_input_file(source_file, target_file.name, temp_root)
        workspace = unpack_edat_to_workspace(workspace_input, temp_root)
        summary = apply_all_patches(workspace, max_packs_99=max_packs_99)
        _validate_summary(summary, max_packs_99=max_packs_99)
        rebuilt = repack_workspace_to_file(workspace, target_file.name, temp_root)
        shutil.copy2(rebuilt, target_file)

    _save_tool_state(target_file, game_root, revision, backup_file, "enabled", max_packs_99)
    print("status: enabled")
    return 0


def _turn_off(game_root: Path, revision: str, target_file: Path, state: dict | None) -> int:
    backup_file = backup_path_for(target_file)
    backup_exists = backup_file.exists()
    state_status = _state_status(state)

    if backup_exists:
        if state_status != "disabled":
            restore_backup(target_file)
        delete_backup(target_file)
        _save_tool_state(target_file, game_root, revision, backup_file, "disabled", False)
        print("status: disabled")
        return 0

    if state_status == "enabled":
        raise RuntimeError(f"Backup file does not exist: {backup_file}")

    _save_tool_state(target_file, game_root, revision, backup_file, "disabled", False)
    print("status: disabled")
    return 0


def _validate_summary(summary: ScanSummary, max_packs_99: bool = False) -> None:
    if summary.map_unlock_matches <= 0:
        raise RuntimeError("Could not patch 10 vs 10 map unlocks")
    if summary.deck_rule_matches != 1:
        raise RuntimeError("Could not patch deck rules")
    if max_packs_99 and summary.max_packs_matches <= 0:
        raise RuntimeError("Could not patch max deck cards per unit")
    if summary.default_slot_key_matches != 9:
        raise RuntimeError("Could not patch all 9 deck slot entries")
    if summary.prototype_matches <= 0:
        raise RuntimeError("Could not patch prototype units")
    if summary.fob_supply_matches <= 0:
        raise RuntimeError("Could not patch FOB supplies")


def _state_max_packs_99(state: dict | None) -> bool:
    return bool(state and state.get("max_packs_99", False))


def _state_status(state: dict | None) -> str | None:
    return None if state is None else state.get("status")


def _save_tool_state(
    target_file: Path,
    game_root: Path,
    revision: str,
    backup_file: Path,
    status: str,
    max_packs_99: bool,
) -> None:
    save_state(
        target_file,
        {
            "status": status,
            "revision": revision,
            "game_root": str(game_root),
            "target_file": str(target_file),
            "backup_file": str(backup_file),
            "max_packs_99": max_packs_99,
        },
    )


def _workspace_input_file(source_file: Path, target_name: str, temp_root: Path) -> Path:
    if source_file.name == target_name:
        return source_file
    temp_source = temp_root / target_name
    shutil.copy2(source_file, temp_source)
    return temp_source


if __name__ == "__main__":
    raise SystemExit(main())
