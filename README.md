# SunSpec translation for PV inverters

This is a project very much in progress.

Essentially the purpose is to take a non-SunSpec inverter, with a RTU
interface, and make it available as a SunSpec inverter via WiFi.

It uses [Microdot][1] for the HTTP server, and a very
stripped-down/modified version of [micropython-modbus][2]. The reason
for stripping down mp-modbus in this manner, was to conserve RAM.

You need an ESP32 board with [Micropython][3] for this to work.

The ESP32 is wired to a MAX485 chip for the RTU side. The default pins used are
pins 16, 17 and 4 (RX, TX, and direction). Of course this can be changed in the
code.

Internally an asyncio event loop is used to support the three concurrent
processes, namely the HTTP server, and the two modbus loops.

It will NOT run on an ESP8266. Not enough RAM.

## Currently implemented
* Sunspec 2017 support: Very slapdash. A lot of the mandatory fields are
deliberately not populated, and will probably never be populated,
because I don't need them.

* Reading a single-phase Solis inverter

* Reading an EM24 energy meter, and presenting the data as if it is a
SunSpec PV-inverter. This was done mostly to aid development at night
time, when the Solis is asleep.

## Not implemented yet, but planned.
* 3-Phase Solis

* Sunspec IEEE 1547 support.

[1]: https://github.com/miguelgrinberg/microdot
[2]: https://github.com/brainelectronics/micropython-modbus
[3]: https://micropython.org/download/
