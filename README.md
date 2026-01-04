# 🎮 Switch 2 Pro Controller - macOS BLE Bridge

**The first working Bluetooth LE client for the Nintendo Switch 2 Pro Controller on macOS.**

A Python-based bridge that connects to the Switch 2 Pro Controller via BLE and translates inputs to keyboard presses for use with emulators like Ryujinx.

<p align="center">
  <img src="assets/demo.gif" alt="Demo" width="600">
</p>

[![macOS](https://img.shields.io/badge/macOS-Ventura%2B-blue?logo=apple)](https://www.apple.com/macos)
[![Python](https://img.shields.io/badge/Python-3.9%2B-green?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## ⚠️ What This Is (and Isn't)

**This is NOT a system driver.** It won't make your controller appear in System Preferences or work natively with games.

**This IS:**
- ✅ A BLE client that reads controller inputs via Bluetooth Low Energy
- ✅ A keyboard bridge that converts inputs to key presses for Ryujinx
- ✅ A reference implementation for the Switch 2 Pro Controller BLE protocol

## 🚀 Features

- ✅ **Full button mapping** - All buttons, triggers, D-pad working
- ✅ **Analog sticks** - Both sticks with 12-bit precision
- ✅ **Grip buttons** - Switch 2 exclusive GL/GR buttons supported
- ✅ **Ryujinx compatible** - Keyboard bridge for emulator support
- ✅ **No pairing required** - Bypasses macOS Bluetooth limitations

## 🤔 Why This Exists

The Nintendo Switch 2 Pro Controller (Product ID: `0x2069`) doesn't work with macOS natively:

| Method | Status | Problem |
|--------|--------|---------|
| USB | ❌ | Firmware blocks non-Switch connections |
| Bluetooth Classic | ❌ | macOS can't discover/pair with it |
| Bluetooth LE | ✅ | Works with custom BLE client (this project) |

This bridge connects via BLE using the `bleak` library, reads the raw input data, and converts it to keyboard presses that Ryujinx can use.

## 📋 Requirements

- macOS Ventura (13.0) or later
- Python 3.9+
- Nintendo Switch 2 Pro Controller

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/AurelienDesert/switch2-mac-bridge.git
cd switch2-mac-bridge

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🎯 Usage

### Option 1: Raw Input Display (for testing)

```bash
python src/client.py
```

Displays all controller inputs in real-time. Great for verifying your controller works.

### Option 2: Ryujinx Keyboard Bridge (for gaming)

```bash
python src/ryujinx_bridge.py
```

Converts controller inputs to keyboard presses for use with Ryujinx.

**⚠️ First run:** macOS will ask for Accessibility permissions. Grant access in:
> System Preferences → Security & Privacy → Privacy → Accessibility

**Ryujinx Configuration:**
1. Open Ryujinx → Options → Settings → Input
2. Set Input Device: **Keyboard**
3. Set Controller Type: **Pro Controller**
4. Map each button according to the table below

## 🎮 Button Mapping

### Controller → Keyboard (Ryujinx Bridge)

| Button | Key | | Button | Key |
|--------|-----|-|--------|-----|
| A | Z | | L | Q |
| B | X | | R | E |
| X | C | | ZL | 1 |
| Y | V | | ZR | 3 |
| + | P | | LS (click) | F |
| - | M | | RS (click) | G |
| Home | H | | GL (grip) | 9 |
| Capture | O | | GR (grip) | 0 |

| D-Pad | Key | | Stick | Keys |
|-------|-----|-|-------|------|
| Up | ↑ | | Left Stick | WASD |
| Down | ↓ | | Right Stick | IJKL |
| Left | ← | | | |
| Right | → | | | |

## 📁 Project Structure

```
switch2-mac-bridge/
├── src/
│   ├── client.py           # BLE client (raw input display)
│   ├── ryujinx_bridge.py   # Keyboard bridge for Ryujinx
│   └── calibrate.py        # Calibration utility
├── docs/
│   └── PROTOCOL.md         # BLE protocol documentation
├── requirements.txt
├── LICENSE
└── README.md
```

## 🔬 Technical Details

### How It Works

```
┌─────────────────┐     BLE      ┌─────────────────┐    pynput    ┌─────────────────┐
│  Switch 2 Pro   │ ──────────▶  │  Python Bridge  │ ──────────▶  │    Ryujinx      │
│   Controller    │   (bleak)    │                 │  (keyboard)  │   (Keyboard)    │
└─────────────────┘              └─────────────────┘              └─────────────────┘
```

1. **BLE Connection**: Uses `bleak` to connect directly via Bluetooth LE
2. **Input Parsing**: Decodes the proprietary Nintendo protocol
3. **Keyboard Simulation**: Uses `pynput` to simulate key presses
4. **Ryujinx**: Reads keyboard input as if from a physical keyboard

### BLE Characteristics

| UUID | Purpose |
|------|---------|
| `7492866c-ec3e-4619-8258-32755ffcc0f9` | Input reports (notifications) |
| `7492866c-ec3e-4619-8258-32755ffcc0f8` | Output (LED, rumble - not working) |

See [docs/PROTOCOL.md](docs/PROTOCOL.md) for full protocol documentation.

## 🚧 Limitations

| Feature | Status | Notes |
|---------|--------|-------|
| Buttons | ✅ Working | All buttons mapped |
| Analog Sticks | ⚠️ Digital | Converted to 8 directions (WASD/IJKL) |
| LED Control | ❌ Not working | Output characteristic doesn't respond |
| Rumble | ❌ Not working | Same issue |
| Motion/Gyro | ❌ Not implemented | Data not decoded |
| Native HID | ❌ Not possible | Would require DriverKit (kernel-level) |

## 🤝 Contributing

Contributions welcome! Areas that need work:

1. **LED/Rumble** - Figure out the output protocol
2. **Motion controls** - Decode gyro/accelerometer data  
3. **True analog** - Virtual HID device (requires DriverKit)
4. **Cross-platform** - Linux/Windows ports

## 📜 Credits

- **Aurélien Desert** - Reverse engineering & implementation
- **Claude (Anthropic)** - Development assistance
- Inspired by [SPro2Win](https://github.com/SquareDonut1/SPro2Win) (Windows)
- Protocol reference from [Nintendo Switch Reverse Engineering](https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering)

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>⭐ Star this repo if it helped you!</b><br>
  <i>First macOS BLE bridge for Switch 2 Pro Controller - January 2026</i>
</p>
