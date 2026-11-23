"""Shared LOIP entity: name, availability, and one command path."""

from __future__ import annotations

from typing import Any

from aiolanbon import LanbonAuthError, LanbonError

from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    device_display_name,
    device_model_label,
)
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


def build_device_info(
    coordinator: LanbonCoordinator, device_id: str
) -> DeviceInfo:
    """Build DeviceInfo from the per-device LOIP row (not gateway /info alone)."""
    info = coordinator.info
    snap = coordinator.data
    device = snap.device(device_id) if snap is not None else None
    gateway_model = info.model if info else None
    model = device_model_label(
        device_model=device.model if device else None,
        gateway_model=gateway_model,
    )
    name = device_display_name(
        device_model=device.model if device else None,
        device_name=device.name if device else None,
        gateway_model=gateway_model,
    )
    manufacturer = (
        (device.manufacturer if device and device.manufacturer else None)
        or MANUFACTURER
    )
    kwargs: dict[str, Any] = {
        "identifiers": {(DOMAIN, device_id)},
        "manufacturer": manufacturer,
        "name": name,
    }
    if model:
        kwargs["model"] = model
    if device and device.firmware_version:
        kwargs["sw_version"] = device.firmware_version
    if device and device.hardware_version:
        kwargs["hw_version"] = device.hardware_version
    gateway_id = info.gateway_id if info else None
    if (
        device
        and gateway_id
        and device.id != gateway_id
        and (device.role or "").lower() == "child"
    ):
        kwargs["via_device"] = (DOMAIN, gateway_id)
    return DeviceInfo(**kwargs)


class LanbonEntity(CoordinatorEntity[LanbonCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: LanbonCoordinator, device_id: str, component_id: str
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._component_id = component_id
        self._attr_unique_id = f"{device_id}_{component_id}"
        self._attr_device_info = build_device_info(coordinator, device_id)
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
