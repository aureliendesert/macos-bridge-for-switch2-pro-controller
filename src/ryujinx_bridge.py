#!/usr/bin/env python3
"""
Switch 2 Pro Controller → Ryujinx Keyboard Bridge
==================================================

Converts controller inputs to keyboard presses for use with Ryujinx emulator.

Usage:
    1. Run this script
    2. In Ryujinx: Settings → Input → Keyboard → Pro Controller
    3. Map each button according to the BUTTON_KEYS mapping below

Author: Aurélien Desert
Date: January 2026
License: MIT
"""

import asyncio
import sys

try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    print("❌ Error: bleak library not installed")
    print("   Run: pip install bleak")
    sys.exit(1)

try:
    from pynput.keyboard import Controller, Key
    keyboard = Controller()
except ImportError:
    print("❌ Error: pynput library not installed")
    print("   Run: pip install pynput")
    print("\n   Then allow accessibility access in:")
    print("   System Preferences → Security → Privacy → Accessibility")
    sys.exit(1)


# BLE Characteristic for input reports
INPUT_CHAR_UUID = "7492866c-ec3e-4619-8258-32755ffcc0f9"

# ============================================================
# KEYBOARD MAPPING
# ============================================================
# Configure Ryujinx with these keys:
#   Settings → Input → Keyboard → Pro Controller
# ============================================================

BUTTON_KEYS = {
    # Face buttons
    'A': 'z',
    'B': 'x',
    'X': 'c',
    'Y': 'v',
    # Shoulders
    'L': 'q',
    'R': 'e',
    'ZL': '1',
    'ZR': '3',
    # System
    '+': 'p',
    '-': 'm',
    'HOME': 'h',
    'CAPT': 'o',
    # Stick clicks
    'LS': 'f',
    'RS': 'g',
    # D-pad
    'DUP': Key.up,
    'DDOWN': Key.down,
    'DLEFT': Key.left,
    'DRIGHT': Key.right,
    # Grip buttons (Switch 2 exclusive)
    'GL': '9',
    'GR': '0',
}

# Stick threshold for digital conversion
STICK_THRESHOLD = 0.5


class RyujinxBridge:
    """Converts controller inputs to keyboard presses."""
    
    def __init__(self):
        self.packet_count = 0
        self.pressed_keys = set()
    
    def key_down(self, key):
        """Press a key if not already pressed."""
        if key not in self.pressed_keys:
            self.pressed_keys.add(key)
            keyboard.press(key)
    
    def key_up(self, key):
        """Release a key if pressed."""
        if key in self.pressed_keys:
            self.pressed_keys.discard(key)
            keyboard.release(key)
    
    def set_key(self, key, active: bool):
        """Set key state."""
        if active:
            self.key_down(key)
        else:
            self.key_up(key)
    
    def parse(self, data: bytes):
        """Parse controller data and update keyboard state."""
        if len(data) < 11:
            return
        
        self.packet_count += 1
        
        # Button bytes
        b2, b3, b4 = data[2], data[3], data[4]
        
        # === FACE BUTTONS (byte 2) ===
        self.set_key(BUTTON_KEYS['B'], b2 & 0x01)
        self.set_key(BUTTON_KEYS['A'], b2 & 0x02)
        self.set_key(BUTTON_KEYS['Y'], b2 & 0x04)
        self.set_key(BUTTON_KEYS['X'], b2 & 0x08)
        self.set_key(BUTTON_KEYS['R'], b2 & 0x10)
        self.set_key(BUTTON_KEYS['ZR'], b2 & 0x20)
        self.set_key(BUTTON_KEYS['+'], b2 & 0x40)
        self.set_key(BUTTON_KEYS['RS'], b2 & 0x80)
        
        # === D-PAD + LEFT TRIGGERS (byte 3) ===
        self.set_key(BUTTON_KEYS['DDOWN'], b3 & 0x01)
        self.set_key(BUTTON_KEYS['DRIGHT'], b3 & 0x02)
        self.set_key(BUTTON_KEYS['DLEFT'], b3 & 0x04)
        self.set_key(BUTTON_KEYS['DUP'], b3 & 0x08)
        self.set_key(BUTTON_KEYS['L'], b3 & 0x10)
        self.set_key(BUTTON_KEYS['ZL'], b3 & 0x20)
        self.set_key(BUTTON_KEYS['-'], b3 & 0x40)
        self.set_key(BUTTON_KEYS['LS'], b3 & 0x80)
        
        # === SPECIAL BUTTONS (byte 4) ===
        self.set_key(BUTTON_KEYS['HOME'], b4 & 0x01)
        self.set_key(BUTTON_KEYS['GR'], b4 & 0x04)
        self.set_key(BUTTON_KEYS['GL'], b4 & 0x08)
        self.set_key(BUTTON_KEYS['CAPT'], b4 & 0x10)
        
        # === ANALOG STICKS ===
        # Parse 12-bit values
        lx_raw = data[5] | ((data[6] & 0x0F) << 8)
        ly_raw = ((data[6] & 0xF0) >> 4) | (data[7] << 4)
        rx_raw = data[8] | ((data[9] & 0x0F) << 8)
        ry_raw = ((data[9] & 0xF0) >> 4) | (data[10] << 4)
        
        # Normalize to -1.0 to 1.0
        lx = (lx_raw - 2048) / 2048.0
        ly = (ly_raw - 2048) / 2048.0
        rx = (rx_raw - 2048) / 2048.0
        ry = (ry_raw - 2048) / 2048.0
        
        # Left stick → WASD
        self.set_key('w', ly > STICK_THRESHOLD)
        self.set_key('s', ly < -STICK_THRESHOLD)
        self.set_key('a', lx < -STICK_THRESHOLD)
        self.set_key('d', lx > STICK_THRESHOLD)
        
        # Right stick → IJKL
        self.set_key('i', ry > STICK_THRESHOLD)
        self.set_key('k', ry < -STICK_THRESHOLD)
        self.set_key('j', rx < -STICK_THRESHOLD)
        self.set_key('l', rx > STICK_THRESHOLD)
    
    def release_all(self):
        """Release all pressed keys."""
        for key in list(self.pressed_keys):
            keyboard.release(key)
        self.pressed_keys.clear()


async def find_controller(timeout: float = 5.0) -> str | None:
    """Scan for Switch 2 Pro Controller."""
    print(f"🔍 Scanning for controller ({timeout}s)...")
    
    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
    
    for address, (device, adv) in devices.items():
        if adv.manufacturer_data:
            for company_id, data in adv.manufacturer_data.items():
                if b'\x7e\x05' in data or b'\x69\x20' in data:
                    print(f"   ✅ Found: {device.name}")
                    return address
    
    print("   ❌ Controller not found")
    return None


async def main():
    """Main entry point."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     Switch 2 Pro Controller → Ryujinx Bridge                  ║
║     First macOS driver - January 2026                         ║
╚═══════════════════════════════════════════════════════════════╝

📋 RYUJINX CONFIGURATION:
   Settings → Input → Configure
   Input Device: Keyboard
   Controller Type: Pro Controller

📋 BUTTON MAPPING:
   ┌─────────────────────────────────────────────┐
   │  A → Z    B → X    X → C    Y → V           │
   │  L → Q    R → E    ZL → 1   ZR → 3          │
   │  + → P    - → M    Home → H   Capture → O   │
   │  LS → F   RS → G   GL → 9   GR → 0          │
   │  D-pad → Arrow keys                         │
   │  Left Stick → WASD    Right Stick → IJKL    │
   └─────────────────────────────────────────────┘
""")
    
    bridge = RyujinxBridge()
    
    address = await find_controller()
    if not address:
        print("\n   Make sure controller is on and LED is blinking")
        return
    
    def on_data(sender, data):
        bridge.parse(data)
    
    async with BleakClient(address, timeout=30.0) as client:
        print("   ✅ Connected!\n")
        
        await client.start_notify(INPUT_CHAR_UUID, on_data)
        
        print("═" * 55)
        print("  🎮 BRIDGE ACTIVE - Press Ctrl+C to stop")
        print("═" * 55 + "\n")
        
        try:
            while client.is_connected:
                await asyncio.sleep(0.1)
                
                # Display active keys
                keys = sorted([
                    str(k) if isinstance(k, str) else k.name 
                    for k in bridge.pressed_keys
                ])
                display = ', '.join(keys) if keys else '(none)'
                print(f"\r  Keys: [{display:40s}] Packets: {bridge.packet_count}", 
                      end='', flush=True)
                
        except asyncio.CancelledError:
            pass
        finally:
            bridge.release_all()
        
        print(f"\n\n📊 Total packets: {bridge.packet_count}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Bridge stopped")
