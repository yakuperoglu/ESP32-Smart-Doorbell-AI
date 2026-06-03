# 🔔 Akıllı Kapı Zili — Yüz Tanımalı (ESP32 + Python)

Kapıya biri yaklaşınca ultrasonik sensör tetiklenir, bilgisayar webcam'den
yüz tanıma yapar; **tanıdıksa yeşil**, **yabancıysa kırmızı** LED yanar.

> 📚 **Hızlı başlangıç:** Sıfırdan kurulum → **[KURULUM.md](KURULUM.md)** · Günlük kullanım (yüz ekleme, başlatma) → **[KULLANIM.md](KULLANIM.md)**

## Çalışma Mantığı

```
[HC-SR04]  →  ESP32  →  (USB Seri)  →  Bilgisayar (Python + Webcam)
                 ↑                              │
                 │                         Yüz tanıma
                 │                              │
        Yeşil/Kırmızı LED  ←─ "GREEN"/"RED" ───┘
```

## Klasör Yapısı

```
Ai Project/
├── esp32/
│   └── main.py          # ESP32'ye yüklenecek (MicroPython)
├── pc/
│   ├── doorbell.py          # Ana program (--test modu + seri + yüz tanıma)
│   ├── enroll.py            # Webcam ile tanıdık yüz ekleme aracı
│   ├── kurulum.ps1          # PC kurulum scripti (.venv + paketler)
│   ├── dogrula_kurulum.py   # Kurulum doğrulama
│   └── requirements.txt
├── known_faces/         # Tanıdık kişilerin fotoğrafları
└── README.md
```

---

## 1) Donanım Bağlantıları (Kablolama)

> ℹ️ Pin numaraları **ESP32-S3** varsayımıyla yazıldı. Board kesinleşince
> güncellenecek. Değiştirirsen `esp32/main.py` içindeki ayarları da güncelle.

### HC-SR04 (ultrasonik sensör)
| HC-SR04 | Nereye | Not |
|---------|--------|-----|
| VCC | ESP32 **5V (VIN)** | Sensör 5V ister |
| GND | ESP32 **GND** | Ortak toprak |
| Trig | ESP32 **GPIO 5** | Doğrudan (3.3V tetiklemeye yeter) |
| Echo | **Logic Converter** → ESP32 **GPIO 4** | Echo 5V verir, düşürmek şart! |

### Logic Level Converter (Echo'yu 5V → 3.3V düşürmek için)
| Converter | Nereye |
|-----------|--------|
| HV | ESP32 **5V (VIN)** |
| LV | ESP32 **3.3V** |
| GND (her iki taraf) | ESP32 **GND** |
| HV1 | HC-SR04 **Echo** |
| LV1 | ESP32 **GPIO 4** |

### WS2812 RGB LED Halkası ("led ışık")
| Halka | Nereye | Not |
|-------|--------|-----|
| 5V | ESP32 **5V (VIN)** | Halka 5V ister |
| GND | ESP32 **GND** | Ortak toprak |
| DI (Data In) | **330 Ω** → ESP32 **GPIO 6** | **Doğrudan** sür; titrerse halkayı 1N5819 diyot ile ~4.3 V besle |
| DO (Data Out) | — | Boş kalsın (zincirleme için, gerekmez) |

> ⚠️ WS2812B data hattını **BSS138 logic converter'dan GEÇİRME** — 800 kbps için
> uygun değil, renkler bozulur. BSS138'i sadece HC-SR04 Echo için kullan.
> Detay: `esp32s3_donanim_raporu.md` Bölüm 3.
> `main.py` içinde `NUM_PIXELS` değerini halkandaki LED sayısına göre ayarla.

---

## 2) ESP32 Kurulumu (MicroPython)

1. **MicroPython firmware**'ini ESP32'ye yükle (bir kerelik):
   - [Thonny IDE](https://thonny.org/) indir → kur.
   - Thonny → `Tools > Options > Interpreter` → "MicroPython (ESP32)" seç.
   - Sağ alttan "Install or update MicroPython" → **board ailesini doğru seç!**
     Board'un **ESP32-S3** ise "ESP32-S3" sürümünü yükle (normal "ESP32" değil).
     Çift USB-C portu olan board'lar genelde ESP32-S3'tür.
   - `neopixel` modülü MicroPython'da hazır gelir, ayrıca kurulum gerekmez.
2. `esp32/main.py` dosyasını Thonny ile aç → **ESP32'ye `main.py` adıyla kaydet**
   (`File > Save as > MicroPython device`). Böylece ESP32 her açılışta otomatik çalıştırır.

> Kod çalışırken REPL'i durdurmak için Thonny'de **Stop/Restart (Ctrl+C)**.

---

## 3) Bilgisayar Kurulumu (Python) — Conda GEREKMEZ

> Python **3.10** + pip yeterli. `dlib`'i önceden derlenmiş (`dlib-bin`) kuruyoruz;
> Visual Studio / derleme derdi YOK. Tek komutla kur:

```powershell
# Proje KÖK dizininde çalıştır:
powershell -ExecutionPolicy Bypass -File pc\kurulum.ps1
```
Bu script otomatik olarak `.venv` sanal ortamını oluşturur ve `dlib-bin`,
`face_recognition`, `opencv`, `pyserial` vb. paketleri **doğru sırada** kurar.

Kurulumu doğrula:
```powershell
.\.venv\Scripts\python.exe pc\dogrula_kurulum.py
```
> ℹ️ "dlib>=19.7 not installed" uyarısı **zararsızdır** (modülün adı `dlib`,
> paketin adı `dlib-bin`). `import dlib` sorunsuz çalışır.

---

## 4) Tanıdık Yüzleri Ekle

`known_faces/` boşken kameraya çıkan **herkes "yabancı"** sayılır. Önce kendini ekle:
```powershell
.\.venv\Scripts\python.exe pc\enroll.py yakup    # kameraya bak, [s] ile kaydet
```
veya `known_faces/` klasörüne elle `isim.jpg` koy.

---

## 5) Çalıştır

### a) ESP32 OLMADAN test et (önce bunu dene)
```powershell
.\.venv\Scripts\python.exe pc\doorbell.py --test
```
Canlı kamera açılır; **[SPACE]** → yüz kontrol (TANIDIK/YABANCI gösterir), **[q]** → çık.
Donanım hazır olmadan PC tarafını tam test etmek için bunu kullan.

### b) ESP32 ile (donanım hazır olunca)
```powershell
# ESP32'nin COM portunu argüman olarak ver (Aygıt Yöneticisi'nden bak):
.\.venv\Scripts\python.exe pc\doorbell.py COM5
```
Artık sensöre yaklaşınca → kamera kontrol eder → LED yanar. 🎉

---

## Test Sırası (parça parça doğrula)

1. **RGB halka testi:** Thonny REPL'de:
   ```python
   import neopixel
   from machine import Pin
   r = neopixel.NeoPixel(Pin(6), 8)
   r.fill((0, 40, 0)); r.write()   # yeşil yanmalı
   ```
2. **Sensör testi:** `main.py` içine geçici `print(dist)` ekleyip mesafe oku.
3. **Kamera testi:** `python enroll.py test` → kamera açılıyor mu?
4. **Yüz tanıma testi:** `doorbell.py`'yi çalıştır, COM portunu kapatıp
   sadece kamera kısmını dene (istersen elle "RING" tetikleriz).
5. **Tam entegrasyon:** Hepsi bağlıyken sensöre yaklaş.

## İnce Ayarlar
- `main.py` → `DISTANCE_THRESHOLD_CM`: kaç cm'den tetiklensin.
- `doorbell.py` → `TOLERANCE`: 0.5 sıkı / 0.6 gevşek. Yabancıyı tanıdık
  sanıyorsa düşür; tanıdığı tanımıyorsa yükselt.
# ESP32-Smart-Doorbell-AI
