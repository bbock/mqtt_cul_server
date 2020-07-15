# Somfy Configuration

Somfy has a rolling encryption key that changes with each sent commend. Therefore,
the current key needs to be stored. If you loose this configuration key, you need
to re-pair this software to the device.

You need to create a state JSON file for each device at `state/somfy/`. An example
file is:

```json
{
  "name": "Badfenster",
  "device_class": "shutter",
  "address": "B0C004",
  "enc_key": 3,
  "rolling_code": 4125,
}
```

The filename doesn't matter as long as it ends with `.json`.

Currently, supported device classes are `shutter` and `shade`.

The CUL is paired as a new, additional remote. You can continue using the existing
remote in parallel.
