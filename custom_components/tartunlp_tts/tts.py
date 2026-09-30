"""Support for TartuNLP Text-to-Speech service."""
from __future__ import annotations

import logging
import re
import aiohttp
from typing import Any

import voluptuous as vol

from homeassistant.components.tts import (
    CONF_LANG,
    PLATFORM_SCHEMA,
    TextToSpeechEntity,
    Voice,
)
from homeassistant.core import HomeAssistant, callback, split_entity_id
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.const import CONF_LANGUAGE, Platform

from .const import (
    DOMAIN,
    DEFAULT_LANG,
    DEFAULT_VOICE,
    DEFAULT_BASE_URL,
    DEFAULT_SPEED,
    MIN_SPEED,
    MAX_SPEED,
    CONF_VOICE,
    CONF_BASE_URL,
    CONF_SPEED,
    SUPPORTED_VOICES,
)
from .util import get_domain_from_url

_LOGGER = logging.getLogger(__name__)


def _clamp_speed(value: Any) -> float:
    """Coerce speed to float within the range the API accepts."""
    try:
        speed = float(value)
    except (TypeError, ValueError):
        _LOGGER.warning("Invalid speed %r, using %s", value, DEFAULT_SPEED)
        return DEFAULT_SPEED
    return min(max(speed, MIN_SPEED), MAX_SPEED)


_LEGACY_ID = re.compile(r"^tartunlp_tts_(\d+)$")


def _legacy_num(value: str) -> int | None:
    """Return N for a legacy "tartunlp_tts_N" identifier, else None."""
    match = _LEGACY_ID.match(value)
    return int(match.group(1)) if match else None


@callback
def _async_prepare_registry(hass: HomeAssistant) -> None:
    """Give every config entry exactly one registry entity keyed by its entry_id.

    Earlier versions derived the unique ID from the number of config entries, so
    all entries ended up with the same ID. Move each entry's lowest legacy entity
    to the new unique ID (keeping its entity_id), drop its unreachable duplicates
    and pre-register entities for entries that have none. New entity IDs continue
    above the highest legacy number, so a removed ID is never handed to another
    voice. This runs synchronously, so concurrent entry setups cannot interleave.
    """
    registry = er.async_get(hass)
    platform_entities = [
        reg for reg in registry.entities.values()
        if reg.platform == DOMAIN and reg.domain == Platform.TTS
    ]

    max_num = 0
    for reg in platform_entities:
        for value in (reg.unique_id, split_entity_id(reg.entity_id)[1]):
            num = _legacy_num(value)
            if num is not None:
                max_num = max(max_num, num)

    entries = hass.config_entries.async_entries(DOMAIN)

    for entry in entries:
        if registry.async_get_entity_id(Platform.TTS, DOMAIN, entry.entry_id):
            continue
        legacy = sorted(
            (
                reg for reg in platform_entities
                if reg.config_entry_id == entry.entry_id
                and _legacy_num(reg.unique_id) is not None
            ),
            key=lambda reg: _legacy_num(reg.unique_id),
        )
        if not legacy:
            continue
        keep, *duplicates = legacy
        registry.async_update_entity(keep.entity_id, new_unique_id=entry.entry_id)
        for duplicate in duplicates:
            registry.async_remove(duplicate.entity_id)
        _LOGGER.info(
            "Migrated %s to unique ID %s, removed %s",
            keep.entity_id, entry.entry_id, [dup.entity_id for dup in duplicates],
        )

    for entry in entries:
        if registry.async_get_entity_id(Platform.TTS, DOMAIN, entry.entry_id):
            continue
        max_num += 1
        registry.async_get_or_create(
            Platform.TTS,
            DOMAIN,
            entry.entry_id,
            config_entry=entry,
            suggested_object_id=f"tartunlp_tts_{max_num}",
        )


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_LANG, default=DEFAULT_LANG): vol.In(["et"]),
        vol.Optional(CONF_VOICE, default=DEFAULT_VOICE): vol.In(SUPPORTED_VOICES),
        vol.Optional(CONF_SPEED, default=DEFAULT_SPEED): vol.All(
            vol.Coerce(float), vol.Range(min=MIN_SPEED, max=MAX_SPEED)
        ),
        vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
    }
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigType,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TartuNLP TTS from config entry."""
    language = config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANG)
    voice = config_entry.data.get(CONF_VOICE, DEFAULT_VOICE)
    speed = config_entry.data.get(CONF_SPEED, DEFAULT_SPEED)
    base_url = config_entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)

    # The registry entry prepared here decides the entity_id
    _async_prepare_registry(hass)

    async_add_entities([TartuNLPTTSEntity(hass, config_entry, language, voice, speed, base_url, config_entry.entry_id)], True)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up TartuNLP TTS platform from YAML."""
    language = config.get(CONF_LANG, DEFAULT_LANG)
    voice = config.get(CONF_VOICE, DEFAULT_VOICE)
    speed = config.get(CONF_SPEED, DEFAULT_SPEED)
    base_url = config.get(CONF_BASE_URL, DEFAULT_BASE_URL)

    # For YAML-based setup, use yaml suffix
    async_add_entities([TartuNLPTTSEntity(hass, None, language, voice, speed, base_url, "tartunlp_tts_yaml", "tts.tartunlp_tts_yaml")], True)

class TartuNLPTTSEntity(TextToSpeechEntity):
    """The TartuNLP TTS API provider."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        config_entry: ConfigType | None,
        language: str, 
        voice: str,
        speed: float,
        base_url: str,
        unique_id: str,
        entity_id: str | None = None,
    ) -> None:
        """Initialize TartuNLP TTS provider."""
        self.hass = hass
        self._language = language
        self._voice = voice
        self._speed = _clamp_speed(speed)
        self._base_url = base_url
        
        # Only YAML presets its entity_id; config entries get it from the registry
        if entity_id is not None:
            self.entity_id = entity_id

        self._attr_unique_id = unique_id
        
        # Set descriptive name for display
        domain = get_domain_from_url(base_url)
        self._attr_name = f"TartuNLP TTS - {voice} ({domain})"

    @property
    def supported_languages(self) -> list[str]:
        """Return list of supported languages."""
        return ["et"]

    @property
    def default_language(self) -> str:
        """Return the default language."""
        return self._language

    @property
    def supported_options(self) -> list[str]:
        """Return list of supported options."""
        return [CONF_VOICE, CONF_SPEED]

    @property
    def default_options(self) -> dict[str, Any]:
        """Return a dict with the default options."""
        return {CONF_VOICE: self._voice, CONF_SPEED: self._speed}

    @property
    def available_voices(self) -> list[Voice] | None:
        """Return a list of available voices."""
        return [Voice(voice_id=voice, name=voice) for voice in SUPPORTED_VOICES]

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any] | None = None
    ) -> tuple[str, bytes]:
        """Load TTS from TartuNLP."""
        options = options or {}
        voice = options.get(CONF_VOICE, self._voice)
        speed = _clamp_speed(options.get(CONF_SPEED, self._speed))

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "text": message,
                    "speaker": voice,
                    "speed": speed,
                }

                async with session.post(self._base_url, json=payload) as response:
                    if response.status != 200:
                        _LOGGER.error(
                            "Error %d on API call: %s", 
                            response.status, 
                            await response.text()
                        )
                        return None, None

                    data = await response.read()
                    return "wav", data

        except aiohttp.ClientError as error:
            _LOGGER.error("Error occurred for '%s': %s", message, error)
            return None, None
