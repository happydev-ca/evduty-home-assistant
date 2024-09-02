[![Test](https://github.com/happydev-ca/evduty-home-assistant/actions/workflows/test.yml/badge.svg)](https://github.com/happydev-ca/evduty-home-assistant/actions/workflows/test.yml)
[![Validate](https://github.com/happydev-ca/evduty-home-assistant/actions/workflows/validate.yml/badge.svg)](https://github.com/happydev-ca/evduty-home-assistant/actions/workflows/validate.yml)

# EVduty Custom Integration for Home Assistant

Use to monitor and control your EVduty charging stations including charging session state, estimated cost and energy consumption.

## Installation

### Automatic

[![Install from Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=happydev-ca&repository=evduty-home-assistant&category=integration)

Or:

- Go to your Home Assistant
- Open [HACS](https://hacs.xyz/)
- Search for `EVduty`
- Click the `Download` button on the bottom right
- Restart Home Assistant

### Manual

- Copy the `evduty` folder your `/path/to/home-assistant/custom_components/` directory
- Restart Home Assistant

## Configuration

- Go to `Settings` -> `Devices & Services`
- Click on the `Integrations` tab
- Click the `Add Integration` button
- Search for EVduty

![Configuration](.img/config.png)

Then click the `Submit` button. Your credentials will be validated, and your charging stations will be created in Home Assistant.

*This custom integration does not support configuration through the `configuration.yaml` file.*

## Sensors

A device is created for each charging station in your account. 

![Device](./.img/device.png)

The following sensors are created for each charging station:

![Sensors](./.img/sensors.png)

![Diagnostic](./.img/diagnostic.png)

## Controls

The maximum charging current can be set in the controls. Setting in to 0 disables the charging station.

![Controls](./.img/controls.png)

## Statistics

The energy consumed and the estimated cost sensors can be used in statistics.

![Stats](./.img/stats.png)

```yaml
- type: statistic
  entity: sensor.evduty_your-station_session_estimated_cost
  period:
    calendar:
      period: year
  stat_type: change
  name: Annual Cost
  icon: mdi:ev-station
```

## Development

### Test locally

```shell
make install
make test
```

### Run locally

```shell
# from ha core repo, setup ha core
script/setup
source venv/bin/activate

# create a symlink in config/custom_component folder to this folder
cd config/custom_components
ln -s ../../../evduty-home-assistant/custom_components/evduty .

# run
hass -c config

# view
open http://localhost:8123/
```

### Release version

```shell
make release bump=patch|minor|major
```