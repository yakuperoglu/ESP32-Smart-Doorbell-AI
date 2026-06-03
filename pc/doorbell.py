# =============================================================
#  AKILLI KAPI ZILI - Bilgisayar (PC) tarafi
# =============================================================
#  IKI CALISMA MODU:
#
#   1) TEST MODU (ESP32 GEREKMEZ):
#        python doorbell.py --test
#      Canli kamera onizlemesi acar. [SPACE] tusuna basinca yuz
#      tanima yapar ve sonucu ekranda gosterir (GREEN/RED). Donanim
#      hazir olmadan PC tarafini denemek icin BUNU kullan.
#
#   2) NORMAL MOD (ESP32 ile):
#        python doorbell.py COM5
#      ESP32'den seri "RING" bekler, webcam'den yuz tanir,
#      tanidiksa "GREEN" yabanciysa "RED" geri gonderir.
#      Port verilmezse sirasiyla: DOORBELL_PORT ortam degiskeni,
#      sonra varsayilan COM3 kullanilir.
# =============================================================

import os
import sys
import time

import cv2
import numpy as np
import face_recognition

# ----------------------- AYARLAR -----------------------------
DEFAULT_PORT = "COM3"            # port verilmezse varsayilan
BAUD = 115200
KNOWN_DIR = os.path.join(os.path.dirname(__file__), "..", "known_faces")
CAMERA_INDEX = 0                 # webcam 0; harici kamera varsa 1,2... dene
WARMUP_FRAMES = 15               # kamera acilinca isinma (oto-pozlama otursun)

# Esik: mesafe bu degerin ALTINDAysa "tanidik". 0.6 gevsek, 0.5 siki (onerilir).
TOLERANCE = 0.5

# Gercek zil modunda kamerayi ekranda goster + sonucu birkac saniye beklet
SHOW_WINDOW = True
RESULT_HOLD_SEC = 3      # tanima sonucu ekranda kac saniye dursun (cok hizli gecmesin)
# -------------------------------------------------------------


def load_known_faces():
    """known_faces/ klasorundeki fotograflari yukle, yuz kodlarini cikar."""
    encodings, names = [], []

    if not os.path.isdir(KNOWN_DIR):
        print(f"[!] '{KNOWN_DIR}' klasoru yok. Tanidik fotograflari oraya koy.")
        return encodings, names

    for fname in os.listdir(KNOWN_DIR):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        path = os.path.join(KNOWN_DIR, fname)
        image = face_recognition.load_image_file(path)   # PIL ile RGB'ye cevirir
        face_encs = face_recognition.face_encodings(image)
        if face_encs:
            encodings.append(face_encs[0])
            names.append(os.path.splitext(fname)[0])
            print(f"[+] Yuklendi: {fname}")
        else:
            print(f"[!] Yuz bulunamadi, atlandi: {fname}")

    print(f"[i] Toplam {len(encodings)} tanidik yuz yuklendi.")
    if not encodings:
        print("[!] UYARI: known_faces bos -> kameraya cikan HERKES 'yabanci' (RED) sayilir.")
        print("    Once tanidik yuz ekle:  python pc\\enroll.py <isim>")
    return encodings, names


def open_camera():
    """Webcam'i bir kez ac ve isit (oto-pozlama/odak otursun)."""
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)  # Windows'ta DSHOW hizli acilir
    if not cap.isOpened():
        return None
    for _ in range(WARMUP_FRAMES):
        cap.read()
        time.sleep(0.03)
    return cap


def grab_frame(cap):
    """Acik kameradan TAZE bir kare al (tampondaki eski kareleri at)."""
    frame = None
    for _ in range(5):
        ret, frame = cap.read()
        if not ret:
            return None
        time.sleep(0.02)
    return frame


def recognize(frame, known_encodings, known_names):
    """Kareyi analiz et. Doner: (sonuc, isim, yuz_konumlari)
       sonuc: 'known' | 'stranger' | 'none'
       Birden cok yuz varsa EN IYI eslesmeye gore karar verir."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb)
    if not locations:
        return "none", None, locations

    encodings = face_recognition.face_encodings(rgb, locations)

    best_name, best_dist = None, None
    for enc in encodings:
        if not known_encodings:
            continue
        distances = face_recognition.face_distance(known_encodings, enc)
        idx = int(np.argmin(distances))
        if best_dist is None or distances[idx] < best_dist:
            best_dist, best_name = distances[idx], known_names[idx]

    if best_dist is not None and best_dist < TOLERANCE:
        return "known", best_name, locations
    return "stranger", None, locations


def resolve_port():
    """Port: once komut satiri argumani, sonra DOORBELL_PORT, sonra DEFAULT_PORT."""
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        return args[0]
    return os.environ.get("DOORBELL_PORT", DEFAULT_PORT)


# --------------------------- TEST MODU -----------------------
def run_test_mode(known_encodings, known_names):
    print("\n[TEST MODU] ESP32 gerekmez. Kamera aciliyor...")
    cap = open_camera()
    if cap is None:
        print("[!] Kamera acilamadi. (CAMERA_INDEX'i 1/2 yapmayi dene.)")
        return

    print("Canli onizleme acildi.  [SPACE] = yuz kontrol et,  [q] = cik")
    text, color = "Hazir - SPACE'e bas", (200, 200, 200)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        disp = frame.copy()
        cv2.putText(disp, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.imshow("Kapi Zili TEST - [SPACE] kontrol, [q] cik", disp)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):           # q veya ESC
            break
        if key == ord(" "):                  # SPACE -> yuz kontrol
            result, name, _ = recognize(frame, known_encodings, known_names)
            if result == "known":
                text, color = f"TANIDIK: {name}  -> GREEN", (0, 200, 0)
            elif result == "stranger":
                text, color = "YABANCI  -> RED", (0, 0, 255)
            else:
                text, color = "Yuz gorunmuyor", (0, 165, 255)
            print(f"  -> {text}")

    cap.release()
    cv2.destroyAllWindows()


# --------------------------- NORMAL MOD ----------------------
def _annotate(frame, locations, etiket, color):
    """Kareye yuz kutusu + sonuc yazisi cizip dondur."""
    disp = frame.copy()
    for (top, right, bottom, left) in locations:
        cv2.rectangle(disp, (left, top), (right, bottom), color, 2)
    cv2.putText(disp, etiket, (10, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    return disp


def run_serial_mode(known_encodings, known_names):
    import serial
    from serial import SerialException

    port = resolve_port()
    print(f"\n[i] {port} portuna baglaniliyor... (BAUD={BAUD})")
    try:
        # timeout=0 -> non-blocking okuma, boylece canli onizleme akici kalir
        ser = serial.Serial(port, BAUD, timeout=0)
    except SerialException as e:
        print(f"[!] {port} acilamadi: {e}")
        print("    - Dogru COM portu mu?  Ornek:  python doorbell.py COM5")
        print("    - Thonny veya baska bir program portu tutuyor olabilir, kapat.")
        return

    time.sleep(2)               # ESP32 reset olup acilana kadar bekle
    ser.reset_input_buffer()    # bayat/birikmis veriyi temizle

    print("[i] Kamera aciliyor...")
    cap = open_camera()
    if cap is None:
        print("[!] Kamera acilamadi. Cikiliyor.")
        ser.close()
        return

    print("[i] Hazir. ESP32'den 'RING' bekleniyor...")
    print("    (Kamera penceresinde [q] = cik)")

    WIN = "Kapi Zili - canli (q=cik)"
    buf = b""
    result_frame = None
    hold_until = 0.0

    try:
        while True:
            ret, live = cap.read()
            now = time.time()

            # Ekran: sonuc bekletme suresindeysek donmus sonuc karesi,
            # degilse canli goruntu + "bekleniyor" yazisi.
            if SHOW_WINDOW:
                if result_frame is not None and now < hold_until:
                    disp = result_frame
                elif ret:
                    disp = live.copy()
                    cv2.putText(disp, "Bekleniyor - sensore yaklas", (10, 36),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
                else:
                    disp = None
                if disp is not None:
                    cv2.imshow(WIN, disp)
                if (cv2.waitKey(1) & 0xFF) == ord("q"):
                    break
            else:
                time.sleep(0.02)

            # Seri porttan gelen satirlari oku (non-blocking)
            data = ser.read(256)
            if not data:
                continue
            buf += data
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                line = raw.decode(errors="ignore").strip()
                if not line:
                    continue

                if line == "RING":
                    print("\n[ZIL] Kapida biri var! Yuz kontrol ediliyor...")
                    # "kontrol ediliyor" geri bildirimi
                    if SHOW_WINDOW and ret:
                        tmp = live.copy()
                        cv2.putText(tmp, "Kontrol ediliyor...", (10, 36),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 200), 2)
                        cv2.imshow(WIN, tmp)
                        cv2.waitKey(1)

                    frame = grab_frame(cap)
                    if frame is None:
                        print("[!] Kamera karesi alinamadi -> yabanci.")
                        ser.write(b"RED\n")
                        continue

                    result, name, locations = recognize(frame, known_encodings, known_names)
                    if result == "known":
                        print(f"[OK] TANIDIK: {name} -> yesil LED")
                        ser.write(b"GREEN\n")
                        result_frame = _annotate(frame, locations, f"TANIDIK: {name}", (0, 200, 0))
                    elif result == "stranger":
                        print("[NO] YABANCI -> kirmizi LED")
                        ser.write(b"RED\n")
                        result_frame = _annotate(frame, locations, "YABANCI", (0, 0, 255))
                    else:
                        print("[??] Yuz gorunmuyor -> yabanci sayiliyor.")
                        ser.write(b"RED\n")
                        result_frame = _annotate(frame, locations, "Yuz yok", (0, 165, 255))
                    hold_until = time.time() + RESULT_HOLD_SEC
                else:
                    # ESP32'nin diger mesajlari (BOOT vs.) - bilgi amacli
                    print(f"[esp32] {line}")
    finally:
        cap.release()
        ser.close()
        cv2.destroyAllWindows()


def main():
    known_encodings, known_names = load_known_faces()
    if "--test" in sys.argv or "-t" in sys.argv:
        run_test_mode(known_encodings, known_names)
    else:
        run_serial_mode(known_encodings, known_names)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[i] Cikiliyor...")
