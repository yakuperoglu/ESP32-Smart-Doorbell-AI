# Smart Doorbell — Hardware Technical Specifications Report

> This report covers the technical specifications of all hardware components
> used in the **face-recognition smart doorbell** project (ESP32-S3 based).

## Components Used (Bill of Materials)

| # | Component | Role |
|---|-----------|------|
| 1 | ESP32-S3-DevKitM-1 (main board) | Reads sensor, talks to PC over USB serial, drives the LED |
| 2 | HC-SR04 ultrasonic distance sensor | Detects someone approaching the door (rings the bell) |
| 3 | WS2812B 8-bit NeoPixel ring | Shows the result: **green = known**, **red = stranger** |
| 4 | BSS138 logic level converter (3.3 V ↔ 5 V) | Steps the HC-SR04 Echo (5 V) signal down to 3.3 V |
| 5 | Breadboard (830 holes) | Solderless prototyping |
| 6 | Jumper wires (M-M 20 cm, M-F 30 cm) | Connections |
| 7 | 330 Ω resistor | WS2812B data-line series resistor |
| 8 | 1000 µF electrolytic capacitor | WS2812B power-line filtering |

> The PC side additionally uses a **webcam** (for face recognition).

### System Flow

```
[HC-SR04]  →  ESP32-S3  →  (USB Serial)  →  PC (Python + Webcam)
                  ↑                                │
                  │                          Face recognition
                  │                                │
        Green/Red LED  ←──── "GREEN"/"RED" ───────┘
```

---

## Table of Contents

1. [ESP32-S3-DevKitM-1 (Main Board)](#1-esp32-s3-devkitm-1-main-board)
2. [HC-SR04 Ultrasonic Distance Sensor](#2-hc-sr04-ultrasonic-distance-sensor)
3. [8-Bit WS2812B NeoPixel Ring](#3-8-bit-ws2812b-neopixel-ring)
4. [Logic Level Converter (3.3 V – 5 V, BSS138)](#4-logic-level-converter-33-v--5-v-bss138)
5. [Breadboard, Jumper Wires, Resistor & Capacitor](#5-breadboard-jumper-wires-resistor--capacitor)
6. [Pin Connection Map (this project)](#6-pin-connection-map-this-project)
7. [System Integrity & General Warnings](#7-system-integrity--general-warnings)

---

## 1. ESP32-S3-DevKitM-1 (Main Board)

The DevKitM-1 carries an **ESP32-S3-MINI-1** module (ESP32-S3FN8 SiP). The `N8`
suffix means **8 MB internal flash, no PSRAM**.

| Parameter | Value |
|---|---|
| MCU | Dual-core Xtensa LX7 @ 240 MHz |
| SRAM | 512 KB |
| Flash | 8 MB (internal SiP) |
| Wireless | Wi-Fi 2.4 GHz + BLE 5 (**not used in this project**) |
| GPIO level | 3.3 V (**NOT 5 V tolerant**) |
| USB | 1× USB 2.0 OTG, 1× USB Serial/JTAG |

> All ESP32 ↔ PC communication in this project is over **USB serial (UART)** —
> Wi-Fi/BLE are not used.

### GPIOs to Avoid

| GPIO | Status |
|---|---|
| GPIO0 / 3 / 45 / 46 | Strapping pins — avoid |
| GPIO19 / 20 | Native USB D− / D+ |
| GPIO26–32 | Internal flash lines — **never use** |
| GPIO33–37 | Not connected on the MINI-1 package |
| GPIO48 | On-board WS2812 RGB LED |

> The pins chosen for this project — **GPIO4, GPIO5, GPIO6** — are all safe
> (none appear above).

### Electrical Limits

- Max output current per GPIO ≈ 40 mA (safe range 12–20 mA).
- The **5V pin is tied directly to USB VBUS**; a PC USB port supplies
  ~500–900 mA. The NeoPixel ring at full white draws ~480 mA, so brightness is
  kept low in software (see §3 and §7).

---

## 2. HC-SR04 Ultrasonic Distance Sensor

Measures distance from **2 cm to 400 cm** using 40 kHz ultrasound. Used here to
detect a person approaching the door and **trigger the doorbell**.

**Operating principle:** a ≥10 µs TTL pulse on `Trig` emits 8 pulses at 40 kHz;
when the echo returns, `Echo` goes HIGH; distance = `pulse_width_µs / 58`.

| Parameter | Value |
|---|---|
| Operating voltage | DC **5 V** |
| Current | ~15 mA |
| Range | 2 cm – 400 cm |
| Accuracy | ~3 mm |
| Beam angle | ~15° |
| Trigger input | 10 µs TTL pulse |
| Echo output | TTL pulse at **5 V level**, width ∝ distance |

| Pin | Description |
|---|---|
| VCC | 5 V power |
| Trig | Trigger input (digital) |
| Echo | Echo output (digital, **5 V**) |
| GND | Ground |

### ⚠️ ESP32-S3 Voltage Compatibility (Critical)

The HC-SR04 runs on 5 V and its `Echo` pin outputs a **5 V** signal. ESP32-S3
GPIOs are **not 5 V tolerant**.

- **Echo → must go through the BSS138 logic level converter** to the ESP32.
- **Trig → can be driven directly** from a 3.3 V GPIO (enough to trigger).
- The Echo pulse is slow (µs–ms range), so the BSS138 handles it fine — unlike
  the WS2812B data line (see §3 and §4).

---

## 3. 8-Bit WS2812B NeoPixel Ring

Addressable RGB LEDs with integrated controller ICs; a single data line drives
all 8. Color order is **GRB**. Used here to show the result:
**green = known, red = stranger**.

| Parameter | Value |
|---|---|
| Supply | 3.5 – 5.3 V (nominal **5 V**) |
| Color depth | 24-bit (16.7M colors) |
| Data rate | **800 kbps** (NRZ) |
| Idle current / LED | ~1 mA |
| Full-white current / LED | ~60 mA |
| 8-LED full-white peak | ~480 mA |
| Data HIGH threshold (V_IH) | min. **0.7 × VDD** (≈3.5 V at 5 V supply) |

| Pin | Function |
|---|---|
| 5V / VCC / + | 5 V power |
| GND / − | Ground |
| DIN | Data input (from ESP32) |
| DOUT | Data output (chaining — unused here) |

### ⚠️ Driving the Data Line at 3.3 V (Key Design Point)

V_IH is **0.7 × VDD ≈ 3.5 V** at a 5 V supply, which is slightly **above** the
ESP32-S3's 3.3 V output. Three solutions:

1. **Direct drive (try this first):** most WS2812B batches work with 3.3 V data,
   especially with short wiring and only 8 LEDs. Flicker / wrong colors on the
   first LED is the typical failure symptom.
2. **Lower the supply (if it flickers):** power the ring through a **1N5819
   Schottky diode** to drop VDD to ~4.3 V — this lowers V_IH to ~3.0 V so the
   3.3 V data is read reliably as HIGH. Fast and effective.
3. **Real level shifter:** a **74AHCT125 / 74HCT245** buffer is the most robust
   option (not required for this project).

> **🔴 IMPORTANT — common mistake:** **Do NOT use the BSS138 bi-directional
> level converter on the WS2812B data line.** Its RC time constant (10 kΩ
> pull-up × wire capacitance) cannot produce the sharp rising edges that 800 kbps
> NRZ needs — the data corrupts and LEDs show random/wrong colors. Use the BSS138
> only for slow signals like the HC-SR04 Echo. Drive WS2812B data either directly
> from the GPIO (with a series resistor) or via methods 2/3 above.

**Other notes:** put a **330 Ω** series resistor right before DIN; add a
**1000 µF** electrolytic capacitor across the ring's 5 V↔GND (close to the ring);
ESP32 and WS2812B grounds **must be common**; keep brightness low in software
(`GREEN=(0,40,0)`, `RED=(40,0,0)`).

---

## 4. Logic Level Converter (3.3 V – 5 V, BSS138)

A **bi-directional** 4-channel module (4× BSS138 MOSFET + 8× 10 kΩ pull-ups,
SparkFun BOB-12009 / NXP AN97055 design). Works automatically without a
direction pin.

| Parameter | Value |
|---|---|
| LV side | 1.8 – 3.3 V |
| HV side | 2.8 – 5 V (**HV must be > LV**) |
| Channels | 4 (bi-directional) |
| Pull-ups | 10 kΩ |
| Safe speed | I²C 100/400 kHz, slow digital signals |

**Usage in this project:** HV → ESP32 5 V, LV → ESP32 3.3 V, both GNDs → common
GND, **HV1 → HC-SR04 Echo**, **LV1 → ESP32 GPIO4**.

**Notes:** HV must be greater than LV; the HV and LV reference pins must not be
left floating; grounds must be common. **🔴 Not suitable for WS2812B (800 kbps)** —
use it only on the HC-SR04 Echo line (or, later, a slow 5 V I²C/UART device).

---

## 5. Breadboard, Jumper Wires, Resistor & Capacitor

- **Breadboard (830 holes):** solderless prototyping; 2 power rails, 60 rows.
  Power rails are limited to ~1 A — use short/thick wires for the WS2812B power.
- **Jumper wires:** M-M (20 cm) for breadboard/module links, M-F (30 cm) from
  header pins to the breadboard. 2.54 mm pitch, 26 AWG.
- **330 Ω resistor (1/4 W):** WS2812B data series resistor right before DIN
  (220–470 Ω acceptable). Color code: Orange-Orange-Brown-Gold.
- **1000 µF / 16 V electrolytic capacitor:** across the WS2812B 5 V↔GND, close
  to the ring, to smooth inrush current. **⚠️ Polarized** — long leg is **(+)**,
  the striped/short leg is **(−)**; reversing it can burst the cap.

---

## 6. Pin Connection Map (this project)

> Pin numbers match `esp32/main.py` exactly. If you change a pin, update the code
> (`TRIG_PIN`, `ECHO_PIN`, `NEOPIXEL_PIN`).

**HC-SR04**
| HC-SR04 | To | Note |
|---|---|---|
| VCC | ESP32 **5V (VIN)** | Sensor needs 5 V |
| GND | ESP32 **GND** | Common ground |
| Trig | ESP32 **GPIO5** | Direct (3.3 V triggers it) |
| Echo | **BSS138 HV1 → LV1** → ESP32 **GPIO4** | Echo is 5 V — must step down! |

**BSS138 Logic Level Converter**
| Converter | To |
|---|---|
| HV | ESP32 **5V (VIN)** |
| LV | ESP32 **3.3V** |
| GND (both sides) | ESP32 **GND** |
| HV1 | HC-SR04 **Echo** |
| LV1 | ESP32 **GPIO4** |

**WS2812B NeoPixel Ring**
| Ring | To | Note |
|---|---|---|
| 5V | ESP32 **5V (VIN)** | (if it flickers: via a 1N5819 diode → ~4.3 V) |
| GND | ESP32 **GND** | Common ground |
| DIN | **330 Ω** → ESP32 **GPIO6** | **Direct — do NOT route through the BSS138!** |
| DOUT | — | Unused |
| 5V↔GND | **1000 µF** capacitor | Close to the ring (watch polarity!) |

```
ESP32-S3 (3.3 V system)
   ├─ GPIO5 ───────────────────► HC-SR04 Trig (direct)
   ├─ GPIO4 ◄── BSS138 (LV1◄HV1) ◄── HC-SR04 Echo (5 V→3.3 V)
   ├─ GPIO6 ──[330Ω]──────────► WS2812B DIN (direct, 3.3 V)
   ├─ 5V (VIN) ──┬─► HC-SR04 VCC
   │             ├─► WS2812B 5V  ──[1000µF ⎓ GND]
   │             └─► BSS138 HV
   ├─ 3.3V ──────► BSS138 LV
   └─ GND ───────► (ALL common ground)
```

---

## 7. System Integrity & General Warnings

| # | Topic | Description |
|---|---|---|
| 1 | **Voltage mismatch** | ESP32-S3 GPIO = 3.3 V; HC-SR04 Echo = 5 V. A level converter on Echo is **mandatory**. |
| 2 | **WS2812B data drive** | BSS138 is unsuitable at 800 kbps. Drive data directly from a GPIO (with 330 Ω); if it flickers, drop the ring's VDD to ~4.3 V via a diode. |
| 3 | **NeoPixel current** | 8 LEDs at full white ≈ 480 mA. Keep brightness low in software (the code already uses 40/255). |
| 4 | **5 V power budget** | A PC USB port gives ~500 mA. Low brightness + a 1000 µF cap keeps it within budget. |
| 5 | **Common ground** | All grounds (ESP32, HC-SR04, WS2812B, BSS138) must meet at a single point. |
| 6 | **Capacitor polarity** | Electrolytic caps are polarized — reversing them causes failure. |
| 7 | **Strapping/flash pins** | Avoid GPIO0, 3, 19, 20, 26–37, 45, 46. The chosen 4/5/6 are safe. |
| 8 | **USB vs external 5 V** | Don't feed USB and external 5 V at the same time. USB power is sufficient for this project. |

---

*Target platform: ESP32-S3-DevKitM-1 | Project: Face-Recognition Smart Doorbell*
