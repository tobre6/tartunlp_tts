# Speech speed option and configuration fix

## Requirements

### R1. Configurable speech speed

The TartuNLP v2 API accepts an optional `speed` field in the request body. It is a multiplier between `0.5` and `2` compared to normal speed `1` ([source](https://github.com/TartuNLP/text-to-speech-api)).

1. Speed can be set when adding the integration and changed later under Configure. Default `1.0`, allowed range 0.5 to 2.0.
2. Speed can be overridden per `tts.speak` call, and the per call value wins over the saved one:
   ```yaml
   service: tts.speak
   data:
     entity_id: media_player.my_player
     message: "Tere!"
     options:
       voice: "mari"
       speed: 1.2
   ```
3. YAML platform setup accepts `speed`.
4. Values outside the range are rejected by the form and are never sent to the API. Per call values outside the range are clamped.
5. Existing entries without a saved speed keep working and use `1.0`. No migration is needed.
6. The new field has English and Estonian translations, and the README documents it.

### R2. Fix the configuration error

1. Opening Configure on an existing entry works without errors, and saved changes take effect after the automatic reload.
2. The fix works on the Home Assistant versions declared in `hacs.json`.

## Root cause of the configuration error

`OptionsFlowHandler.__init__` in `config_flow.py` assigned `self.config_entry = config_entry`. Since Home Assistant 2024.11, `OptionsFlow.config_entry` is a read only property that Home Assistant sets itself. Assigning it first logged a deprecation warning, and from 2025.12 it raises `AttributeError: property 'config_entry' of 'OptionsFlowHandler' object has no setter`, which the UI shows as an error when clicking Configure.

## Implementation plan

1. `const.py`: add `CONF_SPEED`, `DEFAULT_SPEED = 1.0`, `MIN_SPEED = 0.5`, `MAX_SPEED = 2.0`.
2. `config_flow.py`
   1. Remove the `__init__` that assigns `self.config_entry`; `async_get_options_flow` returns `OptionsFlowHandler()` and the handler reads the entry Home Assistant provides.
   2. Add speed to the user and options forms as a slider (`NumberSelector`, 0.5 to 2.0, step 0.05).
   3. Prefill the options form from the current entry data, falling back to `1.0`.
   4. Keep saving everything into `entry.data` and updating the title, as before.
   5. Move the duplicated `get_domain_from_url` into one shared module.
3. `tts.py`
   1. Read speed from the config entry or YAML config; add `speed` to `PLATFORM_SCHEMA`.
   2. Add `speed` to `supported_options` and `default_options`.
   3. In `async_get_tts_audio`, resolve speed from call options first, then the saved value, coerce to float, clamp to 0.5 to 2.0, and send it as `"speed"` in the payload.
4. Delete the unused `options_flow.py`.
5. Add `speed` labels to `translations/en.json` and `translations/et.json` for both forms.
6. Bump `manifest.json` to `0.13.0`, raise the minimum in `hacs.json` to `2024.11.0`, document speed in the README, and update `CLAUDE.md`.
7. Verification
   1. Compile check of all Python files.
   2. Run the config and options flows and a TTS request against a mocked API in a Home Assistant test environment.
   3. Manual check in a real Home Assistant: add an entry, open Configure on an existing entry, call `tts.speak` with and without `speed`.

## Out of scope

1. Reusing Home Assistant's shared HTTP session (`async_get_clientsession`).
2. Tying entity IDs to the entry ID instead of the entry count. This renames existing entities and should be a separate change.
