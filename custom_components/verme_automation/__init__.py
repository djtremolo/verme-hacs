"""The Verme Automation integration."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import paho.mqtt.client as mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_MQTT_HOST,
    CONF_MQTT_PORT,
    CONF_MQTT_USERNAME,
    CONF_MQTT_PASSWORD,
    MQTT_BASE_TOPIC,
    MQTT_SHADES_TOPIC,
    MQTT_NODE_SUFFIX,
    NODE_TYPE_SHADE,
    MANUFACTURER,
    MODEL_SHADE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["cover", "update"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Verme Automation from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create the MQTT coordinator
    coordinator = VermeAutomationCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Connect to MQTT
    await coordinator.async_connect()
    
    # Forward the setup to the cover platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_disconnect()
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


class VermeAutomationCoordinator:
    """Coordinate MQTT communication for Verme Automation."""
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.mqtt_client: mqtt.Client | None = None
        self.devices: dict[str, dict[str, Any]] = {}
        self._listeners: list[callback] = []
        
    async def async_connect(self) -> None:
        """Connect to MQTT broker."""
        def on_connect(client, userdata, flags, rc):
            """Handle MQTT connection."""
            if rc == 0:
                _LOGGER.info("Connected to MQTT broker")
                # Subscribe to all Verme node discovery topics
                client.subscribe(f"{MQTT_BASE_TOPIC}/+/+/{MQTT_NODE_SUFFIX}")
                _LOGGER.info("Subscribed to Verme node discovery topics")
            else:
                _LOGGER.error("Failed to connect to MQTT broker: %s", rc)
        
        def on_message(client, userdata, msg):
            """Handle incoming MQTT messages."""
            try:
                topic_parts = msg.topic.split("/")
                if len(topic_parts) >= 4 and topic_parts[-1] == MQTT_NODE_SUFFIX:
                    device_type = topic_parts[1]  # e.g., "shades"
                    device_id = topic_parts[2]    # e.g., "shade_001"
                    
                    # Parse the JSON payload
                    try:
                        node_info = json.loads(msg.payload.decode())
                        _LOGGER.info("Discovered Verme device: %s", node_info)
                        
                        # Store device info
                        self.devices[device_id] = {
                            "type": device_type,
                            "info": node_info,
                            "topic_base": f"{MQTT_BASE_TOPIC}/{device_type}/{device_id}"
                        }
                        
                        # Notify Home Assistant about the new device
                        self.hass.async_create_task(
                            self._async_handle_new_device(device_id, device_type, node_info)
                        )
                        
                    except json.JSONDecodeError:
                        _LOGGER.error("Invalid JSON in node info message: %s", msg.payload)
                        
            except Exception as err:
                _LOGGER.error("Error processing MQTT message: %s", err)
        
        # Create MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message
        
        # Set credentials if provided
        if self.entry.data[CONF_MQTT_USERNAME] and self.entry.data[CONF_MQTT_PASSWORD]:
            self.mqtt_client.username_pw_set(
                self.entry.data[CONF_MQTT_USERNAME],
                self.entry.data[CONF_MQTT_PASSWORD]
            )
        
        # Connect to broker
        await self.hass.async_add_executor_job(
            self.mqtt_client.connect,
            self.entry.data[CONF_MQTT_HOST],
            self.entry.data[CONF_MQTT_PORT],
            60
        )
        
        # Start the MQTT loop
        await self.hass.async_add_executor_job(self.mqtt_client.loop_start)
    
    async def async_disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self.mqtt_client:
            await self.hass.async_add_executor_job(self.mqtt_client.loop_stop)
            await self.hass.async_add_executor_job(self.mqtt_client.disconnect)
    
    async def _async_handle_new_device(self, device_id: str, device_type: str, node_info: dict) -> None:
        """Handle discovery of a new device."""
        device_registry = dr.async_get(self.hass)
        
        # Create device in device registry
        device_registry.async_get_or_create(
            config_entry_id=self.entry.entry_id,
            identifiers={(DOMAIN, device_id)},
            manufacturer=MANUFACTURER,
            model=MODEL_SHADE if device_type == "shades" else f"Verme {device_type.title()}",
            name=node_info.get("name", f"Verme {device_id}"),
            sw_version=node_info.get("version"),
        )
        
        # Create a persistent notification for the user
        self.hass.components.persistent_notification.async_create(
            f"New Verme device discovered: {node_info.get('name', device_id)}",
            title="Verme Automation - New Device",
            notification_id=f"verme_new_device_{device_id}"
        )
        
        # If it's a shade, reload the cover platform to pick up the new device
        if device_type == "shades":
            await self.hass.config_entries.async_reload(self.entry.entry_id)
    
    def publish_message(self, topic: str, payload: str, retain: bool = False) -> None:
        """Publish a message to MQTT."""
        if self.mqtt_client:
            self.mqtt_client.publish(topic, payload, retain=retain)
