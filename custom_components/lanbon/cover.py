"""Cover entities for curtain panels."""
from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LanbonCoordinator

STATE_OPENING = "opening"
STATE_CLOSING = "closing"
STATE_STOPPED = "stopped"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data.coordinator
    api = entry.runtime_data.api
    entities = []
    for dev in (coordinator.data or {}).get("devices") or []:
        kind = dev.get("kind")
        mac = str(dev.get("mac") or "").upper()
        is_host = bool(dev.get("is_host"))
        covers = dev.get("covers")
        if isinstance(covers, list):
            for i, _ in enumerate(covers):
                entities.append(LanbonCover(coordinator, api, mac, i, is_host))
        elif kind in ("cover", "cover_switch") and "cover_state" in dev:
            entities.append(LanbonCover(coordinator, api, mac, 0, is_host))
    async_add_entities(entities)


class LanbonCover(CoordinatorEntity[LanbonCoordinator], CoverEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "curtain"
    _attr_device_class = CoverDeviceClass.CURTAIN
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    def __init__(self, coordinator, api, mac: str, index: int, is_host: bool) -> None:
        super().__init__(coordinator)
        self._api = api
        self._mac = mac
        self._index = index
        self._attr_unique_id = f"{mac}_cover_{index}"
        self._attr_name = "Curtain" if index == 0 else f"Curtain {index + 1}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            manufacturer="LANBON",
            name="LANBON Host" if is_host else f"LANBON {mac[-4:]}",
        )

    def _state_str(self) -> str | None:
        for d in (self.coordinator.data or {}).get("devices") or []:
            if str(d.get("mac") or "").upper() != self._mac:
                continue
            covers = d.get("covers")
            if isinstance(covers, list) and self._index < len(covers):
                return str(covers[self._index])
            return d.get("cover_state")
        return None

    @property
    def available(self) -> bool:
        for d in (self.coordinator.data or {}).get("devices") or []:
            if str(d.get("mac") or "").upper() == self._mac:
                return bool(d.get("available", True))
        return False

    @property
    def is_opening(self) -> bool:
        return self._state_str() == "opening"

    @property
    def is_closing(self) -> bool:
        return self._state_str() == "closing"

    @property
    def is_closed(self) -> bool | None:
        """No resting open/closed — panel gears are motion/stop only."""
        return None

    @property
    def state(self) -> str | None:
        """正在开启 / 正在关闭 / 停止."""
        st = self._state_str()
        # Accept legacy open/closed from older firmware too
        if st in ("opening", "open"):
            return STATE_OPENING
        if st in ("closing", "closed"):
            return STATE_CLOSING
        if st == "stopped":
            return STATE_STOPPED
        return None

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._api.async_command(
            {"mac": self._mac, "op": "cover_set", "command": "OPEN", "index": self._index}
        )
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._api.async_command(
            {"mac": self._mac, "op": "cover_set", "command": "CLOSE", "index": self._index}
        )
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self._api.async_command(
            {"mac": self._mac, "op": "cover_set", "command": "STOP", "index": self._index}
        )
        await self.coordinator.async_request_refresh()
