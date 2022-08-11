# pibooth-neopixel_spi

This project is a plugin to pibooth that enables you to add neopixels to your project using the SPI bus on Raspberry Pi instead of the PWM bus. The benefits of using SPI over PWM are:

* No need to disable onboard audio on the raspberry pi. Meaning you can have sound as well as neopixels
* No need to run your pibooth software as the root user.

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
plugins = ["<your path to where you copied the file>/pibooth_neopixel-spi.py"]
```
### Files in this repository
#### pibooth-neopixel_spi.py
This is the actual PiBooth plugin and the only file you really need.
#### demo.py
This is a handy file to demonstrate coding for the neopixels. This was originally from the Adafruit examples. But I added a 'countup' feature. This feature isn't used in pibooth-neopixel_spi.py but you could do if you have a use for it.
#### test.py
I can't remember where I found this, but it's useful for ensuring you have the colours setup correctly.

### Executing program

The plugin will automatically be included in your pibooth setup the next time you restart pibooth.

## Help

* If you experience strange neopixel behaviours in the first instance check all of your connections, especially the ground wires between neopixel and raspberry pi and raspberry pi and the power source you are using for your neopixels.

## Version History

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
