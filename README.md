# MQTT CUL server

This software package provides a bridge to connect a CUL wireless transceiver
with an MQTT broker, so that multiple clients (smart home, other apps) can
use it over the network to control various smart home devices.

Currently it is used and tested with Somfy rollershutters and shades as well as
Brennenstuhl RCS switchable power sockets (Intertechno-compatible).

At the moment, this bridge is one-way only: MQTT -> CUL. Receiving messages via CUL
and forwarding to MQTT is currently unsupported (due to the author not having any 
devices supporting that).

Further information about the CUL: [Product page](http://busware.de/tiki-index.php?page=CUL), [firmware details](http://culfw.de/).

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

Somfy configuration is a bit more involved. The documentation is [here](doc/somfy.md).
