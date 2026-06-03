# =============================================================
#  SMART DOORBELL - ESP32 (MicroPython) side
# =============================================================
#  Task:
#   1) Check if someone is approaching via HC-SR04 ultrasonic sensor
#   2) If someone is approaching, send "RING" signal to PC (USB serial)
#   3) Wait for result from PC:
#         "GREEN" -> known person  -> RGB ring turns GREEN
#         "RED"   -> stranger      -> RGB ring turns RED
#
#  NOTE: We use a single WS2812 (NeoPixel) RGB RING for the LED.
#        We can set any color with a single data wire.
# =============================================================

import sys
import time
import uselect
import neopixel
from machine import Pin, time_pulse_us

# ---------------------- PIN SETTINGS -------------------------
# (Assuming ESP32-S3. We'll update once the board is finalized.)
TRIG_PIN      = 5    # HC-SR04 Trig  -> directly to ESP32
ECHO_PIN      = 4    # HC-SR04 Echo  -> to ESP32 via LOGIC CONVERTER
NEOPIXEL_PIN  = 6    # RGB ring DI (Data In) pin
NUM_PIXELS    = 8    # Number of LEDs in the ring (change if yours is different)

# Distance in cm to consider "someone is at the door"
DISTANCE_THRESHOLD_CM = 50

# Cooldown time (ms) to prevent continuous ringing
COOLDOWN_MS = 5000

# Max wait time (ms) for PC response
RESULT_TIMEOUT_MS = 8000

# Colors (brightness kept low to avoid pulling too much current from USB)
GREEN  = (0, 40, 0)
RED    = (40, 0, 0)
BLUE   = (0, 0, 40)
OFF    = (0, 0, 0)
# -------------------------------------------------------------

trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)
ring = neopixel.NeoPixel(Pin(NEOPIXEL_PIN, Pin.OUT), NUM_PIXELS)

# For non-blocking read from USB serial port (REPL)
_poller = uselect.poll()
_poller.register(sys.stdin, uselect.POLLIN)


def fill(color):
    """Fill the entire ring with a single color."""
    for i in range(NUM_PIXELS):
        ring[i] = color
    ring.write()


fill(OFF)


def measure_distance_cm():
    """Measure distance in cm using HC-SR04. Returns None if it fails."""
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    # Measure how long the Echo pin stays HIGH (timeout ~ 30 ms = ~5 m)
    duration = time_pulse_us(echo, 1, 30000)
    if duration < 0:
        return None  # timeout / sensor didn't respond

    # Speed of sound: 0.0343 cm/us. Divide by 2 for round-trip.
    return (duration * 0.0343) / 2


def read_line(timeout_ms):
    """Read a line from PC (until \\n). Returns '' if timeout."""
    buf = ""
    deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        if _poller.poll(50):                 # Check if data available for 50 ms
            ch = sys.stdin.read(1)
            if ch == "\n" or ch == "":
                break
            if ch != "\r":
                buf += ch
    return buf.strip()


def show_result(color, seconds=3):
    """Light up the ring with the given color for 'seconds', then turn off."""
    fill(color)
    time.sleep(seconds)
    fill(OFF)


def startup_blink():
    """Blink blue on startup to indicate 'ready'."""
    for _ in range(2):
        fill(BLUE)
        time.sleep_ms(150)
        fill(OFF)
        time.sleep_ms(150)


# -------------------------- MAIN LOOP ------------------------
startup_blink()
print("BOOT")  # The PC side sees this and knows connection is established

last_ring = time.ticks_ms() - COOLDOWN_MS

while True:
    dist = measure_distance_cm()

    if dist is not None and dist < DISTANCE_THRESHOLD_CM:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_ring) > COOLDOWN_MS:
            last_ring = now

            # 1) Tell PC "someone is at the door"
            print("RING")

            # 2) Wait for face recognition result
            cmd = read_line(RESULT_TIMEOUT_MS)

            if cmd == "GREEN":
                show_result(GREEN)      # known
            elif cmd == "RED":
                show_result(RED)        # stranger
            else:
                # No response / error -> blink red shortly
                for _ in range(3):
                    fill(RED)
                    time.sleep_ms(100)
                    fill(OFF)
                    time.sleep_ms(100)

    time.sleep_ms(100)
