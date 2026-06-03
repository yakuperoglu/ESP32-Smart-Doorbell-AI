# =============================================================
#  NEOPIXEL HALKA TESTI
# =============================================================
#  Bilgisayardan calistir (kart USB'de takiliyken):
#     .\.venv\Scripts\python.exe -m mpremote connect COM10 run esp32\test_neopixel.py
#
#  Kablolama:  Halka 5V->ESP32 5V,  GND->GND,  DI->GPIO6 (istege bagli 330ohm seri)
# =============================================================
import neopixel
import machine
import time

PIN = 6      # NeoPixel DI pini
N = 8        # halkadaki LED sayisi

ring = neopixel.NeoPixel(machine.Pin(PIN), N)


def fill(c):
    for i in range(N):
        ring[i] = c
    ring.write()


print("Yesil...")
fill((0, 40, 0))
time.sleep(2)

print("Kirmizi...")
fill((40, 0, 0))
time.sleep(2)

print("Mavi...")
fill((0, 0, 40))
time.sleep(2)

fill((0, 0, 0))
print("NeoPixel test bitti. Renkler DOGRU yandiysa (yesil/kirmizi/mavi) halka TAMAM.")
