"""Touchwheel SAO (from the 2024 Supercon badge), in any SAO port"""

import machine
import time

import lib.sao as sao

# 0x54 on the 2024 badge's wheels, 0x55 seen on others
TOUCHWHEEL_ADDRS = (0x54, 0x55)
# Also covers hot-plugging, and the wheel's startup animation, during which
# it doesn't answer on I2C
_RETRY_MS = 2000
_REG_LED0 = 18
_REG_VERSION = 27


def _reset_bus():
    """A bus wedged by timeouts stays wedged until it's recreated."""
    sao.i2c = machine.I2C(
        sao.SAO_I2C_BUS, scl=sao.SAO_I2C_SCL, sda=sao.SAO_I2C_SDA, freq=400_000
    )


class Touchwheel:
    def __init__(self) -> None:
        self.addr = None
        self.version = 1
        self._last_try = None

    @property
    def present(self) -> bool:
        return self.addr is not None

    def _available(self) -> bool:
        if self.addr is not None:
            return True
        now = time.ticks_ms()
        if self._last_try is not None and time.ticks_diff(now, self._last_try) < _RETRY_MS:
            return False
        self._last_try = now
        try:
            found = sao.i2c.scan()
        except OSError:
            _reset_bus()
            return False
        for addr in TOUCHWHEEL_ADDRS:
            if addr in found:
                try:
                    self.version = sao.i2c.readfrom_mem(addr, _REG_VERSION, 1)[0]
                except OSError:
                    _reset_bus()
                    return False
                self.addr = addr
                return True
        return False

    def _lost(self) -> None:
        self.addr = None
        _reset_bus()

    def rgb(self, r: int, g: int, b: int) -> None:
        """Set the center RGB LED, each 0-255. No-op if no wheel."""
        if not self._available():
            return
        try:
            sao.i2c.writeto_mem(self.addr, 15, bytes([r]))
            sao.i2c.writeto_mem(self.addr, 16, bytes([g]))
            sao.i2c.writeto_mem(self.addr, 17, bytes([b]))
        except OSError:
            self._lost()

    def rgbs(self, colors) -> None:
        """Set each of the 3 LEDs to its own (r, g, b). Firmware before v2
        gets colors[0] on all of them. No-op if no wheel."""
        if not self._available():
            return
        # v1 firmware doesn't bounds check, so writing reg 18+ trashes its RAM
        if self.version != 2:
            self.rgb(*colors[0])
            return
        try:
            sao.i2c.writeto_mem(self.addr, _REG_LED0, bytes(c for rgb in colors for c in rgb))
        except OSError:
            self._lost()

    def read(self) -> int | None:
        """0 for no touch, 1-255 clockwise from the south. None if no wheel."""
        if not self._available():
            return None
        try:
            return sao.i2c.readfrom_mem(self.addr, 0, 1)[0]
        except OSError:
            self._lost()
            return None


def color_wheel(pos: int) -> tuple[int, int, int]:
    """Rainbow color for pos 0-255"""
    pos &= 0xFF
    if pos < 85:
        return 255 - pos * 3, pos * 3, 0
    if pos < 170:
        pos -= 85
        return 0, 255 - pos * 3, pos * 3
    pos -= 170
    return pos * 3, 0, 255 - pos * 3


touchwheel = Touchwheel()
