"""Constants for LANBON HA integration."""
from __future__ import annotations

from typing import Any

DOMAIN = "lanbon"
DEFAULT_PORT = 8765
CONF_TOKEN = "token"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_WS_DISABLED = "ws_disabled"
SERVICE_SET_CHANNEL_NAME = "set_channel_name"
MANUFACTURER = "LANBON"

# Consecutive WS handshake failures that prove the panel has no WS (not transient offline).
WS_UNSUPPORTED_FAIL_THRESHOLD = 3

# Firmware product tags that serve HTTP-only local API (no /api/v1/ws). L10 keeps WS.
HTTP_ONLY_PRODUCTS = frozenset({"L8", "l8"})


def product_is_http_only(product: Any) -> bool:
    """True when firmware product line has no local WebSocket."""
    if product is None:
        return False
    text = str(product).strip()
    if not text:
        return False
    return text.upper() in {p.upper() for p in HTTP_ONLY_PRODUCTS}


def format_device_name(
    *,
    mac: str,
    is_host: bool = False,
    name: str | None = None,
    sw_type: int | str | None = None,
) -> str:
    """Device registry name from firmware (product line decided by panel).

    Prefer firmware ``name`` / ``type_name``. If missing, map ``sw_type``.
    Fall back to Host / MAC suffix. No hardcoded L8/L10 prefix here.
    """
    text = (name or "").strip()
    if not text and sw_type is not None:
        # Local import: device_types has no dependency on this module.
        from .device_types import dev_type_name

        mapped = dev_type_name(sw_type)
        if mapped and mapped != "LANBON":
            text = mapped

    # Strip legacy HACS-only "LANBON-L10 …" so reload renames cleanly.
    if text.startswith("LANBON-L10 "):
        text = text[len("LANBON-L10 ") :].strip()
    elif text == "LANBON-L10":
        text = ""

    if text:
        return text
    if is_host:
        return "LANBON Host"
    suffix = (mac or "")[-4:].upper()
    return f"LANBON {suffix}".rstrip() if suffix else "LANBON"


def device_name_from_payload(
    dev: dict[str, Any] | None, *, mac: str = "", is_host: bool = False
) -> str:
    """Resolve device display name from a coordinator /devices payload row."""
    if not isinstance(dev, dict):
        return format_device_name(mac=mac, is_host=is_host)
    return format_device_name(
        mac=str(dev.get("mac") or mac or "").upper(),
        is_host=bool(dev.get("is_host", is_host)),
        name=dev.get("name") if isinstance(dev.get("name"), str) else None,
        sw_type=dev.get("sw_type"),
    )
