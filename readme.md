# HID_UPS

Uses hidapi to listen for UPS data.

Currently only tested working with a `CyberPower CP1500PFCLCD`

## Dependencies

Uses [zenlib](https://github.com/desultory/zenlib) and [hidapi](https://github.com/trezor/cython-hidapi)

## Usage

This must be run as root unless the user has privileges to use the `hidraw` socket the UPS uses.

This package can be installed with `sudo pip install --break .` then run with `sudo hid_ups`.

Once started, `hid_ups` will attempt to find UPS devices and listen for stats.

A `SIGHUP` can be sent to the process to re-scan for devices.

> This will close current listeners, and will momentarily throw errors until the socket is re-opened

## Device detection

`hid_ups` detects the device using vendor/device strings. Only one is currently added. The are defined in [hid_devices](src/hid_ups/hid_devices.py)

