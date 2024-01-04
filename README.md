[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

*Component to integrate with [Saleryd HRV Systems](https://saleryd.se/produkt-kategori/ftx-ventilation/)*

## :warning: Disclaimer

:nerd_face: This integration has been developed for my HRV system for personal use.

:biohazard: Be careful when altering settings on your ventilation system. Improper settings on your ventilation system can over time damage your house and personal health.

:bomb: *Use at own risk*.

:grey_exclamation: I am in no way affiliated with Saleryd. All trademarks belong to their respective owners.

## Motivation

Monitor and control HRV system from Home Assistant.

### Ideas for automations

- `airflow/temperature/cooling based on presence/schedule.`
- `cooling/temperature mode based on external temperature/humidity sensors or alarm system state`
- `energy price integration`
- `remote control using dashboard or physical controls`
- `...`

## Features

### Sensors

Name | Description | Unit | State attributes
-- | -- | -- | --
`boost_mode_minutes_left` | minutes left until boost mode expires | `min` |
`extract_fan_speed` | fan speed | `%` |
`filter_months_left` | filter months left | `m` |
`fireplace_mode_minutes_left` | minutes left until fireplace mode expires | `min` |
`heat_exchanger_rotor_speed_percent` | rotor speed of heat exchanger | `%` |
`heat_exchanger_rotor_speed` | rotor speed of heat exchanger | `rpm` |
`heater_active` | auxillary heater active | boolean |
`heater_air_temperature` | air temperature at heater | `°C` |
`heater_power` | auxillary heater power | `W` |
`heater_power_percent` | auxillary heater power | `%` |
`product_number` | product number | `str` |
`supply_air_temperature` | supply air temperature | `°C` |
`supply_fan_speed`  | fan speed | `%` |
`system_active` | status of the system | `On` \| `Off` \| `Reset` |
`system_name` | control system name | `str` |
`system_version` | control system version | `str` |
`system_warning` | system warning | boolean | raw system error/warning codes
`target_temperature` | target air temperature | `°C` |
`temperature_mode` | current temperature mode setting | `str` |
`ventilation_mode` | current ventilation mode setting | `str` |


## Switches

Switch | Description | State attributes
-- | -- | --
`away_mode` | Turn Away vent mode on/off
`boost_mode` | Turn Boost vent mode on/off | minutes left
`cooling_mode` | Turn Cooling vent mode on/off
`fireplace_mode` | Turn Fireplace vent mode on/off | minutes left
`home_mode` | Turn Home vent mode on/off

## Integration services

Name | Description | Fields
-- | -- | --
`set_cooling_mode` | Set cooling mode | value: `integer` (0=On, 1=Off)
`set_fireplace_mode` | Set fireplace mode | value: `integer` (0=On, 1=Off)
`set_temperature_mode` | Set temperature mode | value: `integer` (0=Normal,1=Economy,2=Cool)
`set_ventilation_mode` | Set ventilation mode | value: `integer` (0=Home,1=Away,2=Boost)

## Experimental features

### Switches

Switch | Description | State attributes
-- | -- | --
`cooking_mode` | Turn cooking mode on/off. Emulates cooking mode when fireplace mode is active. Automatically disables fireplace mode before timer expires to reset rotary heat exchanger to normal operation.

## Supported devices

Model | Confirmed supported control system versions | Unsupported control system versions
-- | -- | --
[LOKE01/LOKE BASIC/LS-01](https://saleryd.se/produkt/varmeatervinningsaggregat-loke/) | 4.1.5 | <4.1.5*

\* connectivity issues in versions below 4.1.5

## Prequisites

1. Connect HRV to local network . See instructions in user manual
2. Take note of the assigned IP adress of the HRV system

## Installation

1. In Home Assistant go to `HACS` -> `Integrations` and add this repository as a `custom repository`.
2. In Home Assistant go to `Configuration` -> `Integrations` click `+` and search for `Saleryd HRV`.
3. Click install.

## Configuration

### configuration.yaml

Configuration in `congfiguration.yaml` is not supported

### Configuration in the UI

Setting | Description
-- | --
IP | IP adress of the HRV system on the local network
PORT | Port number of websocket, default 3001

## Troubleshooting

### Can't connect to HRV system
* Check the Home Assitant `logs`
* Confirm system is connected and the UI portal is reachable on the local network. Follow steps in the manual.
* Confirm websocket port by connecting to the UI using a browser and take note of websocket port using debug console in browser.
* The system HRV can only handle a few connected clients. Shut down any additional clients/browsers and try again.

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
