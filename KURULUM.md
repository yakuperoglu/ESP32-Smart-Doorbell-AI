# 🛠️ Kurulum Rehberi — Akıllı Kapı Zili

Bu dosya projeyi **sıfırdan** çalışır hale getirmenin tüm adımlarını anlatır.
Günlük kullanım (yüz ekleme, başlatma) için → **[KULLANIM.md](KULLANIM.md)**.

> Kurulum sırası: **PC kurulumu → Donanım kablolama → ESP32 (MicroPython) kurulumu → Parça testleri**

---

## 0. Bu projede ne kuruyoruz?

```
[HC-SR04]  →  ESP32-S3  →  (USB Seri)  →  PC (Python + Webcam)
                  ↑                              │
                  │                         Yüz tanıma
                  │                              │
        Yeşil/Kırmızı LED  ←─ "GREEN"/"RED" ───┘
```

- **Bilgisayar:** Python ile webcam'den yüz tanıma yapar.
- **ESP32:** MicroPython çalıştırır; sensörü okur, sonuca göre LED'i yakar.

---

## 1. Gereksinimler

### Donanım
| Bileşen | Not |
|---|---|
| ESP32-S3 geliştirme kartı | (bizdeki: çift USB-C, CP210x) |
| HC-SR04 ultrasonik mesafe sensörü | |
| WS2812B 8-bit NeoPixel halka | "led ışık" |
| BSS138 lojik seviye dönüştürücü | 3.3V ↔ 5V |
| Breadboard + jumper kablolar | |
| 330Ω direnç, 1000µF kondansatör | (opsiyonel ama önerilir) |
| USB-C kablo | ESP32 ↔ bilgisayar |
| Webcam | bilgisayara bağlı |

> Donanımın tüm teknik detayı: **[esp32s3_donanim_raporu.md](esp32s3_donanim_raporu.md)**

### Yazılım
- **Windows 10/11**
- **Python 3.10+** (kontrol: `python --version`)
- Conda **gerekmez**.

---

## 2. Projeyi indir

GitHub'dan klonla ya da ZIP indirip aç. Sonra **proje kök dizinine** gir
(içinde `pc/`, `esp32/`, `README.md` olan klasör). Tüm komutlar buradan çalıştırılır.

```powershell
cd C:\...\ESP32-Smart-Doorbell-AI
```

---

## 3. Bilgisayar (PC) Kurulumu

Tek komut her şeyi kurar (sanal ortam + tüm paketler):

```powershell
powershell -ExecutionPolicy Bypass -File pc\kurulum.ps1
```

Bu script:
1. `.venv` adında bir **sanal ortam** oluşturur (sistemdeki Python ile),
2. `dlib`'i **önceden derlenmiş** halde kurar (`dlib-bin` → Visual Studio/derleme derdi YOK),
3. `face_recognition`, `opencv`, `pyserial` paketlerini kurar,
4. ESP32 araçlarını (`esptool`, `mpremote`) kurar.

### Kurulumu doğrula
```powershell
.\.venv\Scripts\python.exe pc\dogrula_kurulum.py
```
Hepsi `[OK]` olmalı:
```
[OK]   cv2                4.x
[OK]   numpy              2.x
[OK]   serial             3.5
[OK]   dlib               20.x
[OK]   face_recognition   1.x
```

> ℹ️ Kurulum sırasında çıkan **"dlib>=19.7 not installed"** uyarısı **zararsızdır**
> (modülün adı `dlib`, paketin adı `dlib-bin`; `import dlib` çalışır).

---

## 4. Donanım Kablolama

> ⚡ Kabloları bağlarken ESP32'yi USB'den **çıkar**, bağladıktan sonra tak.

### Pin haritası
**HC-SR04:**
| HC-SR04 | Nereye | Not |
|---|---|---|
| VCC | ESP32 **5V** | sensör 5V ister |
| GND | ESP32 **GND** | ortak toprak |
| Trig | ESP32 **GPIO5** | **DOĞRUDAN** (converter'dan geçmez!) |
| Echo | **BSS138 HV1 → LV1** → ESP32 **GPIO4** | Echo 5V verir, düşürmek şart |

**BSS138 dönüştürücü:**
| Converter | Nereye |
|---|---|
| HV | ESP32 **5V** |
| LV | ESP32 **3.3V** |
| GND | ESP32 **GND** |
| HV1 | HC-SR04 **Echo** |
| LV1 | ESP32 **GPIO4** |

**WS2812B halka:**
| Halka | Nereye | Not |
|---|---|---|
| 5V | ESP32 **5V** | titrerse 1N5819 diyot ile ~4.3V |
| GND | ESP32 **GND** | |
| DI | **330Ω** → ESP32 **GPIO6** | **DOĞRUDAN** (BSS138'den GEÇİRME!) |
| DO | — | boş |

### ⚠️ En kritik 4 kural (yoksa çalışmaz)
1. **Trig doğrudan GPIO5'e** bağlanır — BSS138'den **geçmez**. (Sadece Echo geçer.)
2. **WS2812B DI doğrudan GPIO6'ya** — BSS138'den **GEÇİRME** (800 kbps için uygun değil, renkler bozulur).
3. **ORTAK GND:** ESP32 GND + HC-SR04 GND + BSS138 GND hepsi birbirine bağlı olmalı.
4. **BSS138 referansları:** HV→5V ve LV→3.3V beslenmeli, yoksa converter çalışmaz.

---

## 5. ESP32 Kurulumu (MicroPython)

### 5.1 — COM portunu bul
ESP32'yi USB ile tak, sonra:
```powershell
.\.venv\Scripts\python.exe -m serial.tools.list_ports -v
```
**Bluetooth olmayan**, `Silicon Labs CP210x` / `CH340` / `USB Serial` yazan portu seç.
(Bizdeki: **COM10**. Seninki farklı olabilir — aşağıda `COM10` yerine kendi portunu yaz.)

### 5.2 — MicroPython firmware'ini yükle
1. Firmware'i indir: <https://micropython.org/download/ESP32_GENERIC_S3/>
   → en güncel **stable** `.bin` (örn. `ESP32_GENERIC_S3-20260406-v1.28.0.bin`).
2. Flash'ı sil:
   ```powershell
   .\.venv\Scripts\python.exe -m esptool --chip esp32s3 --port COM10 erase-flash
   ```
3. Firmware'i yaz (**offset 0**, ESP32-S3 için doğru):
   ```powershell
   .\.venv\Scripts\python.exe -m esptool --chip esp32s3 --port COM10 --baud 460800 write-flash 0 "C:\indirilenler\ESP32_GENERIC_S3-20260406-v1.28.0.bin"
   ```
   Sonunda `Hash of data verified.` görürsen yükleme başarılı.

> 🔌 esptool "Failed to connect" derse: **BOOT** tuşunu basılı tut → **RESET**'e bas → BOOT'u bırak → komutu tekrar çalıştır. (Bizim kartta gerekmedi, otomatik girdi.)

### 5.3 — `main.py`'yi karta yükle
Karta `main.py` adıyla kopyalanır; böylece kart her açılışta otomatik çalıştırır:
```powershell
.\.venv\Scripts\python.exe -m mpremote connect COM10 fs cp esp32\main.py :main.py
.\.venv\Scripts\python.exe -m mpremote connect COM10 reset
```
Reset sonrası **halka 2 kez mavi yanıp sönerse** main.py çalışıyor demektir. 🎉

---

## 6. Parça Testleri (doğrulama)

Her parçayı tek tek dene (kart USB'de takılıyken):

**LED halka testi** — sırayla yeşil → kırmızı → mavi yanmalı:
```powershell
.\.venv\Scripts\python.exe -m mpremote connect COM10 run esp32\test_neopixel.py
```

**HC-SR04 testi** — elini sensörün önünde gezdir, cm değerleri değişmeli:
```powershell
.\.venv\Scripts\python.exe -m mpremote connect COM10 run esp32\test_hcsr04.py
```

> Not: Parça testlerini çalıştırmak için karttaki `main.py`'nin durması gerekir;
> `mpremote run` bunu otomatik yapar. Test sonrası karta tekrar enerji verince
> `main.py` yeniden çalışır.

---

## 7. Sık Karşılaşılan Sorunlar

| Belirti | Çözüm |
|---|---|
| **HC-SR04 hep "timeout"** | Trig'i **doğrudan GPIO5'e** bağladın mı? Ortak GND var mı? HC-SR04 VCC **5V** mi? (Bizde sebep: Trig bağlı değildi.) |
| **LED yanmıyor** | DI gerçekten **GPIO6**'da mı (DO değil)? 5V/GND doğru mu? |
| **LED titriyor / yanlış renk** | 3.3V data sorunu → halkayı **1N5819 diyot** ile ~4.3V besle. |
| **COM portu göremiyorum** | Sürücü eksik olabilir (CP210x/CH340 sürücüsü). Başka USB-C portunu dene. Bluetooth portlarıyla (COM3-8) karıştırma. |
| **`mpremote`/`esptool` bağlanamıyor / port meşgul** | `doorbell.py` veya Thonny gibi başka bir program portu tutuyor olabilir; kapat. |
| **"dlib>=19.7 not installed" uyarısı** | Zararsız, görmezden gel (`dlib-bin` kuruldu). |
| **Kamera açılmıyor** | [pc/doorbell.py](pc/doorbell.py) ve [pc/enroll.py](pc/enroll.py) içindeki `CAMERA_INDEX = 0` → `1` veya `2` yap. |

---

## 8. Kurulum bitti → şimdi ne yapacaksın?

➡️ **[KULLANIM.md](KULLANIM.md)** dosyasına geç: tanıdık yüz ekleme ve projeyi başlatma orada.
