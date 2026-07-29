"""Constants for LANBON HA integration."""
DOMAIN = "lanbon"
DEFAULT_PORT = 8765
CONF_TOKEN = "token"
CONF_HOST = "host"
CONF_PORT = "port"
SERVICE_SET_CHANNEL_NAME = "set_channel_name"

# Device registry display name prefix (HA Devices page / entity device header).
DEVICE_NAME_PREFIX = "LANBON-L10"
MANUFACTURER = "LANBON"


def format_device_name(
    *, mac: str, is_host: bool = False, name: str | None = None
) -> str:
    """Build device name with LANBON-L10 prefix.

    Prefer firmware type name (e.g. 调光器 / 窗帘); fall back to Host / MAC suffix.
    """
    text = (name or "").strip()
    if text:
        for old in (DEVICE_NAME_PREFIX, "LANBON"):
            if text == old or text.startswith(f"{old} "):
                rest = text[len(old) :].strip(" -_")
                return f"{DEVICE_NAME_PREFIX} {rest}" if rest else DEVICE_NAME_PREFIX
        return f"{DEVICE_NAME_PREFIX} {text}"
    if is_host:
        return f"{DEVICE_NAME_PREFIX} Host"
    suffix = mac[-4:].upper() if mac else ""
    return f"{DEVICE_NAME_PREFIX} {suffix}".rstrip()
