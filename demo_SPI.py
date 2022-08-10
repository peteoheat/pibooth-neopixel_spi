#!/usr/bin/python3
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple test for NeoPixels on Raspberry Pi
import time
import board
import neopixel_spi


# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.SPI()

# The number of NeoPixels
num_pixels = 24

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel_spi.GRBW = 'GRBW'

pixels = neopixel_spi.NeoPixel_SPI(
    pixel_pin, num_pixels, bpp=4, brightness=0.2, auto_write=False, pixel_order=ORDER, bit0=0b10000000)

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if ORDER in (neopixel_spi.RGB, neopixel_spi.GRB) else (r, g, b, 0)


def rainbow_cycle(wait):
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

def countdown(time_seconds):
    time_between_pixels = time_seconds / num_pixels
    pixels.fill((0, 255, 0, 0))
    pixels.show()
    for i in range(0, num_pixels):
        pixels[num_pixels - i - 1] = (0, 0, 0, 255)
        pixels.show()
        time.sleep(time_between_pixels)

def countup(time_seconds):
    time_between_pixels = time_seconds / num_pixels
    pixels.fill((255, 0, 0, 0))
    pixels.show()
    for i in range(-1, (num_pixels - 1)):
        pixels[i + 1] = (0, 0, 0, 255)
        pixels.show()
        time.sleep(time_between_pixels)

while True:
    countdown(5)

    countup(5)

    # Uncomment this line if you have RGBW/GRBW NeoPixels
    pixels.fill((0, 0, 0, 255))
    pixels.show()
    time.sleep(5)

    pixels.fill((0, 255, 0, 0))
    pixels.show()
    time.sleep(1)

    pixels.fill((0, 0, 255, 0))
    pixels.show()
    time.sleep(1)

    pixels.fill((255,0,0,0))
    pixels.show()
    time.sleep(1)

    rainbow_cycle(0.002)  # rainbow cycle with 1ms delay per step