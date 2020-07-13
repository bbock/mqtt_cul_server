# MQTT CUL server

This software package provides a bridge to connect a CUL wireless tarnsceiver
with an MQTT bridge, so that multiple clients (smart home, other apps) can
use it over the network to control various smart home devices.

Currently it is used and tested with Somfy rollershutters and shades as well as
Brennenstuhl RCS switchable power sockets (Intertechno-compatible).

At the moment, this bridge is one-way only: MQTT -> CUL. Receiving messages via CUL
and forwarding to MQTT is unsupported (due to the author not having any devices
supporting that).

Further information about the CUL: www.culfw.de

## Device discovery

[Home Assistant](https://www.home-assistant.io/) defines an interface for device
auto-discovery, which is supported by this software.

## Configuration

### CUL

For the CUL, you just need to configure the serial device of the dongle in
`mqtt_cul_server.ini`.

### Intertechno

For Intertechno, you need to configure the system ID, often also called house ID,
in `mqtt_cul_server.ini` and enable it.

### Somfy

Somfy configuration is a bit more involved.

You need to create a state JSON file for each device at `state/somfy`. An example
file is:

```json
{
  "name": "Badfenster",
  "device_class": "shutter",
  "address": "B0C004",
  "enc_key": 6,
  "rolling_code": 1258,
}
```

Currently, supported device classes are `shutter` and `shade`.

TODO: Write how to pair / get initial values.

## TODO

- Improve device onboarding
- Write some tests
