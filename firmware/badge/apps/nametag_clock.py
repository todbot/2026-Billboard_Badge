"""Nametag with an analog clock"""

import machine
import math
import time
from array import array

from apps.base_app import BaseApp
from lib.epd import display
from lib.led_bar import leds
from lib.touchwheel import color_wheel, touchwheel

_BACKGROUND = "/data/graphics/hello_i_am_clock.png"
# The plus sign on the background marks the hand pivot
_CX = 480
_CY = 390
_UPDATE_MINS = 5
# 14 scanner steps per bounce, so about one rainbow per bounce
_HUE_STEP = 18
_SAVED_TIME = "/data/clock_time"
# An unset RTC reads 2000-01-01
_RTC_SET_YEAR = 2025


def _rtc_is_set():
    return time.localtime()[0] >= _RTC_SET_YEAR


def _save_time():
    with open(_SAVED_TIME, "w") as f:
        f.write(str(time.time()))


def _restore_time():
    """Set an unset RTC from the last saved time. It'll be behind by
    however long the badge was off."""
    if _rtc_is_set():
        return
    try:
        with open(_SAVED_TIME) as f:
            t = time.localtime(int(f.read()))
    except (OSError, ValueError):
        return
    machine.RTC().datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))


_restore_time()


def _hand(angle, length, base_w, tip_w, tail):
    """Tapered bar pointing at angle (radians, clockwise from 12).
    Returns the outline and the tip's center, for a round cap."""
    s, c = math.sin(angle), math.cos(angle)
    tip_x, tip_y = s * length, -c * length
    tail_x, tail_y = -s * tail, c * tail
    coords = array("h", [
        int(tail_x + c * base_w), int(tail_y + s * base_w),
        int(tip_x + c * tip_w), int(tip_y + s * tip_w),
        int(tip_x - c * tip_w), int(tip_y - s * tip_w),
        int(tail_x - c * base_w), int(tail_y - s * base_w),
    ])
    return coords, int(tip_x), int(tip_y), tip_w


def draw_clock(hour, minute):
    display.draw_png(_BACKGROUND)
    hands = (
        (math.radians((hour % 12) * 30 + minute * 0.5), 70, 11, 7, 12),
        (math.radians(minute * 6), 105, 8, 5, 16),
    )
    # A pixel set in both framebuffers is ambiguous, so clear red under black
    inks = ((display.red, 0), (display.black, 1))
    for angle, length, base_w, tip_w, tail in hands:
        coords, tx, ty, r = _hand(angle, length, base_w, tip_w, tail)
        for fb, c in inks:
            fb.poly(_CX, _CY, coords, c, True)
            fb.ellipse(_CX + tx, _CY + ty, r, r, c, True)
    for fb, c in inks:
        fb.ellipse(_CX, _CY, 14, 14, c, True)


class NametagClockApp(BaseApp):
    def __init__(self, name: str | None = None) -> None:
        self.name = "Nametag Clock"
        self.sleep_ms = 100
        self.launched = False
        self.last_time = time.ticks_ms()
        self.ledi = 0
        self.led_dir = 1
        self.hue = 0
        self.shown = None
        self.saved_minute = None

    def _slot(self):
        t = time.localtime()
        return t[3], t[4] - t[4] % _UPDATE_MINS

    def run(self):
        if self.launched:
            self.shown = None

        # display.update() is dropped if a refresh is still running
        slot = self._slot()
        if slot != self.shown and display.is_done_updating():
            self.shown = slot
            draw_clock(*slot)
            display.update()

        minute = time.time() // 60
        if minute != self.saved_minute and _rtc_is_set():
            self.saved_minute = minute
            _save_time()

        now = time.ticks_ms()
        fade_by_fl = 0.70
        for i in range(8):
            leds[i] = [max(int(c * fade_by_fl), 0) for c in leds[i]]

        if now - self.last_time > 100:
            self.last_time = now
            self.ledi += self.led_dir
            if self.ledi in (0, 7):
                self.led_dir = -self.led_dir
            leds[self.ledi] = (7, 0, 15)
            leds.write()
            self.hue = (self.hue + _HUE_STEP) % 256
            touchwheel.rgbs([color_wheel(self.hue + n * 85) for n in range(3)])
