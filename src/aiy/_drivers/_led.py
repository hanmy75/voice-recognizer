# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""LED driver for the VoiceHat."""

import itertools
import os
import threading
import time

import _rpi_ws281x as ws

# LED strip configuration:
LED_COUNT      = 8      # Number of LED pixels.
LED_PIN        = 12      # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 0       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_GRB   # Strip type and colour ordering

LED_MAX_BRIGHTNESS = 150

# Define colors which will be used by the example.  Each color is an unsigned
# 32-bit value where the lower 24 bits define the red, green, blue data (each
# being 8 bits long).
# G.B.R
LED_RED = 0x002000
LED_ORANGE = 0x102000
LED_YELLOW = 0x202000
LED_GREEN = 0x200000
LED_LIGHTBLUE = 0x200020
LED_BLUE = 0x000020
LED_PURPLE = 0x001010
LED_PINK = 0x002010
LED_BLACK = 0x000000


# Create a ws2811_t structure from the LED configuration.
# Note that this structure will be created on the heap so you need to be careful
# that you delete its memory by calling delete_ws2811_t when it's not needed.
leds = ws.new_ws2811_t()

# Initialize Neopixel
def InitializeNeopixel():
    # Initialize all channels to off
    for channum in range(2):
        channel = ws.ws2811_channel_get(leds, channum)
        ws.ws2811_channel_t_count_set(channel, 0)
        ws.ws2811_channel_t_gpionum_set(channel, 0)
        ws.ws2811_channel_t_invert_set(channel, 0)
        ws.ws2811_channel_t_brightness_set(channel, 0)
	
    channel = ws.ws2811_channel_get(leds, LED_CHANNEL)
	
    ws.ws2811_channel_t_count_set(channel, LED_COUNT)
    ws.ws2811_channel_t_gpionum_set(channel, LED_PIN)
    ws.ws2811_channel_t_invert_set(channel, LED_INVERT)
    ws.ws2811_channel_t_brightness_set(channel, LED_BRIGHTNESS)

    ws.ws2811_t_freq_set(leds, LED_FREQ_HZ)
    ws.ws2811_t_dmanum_set(leds, LED_DMA)
	
    # Initialize library with LED configuration.
    ws.ws2811_init(leds)
    return channel


# Define functions which animate LEDs in various ways.
def WipeColorLED(channel, color):
    """Wipe color across display a pixel at a time."""
    for i in range(LED_COUNT):
        # Set the LED color buffer value.
        ws.ws2811_led_set(channel, i, color)
        # Send the LED color data to the hardware.
        ws.ws2811_render(leds)


# Define function which control brightnedd
def BrightnessLED(channel, bright):
    ws.ws2811_channel_t_brightness_set(channel, bright)
    # Send the LED color data to the hardware.
    ws.ws2811_render(leds)



class LED:
    """Starts a background thread to show patterns with the LED.

  Simple usage:
    my_led = LED(channel = 25)
    my_led.start()
    my_led.set_state(LED.BEACON)
    my_led.stop()
  """

    OFF = 0
    ON = 1
    BLINK = 2
    BLINK_3 = 3
    BEACON = 4
    BEACON_DARK = 5
    DECAY = 6
    PULSE_SLOW = 7
    PULSE_QUICK = 8

    def __init__(self, channel):
        self.animator = threading.Thread(target=self._animate)
        #self.channel = channel
        self.iterator = None
        self.running = False
        self.state = None
        self.sleep = 0

        self.channel = InitializeNeopixel()

        self.lock = threading.Lock()

    def start(self):
        """Starts the LED driver."""
        with self.lock:
            if not self.running:
                self.running = True
                WipeColorLED(self.channel, LED_BLACK)
                BrightnessLED(self.channel, 0)

                self.animator.start()

    def stop(self):
        """Stops the LED driver and sets the LED to off."""
        with self.lock:
            if self.running:
                self.running = False
                self.animator.join()
                WipeColorLED(self.channel, LED_BLACK)
                BrightnessLED(self.channel, 0)

    def set_state(self, state):
        """Sets the LED driver's new state.

    Note the LED driver must be started for this to have any effect.
    """
        with self.lock:
            self.state = state

    def _animate(self):
        while True:
            state = None
            running = False
            with self.lock:
                state = self.state
                self.state = None
                running = self.running
            if not running:
                return
            if state is not None:
                if not self._parse_state(state):
                    raise ValueError('unsupported state: %d' % state)
            if self.iterator:
                BrightnessLED(self.channel, next(self.iterator))
                time.sleep(self.sleep)
            else:
                # We can also wait for a state change here with a Condition.
                time.sleep(1)

    def _parse_state(self, state):
        self.iterator = None
        self.sleep = 0.0
        if state == self.OFF:
            WipeColorLED(self.channel, LED_BLACK)
            BrightnessLED(self.channel, 0)
            return True
        if state == self.ON:
            WipeColorLED(self.channel, LED_BLUE)
            BrightnessLED(self.channel, LED_MAX_BRIGHTNESS)
            return True
        if state == self.BLINK:
            WipeColorLED(self.channel, LED_RED)
            self.iterator = itertools.cycle([0, 100])
            self.sleep = 0.5
            return True
        if state == self.BLINK_3:
            WipeColorLED(self.channel, LED_RED)
            self.iterator = itertools.cycle([0, 100] * 3 + [0, 0])
            self.sleep = 0.25
            return True
        if state == self.BEACON:
            WipeColorLED(self.channel, LED_PINK)
            self.iterator = itertools.cycle(
                itertools.chain([30] * 100, [100] * 8, range(100, 30, -5)))
            self.sleep = 0.05
            return True
        if state == self.BEACON_DARK:
            WipeColorLED(self.channel, LED_PURPLE)
            self.iterator = itertools.cycle(
                itertools.chain([0] * 100, range(0, 30, 3), range(30, 0, -3)))
            self.sleep = 0.05
            return True
        if state == self.DECAY:
            self.iterator = itertools.cycle(range(100, 0, -2))
            self.sleep = 0.05
            return True
        if state == self.PULSE_SLOW:
            WipeColorLED(self.channel, LED_GREEN)
            self.iterator = itertools.cycle(
                itertools.chain(range(0, 100, 2), range(100, 0, -2)))
            self.sleep = 0.1
            return True
        if state == self.PULSE_QUICK:
            WipeColorLED(self.channel, LED_GREEN)
            self.iterator = itertools.cycle(
                itertools.chain(range(0, 100, 5), range(100, 0, -5)))
            self.sleep = 0.05
            return True
        return False
