# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Home Assistant custom integration (distributed via HACS) that exposes the TartuNLP Estonian text-to-speech API (`https://api.tartunlp.ai/text-to-speech/v2`) as a `tts` platform entity. All code lives in `custom_components/tartunlp_tts/`. The README and release notes are written in Estonian.

## Build, lint, test

There is no local build, lint config, or test suite. Validation happens only in GitHub Actions, and all workflows are `workflow_dispatch` (manual) unless noted:

- `validate.yml`: runs `hassfest` and the HACS action (category `integration`).
- `release.yml`: triggered by pushing a tag named `release` (or manually). Reads `version` from `manifest.json` and creates a GitHub release tagged `v<version>`. The `needs: validate` dependency is commented out, so releases are not blocked by validation failures.
- `bump-version.yml`: increments the patch number in `manifest.json` and commits it.

For a quick local sanity check, `python -m py_compile custom_components/tartunlp_tts/*.py` works without Home Assistant installed. Real testing requires loading the component into a Home Assistant instance (minimum version `2024.1.0`, per `hacs.json`).

When releasing, bump `version` in `custom_components/tartunlp_tts/manifest.json`; that value is the source of truth for release tags.

## Architecture

- `__init__.py`: config entry setup. Forwards to `Platform.TTS` and registers an update listener that reloads the entry whenever it changes.
- `config_flow.py`: contains both the user config flow and the **active** options flow (`OptionsFlowHandler`). The options flow writes changes back into `entry.data` (not `entry.options`) and updates the entry title to `"<voice> (<api domain>)"`, which then triggers a reload via the update listener.
- `options_flow.py`: an older, **unused** options flow (not referenced anywhere, and lacks the `base_url` field). Edit `config_flow.py` instead.
- `tts.py`: `TartuNLPTTSEntity`. Supports both config entry setup and legacy YAML platform setup (`PLATFORM_SCHEMA`). Each request opens a new `aiohttp.ClientSession` and POSTs `{"text": ..., "speaker": <voice>}` to the configured base URL; the response body is returned as `wav`. On errors it logs and returns `(None, None)`.
- `const.py`: domain, defaults (`et`, voice `mari`), config keys, and `SUPPORTED_VOICES`. The voice list is duplicated in the README; keep both in sync.
- `translations/en.json` and `translations/et.json`: UI strings for the `user` config step and `init` options step. Any new form field needs entries in both.

### Things to know before changing behavior

- Entity IDs and unique IDs are derived from the count of other config entries at setup time (`tts.tartunlp_tts_<n>`), or the suffix `yaml` for YAML setup. They are not tied to the entry ID, so adding or removing entries can shift numbering.
- `get_domain_from_url` is duplicated in `config_flow.py` and `tts.py`.
- Only language `et` is supported; the language selector exists in the forms but offers a single choice.
