[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

*Component to integrate with [Saleryd HRV unit](https://saleryd.se/produkt-kategori/ftx-ventilation/)*

## :warning: Disclaimer


**Note:** This integration was developed for personal use with my HRV unit.


**Warning:** Be careful when altering settings on your ventilation system. Improper settings can damage your house and affect personal health over time.


**Use at your own risk.**


I am not affiliated with Saleryd. All trademarks belong to their respective owners.

## Motivation


Monitor and control Saleryd HRV units from Home Assistant.


### Example Automations

- Airflow/temperature/cooling based on presence/schedule or alarm system state.
- Cooling/temperature mode based on external temperature/humidity sensors
- Energy price integration
- Remote control using dashboard or physical controls
- ...

## Integration Features

### Sensors

Name | Description | Unit | State attributes
-- | -- | -- | --
`boost_mode_minutes_left` | Minutes left until boost mode expires | `min` |
`extract_fan_speed` | Extract fan speed | `%` |
`filter_months_left` | Filter months left | `m` |
`fireplace_mode_minutes_left` | Minutes left until fireplace mode expires | `min` |
`heat_exchanger_rotor_speed_percent` | Rotor speed of heat exchanger | `%` |
`heat_exchanger_rotor_speed` | Rotor speed of heat exchanger | `rpm` |
`heater_air_temperature` | Air temperature at heater | `°C` |
`heater_power_percent` | Auxillary heater power | `%` |
`product_number` | Product number | `str` |
`supply_air_temperature` | Supply air temperature | `°C` |
`supply_fan_speed`  | Supply fan speed | `%` |
`system_name` | Control system name | `str` |
`system_version` | Control system version | `str` |
`target_temperature` | Target air temperature | `°C` |
`temperature_mode` | Current temperature mode setting | `Cool` \| `Normal` \| `Economy` |
`ventilation_mode` | Current ventilation mode setting | `Normal` \| `Away` \| `Boost` |
`normal_temperature` | Temperature setting for Normal mode | `°C` |
`economy_temperature` | Temperature setting for Economy mode | `°C` |
`cool_temperature` | Temperature setting for Cool mode | `°C` |
`heater_power_rating` | Auxillary heater power rating | `W` |

### Binary sensors

Name | Description | State | State attributes
-- | -- | -- | --
`connection_state` | Integration websocket connection state | `Connected` \| `Disconnected` | Raw connection state
`heater_active` | Auxillary heater state | `Running` \| `Not running` |
`system_active` | System running state | `Running` \| `Not running` |
`system_warning` | System warning state | `Problem` \| `No problem` | Raw system error/warning codes

### Switches

Name | Description | Installer setting?
-- | -- | --
`cooling_mode` | Turn `cooling` mode on/off
`fireplace_mode` | Turn `fireplace` mode on/off
`heater_active` | Turn `electric auxiliary heater` on/off. Note: Disabling the electric heater is not recommended and may trigger emergency shutdown of the system! Consult the manual for more information. | Yes

### Select

Name | Description  | Installer setting?
-- | -- | --
`system_active` | Set control system state on/off | Yes
`temperature_mode` | Set temperature mode Cool/Normal/Economy
`ventilation_mode` | Set ventilation mode Normal/Away/Boost

### Number
Name | Description | Installer setting?
-- | -- | --
`boost_mode_minutes` | Boost mode duration | Yes
`cool_temperature` | Cool temperature installer setting | Yes
`economy_temperature` | Economy temperature installer setting | Yes
`fireplace_mode_minutes` | Fireplace mode duration | Yes
`normal_temperature` | Normal temperature installer setting  | Yes

### Button
Name | Description | Installer setting?
-- | -- | --
`system_reset` | Reset system warnings | Yes

## Experimental Features

### Sensors

Name | Description | Unit
-- | -- | --
`heater_power` | Estimated electric auxillary heater power. This approximation might be inaccurate as it is a simple calculation based on heater power rating multiplied by heater power percent. | `W` |

### Switches

Switch | Description
-- | --
`cooking_mode` | Turn cooking mode on/off. Emulates cooking mode when fireplace mode is active. When `cooking_mode` is active, it automatically deactivates `fireplace_mode` before its timer expires. This will reset rotary heat exchanger to normal operation as is desirable in warm weather.


## Supported Devices

See [list of supported devices](https://github.com/bj00rn/pysaleryd/blob/master/README.rst#supported-devices)

## Installation

### HACS Install

1. In Home Assistant go to `HACS` -> `Integrations` and add this repository as a `custom repository`.
2. In Home Assistant go to `Configuration` -> `Integrations` click `+` and search for `Saleryd HRV`.
3. Click install.
4. Restart Home Assistant.

### Manual ZIP Install

1. Download release .zip file from [releases](https://github.com/bj00rn/ha-saleryd-ftx/releases) page.
2. Copy the `saleryd_hrv` directory from the release archive to the `/custom_components` directory in your Home Assistant server.
3. Restart Home Assistant.

## Configuration

### Prerequisites

1. Connect HRV system to your local WIFI network. See instructions in user manual.
2. Take note of the assigned IP address of the system

### YAML Configuration

Configuration in `configuration.yaml` is not supported.

### UI Configuration

* [Add Integration](https://www.home-assistant.io/getting-started/integration/) to Home Assistant.

Setting | Description | Default
-- | -- | --
Name | System name. Must be unique as it is used to generate device id |
Websocket IP | IP adress of the HRV system on the local WIFI network |
Port | Port number for websocket connection | 3001
Enable installer settings | Altering HRV system configuration set by the installer from Home Assistant. Don't alter these settings unless you know what you are doing | False
Installer password | Installer password. Required for installer settings |

## Troubleshooting

### I can't connect to HRV system

* Check the Home Assistant `logs`
* Confirm system is connected and the UI portal is reachable on the local network. Follow steps in the manual.
* Confirm websocket port by connecting to the UI using a browser and take note of websocket port using debug console in browser.
* The system HRV can only handle a few connected clients. Shut down any additional clients/browsers and try again.

### I can't modify installer settings
* Ensure installer settings are enabled in integration configuration
* Ensure installer password is correct

## Contributing

Issues and PRs welcome!

See [CONTRIBUTING.md](CONTRIBUTING.md)

### Enable Debug Logging

Add component to the [logger](https://www.home-assistant.io/integrations/logger/) section of homeassistant configuration.yaml.
```yaml
logger:
  logs:
    custom_components.saleryd_hrv: debug
```

## Related Projects

https://github.com/bj00rn/pysaleryd

[saleryd_ftx]: https://github.com/bj00rn/ha-saleryd-ftx
[buymecoffee]: https://www.buymeacoffee.com/bj00rn
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/bj00rn/ha-saleryd-ftx.svg?style=for-the-badge
[commits]: https://github.com/bj00rn/ha-saleryd-ftx/commits/master
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license]: https://github.com/bj00rn/ha-saleryd-ftx/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/bj00rn/ha-saleryd-ftx.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-bj00rn-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/bj00rn/ha-saleryd-ftx.svg?style=for-the-badge
[releases]: https://github.com/bj00rn/ha-saleryd-ftx/releases
[user_profile]: https://github.com/bj00rn
