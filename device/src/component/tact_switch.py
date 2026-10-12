from machine import Pin

import asyncio

from util.runner import Runner

class TactSwitch:
    OFF_VALUE = 1
    ON_VALUE  = 0

    def __init__(self, gpio_number: int):
        self.gpio_number = gpio_number
        self.pin = Pin(gpio_number, Pin.IN, Pin.PULL_UP)
        self._callback = None
        Runner(self._task).loop()

    def on_push(self, callback):
        self._callback = callback
        return self

    def is_pushing(self):
        return self.pin.value() == TactSwitch.ON_VALUE

    async def _task(self):
        if self.pin.value() == TactSwitch.ON_VALUE:
            print(f'TactSwitch \'{self.gpio_number}\' pushed.')
            if self._callback:
                self._callback()
        while self.pin.value() == TactSwitch.ON_VALUE:
            await asyncio.sleep_ms(1)
