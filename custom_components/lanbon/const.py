"""Constants for LANBON HA integration."""
from __future__ import annotations

from typing import Any

DOMAIN = "lanbon"
DEFAULT_PORT = 8765
CONF_TOKEN = "token"
CONF_HOST = "host"
CONF_PORT = "port"
SERVICE_SET_CHANNEL_NAME = "set_channel_name"

# Device registry display name prefix (all types, host + children).
DEVICE_NAME_PREFIX = "LANBON-L10"
MANUFACTURER = "LANBON"


def format_device_name(
    *,
    mac: str,
    is_host: bool = False,
    name: str | None = None,
    sw_type: int | str | None = None,
) -> str:
    """Always return a LANBON-L10-prefixed device name.

    Prefer firmware ``name`` (type label). If missing, map ``sw_type``.
    Fall back to Host / MAC suffix.
    """
    text = (name or "").strip()
    if not text and sw_type is not None:
        # Local import: device_types has no dependency on this module.
        from .device_types import dev_type_name

        mapped = dev_type_name(sw_type)
        if mapped and mapped not in (DEVICE_NAME_PREFIX, "LANBON"):
            text = mapped

    # Strip any previous LANBON / LANBON-L10 prefix before re-applying.
    if text:
        for old in (DEVICE_NAME_PREFIX, "LANBON"):
            if text == old:
                text = ""
                break
            if text.startswith(f"{old} "):
                text = text[len(old) :].strip(" -_")
                break

    if text:
        return f"{DEVICE_NAME_PREFIX} {text}"
    if is_host:
        return f"{DEVICE_NAME_PREFIX} Host"
    suffix = (mac or "")[-4:].upper()
    return f"{DEVICE_NAME_PREFIX} {suffix}".rstrip()


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
