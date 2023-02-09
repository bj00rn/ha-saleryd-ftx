[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]


*Component to integrate with [Saleryd HRV Systems](https://saleryd.se/produkt-kategori/ftx-ventilation/)*

**Disclaimer**

 This integration has been developed for LOKE1 HRV system. *Use at own risk*. I am in no way affiliated with Saleryd. All trademarks belong to their respective owners.

**Sensors**

Name | Description | Unit of measure
-- | -- | --
`heat_exchanger_rpm` | Speed of the heat exchanger rotor | rpm
`heat_exchanger_speed` | Speed of the heat exchanger rotor | percent
`supply_air_temperature` | Supply air temperature | Degrees celsius
`heater_air_temperature` | Air temperature at heater battry | Degrees celsius
`supply_fan_speed` | Speed of the supply air fan | percent
`extract_fan_speed` | Speed of the extract air fan | percent
`ventilation_mode` | Ventilation mode of the system  (0=Home,1=Away,2=High) | integer
`fireplace_mode` | Fireplace mode state (0=Off,1=On) | integer
`temperature_mode` | Temperature mode (0=Cooling,1=Economy,2=Normal)  | integer

***Services***

Name | Description | Fields
-- | -- | --
`set_fireplace_mode` | Set fireplace mode | value: `integer` (0=On, 1=off)
`set_cooling_mode` | Set cooling mode | value: `integer` (0=On, 1=off)
`set_ventilation_mode` | Set ventilation mode | value: `integer` (0=Home,1=Away,2=High)
`set_temperature_mode` | Set temperature mode | value: `integer` (0=Cooling,1=Economy,2=Normal)


## Confirmed supported devices

Model | Control system versions
-- | --
[LOKE01/LOKE BASIC/LS-01](https://saleryd.se/produkt/varmeatervinningsaggregat-loke/) | 4.1.1


## Prequisites
1. Connect HRV to local network . See instructions in user manual
2. Take note of the assigned IP adress of the HRV system

## Installation
1. In the HA UI go to "HACS" and add this repository
2. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Saleryd HRV".
3. Click install


## Configuration
### configuration.yaml

Configuration in congfiguration.yaml is not supported


### Configuration in the UI
Setting | Description
-- | --
IP | IP adress of the HRV system on the local network
PORT | Port number of websocket, default 3001


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
