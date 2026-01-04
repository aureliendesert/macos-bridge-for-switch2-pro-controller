#!/usr/bin/env python3
"""
Switch 2 Pro Controller - macOS BLE Driver
===========================================

The first working Bluetooth driver for Nintendo Switch 2 Pro Controller on macOS.

This driver connects via Bluetooth Low Energy using bleak, bypassing macOS's
inability to pair with the controller through normal Bluetooth.

Author: Aurélien Desert
Date: January 2026
License: MIT
"""

import asyncio
import sys
from dataclasses import dataclass
from typing import Optional, Callable

try:
    from bleak import BleakClient, BleakScanner
    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData
except ImportError:
    print("❌ Error: bleak library not installed")
    print("   Run: pip install bleak")
    sys.exit(1)


# BLE Characteristics
INPUT_CHAR_UUID = "7492866c-ec3e-4619-8258-32755ffcc0f9"  # Notifications (input reports)
OUTPUT_CHAR_UUID = "7492866c-ec3e-4619-8258-32755ffcc0f8"  # Write (LED, rumble)

# Nintendo Vendor ID
NINTENDO_VID = 0x057E
SWITCH2_PRO_PID = 0x2069


@dataclass
class ControllerState:
    """Represents the current state of the controller."""
    # Face buttons
    a: bool = False
    b: bool = False
    x: bool = False
    y: bool = False
    
    # Shoulder buttons
    l: bool = False
    r: bool = False
    zl: bool = False
    zr: bool = False
    
    # System buttons
    plus: bool = False
    minus: bool = False
    home: bool = False
    capture: bool = False
    
    # Stick clicks
    ls: bool = False
    rs: bool = False
    
    # Grip buttons (Switch 2 exclusive)
    gl: bool = False
    gr: bool = False
    
    # D-pad
    dpad_up: bool = False
    dpad_down: bool = False
    dpad_left: bool = False
    dpad_right: bool = False
    
    # Analog sticks (normalized -1.0 to 1.0)
    left_stick_x: float = 0.0
    left_stick_y: float = 0.0
    right_stick_x: float = 0.0
    right_stick_y: float = 0.0
    
    # Raw stick values (0-4095, center ~2048)
    left_stick_x_raw: int = 2048
    left_stick_y_raw: int = 2048
    right_stick_x_raw: int = 2048
    right_stick_y_raw: int = 2048


class Switch2ProController:
    """
    Driver for Nintendo Switch 2 Pro Controller on macOS.
    
    Usage:
        controller = Switch2ProController()
        await controller.connect()
        
        # Option 1: Poll state
        while controller.is_connected:
            state = controller.state
            print(f"A: {state.a}, Left stick: ({state.left_stick_x}, {state.left_stick_y})")
            await asyncio.sleep(0.016)
        
        # Option 2: Use callback
        def on_input(state: ControllerState):
            if state.a:
                print("A pressed!")
        
        controller.on_state_change = on_input
    """
    
    def __init__(self):
        self.state = ControllerState()
        self.is_connected = False
        self.packet_count = 0
        self._client: Optional[BleakClient] = None
        self._address: Optional[str] = None
        self.on_state_change: Optional[Callable[[ControllerState], None]] = None
    
    async def scan(self, timeout: float = 5.0) -> Optional[str]:
        """
        Scan for Switch 2 Pro Controller.
        
        Returns:
            BLE address if found, None otherwise.
        """
        print(f"🔍 Scanning for Switch 2 Pro Controller ({timeout}s)...")
        
        found_address = None
        found_name = None
        
        devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
        
        for address, (device, adv_data) in devices.items():
            if self._is_switch2_controller(adv_data):
                found_address = address
                found_name = device.name or "Unknown"
                break
        
        if found_address:
            print(f"   ✅ Found: {found_name} ({found_address})")
            self._address = found_address
        else:
            print("   ❌ Controller not found")
            print("\n   Make sure:")
            print("   • Controller is turned on (LED blinking)")
            print("   • Controller is not connected to a Switch")
            print("   • Controller is in range")
        
        return found_address
    
    def _is_switch2_controller(self, adv_data: AdvertisementData) -> bool:
        """Check if advertisement data matches Switch 2 Pro Controller."""
        if not adv_data.manufacturer_data:
            return False
        
        for company_id, data in adv_data.manufacturer_data.items():
            # Nintendo company ID is 0x057E (1406)
            # Check for Nintendo identifiers in manufacturer data
            if b'\x7e\x05' in data or b'\x69\x20' in data:
                return True
            if company_id == NINTENDO_VID:
                return True
        
        return False
    
    async def connect(self, address: Optional[str] = None, timeout: float = 30.0) -> bool:
        """
        Connect to the controller.
        
        Args:
            address: BLE address. If None, will scan for controller.
            timeout: Connection timeout in seconds.
        
        Returns:
            True if connected successfully.
        """
        if address is None:
            address = await self.scan()
            if address is None:
                return False
        
        print(f"\n🔗 Connecting...")
        
        try:
            self._client = BleakClient(address, timeout=timeout)
            await self._client.connect()
            
            if not self._client.is_connected:
                print("   ❌ Connection failed")
                return False
            
            # Subscribe to input notifications
            await self._client.start_notify(INPUT_CHAR_UUID, self._on_data)
            
            self.is_connected = True
            print("   ✅ Connected!")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the controller."""
        if self._client and self._client.is_connected:
            await self._client.stop_notify(INPUT_CHAR_UUID)
            await self._client.disconnect()
        
        self.is_connected = False
        print("🔌 Disconnected")
    
    def _on_data(self, sender, data: bytes):
        """Handle incoming data from controller."""
        self.packet_count += 1
        
        if len(data) < 11:
            return
        
        # Parse button bytes
        btn1, btn2, btn3 = data[2], data[3], data[4]
        
        # Byte 2: B, A, Y, X, R, ZR, +, RS
        self.state.b = bool(btn1 & 0x01)
        self.state.a = bool(btn1 & 0x02)
        self.state.y = bool(btn1 & 0x04)
        self.state.x = bool(btn1 & 0x08)
        self.state.r = bool(btn1 & 0x10)
        self.state.zr = bool(btn1 & 0x20)
        self.state.plus = bool(btn1 & 0x40)
        self.state.rs = bool(btn1 & 0x80)
        
        # Byte 3: ↓, →, ←, ↑, L, ZL, -, LS
        self.state.dpad_down = bool(btn2 & 0x01)
        self.state.dpad_right = bool(btn2 & 0x02)
        self.state.dpad_left = bool(btn2 & 0x04)
        self.state.dpad_up = bool(btn2 & 0x08)
        self.state.l = bool(btn2 & 0x10)
        self.state.zl = bool(btn2 & 0x20)
        self.state.minus = bool(btn2 & 0x40)
        self.state.ls = bool(btn2 & 0x80)
        
        # Byte 4: HOME, ●, GR, GL, CAPT
        self.state.home = bool(btn3 & 0x01)
        self.state.gr = bool(btn3 & 0x04)
        self.state.gl = bool(btn3 & 0x08)
        self.state.capture = bool(btn3 & 0x10)
        
        # Parse analog sticks (12-bit values packed in 3 bytes each)
        # Left stick
        lx_raw = data[5] | ((data[6] & 0x0F) << 8)
        ly_raw = ((data[6] & 0xF0) >> 4) | (data[7] << 4)
        
        # Right stick
        rx_raw = data[8] | ((data[9] & 0x0F) << 8)
        ry_raw = ((data[9] & 0xF0) >> 4) | (data[10] << 4)
        
        # Store raw values
        self.state.left_stick_x_raw = lx_raw
        self.state.left_stick_y_raw = ly_raw
        self.state.right_stick_x_raw = rx_raw
        self.state.right_stick_y_raw = ry_raw
        
        # Normalize to -1.0 to 1.0 (center is ~2048)
        self.state.left_stick_x = (lx_raw - 2048) / 2048.0
        self.state.left_stick_y = (ly_raw - 2048) / 2048.0
        self.state.right_stick_x = (rx_raw - 2048) / 2048.0
        self.state.right_stick_y = (ry_raw - 2048) / 2048.0
        
        # Call user callback if set
        if self.on_state_change:
            self.on_state_change(self.state)
    
    def get_pressed_buttons(self) -> list[str]:
        """Return list of currently pressed button names."""
        buttons = []
        s = self.state
        
        if s.a: buttons.append('A')
        if s.b: buttons.append('B')
        if s.x: buttons.append('X')
        if s.y: buttons.append('Y')
        if s.l: buttons.append('L')
        if s.r: buttons.append('R')
        if s.zl: buttons.append('ZL')
        if s.zr: buttons.append('ZR')
        if s.plus: buttons.append('+')
        if s.minus: buttons.append('-')
        if s.home: buttons.append('HOME')
        if s.capture: buttons.append('CAPT')
        if s.ls: buttons.append('LS')
        if s.rs: buttons.append('RS')
        if s.gl: buttons.append('GL')
        if s.gr: buttons.append('GR')
        if s.dpad_up: buttons.append('↑')
        if s.dpad_down: buttons.append('↓')
        if s.dpad_left: buttons.append('←')
        if s.dpad_right: buttons.append('→')
        
        return buttons


async def main():
    """Demo: Display controller inputs in real-time."""
    print("=" * 65)
    print("  🎮 Switch 2 Pro Controller - macOS Driver")
    print("  First working BLE driver for macOS!")
    print("=" * 65)
    
    controller = Switch2ProController()
    
    if not await controller.connect():
        return
    
    print("\n" + "=" * 65)
    print("  Press Ctrl+C to exit")
    print("=" * 65 + "\n")
    
    last_display = ""
    
    try:
        while controller.is_connected:
            await asyncio.sleep(0.05)
            
            # Build display string
            buttons = controller.get_pressed_buttons()
            btn_str = ','.join(buttons) if buttons else '-'
            
            s = controller.state
            lx = int(s.left_stick_x * 100)
            ly = int(s.left_stick_y * 100)
            rx = int(s.right_stick_x * 100)
            ry = int(s.right_stick_y * 100)
            
            display = (
                f"BTN:[{btn_str:20s}] "
                f"L:({lx:+4d},{ly:+4d}) "
                f"R:({rx:+4d},{ry:+4d}) "
                f"[{controller.packet_count} pkts]"
            )
            
            if display != last_display:
                print(f"\r{display}", end='', flush=True)
                last_display = display
                
    except asyncio.CancelledError:
        pass
    finally:
        await controller.disconnect()
    
    print(f"\n\n📊 Total packets received: {controller.packet_count}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped")
