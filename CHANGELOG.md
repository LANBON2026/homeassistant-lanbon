# Changelog

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
