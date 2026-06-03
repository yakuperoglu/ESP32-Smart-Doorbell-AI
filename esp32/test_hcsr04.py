# =============================================================
#  HC-SR04 DISTANCE SENSOR TEST
# =============================================================
#  Run from PC (while board is plugged into USB):
#     .\.venv\Scripts\python.exe -m mpremote connect COM10 run esp32\test_hcsr04.py
#
#  Wiring:     Trig->GPIO5,  Echo->(via BSS138 LV1<-HV1)->GPIO4
#              HC-SR04 VCC->5V,  GND->GND
# =============================================================
import time
from machine import Pin, time_pulse_us

TRIG = 5
ECHO = 4

trig = Pin(TRIG, Pin.OUT)
echo = Pin(ECHO, Pin.IN)


def distance_cm():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    duration = time_pulse_us(echo, 1, 30000)   # timeout ~30 ms (~5 m)
    if duration < 0:
        return None
    return (duration * 0.0343) / 2


print("Taking 10 measurements (wave your hand in front of the sensor):")
for i in range(10):
    d = distance_cm()
    if d is None:
        print("  - NO measurement (timeout) -> Check Echo/Trig wiring and BSS138")
    else:
        print("  - %.1f cm" % d)
    time.sleep(0.5)
print("HC-SR04 test finished.")
