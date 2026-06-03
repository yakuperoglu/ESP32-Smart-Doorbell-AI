# =============================================================
#  AKILLI KAPI ZİLİ - Bilgisayar (PC) tarafı
# =============================================================
#  Görevi:
#   1) ESP32'den USB seri port üzerinden "RING" sinyali bekle
#   2) "RING" gelince webcam'den bir kare yakala
#   3) face_recognition ile yüzü tanımaya çalış:
#        - known_faces/ klasöründeki kişilere benziyorsa -> "GREEN" gönder
#        - benzemiyorsa (yabancı)                         -> "RED"   gönder
# =============================================================

import os
import time

import cv2
import numpy as np
import serial
import face_recognition

# ----------------------- AYARLAR -----------------------------
# ESP32'nin bağlı olduğu COM portu. Aygıt Yöneticisi'nden bak (ör. COM3).
PORT = "COM3"
BAUD = 115200

# Tanıdık yüz fotoğraflarının olduğu klasör (proje kök dizinindeki known_faces)
KNOWN_DIR = os.path.join(os.path.dirname(__file__), "..", "known_faces")

# Webcam index (genelde 0; harici kamera varsa 1, 2... deneyebilirsin)
CAMERA_INDEX = 0

# Eşik (tolerance): mesafe bu değerin ALTINDAysa "tanıdık" sayılır.
# 0.6 = kütüphanenin varsayılanı (gevşek). 0.5 = daha sıkı (önerilir).
# Çok yabancıyı "tanıdık" sayıyorsa düşür, tanıdığı tanımıyorsa yükselt.
TOLERANCE = 0.5
# -------------------------------------------------------------


def load_known_faces():
    """known_faces/ klasöründeki tüm fotoğrafları yükle ve yüz kodlarını çıkar."""
    encodings = []
    names = []

    if not os.path.isdir(KNOWN_DIR):
        print(f"[!] '{KNOWN_DIR}' klasörü yok. Oluşturup tanıdık fotoğrafları koy.")
        return encodings, names

    for fname in os.listdir(KNOWN_DIR):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        path = os.path.join(KNOWN_DIR, fname)
        image = face_recognition.load_image_file(path)
        face_encs = face_recognition.face_encodings(image)
        if face_encs:
            encodings.append(face_encs[0])
            names.append(os.path.splitext(fname)[0])
            print(f"[+] Yüklendi: {fname}")
        else:
            print(f"[!] Yüz bulunamadı, atlandı: {fname}")

    print(f"[i] Toplam {len(encodings)} tanıdık yüz yüklendi.")
    return encodings, names


def capture_frame():
    """Webcam'i aç, birkaç kare ısınma yaptır ve net bir kare döndür."""
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)  # Windows'ta DSHOW daha hızlı açılır
    if not cap.isOpened():
        print("[!] Kamera açılamadı.")
        return None

    frame = None
    for _ in range(5):          # ışık/odak otursun diye birkaç kare at
        ret, frame = cap.read()
        time.sleep(0.05)
    cap.release()

    if frame is None:
        return None
    return frame


def recognize(frame, known_encodings, known_names):
    """Kareyi analiz et. ('known', isim) ya da ('stranger', None) döndür.
       Hiç yüz yoksa ('none', None)."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb)
    if not locations:
        return "none", None

    encodings = face_recognition.face_encodings(rgb, locations)

    for enc in encodings:
        if not known_encodings:
            return "stranger", None
        distances = face_recognition.face_distance(known_encodings, enc)
        best = int(np.argmin(distances))
        if distances[best] < TOLERANCE:
            return "known", known_names[best]

    return "stranger", None


def main():
    known_encodings, known_names = load_known_faces()

    print(f"[i] {PORT} portuna bağlanılıyor...")
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)  # ESP32 resetlenip açılana kadar bekle
    print("[i] Hazır. ESP32'den 'RING' bekleniyor... (çıkmak için Ctrl+C)")

    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue

        if line == "RING":
            print("\n🔔 Kapıda biri var! Yüz kontrol ediliyor...")
            frame = capture_frame()

            if frame is None:
                print("[!] Kamera karesi alınamadı -> yabancı sayılıyor.")
                ser.write(b"RED\n")
                continue

            result, name = recognize(frame, known_encodings, known_names)

            if result == "known":
                print(f"✅ TANIDIK: {name} -> yeşil LED")
                ser.write(b"GREEN\n")
            elif result == "stranger":
                print("⛔ YABANCI -> kırmızı LED")
                ser.write(b"RED\n")
            else:
                print("🤷 Yüz görünmüyor -> yabancı sayılıyor.")
                ser.write(b"RED\n")
        else:
            # ESP32'nin diğer mesajları (BOOT vs.) - sadece bilgi amaçlı yazdır
            print(f"[esp32] {line}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[i] Çıkılıyor...")
