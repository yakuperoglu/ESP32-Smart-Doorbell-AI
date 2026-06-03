# 📖 Kullanım Kılavuzu — Akıllı Kapı Zili

Bu dosya projenin **günlük kullanımını** anlatır: tanıdık yüz nasıl eklenir,
proje nasıl başlatılır, ayarlar nasıl değiştirilir.

> Henüz kurmadıysan önce → **[KURULUM.md](KURULUM.md)**.
> Tüm komutlar **proje kök dizininden** çalıştırılır.

---

## Nasıl çalışır? (kısa özet)

1. Kapıya biri yaklaşır → **HC-SR04** sensörü algılar.
2. **ESP32** bilgisayara `RING` (zil) sinyali gönderir.
3. Bilgisayar webcam'den bir kare alıp **yüz tanıma** yapar:
   - Tanıdık biriyse → ESP32'ye `GREEN` → **halka yeşil** 🟢
   - Yabancıysa → `RED` → **halka kırmızı** 🔴

Tanıdık kişiler `known_faces/` klasöründeki fotoğraflardan belirlenir.

---

## 1. Tanıdık Yüz Ekleme

`known_faces/` klasörü **boşsa kameraya çıkan herkes "yabancı" (kırmızı)** sayılır.
O yüzden önce tanıdık kişileri eklemelisin.

### Yöntem A — Webcam ile (önerilen)
```powershell
.\.venv\Scripts\python.exe pc\enroll.py yakup
```
- Bir kamera penceresi açılır.
- Yüzün net görününce **[s]** tuşuna bas → `known_faces/yakup.jpg` olarak kaydedilir.
- Çıkmak için **[q]**.
- 💡 Program kaydetmeden önce **karede yüz var mı** kontrol eder; yüz yoksa uyarır ve kaydetmez.

**Birden fazla kişi** eklemek için komutu farklı isimle tekrarla:
```powershell
.\.venv\Scripts\python.exe pc\enroll.py annem
.\.venv\Scripts\python.exe pc\enroll.py kardesim
```

### Yöntem B — Elle fotoğraf koyma
`known_faces/` klasörüne doğrudan `isim.jpg` (veya `.png`) koy.
- Her dosyada **tek kişi**, **net**, **önden**, **iyi ışıkta** olsun.
- Dosya adı = kişinin adı (sonuçta o isim gösterilir). Örn: `ahmet.jpg`, `anne.png`.

### İyi fotoğraf ipuçları
- Yüz büyük ve net olsun, ışık önden gelsin.
- Gözlük/maske gibi şeyler tanımayı zorlaştırır.
- Kişi başına 1 net foto yeterli.

---

## 2. Eklenen yüzleri görme / silme

- **Görmek için:** `known_faces/` klasörünü aç — oradaki her `.jpg`/`.png` bir tanıdık.
- **Silmek için:** dosyayı sil (örn. `known_faces/yakup.jpg`). O kişi artık "yabancı" sayılır.

---

## 3. Projeyi Başlatma

### 3.1 — ESP32 OLMADAN test (sadece kamera + yüz tanıma)
Donanım bağlı olmasa bile yüz tanımayı denemek için:
```powershell
.\.venv\Scripts\python.exe pc\doorbell.py --test
```
- Canlı kamera açılır.
- **[SPACE]** → o anki kareyi kontrol eder, sonucu yazar (TANIDIK/YABANCI).
- **[q]** → çıkış.

### 3.2 — Gerçek zil modu (ESP32 ile)
ESP32 takılıyken, **kendi COM portunla** çalıştır (bizdeki COM10):
```powershell
.\.venv\Scripts\python.exe pc\doorbell.py COM10
```

**Ne göreceksin:**
1. Halka kısaca **mavi** yanıp söner (kart resetlenir), terminalde `Hazir. ESP32'den 'RING' bekleniyor...` yazar.
2. **Kamera penceresi** sürekli açık kalır (üstünde `Bekleniyor - sensore yaklas`).
3. Sensöre yaklaşınca (50 cm'den yakın):
   - Pencerede `Kontrol ediliyor...` (sarı) görünür,
   - Yüzünün etrafına **kutu** çizilir,
   - Sonuç **3 saniye** ekranda kalır:
     - 🟢 `TANIDIK: yakup` (yeşil kutu) + halka yeşil
     - 🔴 `YABANCI` (kırmızı kutu) + halka kırmızı
4. **Çıkış:** kamera penceresinde **[q]** tuşu (veya terminalde **Ctrl+C**).

> COM portunu vermezsen sırasıyla `DOORBELL_PORT` ortam değişkeni, sonra varsayılan
> `COM3` denenir. **En garantisi portu komuta yazmaktır:** `doorbell.py COM10`.

---

## 4. İnce Ayarlar

### Bilgisayar tarafı — [pc/doorbell.py](pc/doorbell.py)
| Ayar | Satır | Ne işe yarar |
|---|---|---|
| `TOLERANCE = 0.5` | ~38 | Tanıma sıkılığı. Yabancıyı tanıdık sanıyorsa **düşür** (0.45); tanıdığı tanımıyorsa **yükselt** (0.6). |
| `RESULT_HOLD_SEC = 3` | ~42 | Tanıma sonucu ekranda kaç saniye dursun. |
| `CAMERA_INDEX = 0` | ~32 | Yanlış kamera açılıyorsa `1` veya `2` yap. |
| `SHOW_WINDOW = True` | ~41 | Kamera penceresini kapatmak istersen `False` yap. |

> Bu dosyayı değiştirip kaydetmen yeterli — bir sonraki çalıştırmada geçerli olur.

### ESP32 tarafı — [esp32/main.py](esp32/main.py)
| Ayar | Ne işe yarar |
|---|---|
| `DISTANCE_THRESHOLD_CM = 50` | Kaç cm'den yakına biri gelince zil çalsın. |
| `COOLDOWN_MS = 5000` | İki zil arası bekleme (sürekli çalmasın diye). |
| `GREEN` / `RED` | LED renkleri/parlaklığı (örn. `(0, 40, 0)`). |

> ⚠️ `main.py`'yi değiştirdiysen **karta tekrar yüklemelisin**:
> ```powershell
> .\.venv\Scripts\python.exe -m mpremote connect COM10 fs cp esp32\main.py :main.py
> .\.venv\Scripts\python.exe -m mpremote connect COM10 reset
> ```

---

## 5. Demo İpuçları

- Ortam **iyi aydınlık** olsun; yüz net görünsün.
- Sensöre dokunurken **yüzün kameraya dönük** olsun (kayıt o anda alınır).
- Test için: önce kendini tanıdık ekle → sana **yeşil**, tanımadığı birine **kırmızı** yanmalı.
- `TOLERANCE` ile oynayarak hassasiyeti ayarla.

---

## Sorun mu var?
➡️ **[KURULUM.md](KURULUM.md)** → "Sık Karşılaşılan Sorunlar" bölümüne bak.
