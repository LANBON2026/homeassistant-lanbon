"""Shared LOIP entity: name, availability, and one command path."""

from __future__ import annotations

from aiolanbon import LanbonAuthError, LanbonError

from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import LanbonCoordinator


async def async_send_loip(
    coordinator: LanbonCoordinator,
    device_id: str,
    component_id: str,
    command: str,
    params: dict,
) -> None:
    """Send one LOIP command and refresh. Auth failure reauths the entry."""
    try:
        await coordinator.client.send_command(device_id, component_id, command, params)
    except LanbonAuthError as err:
        raise ConfigEntryAuthFailed("unauthorized") from err
    except LanbonError as err:
        raise HomeAssistantError(str(err)) from err
    await coordinator.async_request_refresh()


class LanbonEntity(CoordinatorEntity[LanbonCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: LanbonCoordinator, device_id: str, component_id: str
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._component_id = component_id
        self._attr_unique_id = f"{device_id}_{component_id}"
        info = coordinator.info
        model = info.model if info else None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer=MANUFACTURER,
            model=model,
            name=(info.model or MANUFACTURER) if info else MANUFACTURER,
        )
        self._sync_name()

    def _pair(self):
        snap = self.coordinator.data
        if snap is None:
            return None, None
        device = snap.device(self._device_id)
        if device is None:
            return None, None
        return device, device.component(self._component_id)

    def _sync_name(self) -> None:
        _device, component = self._pair()
        if component is not None:
            self._attr_name = component.name or self._component_id

    @property
    def available(self) -> bool:
        device, component = self._pair()
        return bool(
            super().available
            and self.coordinator.last_update_success
            and device
            and device.online
            and component
            and component.enabled
        )

    def _handle_coordinator_update(self) -> None:
        self._sync_name()
        super()._handle_coordinator_update()
