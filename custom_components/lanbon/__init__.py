"""LANBON LOIP integration setup. Communication goes only through aiolanbon."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from aiolanbon import LanbonAuthError, LanbonClient
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_GATEWAY_ID,
    CONF_SCHEME,
    CONF_TOKEN,
    DOMAIN,
    MANUFACTURER,
    device_display_name,
    device_model_label,
)
from .coordinator import LanbonCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SWITCH,
    Platform.LIGHT,
    Platform.FAN,
    Platform.COVER,
    Platform.SCENE,
]


@dataclass
class LanbonRuntimeData:
    client: LanbonClient
    coordinator: LanbonCoordinator


LanbonConfigEntry = ConfigEntry


def _sync_devices_from_snapshot(
    hass: HomeAssistant, entry: LanbonConfigEntry, coordinator: LanbonCoordinator
) -> None:
    """Create/update device registry rows from LOIP /devices (per-device model)."""
    snap = coordinator.data
    if snap is None:
        return
    info = coordinator.info
    gateway_model = info.model if info else None
    gateway_id = (info.gateway_id if info else None) or entry.data.get(CONF_GATEWAY_ID)
    registry = dr.async_get(hass)

    for device in snap.devices:
        model = device_model_label(
            device_model=device.model, gateway_model=gateway_model
        )
        name = device_display_name(
            device_model=device.model,
            device_name=device.name,
            gateway_model=gateway_model,
        )
        kwargs: dict = {
            "config_entry_id": entry.entry_id,
            "identifiers": {(DOMAIN, device.id)},
            "manufacturer": device.manufacturer or MANUFACTURER,
            "name": name,
        }
        if model:
            kwargs["model"] = model
        if device.firmware_version:
            kwargs["sw_version"] = device.firmware_version
        if device.hardware_version:
            kwargs["hw_version"] = device.hardware_version
        if (
            gateway_id
            and device.id != gateway_id
            and (device.role or "").lower() == "child"
        ):
            kwargs["via_device"] = (DOMAIN, gateway_id)
        reg_dev = registry.async_get_or_create(**kwargs)
        # Fix stale names from older builds that copied gateway model onto every child.
        updates: dict = {}
        if reg_dev.name_by_user is None and reg_dev.name != name:
            updates["name"] = name
        if model and reg_dev.model != model:
            updates["model"] = model
        if updates:
            registry.async_update_device(reg_dev.id, **updates)


async def async_setup_entry(hass: HomeAssistant, entry: LanbonConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    port = int(entry.data.get(CONF_PORT, 8765))
    token = entry.data[CONF_TOKEN]
    scheme = entry.data.get(CONF_SCHEME, "http")
    session = async_get_clientsession(hass)
    client = LanbonClient(host, port, token, session, scheme=scheme)
    coordinator = LanbonCoordinator(hass, entry, client)
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        raise
    except Exception as err:
        raise ConfigEntryNotReady(str(err)) from err

    entry.runtime_data = LanbonRuntimeData(client=client, coordinator=coordinator)
    entry.async_on_unload(coordinator.async_on_unload)
    _sync_devices_from_snapshot(hass, entry, coordinator)

    @callback
    def _on_coordinator_update() -> None:
        _sync_devices_from_snapshot(hass, entry, coordinator)

    entry.async_on_unload(coordinator.async_add_listener(_on_coordinator_update))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug(
        "LANBON LOIP setup host=%s gateway=%s",
        host,
        entry.data.get(CONF_GATEWAY_ID, ""),
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LanbonConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
