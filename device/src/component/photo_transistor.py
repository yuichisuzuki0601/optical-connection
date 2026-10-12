from machine import Pin

from util.runner import Runner

class PhotoTransistor:
    OFF_VALUE = 1
    ON_VALUE  = 0

    def __init__(self, gpio_number: int):
        self.gpio_number = gpio_number
        self.pin = Pin(gpio_number, Pin.IN, Pin.PULL_UP)
        self._callback = None
        self._last_value = self.pin.value()
        Runner(self._task).loop()

    def on_change(self, callback):
        self._callback = callback
        return self

    def is_light(self):
        return self.pin.value() == PhotoTransistor.ON_VALUE

    async def _task(self):
        value = self.pin.value()
        if value != self._last_value:
            self._last_value = value
            if value == PhotoTransistor.ON_VALUE:
                print(f"PhotoTransistor '{self.gpio_number}' light.")
                if self._callback:
                    self._callback('light')
            else:
                print(f"PhotoTransistor '{self.gpio_number}' dark.")
                if self._callback:
                    self._callback('dark')
