from machine import Pin

import utime

class Led:
    FLASH_TIME_MS = 100 #[ms]
    BLINK_TIME_MS = 100 #[ms]

    def __init__(self, gpio_number: int):
        self.gpio_number = gpio_number
        self.pin = Pin(gpio_number, Pin.OUT)

    def is_on(self):
        return self.pin.value() == 1

    def on(self):
        print(f'Led \'{self.gpio_number}\' emitted.')
        self.pin.on()
        return self

    def off(self):
        self.pin.off()
        return self

    def flash(self, flash_time_ms: int = FLASH_TIME_MS):
        self.on()
        utime.sleep_ms(flash_time_ms)
        self.off()
        return self

    def blink(self, count: int = 5, blink_time_ms: int = BLINK_TIME_MS):
        for _ in range(count):
            self.on()
            utime.sleep_ms(blink_time_ms)
            self.off()
            utime.sleep_ms(blink_time_ms)
        return self
