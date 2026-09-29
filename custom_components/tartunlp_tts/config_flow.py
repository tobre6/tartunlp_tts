"""Config flow for TartuNLP Text-to-Speech integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LANGUAGE
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

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


def _build_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the form schema, prefilled with the given values."""
    return vol.Schema(
        {
            vol.Required(
                CONF_LANGUAGE,
                default=defaults.get(CONF_LANGUAGE, DEFAULT_LANG)
            ): vol.In(["et"]),
            vol.Required(
                CONF_VOICE,
                default=defaults.get(CONF_VOICE, DEFAULT_VOICE)
            ): vol.In(SUPPORTED_VOICES),
            vol.Required(
                CONF_SPEED,
                default=defaults.get(CONF_SPEED, DEFAULT_SPEED)
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_SPEED,
                    max=MAX_SPEED,
                    step=0.05,
                    mode=NumberSelectorMode.SLIDER,
                )
            ),
            vol.Required(
                CONF_BASE_URL,
                default=defaults.get(CONF_BASE_URL, DEFAULT_BASE_URL)
            ): str,
        }
    )


def _entry_data(user_input: dict[str, Any]) -> dict[str, Any]:
    """Convert form input into config entry data."""
    return {
        CONF_LANGUAGE: user_input[CONF_LANGUAGE],
        CONF_VOICE: user_input[CONF_VOICE],
        CONF_SPEED: float(user_input.get(CONF_SPEED, DEFAULT_SPEED)),
        CONF_BASE_URL: user_input[CONF_BASE_URL],
    }


def _entry_title(data: dict[str, Any]) -> str:
    """Build the config entry title."""
    domain = get_domain_from_url(data[CONF_BASE_URL])
    return f"{data[CONF_VOICE]} ({domain})"


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for TartuNLP TTS."""

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            updated_data = _entry_data(user_input)
            # Update the config entry with new data and title
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=updated_data,
                title=_entry_title(updated_data)
            )
            return self.async_create_entry(title="", data=updated_data)

        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(dict(self.config_entry.data)),
        )


class TartuNLPTTSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TartuNLP TTS."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle a flow initiated by the user."""
        if user_input is not None:
            data = _entry_data(user_input)
            return self.async_create_entry(title=_entry_title(data), data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema({}),
        )

    async def async_step_import(self, import_info):
        """Handle import from config file."""
        return await self.async_step_user(import_info)
