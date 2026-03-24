from unittest.mock import patch

from wyzecam.api_models import WyzeCamera, WyzeCredential
from wyzebridge.wyze_api import WyzeApi


def build_api(cam: WyzeCamera) -> WyzeApi:
    api = WyzeApi()
    api.auth = WyzeCredential(access_token="token", phone_id="phone")
    api.cameras = [cam]
    return api


def test_get_kvs_signal_keeps_legacy_kvs_path():
    cam = WyzeCamera(
        p2p_id="legacy",
        p2p_type=1,
        ip="192.168.1.10",
        enr="legacy-enr",
        mac="AA:BB",
        product_model="HL_PAN3",
        nickname="Bedroom Cam",
        timezone_name="Europe/London",
        firmware_ver="4.50.16.6114",
        dtls=1,
        parent_dtls=None,
        parent_enr=None,
        parent_mac=None,
        thumbnail="https://thumb",
        p2p_providers=["webrtc"],
    )
    api = build_api(cam)

    with patch("wyzebridge.wyze_api.get_cam_webrtc", return_value={"signalingUrl": "wss://legacy", "ClientId": "id", "signalToken": "token", "servers": []}) as legacy, patch(
        "wyzebridge.wyze_api.get_cam_webrtc_v4"
    ) as mars:
        result = api.get_kvs_signal(cam.name_uri)

    assert result["result"] == "ok"
    assert result["provider"] == "kvs"
    legacy.assert_called_once_with(api.auth, cam.mac)
    mars.assert_not_called()


def test_get_kvs_signal_reports_mars_as_not_yet_supported():
    cam = WyzeCamera(
        p2p_id=None,
        p2p_type=2,
        ip=None,
        enr=None,
        mac="GW_DUO_80482C6E5E4D",
        product_model="GW_DUO",
        nickname="Bar Cam",
        timezone_name=None,
        firmware_ver="1.0.0.167",
        dtls=None,
        parent_dtls=None,
        parent_enr=None,
        parent_mac=None,
        thumbnail="https://thumb",
        p2p_providers=["mars", "webrtc"],
    )
    api = build_api(cam)

    with patch("wyzebridge.wyze_api.get_cam_webrtc") as legacy, patch(
        "wyzebridge.wyze_api.get_cam_webrtc_v4",
        return_value={"signalingUrl": "wss://mars", "servers": [], "authToken": "", "provider": "webrtc"},
    ) as mars:
        result = api.get_kvs_signal(cam.name_uri)

    assert result["provider"] == "mars"
    assert result["signalingUrl"] == "wss://mars"
    assert "Mars websocket handshake is not yet supported" in result["result"]
    legacy.assert_not_called()
    mars.assert_called_once_with(api.auth, cam)
