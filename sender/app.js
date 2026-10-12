// まずは受信タイミングに余裕を持たせる。実験が安定したら短くする。
const HALF_BIT_MS = 100;
const COUNTDOWN_SECONDS = 3;
const UI_SETTLE_MS = 500;
const TRANSMISSION_GUARD_MS = 2000;
const CALIBRATION_INTERVAL_MS = 500;
const CALIBRATION_CYCLES = 10;

const messageInput = document.querySelector('#message');
const clearButton = document.querySelector('#clear');
const sendButton = document.querySelector('#send');
const calibrateButton = document.querySelector('#calibrate');
const status = document.querySelector('#status');
const byteCount = document.querySelector('#byte-count');
const lightArea = document.querySelector('#light-area');

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

function utf8Bytes(value) {
  return new TextEncoder().encode(value);
}

function crc16(bytes) {
  let crc = 0xffff;
  for (const byte of bytes) {
    crc ^= byte << 8;
    for (let bit = 0; bit < 8; bit += 1) {
      crc = (crc & 0x8000) ? ((crc << 1) ^ 0x1021) & 0xffff : (crc << 1) & 0xffff;
    }
  }
  return crc;
}

function bytesToBits(bytes) {
  return bytes.flatMap((byte) => {
    const bits = [];
    for (let bit = 7; bit >= 0; bit -= 1) bits.push((byte >> bit) & 1);
    return bits;
  });
}

function manchester(bits) {
  return bits.flatMap((bit) => (bit === 0 ? [1, 0] : [0, 1]));
}

function makeFrame(text) {
  const payload = Array.from(utf8Bytes(text));
  const body = [payload.length >> 8, payload.length & 0xff, ...payload];
  const checksum = crc16(body);
  const data = [...body, checksum >> 8, checksum & 0xff];
  const startMarker = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0];
  const endMarker = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1];
  return [...startMarker, ...manchester(bytesToBits(data)), ...endMarker];
}

function setLight(level) {
  lightArea.classList.toggle('is-light', level === 1);
  lightArea.classList.toggle('is-dim', level === 0);
}

function updateByteCount() {
  byteCount.textContent = `UTF-8: ${utf8Bytes(messageInput.value).length} bytes`;
}

async function countdown() {
  for (let seconds = COUNTDOWN_SECONDS; seconds > 0; seconds -= 1) {
    status.textContent = `${seconds}`;
    await sleep(1000);
  }
}

async function settleTransmissionUi() {
  setLight(0);
  status.textContent = 'Align the screen';
  await sleep(UI_SETTLE_MS);
}

async function guardTransmissionStart() {
  setLight(0);
  status.textContent = 'Keep the screen still';
  await sleep(TRANSMISSION_GUARD_MS);
}

async function transmit(text) {
  const frame = makeFrame(text);
  let shownSeconds = null;
  for (let index = 0; index < frame.length; index += 1) {
    const remainingSeconds = Math.ceil((frame.length - index) * HALF_BIT_MS / 1000);
    if (remainingSeconds !== shownSeconds) {
      status.textContent = `SENDING... ${remainingSeconds}s left`;
      shownSeconds = remainingSeconds;
    }
    setLight(frame[index]);
    await sleep(HALF_BIT_MS);
  }
  setLight(0);
}

async function calibrate() {
  for (let cycle = 0; cycle < CALIBRATION_CYCLES; cycle += 1) {
    setLight(1);
    await sleep(CALIBRATION_INTERVAL_MS);
    setLight(0);
    await sleep(CALIBRATION_INTERVAL_MS);
  }
}

function setControlsDisabled(disabled) {
  sendButton.disabled = disabled;
  calibrateButton.disabled = disabled;
  clearButton.disabled = disabled;
  messageInput.disabled = disabled;
  lightArea.classList.toggle('is-guide', !disabled);
}

clearButton.addEventListener('click', () => {
  messageInput.value = '';
  updateByteCount();
  messageInput.focus();
});

messageInput.addEventListener('input', updateByteCount);

sendButton.addEventListener('click', async () => {
  const text = messageInput.value;
  messageInput.blur();
  setControlsDisabled(true);
  try {
    await settleTransmissionUi();
    await countdown();
    await guardTransmissionStart();
    await transmit(text);
    status.textContent = 'Done';
  } finally {
    setLight(0);
    setControlsDisabled(false);
  }
});

calibrateButton.addEventListener('click', async () => {
  messageInput.blur();
  setControlsDisabled(true);
  try {
    await settleTransmissionUi();
    await countdown();
    await guardTransmissionStart();
    status.textContent = 'Testing';
    await calibrate();
    status.textContent = 'Done';
  } finally {
    setLight(0);
    setControlsDisabled(false);
  }
});

updateByteCount();
setLight(0);
lightArea.classList.add('is-guide');
