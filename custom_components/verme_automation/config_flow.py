"""Config flow for Verme Automation integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import paho.mqtt.client as mqtt

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_MQTT_HOST,
    CONF_MQTT_PORT,
    CONF_MQTT_USERNAME,
    CONF_MQTT_PASSWORD,
    DEFAULT_MQTT_PORT,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MQTT_HOST): str,
        vol.Optional(CONF_MQTT_PORT, default=DEFAULT_MQTT_PORT): int,
        vol.Required(CONF_MQTT_USERNAME): str,
        vol.Required(CONF_MQTT_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect to MQTT broker.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    
    def test_connection():
        """Test MQTT connection."""
        client = mqtt.Client()
        
        try:
            if data[CONF_MQTT_USERNAME] and data[CONF_MQTT_PASSWORD]:
                client.username_pw_set(
                    data[CONF_MQTT_USERNAME], 
                    data[CONF_MQTT_PASSWORD]
                )
            
            client.connect(
                data[CONF_MQTT_HOST], 
                data[CONF_MQTT_PORT], 
                60
            )
            client.disconnect()
            return True
        except Exception as err:
            _LOGGER.error("Failed to connect to MQTT broker: %s", err)
            return False
    
    # Test the connection in the executor to avoid blocking
    connection_result = await hass.async_add_executor_job(test_connection)
    
    if not connection_result:
        raise CannotConnect
    
    # Return info that you want to store in the config entry.
    return {"title": f"Verme Automation ({data[CONF_MQTT_HOST]})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Verme Automation."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
