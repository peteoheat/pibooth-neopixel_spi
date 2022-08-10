# pibooth-neopixel_spi

This project is a plugin to pibooth that enables you to add neopixels to your project using the SPI bus on Raspberry Pi instead of the PWM bus. The benefits of using SPI over PWM are:

* No need to disable onboard audio on the raspberry pi. Meaning you can have sound as well as neopixels
* No need to run your pibooth software as the root user.

## Description

https://pibooth.readthedocs.io/en/latest/> is a fantastic project for creating your own Photobooth. I have built one using a Raspberry Pi and more details on my implementation to come. But I really wanted to use an Adafruit neopixel ring to implement things like:
* An attract mode to draw attention to the booth
* A visual countdown timer
* A 'flash' as the virtual-shutter captures the image.

I original followed the Adafruit 
https://learn.adafruit.com/neopixels-on-raspberry-pi/python-usage to get my neopixel ring setup. But then I ran into problems with the fact that the code has to run as the root user. I didn't want to do that for security reasons. So I decided to use the SPI bus instead which does not require root to use it.

## Getting Started

### Dependencies

* On your Raspberry pi you have to enable use of SPI using raspi-config. Look in the 'Interfaces' section to enable it.
* Install the neopixel_spi library https://docs.circuitpython.org/projects/neopixel_spi/en/latest/

### Installing

* How/where to download your program
* Any modifications needed to be made to files/folders

### Executing program

* How to run the program
* Step-by-step bullets
```
code blocks for commands
```

## Help

Any advise for common problems or issues.
```
command to run if program contains helper info
```

## Authors

Contributors names and contact info

ex. Dominique Pizzie  
ex. [@DomPizzie](https://twitter.com/dompizzie)

## Version History

* 0.2
    * Various bug fixes and optimizations
    * See [commit change]() or See [release history]()
* 0.1
    * Initial Release

## License

This project is licensed under the [NAME HERE] License - see the LICENSE.md file for details

## Acknowledgments

Inspiration, code snippets, etc.
* [awesome-readme](https://github.com/matiassingers/awesome-readme)
* [PurpleBooth](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)
* [dbader](https://github.com/dbader/readme-template)
* [zenorocha](https://gist.github.com/zenorocha/4526327)
* [fvcproductions](https://gist.github.com/fvcproductions/1bfc2d4aecb01a834b46)
