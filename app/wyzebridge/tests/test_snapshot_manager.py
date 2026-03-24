from types import SimpleNamespace
from unittest.mock import Mock, mock_open, patch

from wyzebridge.snapshot_manager import SnapshotManager


def test_save_snapshot_rejects_empty_image_body():
    manager = SnapshotManager({})
    response = SimpleNamespace(status_code=200, content=b"")

    with patch("wyzebridge.snapshot_manager.requests.get", return_value=response), patch(
        "wyzebridge.snapshot_manager.open",
        mock_open(),
    ) as file_open:
        assert manager.save_snapshot("bar-cam") is False

    file_open.assert_not_called()


def test_save_snapshot_writes_non_empty_image_body():
    manager = SnapshotManager({})
    response = SimpleNamespace(status_code=200, content=b"jpeg-bytes")

    with patch("wyzebridge.snapshot_manager.requests.get", return_value=response), patch(
        "wyzebridge.snapshot_manager.open",
        mock_open(),
    ) as file_open:
        assert manager.save_snapshot("bar-cam") is True

    file_open.assert_called()
