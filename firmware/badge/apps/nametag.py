"""Nametag app"""

import lvgl
import time

from apps.base_app import BaseApp
from lib.button import MenuMinus, MenuPlus, UserA, UserB, Boot
from lib.epd import display, display_height
from lib.led_bar import leds
from lib.sao import SAO2

_WHITE = lvgl.color_hex(0xFFFFFF)
_RED = lvgl.color_hex(0xFF0000)
_BLACK = lvgl.color_hex(0x000000)
_FONT = lvgl.font_montserrat_48
# White name band on hello_i_am_blank.png. Center the plate there.
_NAME_TOP = 221
_NAME_BOTTOM = 557
_NAME_DY = (_NAME_TOP + _NAME_BOTTOM) // 2 - display_height // 2

# def touchwheel_rgb(bus, r, g, b):
#     """RGB color on the central display.  Each 0-255"""
#     bus.writeto_mem(84, 15, bytes([r]))
#     bus.writeto_mem(84, 16, bytes([g]))
#     bus.writeto_mem(84, 17, bytes([b]))
            


class NametagApp(BaseApp):
    def __init__(self, name: str | None = None) -> None:
        self.name = "Nametag"
        self.sleep_ms = 100
        self.launched = False
        #self.updatetime = 1
        self.last_time = time.ticks_ms()
        self.ledi = 0
        self.led_dir = 1

    def run(self):
        if self.launched:
            leds.fill((0,1,1))
            display.draw_png("/data/graphics/hello_i_am_blank.png")

            scr = lvgl.obj()
            scr.remove_style_all()
            scr.set_size(lvgl.pct(100), lvgl.pct(100))
            scr.set_style_bg_opa(lvgl.OPA.TRANSP, 0)

            plate = lvgl.obj(scr)
            plate.remove_style_all()
            plate.set_size(lvgl.SIZE_CONTENT, lvgl.SIZE_CONTENT)
            plate.align(lvgl.ALIGN.CENTER, 0, _NAME_DY)
            plate.set_flex_flow(lvgl.FLEX_FLOW.COLUMN)
            plate.set_flex_align(
                lvgl.FLEX_ALIGN.CENTER,
                lvgl.FLEX_ALIGN.CENTER,
                lvgl.FLEX_ALIGN.CENTER,
            )
            plate.set_style_bg_color(_WHITE, 0)
            plate.set_style_bg_opa(lvgl.OPA.COVER, 0)
            plate.set_style_pad_all(8, 0)

            hello = lvgl.label(plate)
            hello.set_text("")
            hello.set_style_text_color(_BLACK, 0)
            hello.set_style_text_font(_FONT, 0)

            world = lvgl.label(plate)
            world.set_text("")
            world.set_style_text_color(_BLACK, 0)
            world.set_style_text_font(_FONT, 0)

            lvgl.screen_load(scr)
            scr.update_layout()
            # screen_load dirties the whole panel. Keep the PNG everywhere else.
            display.lv_display.inv_p = 0
            plate.invalidate()
            lvgl.refr_now(display.lv_display)
            display.update()
            leds.fill((0,1,0))

            #touchwheel_rgb(SAO2, 33,0,33)

        else:
            now = time.ticks_ms()
            fade_by = 6
            fade_by_fl = 0.70
            for i in range(8):
                #leds[i] = [max(c - fade_by, 0) for c in leds[i]]
                leds[i] = [max(int(c * fade_by_fl), 0) for c in leds[i]]
            #leds[:] = [[min(max(i+fade_by,0),255) for i in l] for l in leds] # dim all by fade_by

            if now - self.last_time > 100:
                self.last_time = now
                self.ledi += self.led_dir
                if self.ledi in (0, 7):
                    self.led_dir = -self.led_dir
                leds[self.ledi] = (7, 0, 15)
                leds.write()
                #print("hi", self.ledi)
            


