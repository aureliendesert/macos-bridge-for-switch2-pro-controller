# BLE Protocol Documentation

## Overview

The Nintendo Switch 2 Pro Controller uses Bluetooth Low Energy (BLE) for communication, unlike the Switch 1 Pro Controller which uses Bluetooth Classic.

This document describes the protocol reverse-engineered on macOS in January 2026.

## Device Identification

| Property | Value |
|----------|-------|
| Vendor ID | `0x057E` (Nintendo) |
| Product ID | `0x2069` (Switch 2 Pro) |
| Device Name | "Nintendo Switch 2 Pro Controller" |

### Manufacturer Data

The controller advertises with manufacturer data containing:
- `\x7e\x05` - Nintendo vendor ID (little-endian)
- `\x69\x20` - Product ID (little-endian)

## BLE Services & Characteristics

### Primary Service

| Property | Value |
|----------|-------|
| Service UUID | Custom Nintendo service |

### Characteristics

| UUID | Handle | Properties | Purpose |
|------|--------|------------|---------|
| `7492866c-ec3e-4619-8258-32755ffcc0f9` | 45 | Notify | Input reports |
| `7492866c-ec3e-4619-8258-32755ffcc0f8` | 13 | Write | Output (LED, rumble) |

## Input Report Format

Input reports are received via notifications on the input characteristic.
Reports are sent approximately every 60ms (~16.7 Hz).

### Packet Structure

```
Byte 0:    Report ID (varies)
Byte 1:    Timer/sequence
Byte 2:    Button byte 1
Byte 3:    Button byte 2
Byte 4:    Button byte 3
Byte 5-7:  Left stick (12-bit X, 12-bit Y)
Byte 8-10: Right stick (12-bit X, 12-bit Y)
Byte 11+:  Additional data (IMU, etc.)
```

### Button Byte 1 (Byte 2)

| Bit | Mask | Button |
|-----|------|--------|
| 0 | 0x01 | B |
| 1 | 0x02 | A |
| 2 | 0x04 | Y |
| 3 | 0x08 | X |
| 4 | 0x10 | R (shoulder) |
| 5 | 0x20 | ZR (trigger) |
| 6 | 0x40 | + (Plus) |
| 7 | 0x80 | RS (Right stick click) |

### Button Byte 2 (Byte 3)

| Bit | Mask | Button |
|-----|------|--------|
| 0 | 0x01 | D-pad Down |
| 1 | 0x02 | D-pad Right |
| 2 | 0x04 | D-pad Left |
| 3 | 0x08 | D-pad Up |
| 4 | 0x10 | L (shoulder) |
| 5 | 0x20 | ZL (trigger) |
| 6 | 0x40 | - (Minus) |
| 7 | 0x80 | LS (Left stick click) |

### Button Byte 3 (Byte 4)

| Bit | Mask | Button |
|-----|------|--------|
| 0 | 0x01 | HOME |
| 1 | 0x02 | ● (Round button, Switch 2 exclusive) |
| 2 | 0x04 | GR (Grip Right, Switch 2 exclusive) |
| 3 | 0x08 | GL (Grip Left, Switch 2 exclusive) |
| 4 | 0x10 | Capture |

### Analog Stick Format

Both sticks use 12-bit values (0-4095) packed into 3 bytes.

**Left Stick (bytes 5-7):**
```python
lx = byte5 | ((byte6 & 0x0F) << 8)
ly = ((byte6 & 0xF0) >> 4) | (byte7 << 4)
```

**Right Stick (bytes 8-10):**
```python
rx = byte8 | ((byte9 & 0x0F) << 8)
ry = ((byte9 & 0xF0) >> 4) | (byte10 << 4)
```

**Normalization:**
- Center value: ~2048
- Range: 0-4095
- Normalized: `(raw - 2048) / 2048.0` gives -1.0 to 1.0

## Output Commands (WIP)

Output commands are written to the output characteristic.

### Subcommand Format (theoretical)

Based on Switch 1 protocol:
```
Byte 0:    0x01 (Subcommand report)
Byte 1:    Counter (0-15, incrementing)
Byte 2-9:  Rumble data (8 bytes)
Byte 10:   Subcommand ID
Byte 11+:  Subcommand data
```

### Known Subcommands (from Switch 1)

| ID | Command |
|----|---------|
| 0x30 | Set Player LEDs |
| 0x38 | Set HOME LED |
| 0x48 | Enable Vibration |

**Note:** These commands have not been confirmed working on Switch 2 via BLE.
The output characteristic may require different authentication or format.

## Connection Process

1. Scan for BLE devices with Nintendo manufacturer data
2. Connect to device
3. Subscribe to notifications on input characteristic
4. Receive input reports

No pairing or authentication is required for input reading.

## Differences from Switch 1 Pro Controller

| Feature | Switch 1 | Switch 2 |
|---------|----------|----------|
| Bluetooth | Classic | BLE |
| Product ID | 0x2009 | 0x2069 |
| Update rate | ~60 Hz | ~16 Hz (60ms) |
| Grip buttons | No | Yes (GL, GR) |
| Round button | No | Yes |

## References

- [Nintendo Switch Reverse Engineering](https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering)
- [SPro2Win (Windows driver)](https://github.com/SquareDonut1/SPro2Win)
- [Bleak BLE library](https://github.com/hbldh/bleak)
