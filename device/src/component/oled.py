from machine import I2C, Pin

import framebuf

from lib.ssd1306 import SSD1306_I2C

from component.misaki_font import MisakiFont
from util.runner import Runner

class Oled:
    WIDTH       = 128
    HEIGHT      = 64
    FONT_WIDTH  = 8
    FONT_HEIGHT = 8

    def __init__(self, scl_gpio_number: int, sda_gpio_number: int):
        self.scl_gpio_number = scl_gpio_number
        self.sda_gpio_number = sda_gpio_number
        self.scl_pin = Pin(scl_gpio_number)
        self.sda_pin = Pin(sda_gpio_number)
        self._oled = SSD1306_I2C(Oled.WIDTH, Oled.HEIGHT, I2C(0, scl = self.scl_pin, sda = self.sda_pin))
        self._font = MisakiFont()
        self._cursor_y = 0
        self.marquee_x = Oled.WIDTH
        self.clear()

    def write(self, text: str, x: int = 0, y: int = None, scale: int = 1):
        target_y = y if y is not None else self._cursor_y
        missing_font = self._font.font(0x25a1, flgz = False)
        for i, char in enumerate(text):
            char_x = x + (i * Oled.FONT_WIDTH * scale)
            glyph = self._font.font(ord(char), flgz = True)
            if glyph and glyph != missing_font:
                # カスタムフォント描画
                for row in range(Oled.FONT_HEIGHT):
                    for col in range(Oled.FONT_WIDTH):
                        if glyph[row] & (0x80 >> col):
                            self._oled.fill_rect(char_x + col * scale, target_y + row * scale, scale, scale, 1)
            else:
                # フレームバッファ経由の標準描画（フォールバック）
                tmp_fb = framebuf.FrameBuffer(bytearray(Oled.FONT_WIDTH * Oled.FONT_HEIGHT // 8), Oled.FONT_WIDTH, Oled.FONT_HEIGHT, framebuf.MONO_HLSB)
                tmp_fb.text(char, 0, 0)
                for px in range(Oled.FONT_WIDTH):
                    for py in range(Oled.FONT_HEIGHT):
                        if tmp_fb.pixel(px, py):
                            self._oled.fill_rect(char_x + px * scale, target_y + py * scale, scale, scale, 1)
        self._cursor_y = target_y + (Oled.FONT_HEIGHT * scale)
        return self

    def write_center(self, text: str, y: int = None, scale: int = 1):
        text_width = len(text) * Oled.FONT_WIDTH * scale
        x = Oled.WIDTH // 2 - text_width // 2
        return self.write(text, x, y, scale)

    def write_middle(self, text: str, scale: int = 1):
        y = Oled.HEIGHT // 2 - Oled.FONT_HEIGHT * scale // 2
        return self.write_center(text, y, scale)

    def emit(self):
        print(f'Oled \'{(self.scl_gpio_number, self.sda_gpio_number)}\' emitted.')
        self._oled.show()
        return self

    def clear(self):
        self._oled.fill(0)
        self._cursor_y = 0
        return self

    async def _noop():
        pass

    def marquee(self, text: str, scale = 1, on_marquee_end = _noop):
        async def coro():
            # TODO speedは引数で調節できてもいいかも
            speed = scale * 4
            self.clear().write(text, self.marquee_x, Oled.HEIGHT // 2 - Oled.FONT_HEIGHT * scale // 2, scale).emit()
            self.marquee_x -= speed
            if (self.marquee_x < -len(text) * Oled.FONT_WIDTH * scale):
                self.marquee_x = Oled.WIDTH
                await on_marquee_end()
        Runner(coro).loop()

    # TODO marqueeのキャンセル実装
