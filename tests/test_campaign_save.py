import json
import zipfile
from datetime import date
from pathlib import Path

import pytest

from scripts.campaign_memory import create_campaign, create_next_session
from scripts.campaign_save import (
    build_portable_archive,
    cloud_plan,
    commit_cloud_manifest,
    detect_sync_hint,
    inspect_campaign,
    migrate_campaign,
    record_local_save,
    sha256_file,
    stage_cloud_manifest,
)


def create_synthetic_campaign(tmp_path: Path) -> Path:
    return create_campaign(
        tmp_path,
        "The Amber Gate",
        tone="heroic mystery",
        session_date=date(2026, 8, 12),
    ).root


def read_manifest(campaign_root: Path) -> dict:
    return json.loads(
        (campaign_root / "questforge.json").read_text(encoding="utf-8")
    )


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def verified_data_receipt(plan: dict) -> dict:
    return {
        "saveId": plan["saveId"],
        "writeAuthorized": True,
        "remoteBefore": None,
        "files": {
            path: {
                "verified": True,
                "sha256": record["sha256"],
                "remoteId": f"remote-{index}",
            }
            for index, (path, record) in enumerate(
                plan["files"].items(),
                start=1,
            )
        },
    }


def test_new_campaign_has_schema_two_and_local_save_is_idempotent(tmp_path):
    campaign_root = create_synthetic_campaign(tmp_path)

    first = record_local_save(
        campaign_root,
        scene_id="session-001:scene-001",
        scene_label="The gate opens",
    )
    second = record_local_save(campaign_root)
    manifest = read_manifest(campaign_root)

    assert first["status"] == "saved"
    assert first["revision"] == 1
    assert second["status"] == "unchanged"
    assert second["saveId"] == first["saveId"]
    assert manifest["schemaVersion"] == 2
    assert manifest["campaignId"]
    assert manifest["storage"]["snapshot"]["manifestWrittenLast"] is True
    assert manifest["storage"]["snapshot"]["files"]["game-state.json"]


def test_local_save_advances_lineage_only_after_content_change(tmp_path):
    campaign_root = create_synthetic_campaign(tmp_path)
    first = record_local_save(campaign_root)
    session = campaign_root / "sessions" / "session-001.md"
    session.write_text(
        session.read_text(encoding="utf-8") + "\n- The gate opened.\n",
        encoding="utf-8",
    )

    second = record_local_save(
        campaign_root,
        scene_id="session-001:scene-002",
        scene_label="Beyond the gate",
    )
    manifest = read_manifest(campaign_root)

    assert second["revision"] == 2
    assert second["saveId"] != first["saveId"]
    assert manifest["storage"]["snapshot"]["parentSaveId"] == first["saveId"]
    assert manifest["storage"]["history"] == [
        {"revision": 1, "saveId": first["saveId"]},
        {"revision": 2, "saveId": second["saveId"]},
    ]


def test_local_save_advances_resume_point_when_scene_changes(tmp_path):
    campaign_root = create_synthetic_campaign(tmp_path)
    first = record_local_save(campaign_root)

    second = record_local_save(
        campaign_root,
        scene_id="session-001:scene-002",
        scene_label="Beyond the gate",
    )

    assert second["status"] == "saved"
    assert second["revision"] == 2
    assert second["saveId"] != first["saveId"]
    assert read_manifest(campaign_root)["storage"]["snapshot"]["scene"] == {
        "id": "session-001:scene-002",
        "label": "Beyond the gate",
    }


def test_canonical_autosave_does_not_stat_optional_media(
    tmp_path, monkeypatch
):
    campaign_root = create_synthetic_campaign(tmp_path)
    media = campaign_root / "images" / "assets" / "offline-scene.png"
    media.write_bytes(b"optional-media")
    original_stat = Path.stat

    def guarded_stat(path, *args, **kwargs):
        if path == media:
            raise OSError("optional media is offline")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", guarded_stat)

    result = record_local_save(campaign_root, profile="canonical")
    plan = cloud_plan(campaign_root)

    assert result["status"] == "saved"
    assert plan["profile"] == "canonical"
    assert "images/assets/offline-scene.png" not in plan["files"]


def test_cloud_plan_rejects_unsaved_changes(tmp_path):
    campaign_root = create_synthetic_campaign(tmp_path)
    record_local_save(campaign_root)
    (campaign_root / "campaign-state.md").write_text(
        "# Changed after snapshot\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="changed after"):
        cloud_plan(campaign_root)


def test_cloud_manifest_is_staged_and_committed_after_verified_receipts(
    tmp_path,
):
    campaign_root = create_synthetic_campaign(tmp_path)
    record_local_save(campaign_root)
    plan = cloud_plan(campaign_root)
    data_receipt_path = tmp_path / "data-receipt.json"
    write_json(data_receipt_path, verified_data_receipt(plan))
    staged_manifest = tmp_path / "staged-questforge.json"

    staged = stage_cloud_manifest(
        campaign_root,
        data_receipt_path,
        provider="google-drive",
        folder_ref="folder-123",
        folder_url="https://drive.google.com/drive/folders/folder-123",
        output_path=staged_manifest,
    )
    manifest_receipt = tmp_path / "manifest-receipt.json"
    write_json(
        manifest_receipt,
        {
            "saveId": plan["saveId"],
            "sha256": sha256_file(staged_manifest),
            "verified": True,
            "remoteId": "manifest-remote-id",
        },
    )
    result = commit_cloud_manifest(
        campaign_root,
        staged_manifest,
        manifest_receipt,
    )
    manifest = read_manifest(campaign_root)

    assert staged["uploadLastAs"] == "questforge.json"
    assert result["status"] == "cloud-save-complete"
    assert result["manifestWrittenLast"] is True
    assert manifest["storage"]["cloud"]["provider"] == "google-drive"
    assert manifest["storage"]["cloud"]["folderRef"] == "folder-123"
    assert manifest["storage"]["cloud"]["saveId"] == plan["saveId"]


def test_cloud_stage_rejects_hash_mismatch_and_unknown_remote_lineage(
    tmp_path,
):
    campaign_root = create_synthetic_campaign(tmp_path)
    record_local_save(campaign_root)
    plan = cloud_plan(campaign_root)
    receipt = verified_data_receipt(plan)
    receipt["files"]["game-state.json"]["sha256"] = "wrong"
    receipt_path = tmp_path / "bad-hash.json"
    write_json(receipt_path, receipt)

    with pytest.raises(ValueError, match="hash mismatch"):
        stage_cloud_manifest(
            campaign_root,
            receipt_path,
            "google-drive",
            "folder-123",
            tmp_path / "staged.json",
        )

    receipt = verified_data_receipt(plan)
    receipt["remoteBefore"] = {
        "campaignId": plan["campaignId"],
        "saveId": "divergent-save",
        "revision": plan["revision"],
    }
    receipt_path = tmp_path / "bad-lineage.json"
    write_json(receipt_path, receipt)

    with pytest.raises(ValueError, match="known ancestor"):
        stage_cloud_manifest(
            campaign_root,
            receipt_path,
            "google-drive",
            "folder-123",
            tmp_path / "staged.json",
        )


def test_portable_archive_separates_canonical_state_from_media(tmp_path):
    campaign_root = create_synthetic_campaign(tmp_path)
    media = campaign_root / "images" / "assets" / "scene.png"
    media.write_bytes(b"synthetic-image")
    record_local_save(campaign_root)

    canonical_path = tmp_path / "canonical.zip"
    complete_path = tmp_path / "complete.zip"
    build_portable_archive(campaign_root, canonical_path)
    build_portable_archive(campaign_root, complete_path, include_media=True)

    with zipfile.ZipFile(canonical_path) as archive:
        canonical_order = archive.namelist()
        canonical_names = set(canonical_order)
    with zipfile.ZipFile(complete_path) as archive:
        complete_names = set(archive.namelist())

    assert "questforge.json" in canonical_names
    assert canonical_order[-1] == "questforge.json"
    assert "game-state.json" in canonical_names
    assert "characters/" in canonical_names
    assert "checkpoints/" in canonical_names
    assert "images/assets/scene.png" not in canonical_names
    assert "images/assets/scene.png" in complete_names


def test_migration_dry_run_preserves_legacy_copy_and_applies_safely(tmp_path):
    campaign_root = create_synthetic_campaign(tmp_path)
    manifest = read_manifest(campaign_root)
    manifest.pop("schemaVersion")
    manifest.pop("campaignId")
    manifest.pop("storage")
    manifest.pop("canonicalFiles")
    write_json(campaign_root / "questforge.json", manifest)

    journal = campaign_root / "player-journal.md"
    legacy_journal = campaign_root / "player-journal-session-001.md"
    legacy_journal.write_text(
        journal.read_text(encoding="utf-8"), encoding="utf-8"
    )
    journal.unlink()

    dry_run = migrate_campaign(campaign_root)
    assert dry_run["applied"] is False
    assert dry_run["blockers"] == []
    assert not journal.exists()

    applied = migrate_campaign(campaign_root, apply=True)
    migrated = read_manifest(campaign_root)
    assert applied["applied"] is True
    assert journal.read_text(encoding="utf-8") == legacy_journal.read_text(
        encoding="utf-8"
    )
    assert legacy_journal.exists()
    assert migrated["schemaVersion"] == 2
    assert migrated["campaignId"]
    assert migrated["migration"]["legacyCopiesPreserved"] is True


def test_migration_stops_on_session_mismatch_until_explicitly_accepted(
    tmp_path,
):
    campaign_root = create_synthetic_campaign(tmp_path)
    create_next_session(campaign_root, session_date=date(2026, 8, 13))
    manifest = read_manifest(campaign_root)
    manifest["currentSession"] = 1
    manifest["schemaVersion"] = 1
    manifest.pop("campaignId")
    write_json(campaign_root / "questforge.json", manifest)

    blocked = migrate_campaign(campaign_root)
    assert {item["code"] for item in blocked["blockers"]} == {
        "manifest_session_mismatch"
    }

    applied = migrate_campaign(
        campaign_root,
        apply=True,
        accept_latest_session=True,
    )
    assert applied["applied"] is True
    assert read_manifest(campaign_root)["currentSession"] == 2


def test_next_session_updates_manifest_resume_point(tmp_path):
    campaign_root = create_synthetic_campaign(tmp_path)

    create_next_session(campaign_root, session_date=date(2026, 8, 13))
    manifest = read_manifest(campaign_root)

    assert manifest["currentSession"] == 2
    assert manifest["currentScene"] == {
        "id": "session-002:scene-001",
        "label": "session opening",
    }


def test_detect_sync_hint_never_claims_authorization():
    google = detect_sync_hint(
        Path(
            "/Users/test/Library/CloudStorage/GoogleDrive-user/"
            "My Drive/campaigns/amber-gate"
        )
    )
    onedrive = detect_sync_hint(
        Path(
            "/Users/test/Library/CloudStorage/OneDrive-Personal/"
            "campaigns/amber-gate"
        )
    )
    plain = detect_sync_hint(Path("/work/campaigns/amber-gate"))

    assert google == {
        "detected": True,
        "provider": "google-drive",
        "authorization": "not-verified",
    }
    assert onedrive["provider"] == "onedrive"
    assert onedrive["authorization"] == "not-verified"
    assert plain["detected"] is False


def test_inspection_blocks_conflicting_noncanonical_journal(tmp_path):
    campaign_root = create_synthetic_campaign(tmp_path)
    (campaign_root / "player-journal-session-001.md").write_text(
        "# Different journal\n",
        encoding="utf-8",
    )

    inspection = inspect_campaign(campaign_root)

    assert inspection.ok is False
    assert "conflicting_noncanonical_copy" in {
        issue.code for issue in inspection.issues
    }
