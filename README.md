# Tuya IR Bridge for Home Assistant

Tuya IR Bridge exposes Tuya Smart IR remotes in Home Assistant using Tuya Cloud's infrared APIs.

It is built for devices that are visible in the Tuya or Smart Life app but are not useful through the official Home Assistant Tuya integration, especially:

- IR air conditioners as a Home Assistant `climate` entity.
- Generic saved IR remotes, such as ceiling fans, as Home Assistant `button` entities.

## Status

Early prototype. The integration currently supports one IR hub, one optional AC remote, and one optional generic remote per config entry.

Known working examples:

- Daikin AC virtual remote through the AC scene endpoint.
- Atomberg fan virtual remote through raw IR keys.

## Features

- UI configuration flow.
- Tuya Cloud HMAC signing, no external Python package required.
- AC support:
  - on/off
  - target temperature
  - HVAC mode
  - fan mode
- Generic remote support:
  - one Home Assistant button per Tuya raw key.

## Important Limitations

IR is one-way. Home Assistant cannot know whether the physical appliance actually received the signal or whether somebody used the original remote.

Some Tuya remotes expose `PowerOn` and `PowerOff` keys that are accepted by the API but do not emit useful IR for the real device. In that case, use the raw `power` key and treat it as a toggle.

## Installation With HACS

1. Open HACS.
2. Add this repository as a custom repository.
3. Choose category `Integration`.
4. Install **Tuya IR Bridge**.
5. Restart Home Assistant.
6. Go to **Settings -> Devices & services -> Add integration**.
7. Search for **Tuya IR Bridge**.

## Manual Installation

Copy `custom_components/tuya_ir_bridge` into your Home Assistant config directory:

```text
config/custom_components/tuya_ir_bridge
```

Restart Home Assistant, then add the integration from the UI.

## Tuya Cloud Setup

You need a Tuya IoT Cloud project linked to the same Tuya or Smart Life app account that owns the IR hub.

Required values:

- Tuya Cloud client ID
- Tuya Cloud client secret
- Data center region
- IR hub device ID
- Optional AC virtual remote device ID
- Optional generic virtual remote device ID

The required Tuya API permissions vary by Tuya account/project, but these API groups are usually relevant:

- Authorization
- Device Status Notification
- Smart Home Basic Service
- IR Control Hub Open Service

## Finding Device IDs

In Tuya IoT Platform, open your cloud project and link your app account. Under linked devices you should see:

- The physical Smart IR hub.
- Virtual IR remotes, such as AC, fan, TV, etc.

Use the physical Smart IR device ID as **IR hub ID**. Use the virtual remote device IDs for the AC or generic remote fields.

## Example Entities

If you configure an AC named `AC`, Home Assistant creates:

```text
climate.ac
```

If you configure an Atomberg fan named `Atomberg Fan`, Home Assistant creates buttons similar to:

```text
button.atomberg_fan_power
button.atomberg_fan_sleep
button.atomberg_fan_fan_speed1
button.atomberg_fan_fan_speed2
button.atomberg_fan_fan_speed3
button.atomberg_fan_fan_speed4
button.atomberg_fan_fan_speed5
button.atomberg_fan_boost
button.atomberg_fan_timing1
button.atomberg_fan_timing2
button.atomberg_fan_timing3
button.atomberg_fan_timing6
```

## Automation Examples

Turn the AC on at 26 C:

```yaml
action: climate.set_temperature
target:
  entity_id: climate.ac
data:
  temperature: 26
  hvac_mode: cool
```

Press the fan power toggle:

```yaml
action: button.press
target:
  entity_id: button.atomberg_fan_power
```

Set fan speed 3:

```yaml
action: button.press
target:
  entity_id: button.atomberg_fan_fan_speed3
```

## Development

Clone the repository, then copy or symlink `custom_components/tuya_ir_bridge` into a Home Assistant config directory.

Basic syntax check:

```bash
python3 -m compileall custom_components/tuya_ir_bridge
```

## Attribution

This project was created after testing Tuya Cloud IR endpoints against real Smart IR hardware. It intentionally avoids bundling private Home Assistant configuration, device IDs, local keys, or Tuya account secrets.

## License

MIT
