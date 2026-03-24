import sys
import types
from unittest.mock import ANY, Mock

sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None))

from wyzecam.api import get_camera_list
from wyzecam.api_models import WyzeCredential


def test_get_camera_list_keeps_legacy_shape(monkeypatch):
    monkeypatch.setattr(
        "wyzecam.api.get_homepage_object_list",
        lambda auth: {
            "id": "home-1",
            "device_list": [
                {
                    "product_type": "Camera",
                    "device_params": {
                        "p2p_id": "p2p-1",
                        "p2p_type": 1,
                        "ip": "192.168.1.10",
                        "dtls": 1,
                        "main_device_dtls": 0,
                        "camera_thumbnails": {"thumbnails_url": "https://legacy-thumb"},
                    },
                    "enr": "legacy-enr",
                    "mac": "AA:BB:CC:DD",
                    "product_model": "HL_PAN3",
                    "nickname": "Bedroom Cam",
                    "timezone_name": "Europe/London",
                    "firmware_ver": "4.50.16.6114",
                    "parent_device_enr": "parent-enr",
                    "parent_device_mac": "11:22:33:44",
                }
            ],
        },
    )
    monkeypatch.setattr(
        "wyzecam.api.get_home_devices",
        lambda auth, home_id: {"device_list": []},
    )

    cameras = get_camera_list(WyzeCredential(access_token="token", phone_id="phone"))

    assert len(cameras) == 1
    cam = cameras[0]
    assert cam.mac == "AA:BB:CC:DD"
    assert cam.product_model == "HL_PAN3"
    assert cam.nickname == "Bedroom Cam"
    assert cam.thumbnail == "https://legacy-thumb"
    assert cam.enr == "legacy-enr"
    assert cam.ip == "192.168.1.10"


def test_get_camera_list_includes_new_v4_duo_cam_pan(monkeypatch):
    monkeypatch.setattr(
        "wyzecam.api.get_homepage_object_list",
        lambda auth: {"id": "3e5a03c52f62484e983bfb19a1693b41", "device_list": []},
    )
    monkeypatch.setattr(
        "wyzecam.api.get_home_devices",
        lambda auth, home_id: {
            "device_list": [
                {
                    "device_id": "GW_DUO_80482C6E5E4D",
                    "device_param": {
                        "firmware_version": "1.0.0.167",
                        "hardware_version": "1.5.4",
                        "thumbnail": {"url": "https://duo-thumb"},
                        "p2p": {"providers": ["mars", "webrtc"]},
                    },
                    "nickname": "Bar Cam",
                    "device_model": "GW_DUO",
                    "device_category": "Camera",
                }
            ]
        },
    )

    cameras = get_camera_list(WyzeCredential(access_token="token", phone_id="phone"))

    assert len(cameras) == 1
    cam = cameras[0]
    assert cam.mac == "GW_DUO_80482C6E5E4D"
    assert cam.product_model == "GW_DUO"
    assert cam.model_name == "Duo Cam Pan"
    assert cam.nickname == "Bar Cam"
    assert cam.thumbnail == "https://duo-thumb"
    assert cam.p2p_type == 2
    assert cam.p2p_providers == ["mars", "webrtc"]
    assert cam.uses_mars is True
    assert cam.webrtc_support is True


def test_get_camera_list_keeps_unknown_new_models(monkeypatch):
    monkeypatch.setattr(
        "wyzecam.api.get_homepage_object_list",
        lambda auth: {"id": "home-1", "device_list": []},
    )
    monkeypatch.setattr(
        "wyzecam.api.get_home_devices",
        lambda auth, home_id: {
            "device_list": [
                {
                    "device_id": "UNKNOWN_1234",
                    "device_param": {
                        "thumbnail": {"url": "https://unknown-thumb"},
                        "p2p": {"providers": ["webrtc"]},
                    },
                    "nickname": "Mystery Cam",
                    "device_model": "UNKNOWN_MODEL",
                    "device_category": "Camera",
                }
            ]
        },
    )

    cameras = get_camera_list(WyzeCredential(access_token="token", phone_id="phone"))

    assert len(cameras) == 1
    cam = cameras[0]
    assert cam.mac == "UNKNOWN_1234"
    assert cam.product_model == "UNKNOWN_MODEL"
    assert cam.model_name == "UNKNOWN_MODEL"
    assert cam.p2p_providers == ["webrtc"]
    assert cam.uses_mars is False
    assert cam.webrtc_support is True


def test_get_camera_list_logs_skip_reason_for_missing_required_fields(monkeypatch, caplog):
    monkeypatch.setattr(
        "wyzecam.api.get_homepage_object_list",
        lambda auth: {
            "id": "home-1",
            "device_list": [
                {
                    "nickname": "Incomplete Cam",
                    "device_category": "Camera",
                    "device_param": {"p2p": {"providers": ["webrtc"]}},
                }
            ],
        },
    )
    get_home_devices = Mock(return_value={"device_list": []})
    monkeypatch.setattr("wyzecam.api.get_home_devices", get_home_devices)

    with caplog.at_level("DEBUG", logger="WyzeBridge"):
        cameras = get_camera_list(WyzeCredential(access_token="token", phone_id="phone"))

    assert cameras == []
    assert "missing mac/device_id, product_model/device_model" in caplog.text
    get_home_devices.assert_called_once_with(ANY, "home-1")


def test_get_camera_list_falls_back_to_v4_home_lookup(monkeypatch):
    monkeypatch.setattr(
        "wyzecam.api.get_homepage_object_list",
        lambda auth: {
            "device_list": [
                {
                    "product_type": "Camera",
                    "device_params": {
                        "p2p_id": "legacy-p2p",
                        "p2p_type": 0,
                        "ip": "",
                        "camera_thumbnails": {"thumbnails_url": "https://legacy-thumb"},
                    },
                    "enr": "legacy-enr",
                    "mac": "GW_DUO_80482C6E5E4D",
                    "product_model": "GW_DUO",
                    "nickname": "Bar Cam",
                    "timezone_name": "Europe/London",
                    "firmware_ver": "1.0.0.154",
                }
            ]
        },
    )
    get_homes = Mock(return_value=[{"home_id": "home-from-v4", "role": 1}])
    get_home_devices = Mock(
        return_value={
            "device_list": [
                {
                    "device_id": "GW_DUO_80482C6E5E4D",
                    "device_param": {
                        "firmware_version": "1.0.0.167",
                        "thumbnail": {"url": "https://cloud-thumb"},
                        "p2p": {"providers": ["mars", "webrtc"]},
                    },
                    "nickname": "Bar Cam",
                    "device_model": "GW_DUO",
                    "device_category": "Camera",
                }
            ]
        }
    )
    monkeypatch.setattr("wyzecam.api.get_homes", get_homes)
    monkeypatch.setattr("wyzecam.api.get_home_devices", get_home_devices)

    cameras = get_camera_list(WyzeCredential(access_token="token", phone_id="phone"))

    assert len(cameras) == 1
    cam = cameras[0]
    assert cam.mac == "GW_DUO_80482C6E5E4D"
    assert cam.p2p_providers == ["mars", "webrtc"]
    assert cam.uses_mars is True
    get_homes.assert_called_once()
    get_home_devices.assert_called_once_with(ANY, "home-from-v4")


def test_get_camera_list_prefers_legacy_fields_and_logs_v4_validation(monkeypatch, caplog):
    monkeypatch.setenv("LOG_V4_VALIDATION", "true")
    monkeypatch.setattr(
        "wyzecam.api.get_homepage_object_list",
        lambda auth: {
            "id": "home-1",
            "device_list": [
                {
                    "product_type": "Camera",
                    "device_params": {
                        "p2p_id": "legacy-p2p",
                        "p2p_type": 3,
                        "ip": "192.168.1.10",
                        "camera_thumbnails": {"thumbnails_url": "https://legacy-thumb"},
                    },
                    "enr": "legacy-enr",
                    "mac": "GW_DUO_80482C6E5E4D",
                    "product_model": "GW_DUO",
                    "nickname": "Bar Cam",
                    "timezone_name": "Europe/London",
                    "firmware_ver": "1.0.0.154",
                }
            ],
        },
    )
    monkeypatch.setattr(
        "wyzecam.api.get_home_devices",
        lambda auth, home_id: {
            "device_list": [
                {
                    "device_id": "GW_DUO_80482C6E5E4D",
                    "device_param": {
                        "firmware_version": "1.0.0.167",
                        "thumbnail": {"url": "https://cloud-thumb"},
                        "p2p": {"providers": ["mars", "webrtc"]},
                    },
                    "nickname": "Bar Cam",
                    "device_model": "GW_DUO",
                    "device_category": "Camera",
                }
            ]
        },
    )

    with caplog.at_level("INFO", logger="WyzeBridge"):
        cameras = get_camera_list(WyzeCredential(access_token="token", phone_id="phone"))

    assert len(cameras) == 1
    cam = cameras[0]
    assert cam.mac == "GW_DUO_80482C6E5E4D"
    assert cam.firmware_ver == "1.0.0.154"
    assert cam.thumbnail == "https://legacy-thumb"
    assert cam.enr == "legacy-enr"
    assert cam.ip == "192.168.1.10"
    assert cam.p2p_type == 3
    assert "V4 validation summary: legacy=1 cloud=1 shared=1 legacy_only=0 cloud_only=0" in caplog.text
    assert "field differences for Bar Cam [GW_DUO]" in caplog.text
    assert "missing critical fields for Bar Cam [GW_DUO] in cloud data: enr, ip" in caplog.text
