# 🔔 Smart Doorbell — with Face Recognition (ESP32 + Python)

When someone approaches the door, the ultrasonic sensor triggers. The computer then runs face recognition using the webcam; if it's a **known person**, the LED ring turns **green**, if it's a **stranger**, it turns **red**.

> 📚 **Quick Start:** For scratch setup → **[SETUP.md](SETUP.md)** · For daily usage (adding faces, running) → **[USAGE.md](USAGE.md)**

## How it Works

```
[HC-SR04]  →  ESP32  →  (USB Serial)  →  PC (Python + Webcam)
                 ↑                              │
                 │                       Face recognition
                 │                              │
        Green/Red LED  ←─ "GREEN"/"RED" ────────┘
```

## Folder Structure

```
Ai Project/
├── esp32/
│   └── main.py              # MicroPython code for ESP32
├── pc/
│   ├── doorbell.py          # Main program (--test mode + serial + face recognition)
│   ├── enroll.py            # Tool to add known faces via webcam
│   ├── setup.ps1            # PC setup script (.venv + dependencies)
│   ├── verify_setup.py      # Installation verification
│   └── requirements.txt
├── known_faces/             # Photos of known people
├── photos/                  # Other photos/diagrams
└── README.md
```

---

## 1) Hardware Connections (Wiring)

> ℹ️ Pin numbers are based on the **ESP32-S3**. If you change the pins, make sure to update `esp32/main.py`.

### HC-SR04 (Ultrasonic Sensor)
| HC-SR04 | To | Note |
|---------|--------|-----|
| VCC | ESP32 **5V (VIN)** | Sensor requires 5V |
| GND | ESP32 **GND** | Common ground |
| Trig | ESP32 **GPIO 5** | Direct connection (3.3V is enough to trigger) |
| Echo | **Logic Converter** → ESP32 **GPIO 4** | Echo outputs 5V, step-down is required! |

### Logic Level Converter (To step down Echo from 5V → 3.3V)
| Converter | To |
|-----------|--------|
| HV | ESP32 **5V (VIN)** |
| LV | ESP32 **3.3V** |
| GND (both sides) | ESP32 **GND** |
| HV1 | HC-SR04 **Echo** |
| LV1 | ESP32 **GPIO 4** |

### WS2812 RGB LED Ring
| Ring | To | Note |
|-------|--------|-----|
| 5V | ESP32 **5V (VIN)** | Ring requires 5V |
| GND | ESP32 **GND** | Common ground |
| DI (Data In) | **330 Ω** → ESP32 **GPIO 6** | **Direct drive**; if it flickers, supply the ring with ~4.3V using a 1N5819 diode |
| DO (Data Out) | — | Leave disconnected (only needed for daisy-chaining) |

> ⚠️ **DO NOT pass the WS2812B data line through the BSS138 logic converter** — it is not suitable for 800 kbps, and colors will be corrupted. Only use the BSS138 for the HC-SR04 Echo.
> Adjust `NUM_PIXELS` in `main.py` according to your LED count.

---

## 2) ESP32 Setup (MicroPython)

1. Flash the **MicroPython firmware** to the ESP32 (one-time):
   - Download and install [Thonny IDE](https://thonny.org/).
   - Thonny → `Tools > Options > Interpreter` → Select "MicroPython (ESP32)".
   - Click "Install or update MicroPython" at the bottom right → **select the correct board family!**
     If your board is **ESP32-S3**, install the "ESP32-S3" version (not the regular "ESP32").
   - The `neopixel` module comes built-in with MicroPython.
2. Open `esp32/main.py` in Thonny → **Save it to the ESP32 as `main.py`**
   (`File > Save as > MicroPython device`). This ensures the ESP32 runs it automatically on boot.

> To stop the code and access REPL in Thonny, press **Stop/Restart (Ctrl+C)**.

---

## 3) PC Setup (Python) — Conda NOT Required

> Python **3.10+** and pip are sufficient. We use a pre-built `dlib` package (`dlib-bin`);
> NO need for Visual Studio or compiling. Install with one command:

```powershell
# Run this in the project ROOT directory:
powershell -ExecutionPolicy Bypass -File pc\setup.ps1
```
This script automatically creates a `.venv` virtual environment (using the system Python) and installs `dlib-bin`, `face_recognition`, `opencv`, `pyserial`, etc. in the **correct order**.

Verify the installation:
```powershell
.\.venv\Scripts\python.exe pc\verify_setup.py
```
> ℹ️ The "dlib>=19.7 not installed" warning is **harmless** (the module name is `dlib`, but the package is `dlib-bin`). `import dlib` works perfectly.

---

## 4) Add Known Faces

When `known_faces/` is empty, **everyone** on camera is considered a "stranger". Add yourself first:
```powershell
.\.venv\Scripts\python.exe pc\enroll.py john    # Look at the camera, press [s] to save
```
Alternatively, you can manually place a `name.jpg` file inside the `known_faces/` directory.

---

## 5) Run

### a) Test WITHOUT ESP32 (Try this first)
```powershell
.\.venv\Scripts\python.exe pc\doorbell.py --test
```
The live camera will open; press **[SPACE]** to trigger face check (shows KNOWN/STRANGER), press **[q]** to quit. Use this to fully test the PC side before the hardware is ready.

### b) With ESP32 (When hardware is ready)
```powershell
# Provide the ESP32's COM port as an argument (Check Device Manager):
.\.venv\Scripts\python.exe pc\doorbell.py COM5
```
Now, when someone approaches the sensor → the camera checks the face → the LED lights up. 🎉

---

## Testing Order (Verify piece by piece)

1. **RGB Ring test:** In Thonny REPL:
   ```python
   import neopixel
   from machine import Pin
   r = neopixel.NeoPixel(Pin(6), 8)
   r.fill((0, 40, 0)); r.write()   # Should light up green
   ```
2. **Sensor test:** Temporarily add `print(dist)` in `main.py` to read distance.
3. **Camera test:** `python enroll.py test` → Does the camera open?
4. **Face recognition test:** Run `doorbell.py --test` and trigger manually using the SPACE bar.
5. **Full integration:** With everything connected, approach the sensor.

## Fine Tuning
- `main.py` → `DISTANCE_THRESHOLD_CM`: distance to trigger the bell.
- `doorbell.py` → `TOLERANCE`: 0.5 strict / 0.6 loose. If it thinks a stranger is known, lower it; if it doesn't recognize a known person, raise it.
