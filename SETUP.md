# 🛠️ Setup Guide — Smart Doorbell

This document covers all the steps to get the project working **from scratch**.
For daily usage (adding faces, running), refer to → **[USAGE.md](USAGE.md)**.

> Setup order: **PC setup → Hardware wiring → ESP32 (MicroPython) setup → Component tests**

---

## 0. What are we building?

```
[HC-SR04]  →  ESP32-S3  →  (USB Serial)  →  PC (Python + Webcam)
                  ↑                              │
                  │                       Face recognition
                  │                              │
        Green/Red LED  ←─ "GREEN"/"RED" ─────────┘
```

- **PC:** Runs face recognition from a webcam using Python.
- **ESP32:** Runs MicroPython; reads the sensor and lights the LED based on the result.

---

## 1. Requirements

### Hardware
| Component | Note |
|---|---|
| ESP32-S3 dev board | (Ours: dual USB-C, CP210x) |
| HC-SR04 ultrasonic distance sensor | |
| WS2812B 8-bit NeoPixel ring | "LED ring" |
| BSS138 logic level converter | 3.3V ↔ 5V |
| Breadboard + jumper wires | |
| 330Ω resistor, 1000µF capacitor | (Optional but recommended) |
| USB-C cable | ESP32 ↔ PC |
| Webcam | Connected to PC |

> Full technical hardware details: **[ESP32S3_Hardware_Report.md](ESP32S3_Hardware_Report.md)**

### Software
- **Windows 10/11**
- **Python 3.10+** (check: `python --version`)
- Conda is **not required**.

---

## 2. Download the Project

Clone from GitHub or download and extract the ZIP. Then open a terminal in the **project root directory** (where `pc/`, `esp32/`, and `README.md` are located). All commands should be run from here.

```powershell
cd C:\...\ESP32-Smart-Doorbell-AI
```

---

## 3. PC Setup

One command installs everything (virtual environment + all dependencies):

```powershell
powershell -ExecutionPolicy Bypass -File pc\setup.ps1
```

This script:
1. Creates a virtual environment named `.venv` (using the system Python).
2. Installs `dlib` in a **pre-built** format (`dlib-bin` → NO Visual Studio/compilation required).
3. Installs `face_recognition`, `opencv`, and `pyserial`.
4. Installs ESP32 tools (`esptool`, `mpremote`).

### Verify Setup
```powershell
.\.venv\Scripts\python.exe pc\verify_setup.py
```
Everything should say `[OK]`.

> ℹ️ The **"dlib>=19.7 not installed"** warning during setup is **harmless** 
> (the module name is `dlib`, but the package is `dlib-bin`; `import dlib` works fine).

---

## 4. Hardware Wiring

> ⚡ **Unplug** the ESP32 from USB while wiring. Plug it back in only after finishing.

### Pin Map
**HC-SR04:**
| HC-SR04 | To | Note |
|---|---|---|
| VCC | ESP32 **5V** | Sensor requires 5V |
| GND | ESP32 **GND** | Common ground |
| Trig | ESP32 **GPIO5** | **DIRECTLY** (Does not go through the converter!) |
| Echo | **BSS138 HV1 → LV1** → ESP32 **GPIO4** | Echo outputs 5V, step down is required |

**BSS138 Converter:**
| Converter | To |
|---|---|
| HV | ESP32 **5V** |
| LV | ESP32 **3.3V** |
| GND | ESP32 **GND** |
| HV1 | HC-SR04 **Echo** |
| LV1 | ESP32 **GPIO4** |

**WS2812B Ring:**
| Ring | To | Note |
|---|---|---|
| 5V | ESP32 **5V** | If it flickers, use a 1N5819 diode to drop to ~4.3V |
| GND | ESP32 **GND** | |
| DI | **330Ω** → ESP32 **GPIO6** | **DIRECTLY** (Do NOT pass through BSS138!) |
| DO | — | Empty |

### ⚠️ 4 Critical Rules (It won't work otherwise)
1. **Trig connects directly to GPIO5** — it does **not** pass through the BSS138. (Only Echo passes through.)
2. **WS2812B DI connects directly to GPIO6** — Do **NOT** pass through the BSS138 (it's not suitable for 800 kbps, colors will corrupt).
3. **COMMON GND:** ESP32 GND + HC-SR04 GND + BSS138 GND must all be connected together.
4. **BSS138 references:** HV must be fed with 5V, and LV with 3.3V, otherwise the converter will not work.

---

## 5. ESP32 Setup (MicroPython)

### 5.1 — Find the COM port
Plug the ESP32 in via USB, then run:
```powershell
.\.venv\Scripts\python.exe -m serial.tools.list_ports -v
```
Select the port that says `Silicon Labs CP210x` / `CH340` / `USB Serial` (**not Bluetooth**).
(Assume it's **COM10**. Replace `COM10` below with your actual port.)

### 5.2 — Flash MicroPython Firmware
1. Download the firmware: <https://micropython.org/download/ESP32_GENERIC_S3/>
   → Grab the latest **stable** `.bin` (e.g., `ESP32_GENERIC_S3-20260406-v1.28.0.bin`).
2. Erase flash:
   ```powershell
   .\.venv\Scripts\python.exe -m esptool --chip esp32s3 --port COM10 erase-flash
   ```
3. Write firmware (**offset 0** is correct for ESP32-S3):
   ```powershell
   .\.venv\Scripts\python.exe -m esptool --chip esp32s3 --port COM10 --baud 460800 write-flash 0 "C:\downloads\ESP32_GENERIC_S3-20260406-v1.28.0.bin"
   ```
   If you see `Hash of data verified.` at the end, it was successful.

> 🔌 If esptool says "Failed to connect": Hold the **BOOT** button → press **RESET** → release BOOT → run the command again.

### 5.3 — Upload `main.py` to the board
It is copied to the board as `main.py` so the board runs it automatically on boot:
```powershell
.\.venv\Scripts\python.exe -m mpremote connect COM10 fs cp esp32\main.py :main.py
.\.venv\Scripts\python.exe -m mpremote connect COM10 reset
```
After resetting, if the **ring flashes blue twice**, `main.py` is running. 🎉

---

## 6. Component Tests (Verification)

Test each component individually (while the board is connected via USB):

**LED Ring Test** — should light up green → red → blue:
```powershell
.\.venv\Scripts\python.exe -m mpremote connect COM10 run esp32\test_neopixel.py
```

**HC-SR04 Test** — wave your hand in front of the sensor, cm values should change:
```powershell
.\.venv\Scripts\python.exe -m mpremote connect COM10 run esp32\test_hcsr04.py
```

> Note: To run component tests, `main.py` on the board must be stopped;
> `mpremote run` does this automatically. When you power cycle the board,
> `main.py` will run again.

---

## 7. Common Issues

| Symptom | Solution |
|---|---|
| **HC-SR04 always "timeout"** | Is Trig connected **directly to GPIO5**? Common GND? Is HC-SR04 VCC **5V**? |
| **LED not lighting up** | Is DI truly on **GPIO6** (not DO)? 5V/GND correct? |
| **LED flickering / wrong colors** | 3.3V data issue → supply the ring with ~4.3V using a **1N5819 diode**. |
| **Cannot see COM port** | Missing drivers (CP210x/CH340). Try another USB-C port. Do not confuse with Bluetooth ports (COM3-8). |
| **`mpremote`/`esptool` cannot connect / port busy** | Another program like `doorbell.py` or Thonny might be holding the port; close it. |
| **"dlib>=19.7 not installed" warning** | Harmless, ignore it (`dlib-bin` was installed). |
| **Camera not opening** | Change `CAMERA_INDEX = 0` to `1` or `2` inside [pc/doorbell.py](pc/doorbell.py) and [pc/enroll.py](pc/enroll.py). |

---

## 8. Setup finished → what's next?

➡️ Move on to **[USAGE.md](USAGE.md)**: adding known faces and starting the project is covered there.
