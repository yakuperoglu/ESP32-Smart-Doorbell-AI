# =============================================================
#  SMART DOORBELL - PC side
# =============================================================
#  TWO OPERATION MODES:
#
#   1) TEST MODE (ESP32 NOT REQUIRED):
#        python doorbell.py --test
#      Opens live camera preview. Press [SPACE] to trigger face
#      recognition and show the result on screen (GREEN/RED). 
#      Use this to test the PC side before hardware is ready.
#
#   2) NORMAL MODE (with ESP32):
#        python doorbell.py COM5
#      Waits for "RING" over serial from ESP32, recognizes the face
#      via webcam, returns "GREEN" if known, "RED" if stranger.
#      If no port is given, it checks the DOORBELL_PORT environment 
#      variable, then defaults to COM3.
# =============================================================

import os
import sys
import time

import cv2
import numpy as np
import face_recognition

# ----------------------- SETTINGS -----------------------------
DEFAULT_PORT = "COM3"            # Default port if none provided
BAUD = 115200
KNOWN_DIR = os.path.join(os.path.dirname(__file__), "..", "known_faces")
CAMERA_INDEX = 0                 # webcam 0; try 1,2... for external cameras
WARMUP_FRAMES = 15               # Camera warmup frames (for auto-exposure to settle)

# Threshold: Distance below this value is "known". 0.6 is loose, 0.5 is strict (recommended).
TOLERANCE = 0.5

# In real doorbell mode, show the camera on screen + hold the result for a few seconds
SHOW_WINDOW = True
RESULT_HOLD_SEC = 3      # How many seconds the recognition result stays on screen
# -------------------------------------------------------------


def load_known_faces():
    """Load photos from known_faces/ directory and extract face encodings."""
    encodings, names = [], []

    if not os.path.isdir(KNOWN_DIR):
        print(f"[!] '{KNOWN_DIR}' directory is missing. Place known photos there.")
        return encodings, names

    for fname in os.listdir(KNOWN_DIR):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        path = os.path.join(KNOWN_DIR, fname)
        image = face_recognition.load_image_file(path)   # Loads as RGB via PIL
        face_encs = face_recognition.face_encodings(image)
        if face_encs:
            encodings.append(face_encs[0])
            names.append(os.path.splitext(fname)[0])
            print(f"[+] Loaded: {fname}")
        else:
            print(f"[!] No face found, skipping: {fname}")

    print(f"[i] Total {len(encodings)} known faces loaded.")
    if not encodings:
        print("[!] WARNING: known_faces is empty -> EVERYONE on camera will be a 'stranger' (RED).")
        print("    First, add a known face:  python pc\\enroll.py <name>")
    return encodings, names


def open_camera():
    """Open the webcam once and let it warm up (auto-exposure/focus settles)."""
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)  # DSHOW opens faster on Windows
    if not cap.isOpened():
        return None
    for _ in range(WARMUP_FRAMES):
        cap.read()
        time.sleep(0.03)
    return cap


def grab_frame(cap):
    """Grab a FRESH frame from the open camera (discards old buffered frames)."""
    frame = None
    for _ in range(5):
        ret, frame = cap.read()
        if not ret:
            return None
        frame = cv2.flip(frame, 1)
        time.sleep(0.02)
    return frame


def recognize(frame, known_encodings, known_names):
    """Analyze the frame. Returns: (result, name, face_locations)
       result: 'known' | 'stranger' | 'none'
       If there are multiple faces, makes a decision based on the BEST match."""
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
    """Port resolution: Command line arg -> DOORBELL_PORT env var -> DEFAULT_PORT."""
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        return args[0]
    return os.environ.get("DOORBELL_PORT", DEFAULT_PORT)


# --------------------------- TEST MODE -----------------------
def run_test_mode(known_encodings, known_names):
    print("\n[TEST MODE] ESP32 not required. Opening camera...")
    cap = open_camera()
    if cap is None:
        print("[!] Cannot open camera. (Try changing CAMERA_INDEX to 1 or 2.)")
        return

    print("Live preview opened.  [SPACE] = check face,  [q] = quit")
    text, color = "Ready - Press SPACE", (200, 200, 200)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.flip(frame, 1)

        disp = frame.copy()
        cv2.putText(disp, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.imshow("Doorbell TEST - [SPACE] check, [q] quit", disp)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):           # q or ESC
            break
        if key == ord(" "):                  # SPACE -> check face
            result, name, _ = recognize(frame, known_encodings, known_names)
            if result == "known":
                text, color = f"KNOWN: {name}  -> GREEN", (0, 200, 0)
            elif result == "stranger":
                text, color = "STRANGER  -> RED", (0, 0, 255)
            else:
                text, color = "No face visible", (0, 165, 255)
            print(f"  -> {text}")

    cap.release()
    cv2.destroyAllWindows()


# --------------------------- NORMAL MODE ----------------------
def _annotate(frame, locations, label, color):
    """Draw a bounding box and result text on the frame and return it."""
    disp = frame.copy()
    for (top, right, bottom, left) in locations:
        cv2.rectangle(disp, (left, top), (right, bottom), color, 2)
    cv2.putText(disp, label, (10, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    return disp


def run_serial_mode(known_encodings, known_names):
    import serial
    from serial import SerialException

    port = resolve_port()
    print(f"\n[i] Connecting to {port}... (BAUD={BAUD})")
    try:
        # timeout=0 -> non-blocking read, keeps live preview smooth
        ser = serial.Serial(port, BAUD, timeout=0)
    except SerialException as e:
        print(f"[!] Cannot open {port}: {e}")
        print("    - Is it the correct COM port?  Example:  python doorbell.py COM5")
        print("    - Thonny or another program might be using the port, close them.")
        return

    time.sleep(2)               # Wait for ESP32 to reset and boot
    ser.reset_input_buffer()    # Clear stale/buffered data

    print("[i] Opening camera...")
    cap = open_camera()
    if cap is None:
        print("[!] Cannot open camera. Exiting.")
        ser.close()
        return

    print("[i] Ready. Waiting for 'RING' from ESP32...")
    print("    (In the camera window, press [q] to quit)")

    WIN = "Doorbell - Live (q=quit)"
    buf = b""
    result_frame = None
    hold_until = 0.0

    try:
        while True:
            ret, live = cap.read()
            if ret:
                live = cv2.flip(live, 1)
            now = time.time()

            # Display: frozen result frame if within hold time,
            # otherwise live feed + "waiting" text.
            if SHOW_WINDOW:
                if result_frame is not None and now < hold_until:
                    disp = result_frame
                elif ret:
                    disp = live.copy()
                    cv2.putText(disp, "Waiting - approach sensor", (10, 36),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
                else:
                    disp = None
                if disp is not None:
                    cv2.imshow(WIN, disp)
                if (cv2.waitKey(1) & 0xFF) == ord("q"):
                    break
            else:
                time.sleep(0.02)

            # Read lines from serial port (non-blocking)
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
                    print("\n[RING] Someone is at the door! Checking face...")
                    # "checking" visual feedback
                    if SHOW_WINDOW and ret:
                        tmp = live.copy()
                        cv2.putText(tmp, "Checking...", (10, 36),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 200), 2)
                        cv2.imshow(WIN, tmp)
                        cv2.waitKey(1)

                    frame = grab_frame(cap)
                    if frame is None:
                        print("[!] Failed to grab camera frame -> stranger.")
                        ser.write(b"RED\n")
                        continue

                    result, name, locations = recognize(frame, known_encodings, known_names)
                    if result == "known":
                        print(f"[OK] KNOWN: {name} -> green LED")
                        ser.write(b"GREEN\n")
                        result_frame = _annotate(frame, locations, f"KNOWN: {name}", (0, 200, 0))
                    elif result == "stranger":
                        print("[NO] STRANGER -> red LED")
                        ser.write(b"RED\n")
                        result_frame = _annotate(frame, locations, "STRANGER", (0, 0, 255))
                    else:
                        print("[??] No face visible -> treated as stranger.")
                        ser.write(b"RED\n")
                        result_frame = _annotate(frame, locations, "No face", (0, 165, 255))
                    hold_until = time.time() + RESULT_HOLD_SEC
                else:
                    # Other ESP32 messages (BOOT etc.) - for informational purposes
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
        print("\n[i] Exiting...")
