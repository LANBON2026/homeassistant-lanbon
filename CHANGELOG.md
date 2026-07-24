# Changelog

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
