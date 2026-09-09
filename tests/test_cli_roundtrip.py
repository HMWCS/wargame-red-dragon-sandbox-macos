from pathlib import Path

from wrd_sandbox.cli import main
from wrd_sandbox.backup import (
    backup_path_for,
    create_backup,
    load_state,
    save_state,
    state_path_for,
)
from wrd_sandbox.locator import DEFAULT_GAME_ROOT, find_active_ndf_path
from wrd_sandbox.ndf_pipeline import unpack_edat_to_workspace
from wrd_sandbox.ndf_parser import NdfParser


def _make_fake_game_root(tmp_path: Path) -> tuple[Path, Path]:
    revision, source_file = find_active_ndf_path(DEFAULT_GAME_ROOT)
    backup_file = backup_path_for(source_file)
    if backup_file.exists():
        source_file = backup_file
    fake_root = tmp_path / "Wargame Red Dragon"
    binary = fake_root / "WarGame3"
    target = fake_root / "Data" / "WarGame" / "PC" / revision / "NDF_MacOS.dat"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_bytes(f"####SVNREVISION####0{revision}####SVNREVISION####".encode("ascii"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source_file.read_bytes())
    return fake_root, target


def _max_packs_values(target: Path, workspace_root: Path) -> list[int]:
    workspace = unpack_edat_to_workspace(target, workspace_root)
    parser, _ = NdfParser.from_file(workspace / "pc/ndf/patchable/gfx/everything.ndfbin")
    return [
        obj.properties["MaxPacks"].value.value
        for obj in parser.find_objects("TUniteAuSolDescriptor")
        if obj.properties.get("MaxPacks")
    ]


def test_cli_on_default_keeps_original_max_packs_and_reports_no(tmp_path: Path, capsys):
    fake_root, target = _make_fake_game_root(tmp_path)
    original = target.read_bytes()
    original_max_packs = _max_packs_values(target, tmp_path / "original")

    assert main(["status", "--game-root", str(fake_root)]) == 0
    status_output = capsys.readouterr().out
    assert "disabled" in status_output
    assert "max_packs_99: no" in status_output

    assert main(["on", "--game-root", str(fake_root)]) == 0
    on_output = capsys.readouterr().out
    assert "enabled" in on_output
    assert target.read_bytes() != original
    assert _max_packs_values(target, tmp_path / "patched") == original_max_packs

    assert main(["status", "--game-root", str(fake_root)]) == 0
    status_output = capsys.readouterr().out
    assert "enabled" in status_output
    assert "max_packs_99: no" in status_output

    assert main(["off", "--game-root", str(fake_root)]) == 0
    off_output = capsys.readouterr().out
    assert "disabled" in off_output
    assert "max_packs_99: no" not in off_output
    assert target.read_bytes() == original
    assert not backup_path_for(target).exists()

    assert main(["status", "--game-root", str(fake_root)]) == 0
    status_output = capsys.readouterr().out
    assert "disabled" in status_output
    assert "backup_exists: no" in status_output
    assert "max_packs_99: no" in status_output

    assert main(["off", "--game-root", str(fake_root)]) == 0
    assert "disabled" in capsys.readouterr().out


def test_cli_off_fails_when_backup_is_missing(tmp_path: Path, capsys):
    fake_root, target = _make_fake_game_root(tmp_path)

    assert main(["on", "--game-root", str(fake_root)]) == 0
    capsys.readouterr()

    backup_path_for(target).unlink()

    assert main(["off", "--game-root", str(fake_root)]) == 1
    assert "Backup file does not exist" in capsys.readouterr().err
    assert load_state(target)["status"] == "enabled"


def test_cli_on_same_mode_is_idempotent(tmp_path: Path, capsys):
    fake_root, target = _make_fake_game_root(tmp_path)

    assert main(["on", "--game-root", str(fake_root)]) == 0
    capsys.readouterr()
    first_target = target.read_bytes()
    first_backup = backup_path_for(target).read_bytes()
    first_state = load_state(target)

    assert main(["on", "--game-root", str(fake_root)]) == 0
    assert "enabled" in capsys.readouterr().out
    assert target.read_bytes() == first_target
    assert backup_path_for(target).read_bytes() == first_backup
    assert load_state(target) == first_state


def test_cli_on_with_max_packs_99_sets_max_packs_and_reports_yes(tmp_path: Path, capsys):
    fake_root, target = _make_fake_game_root(tmp_path)
    original = target.read_bytes()

    assert main(["on", "--game-root", str(fake_root), "--max-packs-99"]) == 0
    on_output = capsys.readouterr().out
    assert "enabled" in on_output
    assert target.read_bytes() != original
    assert any(value == 99 for value in _max_packs_values(target, tmp_path / "patched"))

    assert main(["status", "--game-root", str(fake_root)]) == 0
    status_output = capsys.readouterr().out
    assert "enabled" in status_output
    assert "max_packs_99: yes" in status_output

    assert main(["off", "--game-root", str(fake_root)]) == 0
    capsys.readouterr()

    assert main(["status", "--game-root", str(fake_root)]) == 0
    status_output = capsys.readouterr().out
    assert "disabled" in status_output
    assert "max_packs_99: no" in status_output


def test_cli_off_cleans_redundant_backup_for_disabled_state(tmp_path: Path, capsys):
    fake_root, target = _make_fake_game_root(tmp_path)
    original = target.read_bytes()
    create_backup(target)
    save_state(
        target,
        {
            "status": "disabled",
            "revision": "510064564",
            "game_root": str(fake_root),
            "target_file": str(target),
            "backup_file": str(backup_path_for(target)),
            "max_packs_99": False,
        },
    )

    assert main(["off", "--game-root", str(fake_root)]) == 0
    assert "disabled" in capsys.readouterr().out
    assert target.read_bytes() == original
    assert not backup_path_for(target).exists()


def test_cli_on_rebuilds_stale_backup_from_disabled_baseline(tmp_path: Path, capsys):
    fake_root, target = _make_fake_game_root(tmp_path)
    original = target.read_bytes()
    backup_path_for(target).write_bytes(b"stale")
    save_state(
        target,
        {
            "status": "disabled",
            "revision": "510064564",
            "game_root": str(fake_root),
            "target_file": str(target),
            "backup_file": str(backup_path_for(target)),
            "max_packs_99": False,
        },
    )

    assert main(["on", "--game-root", str(fake_root)]) == 0
    assert "enabled" in capsys.readouterr().out
    assert backup_path_for(target).read_bytes() == original


def test_cli_on_fails_when_enabled_state_lost_backup(tmp_path: Path, capsys):
    fake_root, target = _make_fake_game_root(tmp_path)

    assert main(["on", "--game-root", str(fake_root)]) == 0
    capsys.readouterr()
    backup_path_for(target).unlink()

    assert main(["on", "--game-root", str(fake_root)]) == 1
    assert "Backup file does not exist" in capsys.readouterr().err


def test_cli_on_without_state_uses_backup_as_legacy_enabled_source(tmp_path: Path, capsys):
    fake_root, target = _make_fake_game_root(tmp_path)
    original_max_packs = _max_packs_values(target, tmp_path / "original")

    assert main(["on", "--game-root", str(fake_root), "--max-packs-99"]) == 0
    capsys.readouterr()
    state_path_for(target).unlink()

    assert main(["on", "--game-root", str(fake_root)]) == 0
    assert "enabled" in capsys.readouterr().out
    assert _max_packs_values(target, tmp_path / "patched") == original_max_packs
    assert load_state(target)["max_packs_99"] is False


def test_cli_status_defaults_missing_max_packs_flag_to_no(tmp_path: Path, capsys):
    fake_root, target = _make_fake_game_root(tmp_path)
    create_backup(target)
    save_state(
        target,
        {
            "status": "enabled",
            "revision": "510064564",
            "game_root": str(fake_root),
            "target_file": str(target),
            "backup_file": str(backup_path_for(target)),
        },
    )

    assert main(["status", "--game-root", str(fake_root)]) == 0
    status_output = capsys.readouterr().out
    assert "enabled" in status_output
    assert "max_packs_99: no" in status_output
