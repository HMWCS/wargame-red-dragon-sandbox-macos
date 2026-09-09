from pathlib import Path

from wrd_sandbox.backup import backup_path_for
from wrd_sandbox.locator import DEFAULT_GAME_ROOT, find_active_ndf_path
from wrd_sandbox.ndf_pipeline import unpack_edat_to_workspace
from wrd_sandbox.patch_all import scan_workspace_targets


def test_real_game_workspace_contains_expected_patch_targets(tmp_path: Path):
    _, target_file = find_active_ndf_path(DEFAULT_GAME_ROOT)
    source_file = backup_path_for(target_file)
    if not source_file.exists():
        source_file = target_file

    workspace = unpack_edat_to_workspace(source_file, tmp_path)
    summary = scan_workspace_targets(workspace)

    assert summary.map_unlock_matches > 0
    assert summary.deck_rule_matches == 1
    assert summary.max_packs_matches > 0
    assert summary.prototype_matches > 0
    assert summary.fob_supply_matches > 0
    assert summary.default_slot_key_matches == 9
