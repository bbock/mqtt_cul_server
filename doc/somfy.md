# Somfy Configuration

Please note that this software is intended for the **Somfy RTS** system only. It
is NOT compatible with TaHoma. The RTS system provides no backchannel for
reporting status (RF commands are fire-and-forget), while TaHoma can get the
actual status of the devices. It is also not compatible with the "io" wireless
system.

Somfy RTS has a rolling encryption key that changes with each sent commend.
Therefore, the current key needs to be stored. If you loose this configuration
key, you need to re-pair this software to the device.

## Config file

You need to create a state JSON file for each device at `state/somfy/`. An example
file is:

```json
{
  "name": "Badfenster",
  "device_class": "shutter",
  "address": "B0C004",
  "enc_key": 1,
  "rolling_code": 4125,
}
```

The filename doesn't matter as long as it ends with `.json`.

The `name`attribute is just for reporting a user-friedly name on device discovery,
it is not used for any other purpose.

Currently, supported device classes are `shutter` and `shade`.

The address must be a 6 character long hexadecimal address. You can choose freely,
your shutters will learn it during pairing.

The encryption key is updated by the software each time a command is sent. If it
doesn't match the state in the shutters, they will not accept the command. This
is the primary security function of Somfy. If you loose this key or only have an
outdated one from a backup, you need to re-pair.

The CUL is paired as a new, additional remote. You can continue using the existing
remote in parallel.

## Pairing

You need an MQTT client for pairing, e.g. the Linux command line client
`mosquitto_pub` from the [Mosquitto](https://mosquitto.org/) package.

Start programming mode on your existing, physical Somfy remote. There's a button
for that (on mine it's a pinhole button on the backside.)

Then, send the string `PROG` to the MQTT `set` topic with the address you chose
in the config file. The exact topic name can be found by listening to the 
discovery messages, it is e.g. `homeassistant/cover/somfy/B0C102/set`
