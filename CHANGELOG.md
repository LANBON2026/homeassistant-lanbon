# Changelog

## 0.2.12 — 2026-08-07

### Fixed
- Stop WebSocket reconnect storms on HTTP-only panels (e.g. L8 `product=L8`, no `/api/v1/ws`). After product detection or 3 consecutive WS-reject handshakes, disable WS for that config entry and use 30s HTTP poll only. L10 (WS available) unchanged; transient offline does not disable WS.

## 0.2.11 — 2026-08-06

### Fixed
- Entity availability now follows hub reachability: `available = coordinator OK ∧ device.available`. Root unreachable → all entities unavailable; child keepalive 0 → that child only. Does not change control/rename when online.

## 0.2.10 — 2026-08-04

### Changed
- Device registry names no longer hardcode `LANBON-L10`. Display name comes from firmware `name` / `type_name`.
- L10 firmware tags `name`/`type_name` with `L10 …` (same role as L8 embedding product in its label).

## 0.2.7 — 2026-07-29

### Fixed
- Fan platform import crash: use `FanEntityFeature.SET_SPEED` (HA has no `SET_PERCENTAGE` feature flag). Adding a fan panel via HACS left the config entry unable to set up.

## 0.2.6 — 2026-07-29

### Added
- Fan platform for `esdtFan` / `esdtFanEx` (percentage gears 1–3)
- FanEx light channel as a separate switch entity
- Curtain states: opening / closing / stopped

## 0.2.3 — 2026-07-28

### Fixed
- Dimmer brightness mapped 0–100% 1:1 with panel (not 0–127)

## 0.2.2 — 2026-07-24

### Changed
- Use `ConfigEntry.runtime_data` (`LanbonRuntimeData`) instead of `hass.data`
- Service `set_channel_name` unload when last config entry is removed (Bronze action-setup)

### Added
- Config flow unit tests (`tests/test_config_flow.py`)
- HA.io documentation draft (`docs/lanbon.markdown`)

## 0.2.1 — 2026-07-24

### Fixed
- Brand images resized to HA brands specs; added `@2x` assets in `brand/`
- Require Home Assistant **≥ 2026.3.0** so local `brand/` icons show in the UI

### Note
- `home-assistant/brands` no longer accepts custom-integration icons (auto-closed). Icons ship inside this repo under `custom_components/lanbon/brand/`.

## 0.2.0 — 2026-07-24

### Added
- Frozen local API contract (`docs/API.md`, proto **1**)
- Bronze quality-scale tracking (`quality_scale.yaml`, `BRONZE_CHECKLIST.md`)
- HACS-oriented README and install paths

### Fixed
- `services.yaml` format for Home Assistant service registration
- Config flow / translation strings (English base + zh-Hans)

### Notes
- Child channel names in mesh detail cache: indices **0–2** only (firmware `DM_LPOLD_DEV_CTRL_OBJ_NUM_MAX=3`). Index **3+** still applies on the child via espnow, but is not stored in root detail list.

## 0.1.0

- Initial custom integration: mDNS discovery, HTTP/WS local API, switch/light/cover, channel rename.
