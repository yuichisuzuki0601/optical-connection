# Optical Connection

Optical Connection sends a short text message from a phone screen to a Seeed Studio XIAO ESP32C3. The sender displays a timed black-and-white pattern; a phototransistor on the device detects it, and a 128 x 64 OLED displays the decoded message. The device runs MicroPython, while the sender is a small web app served by Node.js.

## What you need

- A Seeed Studio XIAO ESP32C3 running MicroPython
- A phototransistor, a 128 x 64 SSD1306 I2C OLED, and a push button
- A phone and a computer on the same local network
- Node.js and npm on the computer
- `just` and `mpremote` for the commands below; `esptool` is needed only to flash firmware

The provided `just sender-start` recipe uses macOS commands (`ifconfig en0` and `open`). The sender itself runs anywhere Node.js is available.

## Hardware connections

The current device code uses these **GPIO numbers**, not the XIAO's `D` numbers:

| Component | XIAO ESP32C3 pin | GPIO | Behavior |
| --- | --- | ---: | --- |
| Phototransistor signal | D8 | 8 | Active low; the input uses the internal pull-up |
| Push button | D7 | 20 | Connects the input to GND when pressed |
| OLED SCL | D6 | 21 | I2C clock |
| OLED SDA | D5 | 7 | I2C data |

Connect the OLED and sensor power according to their own module specifications. The firmware configures the OLED as I2C bus 0 and expects a 128 x 64 SSD1306 display. For battery operation, the XIAO ESP32C3 has separate battery pads on its back; consult the [Seeed Studio battery wiring guide](https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/#battery-usage) before connecting a cell.

## Quick start

Run these commands from the repository root unless a step says otherwise.

1. Connect the XIAO ESP32C3 by USB. If it does not already have MicroPython, flash the bundled firmware:

   ```sh
   just firmware-flash-esp32c3
   ```

   Flashing replaces the firmware currently on the board. The recipe selects the first matching `/dev/cu.usb*` port.

2. Install the OLED library once for a fresh checkout and board:

   ```sh
   just device-install-lib
   ```

   This installs `ssd1306` through `mpremote` and copies it into `device/src/lib/` so subsequent uploads include it. That local directory is ignored by Git.

3. Upload the device code and start the receiver:

   ```sh
   just device-start
   ```

   The command copies `device/src/` to the board, runs `main.py`, and saves serial output to `device/.log`. Leave it running while testing. Once uploaded, `main.py` also starts when the board boots on its own.

4. In another terminal, start the sender:

   ```sh
   just sender-start
   ```

   On macOS, this opens `http://<en0 IPv4 address>:3000` and then starts the server. If the browser opens before the server is ready, reload the page. Open the same URL on a phone connected to the same local network.

If you are not using `just`, start the sender with:

```sh
cd sender
npm run start
```

Then open `http://localhost:3000` on the computer or `http://<computer LAN IPv4 address>:3000` on the phone. The server uses port 3000 by default; set `PORT` to change it when starting through npm directly. The sender has no third-party npm dependencies.

## Send a message

1. Place the phone's circular display area against the phototransistor. Keep the phone awake and its position steady.
2. Enter a message and tap **Send**. The sender waits 0.5 seconds, shows a three-second countdown, and holds the display dark for two seconds before transmission.
3. During transmission, the phone shows `SENDING...` with an estimated time remaining. The OLED changes from `HELLO` to `RECEIVING...` after it recognizes the start marker, then displays the decoded text when the complete frame passes validation.

The OLED shows up to eight lines of 16 characters. Pressing the device button replaces the current display with `CLEAR`.

**Connection Check** alternates white and black every 500 ms for ten cycles after the same preparation sequence. It is useful for checking whether the phototransistor responds; it does not confirm that a message was decoded. Likewise, `Done` on the phone means the display sequence finished, not that the device acknowledged receipt.

## How the transfer works

The sender converts the input to UTF-8 bytes and constructs this frame:

```text
start marker | payload length (2 bytes) | payload | CRC-16 (2 bytes) | end marker
```

The start marker is six alternating light/dark slots; the end marker is six alternating dark/light slots. The length, payload, and CRC bytes are Manchester encoded (`0` = light/dark, `1` = dark/light). Each light or dark slot currently lasts 70 ms, approximately 1.43 times faster than the original 100 ms setting. The CRC uses polynomial `0x1021` and an initial value of `0xffff`.

The receiver samples the phototransistor, reconstructs the slots from observed light and dark durations, validates the markers and CRC, and decodes the payload as UTF-8. Its timing correction is tuned from measurements on the current hardware. If you change the slot duration in `sender/app.js` (`HALF_BIT_MS`), update `OpticalReceiver.HALF_BIT_MS` in `device/src/protocol/optical_receiver.py` as well.

## Troubleshooting

- **The phone page does not load:** Make sure the server is running, the phone and computer are on the same LAN, and you are using the computer's LAN IPv4 address. The `just` recipe assumes the Mac's network interface is `en0`.
- **The sensor does not change state:** Check its power, polarity, connection to GPIO8, and alignment with the phone. The input is active low: `light` means the GPIO reads `0`.
- **The OLED stays on `HELLO` or `RECEIVING...`:** Inspect `device/.log` for phototransistor transitions, start-marker detection, frame errors, and decoded messages. Keep the phone aligned and avoid changing brightness during a transfer.
- **The board is not found:** Check the USB cable and serial port. The `just` recipes use `mpremote`'s automatic device selection; run `mpremote connect <port> ls` to test a specific port.

## Repository layout

| Path | Purpose |
| --- | --- |
| `sender/` | Web interface and Node.js HTTP server |
| `device/src/main.py` | OLED state and receiver callbacks |
| `device/src/protocol/optical_receiver.py` | Sampling, frame decoding, and validation |
| `device/src/component/` | Hardware components |
| `device/firmware/` | MicroPython firmware files and source links |
| `justfile` | Development and device commands (`just --list`) |
