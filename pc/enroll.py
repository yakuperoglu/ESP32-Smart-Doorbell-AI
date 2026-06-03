# =============================================================
#  TANIDIK YUZ EKLEME ARACI
# =============================================================
#  Webcam acar, canli goruntu gosterir.
#    [s] -> o anki kareyi known_faces/<isim>.jpg olarak kaydeder
#           (KAYDETMEDEN ONCE karede yuz var mi kontrol eder)
#    [q] -> cikar
#
#  Kullanim:
#     python enroll.py yakup
#  (kaydedecegin kisinin adini arguman olarak ver)
# =============================================================

import os
import sys

import cv2
import face_recognition

CAMERA_INDEX = 0
KNOWN_DIR = os.path.join(os.path.dirname(__file__), "..", "known_faces")


def main():
    if len(sys.argv) < 2:
        print("Kullanim: python enroll.py <isim>")
        print("Ornek:    python enroll.py yakup")
        return

    name = sys.argv[1]
    os.makedirs(KNOWN_DIR, exist_ok=True)
    save_path = os.path.join(KNOWN_DIR, f"{name}.jpg")

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[!] Kamera acilamadi. (CAMERA_INDEX'i 1/2 yapmayi dene.)")
        return

    print("Kameraya bak. Kaydetmek icin [s], cikmak icin [q].")
    info, color = "[s] kaydet   [q] cik", (200, 200, 200)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        disp = frame.copy()
        cv2.putText(disp, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.imshow("Yuz Ekle - [s] kaydet, [q] cik", disp)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            # Kaydetmeden once karede gercekten yuz var mi kontrol et
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if not face_recognition.face_locations(rgb):
                print("[!] Karede yuz bulunamadi, KAYDEDILMEDI. Isiga/aciya dikkat et, tekrar dene.")
                info, color = "Yuz bulunamadi - tekrar dene", (0, 0, 255)
                continue
            cv2.imwrite(save_path, frame)
            print(f"[+] Kaydedildi: {save_path}")
            break
        elif key == ord("q"):
            print("[i] Iptal edildi.")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
