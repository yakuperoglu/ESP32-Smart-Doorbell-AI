# =============================================================
#  TANIDIK YÜZ EKLEME ARACI
# =============================================================
#  Webcam açar, canlı görüntü gösterir.
#    [s] tuşu -> o anki kareyi known_faces/<isim>.jpg olarak kaydeder
#    [q] tuşu -> çıkar
#
#  Kullanım:
#     python enroll.py ahmet
#  (yani kaydedeceğin kişinin adını argüman olarak ver)
# =============================================================

import os
import sys

import cv2

CAMERA_INDEX = 0
KNOWN_DIR = os.path.join(os.path.dirname(__file__), "..", "known_faces")


def main():
    if len(sys.argv) < 2:
        print("Kullanım: python enroll.py <isim>")
        print("Örnek:    python enroll.py ahmet")
        return

    name = sys.argv[1]
    os.makedirs(KNOWN_DIR, exist_ok=True)
    save_path = os.path.join(KNOWN_DIR, f"{name}.jpg")

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[!] Kamera açılamadı.")
        return

    print("Kameraya bak. Kaydetmek için [s], çıkmak için [q].")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Yuz Ekle - [s] kaydet, [q] cik", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            cv2.imwrite(save_path, frame)
            print(f"[+] Kaydedildi: {save_path}")
            break
        elif key == ord("q"):
            print("[i] İptal edildi.")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
