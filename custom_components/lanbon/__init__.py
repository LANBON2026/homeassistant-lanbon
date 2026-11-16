"""LANBON LOIP integration setup. Communication goes only through aiolanbon."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from aiolanbon import LanbonAuthError, LanbonClient
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_GATEWAY_ID, CONF_SCHEME, CONF_TOKEN, DOMAIN
from .coordinator import LanbonCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SWITCH, Platform.LIGHT, Platform.FAN]


@dataclass
class LanbonRuntimeData:
    client: LanbonClient
    coordinator: LanbonCoordinator


LanbonConfigEntry = ConfigEntry


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
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug(
        "LANBON LOIP setup host=%s gateway=%s",
        host,
        entry.data.get(CONF_GATEWAY_ID, ""),
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LanbonConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
