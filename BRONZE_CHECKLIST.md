# Path to official Home Assistant Core (Bronze)

Use this checklist before opening a PR against [home-assistant/core](https://github.com/home-assistant/core).
Rules: [Quality scale checklist](https://developers.home-assistant.io/docs/core/integration-quality-scale/checklist/).

## Repos to open (3 PRs) — still pending

1. **Core** — `homeassistant/components/lanbon/` (code from this package)
2. **Brands** — `home-assistant/brands` → `core_integrations/lanbon/` (**only after** Core accepts the integration; custom_integrations PRs are rejected)
3. **Docs** — `home-assistant/home-assistant.io` — copy from [docs/lanbon.markdown](docs/lanbon.markdown)

## Bronze status (LANBON **0.2.2**)

| Rule | Status | Notes |
|---|---|---|
| config-flow | Done | User + zeroconf |
| test-before-configure | Done | GET `/api/v1/info` |
| test-before-setup | Done | Coordinator first refresh |
| unique-config-entry | Done | MAC unique_id |
| entity-unique-id | Done | `{mac}_sw_{i}` etc. |
| has-entity-name | Done | |
| appropriate-polling | Done | WS + 30s poll |
| docs-installation-instructions | Done | README + `docs/lanbon.markdown` |
| docs-description / removal | Done | `docs/lanbon.markdown` |
| brands | Exempt (pre-Core) | Local `brand/` for HA≥2026.3 |
| config-flow-test-coverage | Done | `tests/test_config_flow.py` |
| action-setup | Done | Service register / last-entry remove |
| runtime-data | Done | `LanbonRuntimeData` |
| reauthentication-flow | Todo (Silver) | Token change |

## Before Core PR

- [x] Split / publish public git repo — https://github.com/LANBON2026/homeassistant-lanbon
- [x] Replace `manifest.json` `documentation` / `issue_tracker` / `codeowners` with real URLs
- [x] English base strings + translations
- [x] Add config_flow tests with mocked API (`tests/test_config_flow.py`)
- [x] Draft HA.io page (`docs/lanbon.markdown`)
- [ ] Remove HACS-only files from the Core copy (`hacs.json`, `tools_*.py`) when opening the PR
- [ ] Open Core PR + run `script.hassfest` / `pytest tests/components/lanbon` in core tree
- [ ] Open home-assistant.io PR from `docs/lanbon.markdown`
- [ ] After Core merge: brands `core_integrations/lanbon/`

## Do not expand yet

- Changing `DM_LPOLD_DEV_CTRL_OBJ_NUM_MAX` (mesh) — separate firmware PR
- Cloud MQTT as a dependency for local control
