"""Update platform for Verme Automation integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.update import (
    UpdateEntity,
    UpdateEntityFeature,
    UpdateDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
import json

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL_SHADE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Verme update entities from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Create update entities for all discovered devices
    entities = []
    for device_id, device_data in coordinator.devices.items():
        entities.append(
            VermeUpdateEntity(
                coordinator,
                device_id,
                device_data,
                config_entry.entry_id
            )
        )
    
    async_add_entities(entities)


class VermeUpdateEntity(UpdateEntity):
    """Representation of a Verme device update entity."""
    
    def __init__(
        self,
        coordinator,
        device_id: str,
        device_data: dict[str, Any],
        config_entry_id: str,
    ) -> None:
        """Initialize the update entity."""
        self._coordinator = coordinator
        self._device_id = device_id
        self._device_data = device_data
        self._config_entry_id = config_entry_id
        
        # Set up MQTT topics
        self._topic_base = device_data["topic_base"]
        self._update_status_topic = f"{self._topic_base}/update/status"
        self._update_available_topic = f"{self._topic_base}/update/available"
        self._update_start_topic = f"{self._topic_base}/update/start"
        self._update_check_topic = f"{self._topic_base}/update/check"
        
        # Update state
        self._installed_version = device_data["info"].get("version", "unknown")
        self._latest_version = None
        self._update_available = False
        self._in_progress = False
        self._progress = 0
        self._release_notes = None
        self._last_status = {}
        
        # Subscribe to update topics
        if coordinator.mqtt_client:
            coordinator.mqtt_client.subscribe(self._update_status_topic)
            coordinator.mqtt_client.subscribe(self._update_available_topic)
            coordinator.mqtt_client.message_callback_add(
                self._update_status_topic,
                self._on_status_message
            )
            coordinator.mqtt_client.message_callback_add(
                self._update_available_topic,
                self._on_available_message
            )
    
    def _on_status_message(self, client, userdata, msg):
        """Handle update status messages."""
        try:
            status = json.loads(msg.payload.decode())
            self._last_status = status
            
            # Update state based on status
            current_status = status.get("status", "idle")
            self._in_progress = current_status in ["checking", "downloading", "installing"]
            self._progress = status.get("progress", 0)
            
            # Update installed version if update was successful
            if current_status == "success":
                self._installed_version = status.get("current_version", self._installed_version)
                self._update_available = False
                self._latest_version = None
            
            self.schedule_update_ha_state()
            
        except (json.JSONDecodeError, KeyError) as err:
            _LOGGER.warning("Invalid update status message: %s", err)
    
    def _on_available_message(self, client, userdata, msg):
        """Handle update available messages."""
        try:
            available_info = json.loads(msg.payload.decode())
            
            if available_info.get("available", False):
                self._latest_version = available_info.get("version")
                self._release_notes = available_info.get("release_notes")
                self._update_available = True
            else:
                self._update_available = False
                self._latest_version = None
                self._release_notes = None
            
            self.schedule_update_ha_state()
            
        except (json.JSONDecodeError, KeyError) as err:
            _LOGGER.warning("Invalid update available message: %s", err)
    
    @property
    def unique_id(self) -> str:
        """Return a unique ID for this entity."""
        return f"{DOMAIN}_{self._device_id}_update"
    
    @property
    def name(self) -> str:
        """Return the name of the update entity."""
        device_name = self._device_data["info"].get("name", f"Verme {self._device_id}")
        return f"{device_name} Firmware"
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_type = self._device_data["type"]
        model = MODEL_SHADE if device_type == "shades" else f"Verme {device_type.title()}"
        
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self._device_data["info"].get("name", f"Verme {self._device_id}"),
            manufacturer=MANUFACTURER,
            model=model,
            sw_version=self._installed_version,
        )
    
    @property
    def device_class(self) -> UpdateDeviceClass:
        """Return the device class."""
        return UpdateDeviceClass.FIRMWARE
    
    @property
    def supported_features(self) -> UpdateEntityFeature:
        """Flag supported features."""
        features = UpdateEntityFeature.INSTALL
        
        # Add progress support if device supports it
        if self._in_progress and self._progress > 0:
            features |= UpdateEntityFeature.PROGRESS
        
        return features
    
    @property
    def installed_version(self) -> str | None:
        """Version currently installed and in use."""
        return self._installed_version
    
    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        return self._latest_version if self._update_available else self._installed_version
    
    @property
    def release_summary(self) -> str | None:
        """Summary of the release."""
        return self._release_notes
    
    @property
    def release_url(self) -> str | None:
        """URL to the full release notes."""
        # Could link to your release notes page
        return None
    
    @property
    def in_progress(self) -> bool:
        """Update installation progress."""
        return self._in_progress
    
    @property
    def update_percentage(self) -> int | None:
        """Update installation progress as a percentage."""
        return self._progress if self._in_progress else None
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = {
            "device_id": self._device_id,
            "update_channel": "stable",  # Could be made configurable
        }
        
        if self._last_status:
            attrs.update({
                "last_check": self._last_status.get("last_check"),
                "update_status": self._last_status.get("status"),
                "update_progress": self._last_status.get("progress"),
            })
        
        return attrs
    
    async def async_install(
        self, version: str | None = None, backup: bool = True, **kwargs: Any
    ) -> None:
        """Install an update."""
        _LOGGER.info("Starting firmware update for %s", self._device_id)
        
        # Send update start command to device
        await self.hass.async_add_executor_job(
            self._coordinator.publish_message,
            self._update_start_topic,
            "start",
            False
        )
        
        # Update state to show update in progress
        self._in_progress = True
        self._progress = 0
        self.async_write_ha_state()
    
    async def async_check_update(self) -> None:
        """Check for updates."""
        _LOGGER.info("Checking for updates for %s", self._device_id)
        
        # Send update check command to device
        await self.hass.async_add_executor_job(
            self._coordinator.publish_message,
            self._update_check_topic,
            "check",
            False
        )
    
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Entity is available if device is online and supports updates
        return True  # Could check device online status
