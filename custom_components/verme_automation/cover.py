"""Cover platform for Verme Automation integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
    CoverDeviceClass,
    ATTR_POSITION,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN,
    MQTT_POSITION_SUFFIX,
    MQTT_STATE_SUFFIX,
    MANUFACTURER,
    MODEL_SHADE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Verme cover entities from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Create cover entities for all discovered shade devices
    entities = []
    for device_id, device_data in coordinator.devices.items():
        if device_data["type"] == "shades":
            entities.append(
                VermeShadeCover(
                    coordinator,
                    device_id,
                    device_data,
                    config_entry.entry_id
                )
            )
    
    async_add_entities(entities)


class VermeShadeCover(CoverEntity):
    """Representation of a Verme Shade cover."""
    
    def __init__(
        self,
        coordinator,
        device_id: str,
        device_data: dict[str, Any],
        config_entry_id: str,
    ) -> None:
        """Initialize the cover."""
        self._coordinator = coordinator
        self._device_id = device_id
        self._device_data = device_data
        self._config_entry_id = config_entry_id
        self._current_position: int | None = None
        self._is_available = True
        
        # Set up MQTT topics
        self._topic_base = device_data["topic_base"]
        self._position_topic = f"{self._topic_base}/{MQTT_POSITION_SUFFIX}"
        self._state_topic = f"{self._topic_base}/{MQTT_STATE_SUFFIX}"
        
        # Subscribe to state updates if available
        if coordinator.mqtt_client:
            coordinator.mqtt_client.subscribe(self._state_topic)
            coordinator.mqtt_client.message_callback_add(
                self._state_topic,
                self._on_state_message
            )
    
    def _on_state_message(self, client, userdata, msg):
        """Handle state update messages."""
        try:
            position = int(msg.payload.decode())
            if 0 <= position <= 100:
                self._current_position = position
                self.schedule_update_ha_state()
        except (ValueError, TypeError):
            _LOGGER.warning("Invalid position value received: %s", msg.payload)
    
    @property
    def unique_id(self) -> str:
        """Return a unique ID for this entity."""
        return f"{DOMAIN}_{self._device_id}"
    
    @property
    def name(self) -> str:
        """Return the name of the cover."""
        return self._device_data["info"].get("name", f"Verme Shade {self._device_id}")
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self.name,
            manufacturer=MANUFACTURER,
            model=MODEL_SHADE,
            sw_version=self._device_data["info"].get("version"),
        )
    
    @property
    def device_class(self) -> CoverDeviceClass:
        """Return the device class of the cover."""
        return CoverDeviceClass.SHADE
    
    @property
    def supported_features(self) -> CoverEntityFeature:
        """Flag supported features."""
        return (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.SET_POSITION
        )
    
    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of the cover."""
        return self._current_position
    
    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        if self._current_position is None:
            return None
        return self._current_position == 0
    
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._is_available
    
    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.async_set_cover_position(position=100)
    
    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self.async_set_cover_position(position=0)
    
    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        if position is None:
            return
        
        # Ensure position is within valid range
        position = max(0, min(100, int(position)))
        
        # Publish position command to MQTT
        await self.hass.async_add_executor_job(
            self._coordinator.publish_message,
            self._position_topic,
            str(position),
            True  # Retain position commands for battery devices
        )
        
        # Optimistically update the position
        self._current_position = position
        self.async_write_ha_state()
        
        _LOGGER.debug(
            "Set position %d for cover %s (topic: %s)",
            position,
            self._device_id,
            self._position_topic
        )
