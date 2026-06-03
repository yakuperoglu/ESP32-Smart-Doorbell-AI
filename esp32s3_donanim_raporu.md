# Akıllı Kapı Zili — Donanım Teknik Raporu (ESP32-S3)

> Bu rapor, **yüz tanımalı akıllı kapı zili** projesi için kullanılan donanım
> modüllerinin teknik özelliklerini, pin yapısını, çalışma prensiplerini ve
> dikkat edilmesi gereken noktaları özetler. Rapor; resmi datasheet'ler
> (Espressif, Worldsemi, ON Semi/Diodes), Adafruit/SparkFun referansları ve
> genel topluluk uygulama notları temel alınarak hazırlanmıştır.

## Projede Kullanılan Donanım (Malzeme Listesi)

| # | Bileşen | Görevi |
|---|---------|--------|
| 1 | ESP32-S3-DevKitM-1 (ana kart) | Sensörü okur, PC ile USB seri haberleşir, LED'i sürer |
| 2 | HC-SR04 ultrasonik mesafe sensörü | Kapıya biri yaklaştı mı algılar (zili tetikler) |
| 3 | WS2812B 8-bit NeoPixel halka | Sonucu gösterir: **yeşil = tanıdık**, **kırmızı = yabancı** |
| 4 | BSS138 lojik seviye dönüştürücü (3.3 V ↔ 5 V) | HC-SR04 Echo (5 V) sinyalini 3.3 V'a düşürür |
| 5 | Breadboard (830 delik) | Lehimsiz prototipleme |
| 6 | Jumper kablolar (M-M 20 cm, M-F 30 cm) | Bağlantılar |
| 7 | 330 Ω direnç | WS2812B data hattı seri direnci |
| 8 | 1000 µF elektrolitik kondansatör | WS2812B besleme hattı filtreleme |

> Bilgisayar tarafında ayrıca bir **webcam** kullanılır (yüz tanıma için).

### Sistem Akışı

```
[HC-SR04]  →  ESP32-S3  →  (USB Seri)  →  PC (Python + Webcam)
                  ↑                              │
                  │                         Yüz tanıma
                  │                              │
        Yeşil/Kırmızı LED  ←─ "GREEN"/"RED" ───┘
```

İçindekiler:

1. ESP32-S3-DevKitM-1 (Ana kart)
2. HC-SR04 — Ultrasonik Mesafe Sensörü
3. WS2812B 8-bit NeoPixel Halka (RGB LED)
4. Lojik Seviye Dönüştürücü (3.3 V ↔ 5 V, BSS138)
5. Breadboard, Jumper Kablolar, Direnç ve Kondansatör
6. Pin Bağlantı Şeması (bu proje)
7. Sistem Bütünlüğü ve Genel Uyarılar
8. Kaynaklar

---

## 1. ESP32-S3-DevKitM-1 (Ana Kart)

### Modül Özeti

DevKitM-1, üzerinde **ESP32-S3-MINI-1** modülü taşıyan giriş seviyesi bir
geliştirme kartıdır. Modülün üzerindeki SiP yonga **ESP32-S3FN8**'dir. `N8`
soneki paketin **8 MB dahili Quad SPI flash** içerdiğini ve **PSRAM
içermediğini** belirtir.

| Özellik | Değer |
|---|---|
| MCU | Çift çekirdek Xtensa LX7 @ 240 MHz |
| SRAM | 512 KB |
| Flash | 8 MB (dahili SiP) |
| PSRAM | Yok |
| Kablosuz | Wi-Fi 2.4 GHz b/g/n + BLE 5 (LE) |
| GPIO seviyesi | 3.3 V (5 V toleranslı **DEĞİL**) |
| USB | 1× USB 2.0 OTG, 1× USB Serial/JTAG |
| USB konektörü | Çoğunlukla 2 adet: biri CP210x/CH340 (UART), diğeri yerel USB |

> **Bu projede kablosuz (Wi-Fi/BLE) KULLANILMIYOR.** ESP32 ile bilgisayar
> arasındaki tüm haberleşme **USB seri (UART)** üzerinden yapılır.

### Kritik / Kaçınılması Gereken GPIO'lar

| GPIO | Durum | Açıklama |
|---|---|---|
| **GPIO0** | Strapping (boot mode) | Açılışta 0 = bootloader. Bağlı devre LOW çekmemeli. |
| **GPIO3** | Strapping (JTAG kaynağı) | Mecbur kalmadıkça kullanma. |
| **GPIO45** | Strapping (VDD_SPI) | Genelde boş bırak. |
| **GPIO46** | Strapping (boot log) | Açılışta HIGH çekilmemeli. |
| **GPIO19 / GPIO20** | USB D− / D+ | Yerel USB kullanılıyorsa rezerve. |
| **GPIO26 – GPIO32** | Dahili 8 MB flash hatları | **Asla kullanma**, kart bozulur. |
| **GPIO33 – GPIO37** | MINI-1 paketinde **bağlı değil** | Header'da görünse bile NC. |
| **GPIO43 / GPIO44** | UART0 TX/RX (boot logları) | Kullanılabilir ama log kaybedilir. |
| **GPIO48** | Kart üzerindeki RGB LED (WS2812) | Boş bırakılabilir. |

> **Bu projede seçilen pinler (GPIO4, GPIO5, GPIO6) yukarıdaki listede yok →
> hepsi güvenli.** ESP32-S3'te eski ESP32'nin aksine giriş-only pin yoktur;
> kullanılabilir tüm GPIO'lar hem giriş hem çıkış yapabilir.

### Elektriksel Sınırlar

- GPIO başına maksimum çıkış akımı ≈ **40 mA**; tipik güvenli kullanım 12–20 mA.
- Kart üzerindeki **3.3 V LDO** ~500–800 mA verebilir.
- **5V pini doğrudan USB VBUS'a** bağlıdır; PC USB portu 500–900 mA ile
  sınırlıdır. WS2812B halka tam beyazda ~480 mA çeker — bu yüzden parlaklığı
  yazılımdan düşük tutuyoruz (bkz. Bölüm 3 ve 7).

---

## 2. HC-SR04 — Ultrasonik Mesafe Sensörü

### Çalışma Prensibi

HC-SR04, 40 kHz ultrasonik ses dalgası ile **2 cm – 400 cm** arasında mesafe
ölçen, ucuz ve yaygın bir sensördür. Bu projede kapıya birinin yaklaşıp
yaklaşmadığını anlayıp **zili tetiklemek** için kullanılır.

1. `Trig` pinine en az **10 µs** TTL HIGH sinyali uygulanır.
2. Sensör 40 kHz'de 8 ultrasonik darbe gönderir.
3. Ses bir engele çarpıp dönünce `Echo` pini HIGH olur.
4. Echo'nun HIGH kaldığı süreden mesafe hesaplanır:
   `Mesafe (cm) = Süre (µs) / 58` (veya `Süre × 0.0343 / 2`).

### Temel Özellikler

| Parametre | Değer |
|---|---|
| Çalışma voltajı | DC **5 V** |
| Akım | ~15 mA |
| Frekans | 40 kHz |
| Min. mesafe | 2 cm |
| Maks. mesafe | 4 m (400 cm) |
| Doğruluk | ~3 mm |
| Algılama açısı | ~15° |
| Trig girişi | 10 µs TTL darbe |
| Echo çıkışı | Mesafeyle orantılı TTL darbe (genişliği değişken) |

### Pin Yapısı

| Pin | Açıklama |
|---|---|
| VCC | 5 V güç girişi (sensör 5 V ister) |
| Trig | Tetik girişi (dijital) |
| Echo | Yankı çıkışı (dijital, **5 V seviyesinde**) |
| GND | Toprak |

### ⚠️ ESP32-S3 ile Voltaj Uyumu (Kritik Nokta)

HC-SR04 **5 V** ile çalışır ve `Echo` çıkışı da **5 V** seviyesinde sinyal
verir. ESP32-S3 GPIO'ları **5 V toleranslı değildir** → Echo'yu doğrudan
bağlamak pini zamanla bozabilir.

- **Echo → mutlaka lojik seviye dönüştürücü (BSS138) üzerinden** ESP32'ye.
- **Trig → doğrudan** ESP32 GPIO'sundan sürülebilir. ESP32'nin 3.3 V çıkışı,
  HC-SR04'ün giriş eşiğini tetiklemeye yeter (genelde ~2 V yeterli).
- Echo darbesi yavaştır (mikrosaniye–milisaniye mertebesi); BSS138 bu hız için
  **uygundur** (WS2812B'nin aksine — bkz. Bölüm 3 ve 4).

---

## 3. WS2812B 8-Bit NeoPixel Halka (RGB LED — "led ışık")

### Çalışma Prensibi

WS2812B, içine entegre kontrol IC'si + RGB LED'i birleştirmiş **adreslenebilir**
bir LED'dir. Her LED ilk gelen 24 bit'i (kendi rengi, **GRB** sırasında,
MSB-first) tutar, kalanı DOUT'tan sonrakine geçirir. Tek data hattıyla 8
LED'in hepsini istediğimiz renge boyarız. Bu projede sonucu gösterir:
**yeşil = tanıdık**, **kırmızı = yabancı**.

### Temel Özellikler

| Özellik | Değer |
|---|---|
| Besleme | 3.5 – 5.3 V (nominal **5 V**) |
| Renk derinliği | 24-bit (8-bit × R/G/B), 16.7M renk |
| Veri hızı | **800 kbps** (NRZ kodlama) |
| LED başına idle akım | ~1 mA |
| LED başına tam beyaz akım | ~60 mA (3 × 20 mA) |
| 8-LED tam beyaz tepe akım | ~480 mA |
| Data HIGH eşiği (V_IH) | min. **0.7 × VDD** (5 V besleme → ~3.5 V) |

### Bağlantı Noktaları

| Pin | İşlev |
|---|---|
| VCC / 5V / + | 5 V besleme |
| GND / − | Toprak |
| DIN | Data girişi (ESP32'den) |
| DOUT | Data çıkışı (zincirleme için — bu projede boş) |

### ⚠️ 3.3 V Data ile Sürme (Bu Projenin Kilit Noktası)

Datasheet V_IH için **0.7 × VDD** ister. 5 V besleme ile bu **3.5 V** demektir;
ESP32-S3'ün **3.3 V** GPIO çıkışı bu eşiğin biraz **altındadır**. Üç çözüm:

1. **Doğrudan sürme (önce bunu dene):** Pratikte çoğu WS2812B partisi 3.3 V
   data ile çalışır — özellikle **kısa kablo + düşük LED sayısı (8)** ile.
   İlk LED'in titremesi/yanlış renk vermesi tipik sorun belirtisidir.
2. **VDD düşürme (titrerse):** Halkayı 5 V yerine bir **1N5819 Schottky diyot**
   üzerinden besleyerek VDD'yi ~4.3 V'a indir. Bu, V_IH eşiğini ~3.0 V'a
   düşürür ve 3.3 V data'yı güvenle "HIGH" yapar. Hızlı ve etkili çözüm.
3. **Gerçek level shifter:** **74AHCT125 / 74HCT245** gibi tek-yönlü tampon
   IC'ler en sağlam yoldur (bu projede zorunlu değil).

> **🔴 ÖNEMLİ — Sık Yapılan Hata:** Elinizdeki **BSS138 tabanlı bi-directional
> level converter'ı WS2812B data hattı için KULLANMAYIN.** RC zaman sabiti
> (10 kΩ pull-up × kablo kapasitansı) 800 kbps NRZ'nin gerektirdiği keskin
> yükselen kenarları tutturamaz; data bozulur, LED'ler rastgele/yanlış renk
> yanar. **BSS138'i sadece HC-SR04 Echo gibi yavaş sinyaller için kullanın.**
> WS2812B data'sını ya doğrudan GPIO'dan (seri direnç ile), ya da yukarıdaki
> 2./3. yöntemle sürün.

### Diğer Önemli Notlar

- **Seri direnç:** DIN'in hemen önüne **330 Ω** (220–470 Ω arası) seri direnç
  koy → hem ESP32 pinini hem ilk LED'i yansımalardan korur.
- **Dekuplaj:** Besleme hattına **1000 µF** elektrolitik kondansatör (halkaya
  yakın, 5 V ↔ GND arası) → ani akım dalgalanmasını yumuşatır.
- **Ortak GND:** ESP32 ile WS2812B GND'leri mutlaka birleşmelidir.
- **Renk sırası GRB'dir** (MicroPython `neopixel` modülü bunu zaten halleder).
- **Güç:** 8 × 60 mA = ~480 mA, USB sınırına yakın. Parlaklığı yazılımdan
  düşük tut: kodda `GREEN=(0,40,0)`, `RED=(40,0,0)` (255 yerine 40) → hem
  akımı düşürür hem göz konforu sağlar.

---

## 4. Lojik Seviye Dönüştürücü (3.3 V ↔ 5 V, 4 Kanal, BSS138)

### Çalışma Prensibi

SparkFun BOB-12009 referansına dayanan, **4 adet BSS138 N-kanal MOSFET +
8 adet 10 kΩ pull-up** kullanan **çift yönlü** bir modüldür (NXP AN97055
standardı). DIR (yön) pini gerektirmeden otomatik iki yönlü çalışır:

- LV tarafı LOW çektiğinde MOSFET iletime geçer, HV tarafını da LOW yapar.
- HV tarafı LOW çektiğinde gövde diyotu üzerinden LV de LOW olur.
- İki taraf da serbestken pull-up'lar her tarafı kendi referansına çeker
  (LV = 3.3 V, HV = 5 V).

### Temel Özellikler

| Özellik | Değer |
|---|---|
| LV tarafı | 1.8 – 3.3 V |
| HV tarafı | 2.8 – 5 V (**HV > LV olmalı**) |
| Kanal | 4 (bi-directional) |
| Pull-up | 10 kΩ |
| Güvenli hız | I²C 100/400 kHz, yavaş dijital sinyaller |

### Pin Yapısı

| LV tarafı | HV tarafı |
|---|---|
| LV (referans, 3.3 V) | HV (referans, 5 V) |
| GND | GND (dahili bağlı) |
| LV1 ↔ HV1 | (kanal 1) |
| LV2 ↔ HV2 | (kanal 2) |
| ... | ... |

### Bu Projedeki Kullanımı

| Bağlantı | Açıklama |
|---|---|
| HV | ESP32 **5V (VIN)** |
| LV | ESP32 **3.3V** |
| GND (iki taraf) | ESP32 **GND** |
| **HV1** | HC-SR04 **Echo** (5 V çıkış) |
| **LV1** | ESP32 **GPIO4** (3.3 V'a düşürülmüş) |

### Önemli Notlar

- **HV > LV zorunludur**, yoksa MOSFET'ler sürekli iletime geçer.
- **HV ve LV referans pinleri boş bırakılmaz** (5 V ve 3.3 V verilmeli).
- **GND ortak** olmalı.
- **🔴 WS2812B (800 kbps) için UYGUN DEĞİL** (Bölüm 3'teki uyarı). Bu modülü
  yalnızca **HC-SR04 Echo** hattında kullan. (İleride 5 V'lık yavaş bir cihaz
  -I²C/UART vb.- eklersen orada da kullanılabilir.)

---

## 5. Breadboard, Jumper Kablolar, Direnç ve Kondansatör

### Breadboard (830 Delik)
Lehimsiz prototipleme kartı. 2 güç rayı (+/−), 60 sıra. ESP32 ve modüller
arası bağlantıları hızlıca test etmek için ideal. Güç rayları ~1 A ile
sınırlıdır; yüksek akımlı (WS2812B) hatlar için kalın/kısa kablo kullan.

### Jumper Kablolar
- **M-M (erkek-erkek) 20 cm:** Breadboard içi ve modül bağlantıları.
- **M-F (erkek-dişi) 30 cm:** ESP32/modül header pinlerinden breadboard'a.
- 2.54 mm standart aralık, 26 AWG.

### 330 Ω Direnç (1/4 W)
- **WS2812B data seri direnci:** DIN'in hemen önüne 330 Ω → pin ve ilk LED
  koruması (220–470 Ω arası uygundur).
- Renk kodu: Turuncu – Turuncu – Kahverengi – Altın.

### 1000 µF / 16 V Elektrolitik Kondansatör
- **WS2812B besleme filtresi:** Halkaya yakın, **5 V ↔ GND** arasına bağlanır;
  ani akım çekişini (LED'ler aniden yanınca) yumuşatır.
- **⚠️ Kutupludur:** Uzun bacak **(+)**, beyaz şeritli/kısa bacak **(−)**.
  Ters bağlamak kondansatörü patlatabilir.

---

## 6. Pin Bağlantı Şeması (Bu Proje)

> Pin numaraları `esp32/main.py` ile birebir aynıdır. Pini değiştirirsen kodu
> da güncelle (`TRIG_PIN`, `ECHO_PIN`, `NEOPIXEL_PIN`).

### HC-SR04 (ultrasonik sensör)
| HC-SR04 | Nereye | Not |
|---------|--------|-----|
| VCC | ESP32 **5V (VIN)** | Sensör 5 V ister |
| GND | ESP32 **GND** | Ortak toprak |
| Trig | ESP32 **GPIO5** | Doğrudan (3.3 V tetiklemeye yeter) |
| Echo | **BSS138 HV1 → LV1** → ESP32 **GPIO4** | Echo 5 V verir, düşürmek şart! |

### BSS138 Lojik Seviye Dönüştürücü
| Converter | Nereye |
|-----------|--------|
| HV | ESP32 **5V (VIN)** |
| LV | ESP32 **3.3V** |
| GND (her iki taraf) | ESP32 **GND** |
| HV1 | HC-SR04 **Echo** |
| LV1 | ESP32 **GPIO4** |

### WS2812B NeoPixel Halka
| Halka | Nereye | Not |
|-------|--------|-----|
| 5V | ESP32 **5V (VIN)** | (titrerse: 1N5819 diyot üzerinden ~4.3 V) |
| GND | ESP32 **GND** | Ortak toprak |
| DIN | **330 Ω** → ESP32 **GPIO6** | **Doğrudan**, BSS138'den GEÇİRME! |
| DOUT | — | Boş |
| 5V↔GND | **1000 µF** kondansatör | Halkaya yakın (kutup!) |

### Bağlantı Özeti
```
ESP32-S3 (3.3 V sistem)
   │
   ├─ GPIO5 ───────────────────► HC-SR04 Trig (doğrudan)
   ├─ GPIO4 ◄── BSS138 (LV1◄HV1) ◄── HC-SR04 Echo (5 V→3.3 V)
   ├─ GPIO6 ──[330Ω]──────────► WS2812B DIN (doğrudan, 3.3 V)
   │
   ├─ 5V (VIN) ──┬─► HC-SR04 VCC
   │             ├─► WS2812B 5V  ──[1000µF ⎓ GND]
   │             └─► BSS138 HV
   ├─ 3.3V ──────► BSS138 LV
   └─ GND ───────► (HEPSİ ortak GND)
```

---

## 7. Sistem Bütünlüğü ve Genel Uyarılar

| # | Konu | Açıklama |
|---|------|----------|
| 1 | **Voltaj uyumsuzluğu** | ESP32-S3 GPIO = 3.3 V; HC-SR04 Echo = 5 V. Echo için lojik seviye dönüştürücü **zorunlu**. |
| 2 | **WS2812B data sürme** | BSS138 800 kbps için uygun değil. Data'yı doğrudan GPIO'dan (330 Ω ile) sür; titrerse halka VDD'sini diyotla ~4.3 V'a düşür. |
| 3 | **NeoPixel akımı** | 8 LED tam beyaz ~480 mA. Parlaklığı yazılımdan düşük tut (kod zaten 40/255 kullanıyor). |
| 4 | **5 V güç bütçesi** | USB tek başına ~500 mA verir. Tek anda hem halka tam parlak hem sensör çekerse sınırda kalır; düşük parlaklık + 1000 µF kondansatör bunu çözer. |
| 5 | **Ortak toprak** | Tüm GND'ler (ESP32, HC-SR04, WS2812B, BSS138) **tek noktada** birleşmeli. |
| 6 | **Kondansatör kutbu** | Elektrolitik kutupludur; ters bağlama patlatır. |
| 7 | **Strapping/flash pinleri** | GPIO0, 3, 19, 20, 26–37, 45, 46 kullanma. Seçilen 4/5/6 güvenli. |
| 8 | **USB ↔ harici 5 V** | Aynı anda hem USB hem harici 5 V verme (PC portuna ters akım). Bu projede USB beslemesi yeterli. |

---

## 8. Kaynaklar

**ESP32-S3:**
- ESP32-S3-DevKitM-1 User Guide — docs.espressif.com
- ESP32-S3-MINI-1 Datasheet — documentation.espressif.com
- ESP32-S3 Series Datasheet / Technical Reference Manual — espressif.com

**HC-SR04:**
- HC-SR04 Ultrasonik Mesafe Sensörü — robotistan.com
- HC-SR04 Datasheet (Cytron / Elecfreaks application notes)

**WS2812B:**
- Worldsemi WS2812B Datasheet (V1.1 / V5) — worldsemi.com
- Adafruit NeoPixel Überguide — learn.adafruit.com
- 74AHCT125 / 74HCT245 Datasheet — TI / NXP

**BSS138 Logic Level Converter:**
- ON Semi / Diodes BSS138 Datasheet
- SparkFun BOB-12009 Hookup Guide — sparkfun.com
- NXP AN97055 — Bi-directional level shifter for I²C-bus

**Pasif/yardımcı bileşenler:**
- Breadboard 830 delik, M-M / M-F jumper, 330 Ω direnç, 1000 µF kondansatör — robotistan.com
