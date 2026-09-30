# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Home Assistant custom integration (distributed via HACS) that exposes the TartuNLP Estonian text-to-speech API (`https://api.tartunlp.ai/text-to-speech/v2`) as a `tts` platform entity. All code lives in `custom_components/tartunlp_tts/`. The README and release notes are written in Estonian.

## Build, lint, test

There is no local build, lint config, or test suite. Validation happens only in GitHub Actions, and all workflows are `workflow_dispatch` (manual) unless noted:

- `validate.yml`: runs `hassfest` and the HACS action (category `integration`).
- `release.yml`: triggered by pushing a tag named `release` (or manually). Reads `version` from `manifest.json` and creates a GitHub release tagged `v<version>`. The `needs: validate` dependency is commented out, so releases are not blocked by validation failures.
- `bump-version.yml`: increments the patch number in `manifest.json` and commits it.

For a quick local sanity check, `python -m py_compile custom_components/tartunlp_tts/*.py` works without Home Assistant installed. Real testing requires loading the component into a Home Assistant instance (minimum version `2024.11.0`, per `hacs.json`).

When releasing, bump `version` in `custom_components/tartunlp_tts/manifest.json`; that value is the source of truth for release tags.

## Architecture

- `__init__.py`: config entry setup. Forwards to `Platform.TTS` and registers an update listener that reloads the entry whenever it changes.
- `config_flow.py`: the user config flow and the options flow (`OptionsFlowHandler`) share one form schema (`_build_schema`). The options flow writes changes back into `entry.data` (not `entry.options`) and updates the entry title to `"<voice> (<api domain>)"`, which then triggers a reload via the update listener. Do not assign `self.config_entry` in the options flow; Home Assistant provides it, and assigning it raises an error on 2025.12 and later.
- `tts.py`: `TartuNLPTTSEntity`. Supports both config entry setup and legacy YAML platform setup (`PLATFORM_SCHEMA`). Each request opens a new `aiohttp.ClientSession` and POSTs `{"text": ..., "speaker": <voice>, "speed": <0.5 to 2>}` to the configured base URL; the response body is returned as `wav`. `voice` and `speed` can be overridden per call via `tts.speak` options, and speed is clamped to the API range. On errors it logs and returns `(None, None)`.
- `const.py`: domain, defaults (`et`, voice `mari`, speed `1.0`), config keys, speed range, and `SUPPORTED_VOICES`. The voice list is duplicated in the README; keep both in sync.
- `util.py`: `get_domain_from_url`, used for entry titles and entity names.
- `translations/en.json` and `translations/et.json`: UI strings for the `user` config step and `init` options step. Any new form field needs entries in both.

### Things to know before changing behavior

- Unique IDs are the config entry ID. On setup, `_async_prepare_registry` in `tts.py` migrates older count based IDs (`tartunlp_tts_<n>`) to the entry ID, keeping the existing `entity_id`, and pre-registers new entities as `tts.tartunlp_tts_<n>` numbered above the highest legacy number. YAML setup uses `tartunlp_tts_yaml`.
- Entries created before speed existed have no `speed` in `entry.data`; always read it with a `DEFAULT_SPEED` fallback.
- Design notes for larger changes live in `docs/`.
- Only language `et` is supported; the language selector exists in the forms but offers a single choice.
