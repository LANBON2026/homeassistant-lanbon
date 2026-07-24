# Path to official Home Assistant Core (Bronze)

Use this checklist before opening a PR against [home-assistant/core](https://github.com/home-assistant/core).
Rules: [Quality scale checklist](https://developers.home-assistant.io/docs/core/integration-quality-scale/checklist/).

## Repos to open (3 PRs)

1. **Core** — `homeassistant/components/lanbon/` (code from this package)
2. **Brands** — `home-assistant/brands` — `lanbon/icon.png` + `logo.png` (see `custom_components/lanbon/brand/`)
3. **Docs** — `home-assistant/home-assistant.io` — `source/_integrations/lanbon.markdown`

## Bronze status (LANBON 0.2.0)

| Rule | Status | Notes |
|---|---|---|
| config-flow | Done | User + zeroconf |
| test-before-configure | Done | GET `/api/v1/info` |
| test-before-setup | Done | Coordinator first refresh |
| unique-config-entry | Done | MAC unique_id |
| entity-unique-id | Done | `{mac}_sw_{i}` etc. |
| has-entity-name | Done | |
| appropriate-polling | Done | WS + 30s poll |
| docs-installation-instructions | Done (HACS README) | Need HA.io page for Core |
| brands | Todo | Submit brand assets |
| config-flow-test-coverage | Todo | pytest in core tree |
| action-setup | Todo | Core service registration style |
| docs-description / removal | Todo | HA.io |
| reauthentication-flow | Todo (Silver) | Token change |

## Before Core PR

- [ ] Split / publish public git repo for HA (not only firmware monorepo)
- [ ] Replace `manifest.json` `documentation` / `issue_tracker` / `codeowners` with real URLs
- [ ] Remove HACS-only files from the Core copy (`hacs.json`, tools_*.py)
- [ ] Add `tests/components/lanbon/` with mocked aiohttp (info / devices / command / WS)
- [ ] Run `python -m script.hassfest` and `pytest tests/components/lanbon`
- [ ] Confirm firmware `proto: 1` devices available for reviewers (or provide mock)
- [ ] English-only strings in Core; keep translations in `translations/`

## Do not expand yet

- Changing `DM_LPOLD_DEV_CTRL_OBJ_NUM_MAX` (mesh) — separate firmware PR
- Cloud MQTT as a dependency for local control
