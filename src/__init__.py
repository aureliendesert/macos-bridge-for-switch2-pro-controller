"""
Switch 2 Pro Controller - macOS Driver
=======================================

The first working Bluetooth driver for Nintendo Switch 2 Pro Controller on macOS.

Usage:
    from switch2_mac_driver import Switch2ProController
    
    controller = Switch2ProController()
    await controller.connect()
    
    while controller.is_connected:
        state = controller.state
        print(f"A: {state.a}, Left stick: ({state.left_stick_x}, {state.left_stick_y})")
        await asyncio.sleep(0.016)

Author: Aurélien Desert
Date: January 2026
License: MIT
"""

from .client import Switch2ProController, ControllerState

__version__ = "1.0.0"
__author__ = "Aurélien Desert"
__all__ = ["Switch2ProController", "ControllerState"]
