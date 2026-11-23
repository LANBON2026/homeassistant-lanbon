"""Constants for the LANBON LOIP Home Assistant integration."""

from __future__ import annotations

DOMAIN = "lanbon"
DEFAULT_PORT = 8765
MANUFACTURER = "LANBON"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_TOKEN = "token"
CONF_GATEWAY_ID = "gateway_id"
CONF_SCHEME = "scheme"

AIOLANBON_COMMIT = "706e56dccd003c79f83c7ddbcdb6d36ae4c71234"
LOIP_PROTOCOL_TAG = "v1.0.0-internal.1"
LOIP_PROTOCOL_COMMIT = "c24f7cdacfee9e2e89d57ce40c84b5c242013680"
PUBLIC_SOURCE_COMMIT = "5440efd351de5f0ef76ae97ea807abdb5dad7f80"


def device_display_name(
    *,
    device_model: str | None = None,
    device_name: str | None = None,
    gateway_model: str | None = None,
) -> str:
    """Device registry title: prefer per-device model (e.g. L8-3G), then name, then gateway model."""
    for candidate in (device_model, device_name, gateway_model):
        text = (candidate or "").strip()
        if text:
            return text
    return MANUFACTURER


def device_model_label(
    *,
    device_model: str | None = None,
    gateway_model: str | None = None,
) -> str | None:
    """Model string for DeviceInfo; prefer the device row over gateway /info."""
    text = (device_model or gateway_model or "").strip()
    return text or None
