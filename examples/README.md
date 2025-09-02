# Home Assistant Configuration Examples

This directory contains examples of how to use the Verme Automation integration in Home Assistant.

## MQTT Broker Configuration

### Using Mosquitto in Docker
```yaml
# docker-compose.yml
version: '3.7'
services:
  mosquitto:
    image: eclipse-mosquitto:latest
    container_name: mosquitto
    restart: unless-stopped
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - ./mosquitto/data:/mosquitto/data
      - ./mosquitto/logs:/mosquitto/logs
```

### Mosquitto Configuration
```conf
# mosquitto/config/mosquitto.conf
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/logs/mosquitto.log
```

## Home Assistant Configuration

### Basic MQTT Setup
```yaml
# configuration.yaml
mqtt:
  broker: 192.168.1.100
  port: 1883
  username: your_username
  password: your_password
  discovery: true
  discovery_prefix: homeassistant
```

### Integration Configuration
The Verme Automation integration is configured via the UI:
1. Settings → Devices & Services → Add Integration
2. Search for "Verme Automation"
3. Enter MQTT broker details

## Dashboard Examples

### Shade Control Card
```yaml
# dashboard configuration
type: entities
title: Window Shades
entities:
  - entity: cover.living_room_shade
    name: Living Room
    secondary_info: last-updated
  - entity: cover.bedroom_shade
    name: Bedroom
    secondary_info: last-updated
  - entity: cover.kitchen_shade
    name: Kitchen
    secondary_info: last-updated
```

### Shade Position Control
```yaml
type: vertical-stack
cards:
  - type: entity
    entity: cover.living_room_shade
    name: Living Room Shade
  - type: horizontal-stack
    cards:
      - type: button
        tap_action:
          action: call-service
          service: cover.open_cover
          target:
            entity_id: cover.living_room_shade
        name: Open
        icon: mdi:window-shutter-open
      - type: button
        tap_action:
          action: call-service
          service: cover.close_cover
          target:
            entity_id: cover.living_room_shade
        name: Close
        icon: mdi:window-shutter
```

### Firmware Update Management
```yaml
type: entities
title: Firmware Updates
entities:
  - entity: update.living_room_shade_firmware
    name: Living Room Shade
    secondary_info: last-updated
  - entity: update.bedroom_shade_firmware
    name: Bedroom Shade
    secondary_info: last-updated
  - entity: update.kitchen_shade_firmware
    name: Kitchen Shade
    secondary_info: last-updated
```

## Automation Examples

### Schedule Shade Operations
```yaml
# automations.yaml
- id: 'morning_shades_open'
  alias: Morning - Open Shades
  trigger:
    - platform: sun
      event: sunrise
      offset: '+00:30:00'
  condition:
    - condition: state
      entity_id: binary_sensor.workday_sensor
      state: 'on'
  action:
    - service: cover.open_cover
      target:
        entity_id: 
          - cover.living_room_shade
          - cover.bedroom_shade

- id: 'evening_shades_close'
  alias: Evening - Close Shades
  trigger:
    - platform: sun
      event: sunset
      offset: '-00:30:00'
  action:
    - service: cover.close_cover
      target:
        entity_id: all
        device_class: shade
```

### Automatic Firmware Updates
```yaml
- id: 'auto_firmware_updates'
  alias: Auto Update Firmware (Stable Only)
  trigger:
    - platform: state
      entity_id: 
        - update.living_room_shade_firmware
        - update.bedroom_shade_firmware
        - update.kitchen_shade_firmware
      to: 'on'
  condition:
    - condition: template
      value_template: "{{ 'stable' in trigger.to_state.attributes.get('release_notes', '').lower() }}"
  action:
    - service: update.install
      target:
        entity_id: "{{ trigger.entity_id }}"
    - service: notify.persistent_notification
      data:
        title: "Firmware Update Started"
        message: "Updating {{ trigger.to_state.attributes.friendly_name }}"
```

### Battery Level Monitoring
```yaml
- id: 'low_battery_notification'
  alias: Low Battery Notification
  trigger:
    - platform: numeric_state
      entity_id: 
        - sensor.living_room_shade_battery
        - sensor.bedroom_shade_battery
        - sensor.kitchen_shade_battery
      below: 20
  action:
    - service: notify.mobile_app_your_phone
      data:
        title: "Low Battery Alert"
        message: "{{ trigger.to_state.attributes.friendly_name }} battery is at {{ trigger.to_state.state }}%"
```

## Script Examples

### Shade Scene Control
```yaml
# scripts.yaml
morning_routine:
  alias: Morning Routine
  sequence:
    - service: cover.set_cover_position
      target:
        entity_id: cover.living_room_shade
      data:
        position: 75
    - service: cover.set_cover_position
      target:
        entity_id: cover.bedroom_shade
      data:
        position: 50
    - delay: '00:00:02'
    - service: cover.set_cover_position
      target:
        entity_id: cover.kitchen_shade
      data:
        position: 100

privacy_mode:
  alias: Privacy Mode
  sequence:
    - service: cover.close_cover
      target:
        entity_id: all
        device_class: shade
    - service: notify.persistent_notification
      data:
        message: "All shades closed for privacy"
```

## MQTT Message Examples

### Device Discovery Message
```json
Topic: verme/shades/shade_001/node
Payload: {
  "device_id": "shade_001",
  "device_name": "Living Room Shade",
  "device_type": "shade",
  "version": "1.0.0",
  "ip_address": "192.168.1.150",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "capabilities": ["position", "tilt"],
  "battery_powered": true
}
Retain: true
```

### Shade State Message
```json
Topic: verme/shades/shade_001/state
Payload: {
  "position": 75,
  "state": "open",
  "battery_level": 85,
  "wifi_rssi": -65,
  "last_seen": "2025-08-25T10:30:00Z"
}
Retain: true
```

### Update Available Message
```json
Topic: verme/shades/shade_001/update/available
Payload: {
  "available": true,
  "version": "1.1.0",
  "current_version": "1.0.0",
  "release_notes": "Bug fixes and performance improvements",
  "critical": false,
  "file_size": 1048576
}
Retain: true
```

## Troubleshooting

### Enable Debug Logging
```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.verme_automation: debug
    homeassistant.components.mqtt: debug
```

### MQTT Topic Monitoring
Use MQTT Explorer or mosquitto_sub to monitor messages:
```bash
# Monitor all Verme topics
mosquitto_sub -h 192.168.1.100 -t "verme/+/+/+"

# Monitor specific device
mosquitto_sub -h 192.168.1.100 -t "verme/shades/shade_001/+"
```

### Manual MQTT Testing
```bash
# Simulate device discovery
mosquitto_pub -h 192.168.1.100 -t "verme/shades/test_shade/node" \
  -m '{"device_id":"test_shade","device_name":"Test Shade","device_type":"shade","version":"1.0.0"}' \
  -r

# Simulate position update
mosquitto_pub -h 192.168.1.100 -t "verme/shades/test_shade/state" \
  -m '{"position":50,"state":"open"}' \
  -r
```

## See Also

- [ESP32 Firmware Development](../../node-firmware/README.md) - For hardware development
- [Automatic Updates Guide](../../docs/AUTOMATIC_UPDATES.md) - OTA update system
- [GitHub OTA Setup](../../docs/GITHUB_OTA_SETUP.md) - Release management
