# =============================================================
#  KNOWN FACE ENROLLMENT TOOL
# =============================================================
#  Opens the webcam and displays a live feed.
#    [s] -> saves the current frame as known_faces/<name>.jpg
#           (Checks if a face is in the frame BEFORE SAVING)
#    [q] -> quits
#
#  Usage:
#     python enroll.py john
#  (Provide the name of the person as an argument)
# =============================================================

import os
import sys

import cv2
import face_recognition

CAMERA_INDEX = 0
KNOWN_DIR = os.path.join(os.path.dirname(__file__), "..", "known_faces")


def main():
    if len(sys.argv) < 2:
        print("Usage: python enroll.py <name>")
        print("Example: python enroll.py john")
        return

    name = sys.argv[1]
    os.makedirs(KNOWN_DIR, exist_ok=True)
    save_path = os.path.join(KNOWN_DIR, f"{name}.jpg")

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[!] Cannot open camera. (Try changing CAMERA_INDEX to 1 or 2.)")
        return

    print("Look at the camera. Press [s] to save, [q] to quit.")
    info, color = "[s] save   [q] quit", (200, 200, 200)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        disp = frame.copy()
        cv2.putText(disp, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.imshow("Add Face - [s] save, [q] quit", disp)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            # Check if there's actually a face in the frame before saving
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if not face_recognition.face_locations(rgb):
                print("[!] No face found in the frame, NOT SAVED. Check lighting/angle and try again.")
                info, color = "No face found - try again", (0, 0, 255)
                continue
            cv2.imwrite(save_path, frame)
            print(f"[+] Saved: {save_path}")
            break
        elif key == ord("q"):
            print("[i] Cancelled.")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
