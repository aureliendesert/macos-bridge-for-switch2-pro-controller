#!/usr/bin/env python3
"""
Switch 2 Pro Controller - Calibration Utility
==============================================

Use this to analyze raw controller data and calibrate button mappings.

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


INPUT_CHAR_UUID = "7492866c-ec3e-4619-8258-32755ffcc0f9"


class Calibrator:
    def __init__(self):
        self.packet_count = 0
        self.last_bytes = None
    
    def on_data(self, sender, data: bytes):
        self.packet_count += 1
        
        if len(data) < 11:
            return
        
        # Only display when data changes
        current = (data[2], data[3], data[4])
        if current != self.last_bytes:
            self.last_bytes = current
            
            # Show raw hex
            hex_str = ' '.join(f'{b:02x}' for b in data[:15])
            
            # Show button bytes in binary
            btn1_bin = f'{data[2]:08b}'
            btn2_bin = f'{data[3]:08b}'
            btn3_bin = f'{data[4]:08b}'
            
            # Parse sticks
            lx = data[5] | ((data[6] & 0x0F) << 8)
            ly = ((data[6] & 0xF0) >> 4) | (data[7] << 4)
            rx = data[8] | ((data[9] & 0x0F) << 8)
            ry = ((data[9] & 0xF0) >> 4) | (data[10] << 4)
            
            print(f"\n[{self.packet_count:5d}] RAW: {hex_str}")
            print(f"        BTN1: {btn1_bin} ({data[2]:3d}) | BTN2: {btn2_bin} ({data[3]:3d}) | BTN3: {btn3_bin} ({data[4]:3d})")
            print(f"        L:({lx:4d},{ly:4d}) R:({rx:4d},{ry:4d})")


async def find_controller(timeout: float = 5.0) -> str | None:
    """Scan for Switch 2 Pro Controller."""
    print(f"🔍 Scanning ({timeout}s)...")
    
    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
    
    for address, (device, adv) in devices.items():
        if adv.manufacturer_data:
            for company_id, data in adv.manufacturer_data.items():
                if b'\x7e\x05' in data or b'\x69\x20' in data:
                    print(f"   ✅ Found: {device.name}")
                    return address
    
    print("   ❌ Not found")
    return None


async def main():
    print("=" * 70)
    print("  Switch 2 Pro Controller - Calibration Mode")
    print("=" * 70)
    print("""
  This tool displays raw packet data to help calibrate button mappings.
  
  Button byte format:
    BTN1 (byte 2): B=0x01, A=0x02, Y=0x04, X=0x08, R=0x10, ZR=0x20, +=0x40, RS=0x80
    BTN2 (byte 3): ↓=0x01, →=0x02, ←=0x04, ↑=0x08, L=0x10, ZL=0x20, -=0x40, LS=0x80
    BTN3 (byte 4): HOME=0x01, ●=0x02, GR=0x04, GL=0x08, CAPT=0x10
  
  Stick format: 12-bit (0-4095), center ~2048
""")
    
    calibrator = Calibrator()
    
    address = await find_controller()
    if not address:
        return
    
    print("\n🔗 Connecting...")
    
    async with BleakClient(address, timeout=30.0) as client:
        print("   ✅ Connected!")
        print("\n" + "=" * 70)
        print("  Press buttons to see their bit patterns. Ctrl+C to exit.")
        print("=" * 70)
        
        await client.start_notify(INPUT_CHAR_UUID, calibrator.on_data)
        
        try:
            while client.is_connected:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
    
    print(f"\n\n📊 Total packets: {calibrator.packet_count}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped")
