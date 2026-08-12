"""Config flow for NeoRé."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .api import (
    NeoApiAuthError,
    NeoApiClient,
    NeoApiConnectionError,
    NeoApiError,
    controller_id,
    normalize_base_url,
)
from .const import CONF_BASE_URL, DEFAULT_PASSWORD, DEFAULT_USERNAME, DOMAIN


class NeoReConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a NeoRé config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                base_url = normalize_base_url(user_input[CONF_HOST])
                api = NeoApiClient(
                    base_url,
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
                await self.hass.async_add_executor_job(api.validate_connection)
            except ValueError:
                errors["base"] = "invalid_host"
            except NeoApiAuthError:
                errors["base"] = "invalid_auth"
            except NeoApiConnectionError:
                errors["base"] = "cannot_connect"
            except NeoApiError:
                errors["base"] = "invalid_response"
            except Exception:  # noqa: BLE001 - keep config flow user friendly
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(controller_id(base_url))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=controller_id(base_url),
                    data={
                        CONF_BASE_URL: base_url,
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
                vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
                vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
