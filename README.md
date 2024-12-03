[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

*Component to integrate with [Saleryd HRV unit](https://saleryd.se/produkt-kategori/ftx-ventilation/)*

## :warning: Disclaimer

:nerd_face: This integration has been developed for my HRV unit for personal use.

:biohazard: Be careful when altering settings on your ventilation system. Improper settings on your ventilation system can over time damage your house and personal health.

:bomb: *Use at own risk*.

:grey_exclamation: I am in no way affiliated with Saleryd. All trademarks belong to their respective owners.

## Motivation

Monitor and control Saleryd HRV units from Home Assistant.

### Ideas for automations

- `airflow/temperature/cooling based on presence/schedule.`
- `cooling/temperature mode based on external temperature/humidity sensors or alarm system state`
- `energy price integration`
- `remote control using dashboard or physical controls`
- `...`

## Integration features

### Sensors

Name | Description | Unit | State attributes
-- | -- | -- | --
`boost_mode_minutes_left` | minutes left until boost mode expires | `min` |
`extract_fan_speed` | fan speed | `%` |
`filter_months_left` | filter months left | `m` |
`fireplace_mode_minutes_left` | minutes left until fireplace mode expires | `min` |
`heat_exchanger_rotor_speed_percent` | rotor speed of heat exchanger | `%` |
`heat_exchanger_rotor_speed` | rotor speed of heat exchanger | `rpm` |
`heater_active` | auxillary heater active  | `Running` \| `Not running` |
`heater_air_temperature` | air temperature at heater | `°C` |
`heater_power_percent` | auxillary heater power | `%` |
`product_number` | product number | `str` |
`supply_air_temperature` | supply air temperature | `°C` |
`supply_fan_speed`  | fan speed | `%` |
`system_active` | status of the system | `Running` \| `Not running`
`system_name` | control system name | `str` |
`system_version` | control system version | `str` |
`system_warning` | system warning | `Problem` \| `No problem` | raw system error/warning codes
`target_temperature` | target air temperature | `°C` |
`temperature_mode` | current temperature mode setting | `Cool` \| `Normal` \| `Economy` |
`ventilation_mode` | current ventilation mode setting | `Normal` \| `Away` \| `Boost` |
`normal_temperature` | temperature setting for Normal mode | `°C` |
`economy_temperature` | temperature setting for Economy mode | `°C` |
`cool_temperature` | temperature setting for Cool mode | `°C` |
`heater_power_rating` | auxillary heater power rating | `W` |

### Switches

Name | Description
-- | --
`cooling_mode` | Turn `cooling` mode on/off
`fireplace_mode` | Turn `fireplace` mode on/off

### Select

Name | Description
-- | --
`ventilation_mode` | set ventilation mode Normal/Away/Boost
`temperature_mode` | set temperature mode Cool/Normal/Economy
`system state` | set control system state on/off

### Number
Name | Description
-- | --
`cool_temperature` | Cool temperature installer setting
`economy_temperature` | Economy temperature installer setting
`normal_temperature` | Normal temperature installer setting

### Button
Name | Description
-- | --
`system_reset` | Reset system warnings

## Experimental features

### Sensors

Name | Description | Unit
-- | -- | --
`heater_power` | Estimated auxillary heater power | `W` |

### Switches

Switch | Description
-- | --
`cooking_mode` | Turn `cooking` mode on/off. Emulates cooking mode when fireplace mode is active. When `cooking mode` is active, it automatically deactivates `fireplace_mode` before its timer expires. This will reset rotary heat exchanger to normal operation as is desirable in warm weather.

## Supported devices

Model | Confirmed supported control system versions | Unsupported control system versions
-- | -- | --
[LOKE LS-01](https://saleryd.se/produkt/varmeatervinningsaggregat-loke/) | 4.1.5 | <4.1.5*
[LOKE LT-01](https://saleryd.se/produkt/varmeatervinningsaggregat-loke/) | unconfirmed |
[LOKE LS-02](https://saleryd.se/produkt/varmeatervinningsaggregat-loke/) | unconfirmed |
[LOKE LT-02](https://saleryd.se/produkt/varmeatervinningsaggregat-loke/) | unconfirmed |

\* connectivity issues in versions below 4.1.5

## Installation

## HACS Install

1. In Home Assistant go to `HACS` -> `Integrations` and add this repository as a `custom repository`.
2. In Home Assistant go to `Configuration` -> `Integrations` click `+` and search for `Saleryd HRV`.
3. Click install.
4. Restart Home Assistant.

## Manual ZIP install

1. Download release .zip file from [releases](https://github.com/bj00rn/ha-saleryd-ftx/releases) page.
2. Copy the `saleryd_hrv` directory from the release archive to the `/custom_components` directory in your Home Assistant server.
3. Restart Home Assistant.

## Configuration

### Prequisites

1. Connect HRV system to your local WIFI network. See instructions in user manual.
2. Take note of the assigned IP adress of the system

### YAML Configuration

Configuration in `congfiguration.yaml` is not supported

### UI Configuration

* [Add Intergration](https://www.home-assistant.io/getting-started/integration/) to Home Assistant.

Setting | Description | Default
-- | -- | --
Name | System name. Must be unique. |
Websocket IP | IP adress of the HRV system on the local WIFI network |
Port | Port number for websocket connection | 3001
Enable installer settings | Altering HRV system configuration set by the installer from Home Assistant. Don't alter these settings unless you know what you are doing | False
Installer password | Installer password. Required for installer settings |

## Troubleshooting

### I can't connect to HRV system

* Check the Home Assitant `logs`
* Confirm system is connected and the UI portal is reachable on the local network. Follow steps in the manual.
* Confirm websocket port by connecting to the UI using a browser and take note of websocket port using debug console in browser.
* The system HRV can only handle a few connected clients. Shut down any additional clients/browsers and try again.

### I can't modify installer settings
* Ensure installer settings are enabled in integration configuration
* Ensure installer password is correct

### Contributing

Issues and PRs welcome!

See [CONTRIBUTING.md](CONTRIBUTING.md)

### Enable debug logging

Add component to the [logger](https://www.home-assistant.io/integrations/logger/) section of homeassistant configuration.yaml.
```yaml
logger:
  logs:
    custom_components.saleryd_hrv: debug
```

## Related projects

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
