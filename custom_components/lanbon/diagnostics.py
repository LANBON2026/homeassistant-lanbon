"""Diagnostics without token, URL query, or Authorization header."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import LanbonConfigEntry
from .const import CONF_TOKEN

_REDACT = {CONF_TOKEN, "token", "authorization", "Authorization"}


def _component_rows(snap, type_name: str) -> list[dict[str, Any]]:
    return [
        {
            "device_id": device.id,
            "component_id": component.id,
            "type": component.type,
            "commands": list(component.commands),
        }
        for device in (snap.devices if snap else ())
        for component in device.components
        if component.type == type_name
    ]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: LanbonConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data.coordinator
    snap = coordinator.data
    info = coordinator.info
    payload = {
        "entry": {
            "host": entry.data.get("host"),
            "port": entry.data.get("port"),
            "scheme": entry.data.get("scheme"),
            "gateway_id": entry.data.get("gateway_id"),
        },
        "info": {
            "protocol": info.protocol if info else None,
            "protocol_version": info.protocol_version if info else None,
            "gateway_id": info.gateway_id if info else None,
            "api_enabled": info.api_enabled if info else None,
            "events": info.transports.events if info else None,
            "model": info.model if info else None,
        },
        "revision": snap.revision if snap else None,
        "switch_components": _component_rows(snap, "switch"),
        "light_components": _component_rows(snap, "light"),
        "fan_components": _component_rows(snap, "fan"),
        "client": repr(entry.runtime_data.client),
    }
    return async_redact_data(payload, _REDACT)
