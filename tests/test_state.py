import json
from pathlib import Path

from wrd_sandbox.backup import (
    backup_path_for,
    create_backup,
    delete_backup,
    load_state,
    rebuild_backup,
    restore_backup,
    save_state,
    state_path_for,
)


def test_create_backup_and_restore_round_trip(tmp_path: Path):
    target = tmp_path / "NDF_MacOS.dat"
    target.write_bytes(b"original")

    backup = create_backup(target)
    target.write_bytes(b"patched")
    restore_backup(target)

    assert backup == backup_path_for(target)
    assert target.read_bytes() == b"original"


def test_delete_backup_removes_existing_backup(tmp_path: Path):
    target = tmp_path / "NDF_MacOS.dat"
    target.write_bytes(b"original")
    create_backup(target)

    delete_backup(target)

    assert not backup_path_for(target).exists()


def test_rebuild_backup_overwrites_existing_backup(tmp_path: Path):
    target = tmp_path / "NDF_MacOS.dat"
    target.write_bytes(b"current")
    backup_path_for(target).write_bytes(b"stale")

    backup = rebuild_backup(target)

    assert backup == backup_path_for(target)
    assert backup.read_bytes() == b"current"


def test_state_round_trip(tmp_path: Path):
    target = tmp_path / "NDF_MacOS.dat"
    target.write_bytes(b"x")
    payload = {
        "status": "enabled",
        "revision": "510064564",
        "target_file": str(target),
        "backup_file": str(backup_path_for(target)),
    }

    save_state(target, payload)

    assert load_state(target) == payload
    assert json.loads(state_path_for(target).read_text(encoding="utf-8")) == payload
