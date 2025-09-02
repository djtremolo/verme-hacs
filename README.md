# Verme Automation - Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg?style=for-the-badge)](https://github.com/your-username/verme-integration)

A comprehensive Home Assistant integration for Verme Node devices, providing automatic device discovery, control, and firmware management.

## ✨ Features

- 🔍 **Automatic Device Discovery** - Zero-configuration detection via MQTT
- 🏠 **Native HA Integration** - Seamless integration with Home Assistant ecosystem
- 🎛️ **Device Control** - Full control of window shades, lights, sensors, and more
- 🔄 **Firmware Management** - OTA updates with user approval and progress tracking
- 🔋 **Battery Optimization** - Intelligent handling of battery-powered devices
- 📱 **Rich UI** - Native Home Assistant cards and controls
- 🌐 **Multi-Device Support** - Extensible architecture for different node types

## 🚀 Quick Start

### Prerequisites
- Home Assistant 2023.1+
- MQTT broker (Mosquitto recommended)
- HACS (Home Assistant Community Store)

### Installation via HACS

1. **Add Custom Repository**:
   - HACS → Integrations → ⋮ → Custom repositories
   - URL: `https://github.com/your-username/verme-integration`
   - Category: Integration

2. **Install Integration**:
   - Search for "Verme Automation"
   - Click Install
   - Restart Home Assistant

3. **Configure Integration**:
   - Settings → Devices & Services → Add Integration
   - Search for "Verme Automation"
   - Enter MQTT broker details

### Manual Installation

1. Copy `custom_components/verme_automation` to your HA config directory
2. Restart Home Assistant
3. Add integration via UI

## 📋 Configuration

### MQTT Broker Setup
```yaml
# configuration.yaml
mqtt:
  broker: 192.168.1.100
  port: 1883
  username: your_username
  password: your_password
```

### Integration Configuration
The integration uses a configuration flow - no YAML needed!

1. **Broker Connection**: Enter MQTT broker details
2. **Device Discovery**: Automatic discovery of Verme nodes
3. **Device Setup**: Devices appear automatically in HA

## 🎯 Supported Device Types

| Device Type | Entity Platform | Features |
|-------------|----------------|----------|
| **Window Shades** | `cover` | Open/Close, Position, Tilt |
| **Lights** | `light` | On/Off, Brightness, Color |
| **Sensors** | `sensor` | Temperature, Humidity, Motion |
| **Switches** | `switch` | On/Off Control |
| **Generic Nodes** | `sensor` | Custom functionality |

## 🔄 Firmware Updates

The integration provides seamless firmware update management:

- **Update Detection**: Automatic GitHub release monitoring
- **User Control**: Approve updates via HA interface
- **Progress Tracking**: Real-time update progress
- **Rollback Support**: Automatic rollback on failure
- **Release Notes**: View changelog before updating

### Update Process
1. Integration detects new firmware on GitHub
2. Update entity appears in HA with available version
3. User clicks "Install" to approve update
4. Device downloads and installs firmware
5. Device reports success/failure status

## 📡 MQTT Topics

### Device Discovery
```
verme/{device_type}/{device_id}/node
```

### Device Control
```
verme/{device_type}/{device_id}/command
verme/{device_type}/{device_id}/state
verme/{device_type}/{device_id}/status
```

### Firmware Updates
```
verme/{device_type}/{device_id}/update/available
verme/{device_type}/{device_id}/update/status
verme/{device_type}/{device_id}/update/start
```

## 🛠️ Development

### File Structure
```
custom_components/verme_automation/
├── __init__.py           # Integration setup
├── config_flow.py        # Configuration UI
├── const.py             # Constants
├── cover.py             # Cover platform
├── update.py            # Update platform
├── manifest.json        # Integration metadata
└── translations/        # UI translations
    └── en.json
```

### Adding New Device Types

1. **Create Platform File**: `{platform}.py`
2. **Add to Manifest**: Update supported platforms
3. **Device Registration**: Handle discovery in `__init__.py`
4. **MQTT Topics**: Define topic structure
5. **Entity Class**: Implement platform-specific entity

### Testing
```bash
# Run with Home Assistant test environment
pytest tests/
```

## 📖 API Reference

### VermeCoordinator
Main coordinator class handling MQTT communication and device management.

```python
coordinator = VermeCoordinator(hass, mqtt_config)
await coordinator.async_setup()
```

### Device Entities
Each device type implements the corresponding HA platform:

- `VermeCover`: Window shade control
- `VermeUpdate`: Firmware update management
- `VermeSensor`: Sensor data (future)
- `VermeLight`: Light control (future)

## 🔧 Troubleshooting

### Common Issues

**No devices discovered**:
- Check MQTT broker connection
- Verify device MQTT configuration
- Check firewall settings

**Update failures**:
- Ensure internet connectivity
- Check GitHub repository access
- Verify firmware compatibility

**Performance issues**:
- Reduce MQTT message frequency
- Check network latency
- Monitor HA logs

### Debug Logging
```yaml
# configuration.yaml
logger:
  logs:
    custom_components.verme_automation: debug
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🙏 Acknowledgments

- Home Assistant community for excellent documentation
- HACS for simplified custom component distribution
- MQTT community for robust messaging protocol
- PlatformIO for ESP32 development platform

---

## 🔗 Related Projects

- **[Node Firmware](../node-firmware/)** - ESP32 firmware for Verme nodes
- **[Documentation](../docs/)** - Comprehensive project documentation
- **[Examples](examples/)** - Usage examples and templates

For hardware setup and ESP32 development, see the [Node Firmware documentation](../node-firmware/README.md).
