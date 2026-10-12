import asyncio

from component.oled import Oled
from component.photo_transistor import PhotoTransistor
from component.tact_switch import TactSwitch
from protocol.optical_receiver import OpticalReceiver

tact_switch = TactSwitch(20)
photo_transistor = PhotoTransistor(8)
oled = Oled(21, 7).write_middle('HELLO').emit()

def handle_tact_switch_push():
    oled.clear().write_middle('CLEAR').emit()

def handle_start_marker():
    oled.clear().write_middle('RECEIVING...').emit()

def handle_received_message(message):
    characters_per_line = Oled.WIDTH // Oled.FONT_WIDTH
    maximum_lines = Oled.HEIGHT // Oled.FONT_HEIGHT
    lines = [
        message[index:index + characters_per_line]
        for index in range(0, len(message), characters_per_line)
    ][:maximum_lines]

    oled.clear()
    first_line_y = (Oled.HEIGHT - len(lines) * Oled.FONT_HEIGHT) // 2
    for index, line in enumerate(lines):
        oled.write_center(line, y=first_line_y + index * Oled.FONT_HEIGHT)
    oled.emit()

tact_switch.on_push(handle_tact_switch_push)
receiver = (OpticalReceiver(photo_transistor)
    .on_start_marker(handle_start_marker)
    .on_message(handle_received_message))

print('optical-connection-receiver start.')
try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    pass
finally:
    oled.clear().emit()
    print('optical-connection-receiver end.')
