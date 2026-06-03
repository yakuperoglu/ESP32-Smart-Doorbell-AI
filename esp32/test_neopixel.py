# =============================================================
#  NEOPIXEL RING TEST
# =============================================================
#  Run from PC (while board is plugged into USB):
#     .\.venv\Scripts\python.exe -m mpremote connect COM10 run esp32\test_neopixel.py
#
#  Wiring:     Ring 5V->ESP32 5V,  GND->GND,  DI->GPIO6 (optional 330ohm series resistor)
# =============================================================
import neopixel
import machine
import time

PIN = 6      # NeoPixel DI pin
N = 8        # Number of LEDs in the ring

ring = neopixel.NeoPixel(machine.Pin(PIN), N)


def fill(c):
    for i in range(N):
        ring[i] = c
    ring.write()


print("Green...")
fill((0, 40, 0))
time.sleep(2)

print("Red...")
fill((40, 0, 0))
time.sleep(2)

print("Blue...")
fill((0, 0, 40))
time.sleep(2)

fill((0, 0, 0))
print("NeoPixel test finished. If the colors were CORRECT (green/red/blue), the ring is GOOD.")
