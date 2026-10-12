DEVICE_DIR := 'device'
SENDER_DIR := 'sender'
USB_PORT   := `ls /dev/cu.usb* /dev/cu.SLAB_USBtoUART 2>/dev/null | head -n 1`

_default:
    @just --list --unsorted

# esp32のファームウェアを削除します
[group('firmware')]
firmware-nuke-esp32:
    #!/bin/sh
    esptool --port {{ USB_PORT }} erase-flash

# XIAO ESP32C3へファームウェアを書き込みます
[group('firmware')]
firmware-flash-esp32c3:
    #!/bin/sh
    esptool --chip esp32c3 --port {{ USB_PORT }} --baud 460800 --before default-reset --after hard-reset write-flash --flash-mode dio --flash-size detect --flash-freq 80m 0x0 {{ DEVICE_DIR }}/firmware/SEEED_XIAO_ESP32C3-20260824-v1.29.0.bin

# esp32c6へファームウェアを書き込みます
[group('firmware')]
firmware-flash-esp32c6:
    #!/bin/sh
    esptool --chip esp32c6 --port {{ USB_PORT }} --baud 460800 --before default-reset --after hard-reset write-flash --flash-mode dio --flash-size detect --flash-freq 80m 0x0 {{ DEVICE_DIR }}/firmware/ESP32C6_MicroPython.bin

# device開発用に必要なstubをインストールします
[group('device')]
device-install-stub:
    #!/bin/sh
    rm -rf {{ DEVICE_DIR }}/.stub/micropython/esp32
    python3 -m pip install --target {{ DEVICE_DIR }}/.stub/micropython/esp32 micropython-stdlib-stubs micropython-esp32-stubs

# device開発に必要なライブラリをインストールします
[group('device')]
device-install-lib:
    #!/bin/sh
    set -e
    cd {{ DEVICE_DIR }}
    mpremote mip --no-mpy install ssd1306
    mpremote cp -r :lib ./src

# deviceのファイルを一覧します
[group('device')]
device-ls dir=':':
    #!/bin/sh
    mpremote ls {{ dir }}

# deviceから全てのファイルを削除します
[group('device')]
device-delete-all:
    #!/bin/sh
    mpremote rm -r :

# deviceにソースを適用してプログラムを実行します
[group('device')]
device-start:
    #!/bin/sh
    mpremote cp -r {{ DEVICE_DIR }}/src/. :.
    mpremote exec --no-follow 'import main' repl | tee {{ DEVICE_DIR }}/.log

# senderを実行します
[group('sender')]
sender-start:
    #!/bin/sh
    cd {{ SENDER_DIR }}
    open "http://$(ifconfig en0 | awk '$1 == "inet" { print $2; exit }'):3000"
    npm run start
