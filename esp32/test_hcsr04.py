# =============================================================
#  HC-SR04 MESAFE SENSORU TESTI
# =============================================================
#  Bilgisayardan calistir (kart USB'de takiliyken):
#     .\.venv\Scripts\python.exe -m mpremote connect COM10 run esp32\test_hcsr04.py
#
#  Kablolama:  Trig->GPIO5,  Echo->(BSS138 LV1<-HV1 uzerinden)->GPIO4
#              HC-SR04 VCC->5V,  GND->GND
# =============================================================
import time
from machine import Pin, time_pulse_us

TRIG = 5
ECHO = 4

trig = Pin(TRIG, Pin.OUT)
echo = Pin(ECHO, Pin.IN)


def mesafe_cm():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    sure = time_pulse_us(echo, 1, 30000)   # timeout ~30 ms (~5 m)
    if sure < 0:
        return None
    return (sure * 0.0343) / 2


print("10 olcum yapiliyor (elini sensorun onunde gezdir):")
for i in range(10):
    d = mesafe_cm()
    if d is None:
        print("  - olcum YOK (timeout) -> Echo/Trig kablosunu ve BSS138'i kontrol et")
    else:
        print("  - %.1f cm" % d)
    time.sleep(0.5)
print("HC-SR04 test bitti.")
