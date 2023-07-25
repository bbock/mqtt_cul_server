# MQTT CUL server

** THIS BRANCH IS WORK-IN-PROGRESS FOR CONVERTING THIS INTO AN HA ADDON. IT IS
NOT FUNCTIONAL YET. PLEASE USE THE MASTER BRANCH AS SIMPLE DOCKER CONTAINER FOR
NOW. **

This software package provides a bridge to connect a CUL wireless transceiver
with an MQTT broker, so that multiple clients (smart home, other apps) can
use it over the network to control various smart home devices.

Currently it is used and tested with Somfy RTS rollershutters and shades as well as
Brennenstuhl RCS switchable power sockets (Intertechno-compatible) for control
and LaCrosse IT+ temperature / humidity sensors (Technoline TX29 DTH-IT) for receiving.

Further information about the CUL: [Product page](http://busware.de/tiki-index.php?page=CUL), [firmware details](http://culfw.de/).

This software is provided not only as source code, but also as Docker image for
ARMv7 processors (Raspberry Pi). An example `docker-compose.yml` is included.

## Device discovery

[Home Assistant](https://www.home-assistant.io/) defines an [interface for device
auto-discovery](https://www.home-assistant.io/docs/mqtt/discovery/), which is
supported by this software.

## Configuration

### CUL

The software supports both the 433 MHz and 868 MHz hardware.

For the CUL, you just need to configure the serial device of the dongle in
`mqtt_cul_server.ini`.

### Intertechno

For Intertechno-based switches, you need to configure the system ID,
often also called house ID, in `mqtt_cul_server.ini` and enable it.

### Somfy

Somfy RTS configuration is a bit more involved. The documentation is
[here](doc/somfy.md).

### LaCrosse IT+

No configuration required.
