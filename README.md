pibooth-neopixel_spi
====================
A powerful and feature-rich plugin for `pibooth <https://github.com/pibooth/pibooth>`_
that drives NeoPixel / WS281x LEDs using the **SPI bus** instead of PWM.

This avoids the common limitations of PWM-based NeoPixel libraries:

* No need to disable onboard audio
* No need to run pibooth as root
* More stable timing on Raspberry Pi
* Compatible with RGB and RGBW LEDs

This plugin provides:

* A fully configurable attract-mode animation engine
* Preview countdown ring animation with auto-calibration
* Flash effects during capture
* Clean integration with all pibooth state hooks
* Persistent timing calibration for consistent countdown behaviour

The plugin is implemented in a single file: ``pibooth-neopixel_spi.py``.

Features
========

* SPI‑driven NeoPixel control using ``neopixel_spi`` and ``board.SPI()``
* Configurable number of pixels, brightness, BPP, pixel order, and SPI timing
* Rich attract-mode engine with multiple patterns:
  - rainbow
  - color_wipe
  - theater_chase
  - pulse
  - comet
  - sparkle
  - gradient
  - chase_multi
  - fire
  - ocean
* Sequence-based attract mode (pattern|R,G,B[,W]|duration)
* Preview countdown ring with automatic timing calibration
* Flash colour during capture
* Persistent multiplier stored in ``~/.config/neopixel_multiplier.json``
* Clean shutdown and state transitions

## Description

[PiBooth](https://pibooth.readthedocs.io/en/latest/) is a fantastic project for creating your own Photobooth. I have built one using a Raspberry Pi and more details on my implementation to come. But I really wanted to use an Adafruit neopixel ring to implement things like:
* An attract mode to draw attention to the booth
* A visual countdown timer
* A 'flash' as the virtual-shutter captures the image.

I original followed the Adafruit 
[Adafruit NeoPixel Python usage guide](https://learn.adafruit.com/neopixels-on-raspberry-pi/python-usage) to get my neopixel ring setup. But then I ran into problems with the fact that the code has to run as the root user. I didn't want to do that for security reasons. So I decided to use the SPI bus instead which does not require root to use it.

## Getting Started

### Dependencies

* On your Raspberry pi you have to enable use of SPI using raspi-config. Look in the 'Interfaces' section to enable it.
* Connect the 'Data In' or DIN line of the neopixels to GPIO Pin 10 (SPI0 MOSI) Physical pin 19 on your Raspberry Pi https://pinout.xyz/pinout/pin19_gpio10
* Install the [neopixel_spi library](https://docs.circuitpython.org/projects/neopixel_spi/en/latest/)

### Installing

* git clone this respository to your raspberry pi
* move or copy the file pibooth-neopixel_spi.py to the location where you keep your pibooth plugins that are not directly installed using pip.
* Edit your pibooth.config file and edit this line to add pibooth-neopixel_spi
```
# Path to custom plugin(s) not installed with pip (list of quoted paths accepted)
plugins = ["<your path to where you copied the file>/pibooth-neopixel_spi.py"]
```

Configuration Options
=====================

All options live under the ``[NEOPIXEL]`` section of ``pibooth.cfg``.

General LED Settings
--------------------

``pixels``  
    Number of LEDs (default: 24)

``brightness``  
    Float 0.0–1.0 (default: 0.2)

``bpp``  
    Bytes per pixel: 3=RGB, 4=RGBW (default: 4)

``bit0``  
    SPI timing bit value (default: 0b10000000)

``pixel_order``  
    One of: RGB, GRB, RGBW, etc. (default: RGBW)

``auto_write``  
    Whether pixel changes auto‑flush (default: False)


Attract Mode Settings
---------------------

``attract_sequence``  
    A semicolon-separated list of entries::

        pattern|R,G,B[,W]|duration

    Example::

        rainbow||6; pulse|0,0,255|4; sparkle|255,255,255|2

``attract_speed``  
    Base delay between animation steps (default: 0.02)

``attract_default_duration``  
    Duration used when a sequence entry omits one (default: 6.0)


Preview & Flash Settings
------------------------

``preview_delay``  
    Duration of preview state (default: 5.0)

``preview_countdown``  
    Whether to show countdown ring (default: True)

``flash_color``  
    Flash colour during capture, CSV format (default: 255,255,255,0)


Calibration Settings
--------------------

``neopixel_multiplier``  
    Manual multiplier for countdown timing (default: 1.75)

``neopixel_auto_calibrate``  
    Whether to auto‑calibrate at startup (default: True)

``neopixel_calibrate_steps``  
    Number of cycles used for calibration (default: 8)

``neopixel_multiplier_min``  
    Minimum allowed multiplier (default: 0.5)

``neopixel_multiplier_max``  
    Maximum allowed multiplier (default: 4.0)

Attract Mode Patterns
=====================

The plugin includes a rich set of built‑in patterns:

* ``rainbow`` — classic rotating rainbow wheel
* ``color_wipe`` — sequential fill
* ``theater_chase`` — marquee-style chase
* ``pulse`` — smooth brightness pulsing
* ``comet`` — moving head with fading tail
* ``sparkle`` — random twinkles
* ``gradient`` — HSV-based colour shifting
* ``chase_multi`` — multi-colour repeating chase
* ``fire`` — flame simulation
* ``ocean`` — slow blue-green wave motion

Each pattern accepts optional colour and duration parameters via the sequence field.


Runtime Behaviour
=================

The plugin integrates with pibooth’s state machine:

* **WAIT state**  
  Attract mode runs continuously.

* **CHOOSE state**  
  LEDs turn solid red.

* **PREVIEW state**  
  LEDs turn green.  
  If enabled, a countdown ring animates based on calibrated timing.

* **CAPTURE state**  
  A flash colour is shown briefly, then LEDs turn white.

* **CLEANUP**  
  Attract mode stops and LEDs are cleared.


Countdown Calibration
=====================

The plugin measures SPI write speed and LED count to compute a timing multiplier.

Order of precedence:

1. Persisted multiplier (``~/.config/neopixel_multiplier.json``)
2. Auto-calibration (if enabled)
3. Configured ``neopixel_multiplier``

This ensures countdown animations remain consistent across hardware variations.


Persistence File
================

The calibration multiplier is stored at::

    ~/.config/neopixel_multiplier.json

Example::

    { "multiplier": 1.842 }


Troubleshooting
===============

**LEDs flicker or behave erratically**  
    Ensure wiring is correct and SPI is enabled.

**Countdown timing feels too fast/slow**  
    Disable auto-calibration and set ``neopixel_multiplier`` manually.

**Attract mode does not start**  
    Check your ``attract_sequence`` formatting.

**Flash colour not visible**  
    Ensure your LEDs support RGBW if using a W component.
    
### Files in this repository
#### pibooth-neopixel_spi.py
This is the actual PiBooth plugin and the only file you really need.
#### neopixel_countdown_calibrate.py
This can be used as a standalone neopixel multiplier calculation script.
#### demo.py
This is a handy file to demonstrate coding for the neopixels. This was originally from the Adafruit examples. But I added a 'countup' feature. This feature isn't used in pibooth-neopixel_spi.py but you could do if you have a use for it.
#### test.py
I can't remember where I found this, but it's useful for ensuring you have the colours setup correctly.

### Executing program

The plugin will automatically be included in your pibooth setup the next time you restart pibooth.

## Help

* If you experience strange neopixel behaviours in the first instance check all of your connections, especially the ground wires between neopixel and raspberry pi and raspberry pi and the power source you are using for your neopixels.

## Version History

* 2.0
   * All new version with much much more functionality.
* 0.1
    * Initial Release

## License

This software is unlicensed - see the LICENSE.md file for details

## Acknowledgments

Inspiration, code snippets, etc.
* [PiBooth](https://pibooth.readthedocs.io/en/latest/)
* [Matt Steele](https://github.com/mattdsteele/pibooth-config) for creating the pibooth-neopixel plugin that I started with.
* [Adafruit Neopixel](https://github.com/adafruit/Adafruit_CircuitPython_NeoPixel) for all of the great examples.
* [Adafruit Neopixel Uberguide](https://learn.adafruit.com/adafruit-neopixel-uberguide)
