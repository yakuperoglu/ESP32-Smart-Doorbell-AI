# 📖 User Guide — Smart Doorbell

This document explains the **daily usage** of the project: how to add known faces, how to start the project, and how to change settings.

> If you haven't set it up yet, check → **[SETUP.md](SETUP.md)** first.
> All commands should be run from the **project root directory**.

---

## How it works? (short summary)

1. Someone approaches the door → the **HC-SR04** sensor detects them.
2. **ESP32** sends a `RING` signal to the PC.
3. The PC takes a frame from the webcam and performs **face recognition**:
   - If it's a known person → `GREEN` sent to ESP32 → **ring turns green** 🟢
   - If it's a stranger → `RED` sent to ESP32 → **ring turns red** 🔴

Known people are determined from the photos in the `known_faces/` folder.

---

## 1. Adding a Known Face

If the `known_faces/` folder is **empty, everyone on camera is considered a "stranger" (red)**.
Therefore, you must add known people first.

### Method A — Using the Webcam (Recommended)
```powershell
.\.venv\Scripts\python.exe pc\enroll.py john
```
- A camera window opens.
- When your face is clear, press the **[s]** key → it will be saved as `known_faces/john.jpg`.
- Press **[q]** to quit.
- 💡 The program checks if **there is a face in the frame** before saving; if not, it warns you and does not save.

To add **multiple people**, repeat the command with a different name:
```powershell
.\.venv\Scripts\python.exe pc\enroll.py mom
.\.venv\Scripts\python.exe pc\enroll.py brother
```

### Method B — Manually adding a photo
Place a `name.jpg` (or `.png`) directly into the `known_faces/` folder.
- Ensure each file contains **only one person**, is **clear**, **front-facing**, and in **good lighting**.
- File name = the person's name (this name is displayed in the result). E.g., `ahmet.jpg`, `mom.png`.

### Tips for good photos
- The face should be large and clear, with lighting coming from the front.
- Items like glasses/masks make recognition harder.
- 1 clear photo per person is enough.

---

## 2. Viewing / Deleting added faces

- **To view:** Open the `known_faces/` folder — every `.jpg`/`.png` there is a known person.
- **To delete:** Delete the file (e.g., `known_faces/john.jpg`). That person will now be considered a "stranger".

---

## 3. Starting the Project

### 3.1 — Test WITHOUT ESP32 (only camera + face recognition)
To test face recognition even if the hardware is not connected:
```powershell
.\.venv\Scripts\python.exe pc\doorbell.py --test
```
- A live camera feed opens.
- **[SPACE]** → Checks the current frame and displays the result (KNOWN/STRANGER).
- **[q]** → Exit.

### 3.2 — Real Doorbell Mode (With ESP32)
While the ESP32 is plugged in, run it with **your COM port** (e.g. COM10):
```powershell
.\.venv\Scripts\python.exe pc\doorbell.py COM10
```

**What you will see:**
1. The ring briefly flashes **blue** (board resets), the terminal says `Ready. Waiting for 'RING' from ESP32...`.
2. The **Camera window** stays open constantly (displaying `Waiting - approach the sensor`).
3. When you approach the sensor (closer than 50 cm):
   - The window shows `Checking...` (yellow),
   - A **box** is drawn around your face,
   - The result stays on screen for **3 seconds**:
     - 🟢 `KNOWN: john` (green box) + ring turns green
     - 🔴 `STRANGER` (red box) + ring turns red
4. **To exit:** Press the **[q]** key in the camera window (or **Ctrl+C** in the terminal).

> If you omit the COM port, the script checks the `DOORBELL_PORT` environment variable, then defaults to `COM3`. **The safest way is to provide the port in the command:** `doorbell.py COM10`.

---

## 4. Fine Tuning

### PC Side — [pc/doorbell.py](pc/doorbell.py)
| Setting | Line | What it does |
|---|---|---|
| `TOLERANCE = 0.5` | ~38 | Recognition strictness. If it mistakes a stranger for someone known, **lower it** (0.45); if it doesn't recognize a known person, **raise it** (0.6). |
| `RESULT_HOLD_SEC = 3` | ~42 | How many seconds the recognition result stays on screen. |
| `CAMERA_INDEX = 0` | ~32 | If the wrong camera opens, change to `1` or `2`. |
| `SHOW_WINDOW = True` | ~41 | Set to `False` if you want to hide the camera window. |

> Simply edit and save this file — changes apply on the next run.

### ESP32 Side — [esp32/main.py](esp32/main.py)
| Setting | What it does |
|---|---|
| `DISTANCE_THRESHOLD_CM = 50` | Proximity required (in cm) to trigger the doorbell. |
| `COOLDOWN_MS = 5000` | Wait time between rings (prevents spamming). |
| `GREEN` / `RED` | LED colors/brightness (e.g., `(0, 40, 0)`). |

> ⚠️ If you modify `main.py`, you **must re-upload it to the board**:
> ```powershell
> .\.venv\Scripts\python.exe -m mpremote connect COM10 fs cp esp32\main.py :main.py
> .\.venv\Scripts\python.exe -m mpremote connect COM10 reset
> ```

---

## 5. Demo Tips

- Ensure the environment is **well lit**; faces must be clearly visible.
- Make sure your **face is looking at the camera** when triggering the sensor (the snapshot is taken at that exact moment).
- For testing: add yourself as known first → you should get a **green** light, and someone it doesn't know should get a **red** light.
- Play with the `TOLERANCE` value to adjust sensitivity.

---

## Having Issues?
➡️ Refer to the "Common Issues" section in **[SETUP.md](SETUP.md)**.
