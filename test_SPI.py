#!/usr/bin/python3
# minimal test for NeoPixels on Raspberry Pi
import time
import board
import neopixel_spi


num_pixels = 24

pixels = neopixel_spi.NeoPixel_SPI(
    board.SPI(),
    num_pixels,
    bpp=4,
    brightness=0.5,
    auto_write=False,
    pixel_order=neopixel_spi.GRBW,
    bit0=0b10000000)


while True:
    print('red')
    pixels.fill((255, 0, 0, 0))
    pixels.show()
    time.sleep(2)

    print('green')
    pixels.fill((0, 255, 0, 0))
    pixels.show()
    time.sleep(2)

    print('blue')
    pixels.fill((0, 0, 255, 0))
    pixels.show()
    time.sleep(2)

    print('white')
    pixels.fill((0, 0, 0, 255))
    pixels.show()
    time.sleep(2)

    #print('rgb full')
    #pixels.fill((255, 255, 255, 0))
    #pixels.show()
    #time.sleep(2)

    #print('rgbw 10')
    #pixels.fill((10, 10, 10, 10))
    #pixels.show()
    #time.sleep(2)

    #print('rgb 1, w 100')
    #pixels.fill((1, 1, 1, 100))
    #pixels.show()
    #time.sleep(2)

    #print('rgb 1, w 255')
    #pixels.fill((1, 1, 1, 255))
    #pixels.show()
    #time.sleep(2)

    #print('b 1, w 100')
    #pixels.fill((0, 0, 1, 100))
    #pixels.show()
    #time.sleep(2)
