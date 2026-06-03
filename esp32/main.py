# =============================================================
#  AKILLI KAPI ZİLİ - ESP32 (MicroPython) tarafı
# =============================================================
#  Görevi:
#   1) HC-SR04 ultrasonik sensör ile kapıya biri yaklaştı mı bak
#   2) Yaklaşan varsa bilgisayara "RING" sinyali gönder (USB seri)
#   3) Bilgisayardan gelen sonucu bekle:
#         "GREEN" -> tanıdık  -> RGB halka YEŞİL yansın
#         "RED"   -> yabancı  -> RGB halka KIRMIZI yansın
#
#  NOT: LED olarak tek bir WS2812 (NeoPixel) RGB HALKA kullanıyoruz.
#       Tek data kablosuyla istediğimiz rengi veririz.
# =============================================================

import sys
import time
import uselect
import neopixel
from machine import Pin, time_pulse_us

# ---------------------- PİN AYARLARI -------------------------
# (ESP32-S3 varsayıldı. Board'u kesinleştirince güncelleriz.)
TRIG_PIN      = 5    # HC-SR04 Trig  -> doğrudan ESP32'ye
ECHO_PIN      = 4    # HC-SR04 Echo  -> LOGIC CONVERTER üzerinden ESP32'ye
NEOPIXEL_PIN  = 6    # RGB halkanın DI (Data In) pini
NUM_PIXELS    = 8    # Halkadaki LED sayısı (azsa/çoksa burayı değiştir)

# Kaç cm'den yakına biri gelirse "kapıda biri var" sayalım
DISTANCE_THRESHOLD_CM = 50

# Zilin sürekli çalmaması için bekleme süresi (ms)
COOLDOWN_MS = 5000

# Bilgisayardan sonuç gelmesini en fazla kaç ms bekleyelim
RESULT_TIMEOUT_MS = 8000

# Renkler (parlaklık düşük tutuldu ki USB'den çok akım çekmesin)
GREEN  = (0, 40, 0)
RED    = (40, 0, 0)
BLUE   = (0, 0, 40)
OFF    = (0, 0, 0)
# -------------------------------------------------------------

trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)
ring = neopixel.NeoPixel(Pin(NEOPIXEL_PIN, Pin.OUT), NUM_PIXELS)

# USB seri porttan (REPL) gelen veriyi bloklamadan okumak için
_poller = uselect.poll()
_poller.register(sys.stdin, uselect.POLLIN)


def fill(color):
    """Tüm halkayı tek renge boya."""
    for i in range(NUM_PIXELS):
        ring[i] = color
    ring.write()


fill(OFF)


def measure_distance_cm():
    """HC-SR04 ile mesafeyi cm cinsinden ölç. Okuyamazsa None döner."""
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    # Echo pininin ne kadar süre HIGH kaldığını ölç (timeout ~ 30 ms = ~5 m)
    duration = time_pulse_us(echo, 1, 30000)
    if duration < 0:
        return None  # zaman aşımı / sensör cevap vermedi

    # Sesin hızı: 0.0343 cm/us. Gidiş-dönüş olduğu için 2'ye böl.
    return (duration * 0.0343) / 2


def read_line(timeout_ms):
    """Bilgisayardan bir satır oku (\\n'e kadar). Süre dolarsa '' döner."""
    buf = ""
    deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        if _poller.poll(50):                 # 50 ms boyunca veri var mı bak
            ch = sys.stdin.read(1)
            if ch == "\n" or ch == "":
                break
            if ch != "\r":
                buf += ch
    return buf.strip()


def show_result(color, seconds=3):
    """Halkayı belirtilen renkte belirtilen süre kadar yak, sonra söndür."""
    fill(color)
    time.sleep(seconds)
    fill(OFF)


def startup_blink():
    """Açılışta mavi yanıp sönerek 'hazırım' de."""
    for _ in range(2):
        fill(BLUE)
        time.sleep_ms(150)
        fill(OFF)
        time.sleep_ms(150)


# -------------------------- ANA DÖNGÜ ------------------------
startup_blink()
print("BOOT")  # Bilgisayar tarafı bu satırı görünce bağlantının kurulduğunu anlar

last_ring = time.ticks_ms() - COOLDOWN_MS

while True:
    dist = measure_distance_cm()

    if dist is not None and dist < DISTANCE_THRESHOLD_CM:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_ring) > COOLDOWN_MS:
            last_ring = now

            # 1) Bilgisayara "kapıda biri var" de
            print("RING")

            # 2) Yüz tanıma sonucunu bekle
            cmd = read_line(RESULT_TIMEOUT_MS)

            if cmd == "GREEN":
                show_result(GREEN)      # tanıdık
            elif cmd == "RED":
                show_result(RED)        # yabancı
            else:
                # Cevap gelmedi / hata -> kısa kırmızı uyarı kırpıştır
                for _ in range(3):
                    fill(RED)
                    time.sleep_ms(100)
                    fill(OFF)
                    time.sleep_ms(100)

    time.sleep_ms(100)
