"""Cover entities from LOIP components with type=cover.

Only open/close/stop is guaranteed; position reporting depends on the
declared LOIP constraints (L10 host declares it, L10 mesh child and
2749 baseline do not). Never fabricate set_position when the gateway
does not advertise it.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LanbonConfigEntry
from .entity import LanbonEntity, async_send_loip
from .entity_map import cover_position_range, iter_cover_components


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LanbonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities = [
        LanbonCover(coordinator, device.id, component.id)
        for device, component in iter_cover_components(coordinator.data)
    ]
    async_add_entities(entities)


class LanbonCover(LanbonEntity, CoverEntity):
    @property
    def supported_features(self) -> CoverEntityFeature:
        features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        if self._position_range() is not None:
            features |= CoverEntityFeature.SET_POSITION
        return features

    def _position_range(self) -> tuple[int, int] | None:
        _device, component = self._pair()
        return cover_position_range(component)

    @property
    def current_cover_position(self) -> int | None:
        _device, component = self._pair()
        if component is None or self._position_range() is None:
            return None
        value = component.state.get("position")
        if not isinstance(value, int) or isinstance(value, bool):
            return None
        lo, hi = self._position_range()
        return max(lo, min(hi, value))

    @property
    def is_closed(self) -> bool | None:
        _device, component = self._pair()
        if component is None:
            return None
        if self._position_range() is not None:
            position = self.current_cover_position
            return None if position is None else position <= 0
        # No position declared: cannot tell open/closed from motion alone.
        return None

    @property
    def is_opening(self) -> bool | None:
        _device, component = self._pair()
        if component is None:
            return None
        return component.state.get("motion") == "opening"

    @property
    def is_closing(self) -> bool | None:
        _device, component = self._pair()
        if component is None:
            return None
        return component.state.get("motion") == "closing"

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._send("open", {})

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._send("close", {})

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self._send("stop", {})

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        position = kwargs.get("position")
        lo, hi = self._position_range() or (0, 100)
        if not isinstance(position, int) or isinstance(position, bool):
            raise HomeAssistantError("position must be an integer")
        await self._send("set_position", {"position": max(lo, min(hi, position))})

    async def _send(self, command: str, params: dict) -> None:
        await async_send_loip(
            self.coordinator, self._device_id, self._component_id, command, params
        )
