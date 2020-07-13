# MQTT to CUL bridge

This software package provides a bridge to connect a CUL wireless tarnsceiver
with an MQTT bridge, so that multiple clients (smart home, other apps) can
use it over the network to control various smart home devices.

Currently used and tested with Somfy rollershutters and shades as well as
Brennenstuhl RCS switchable power sockets (Intertechno-compatible).

At the moment, this bridge is one-way: MQTT -> CUL. Receiving messages via CUL
and forwarding to MQTT is unsupported (due to the author not having any devices
supporting that).

Further information about the CUL: www.culfw.de

# TODO

-   Config / cmd argument for MQTT broker
-   Improve device onboarding
-   Write more documentation
-   Write some tests
-   Make python 3 compatible
