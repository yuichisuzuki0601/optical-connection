# AI-maintained protocol implementation.
# Do not edit manually. Tune this file from observed hardware logs and tests.

import utime

from util.runner import Runner

class OpticalReceiver:
    """PhotoTransistorの明暗の継続時間から実験用フレームを復元する。"""

    HALF_BIT_MS = 70
    # 現在の実機ログでは100ms送信時に明が約130〜150ms、暗が約60〜90ms。
    # 明暗の切り替わりに生じる偏りを補正してから区間数へ丸める。
    LIGHT_DURATION_BIAS_MS = 40
    DARK_DURATION_BIAS_MS = -30
    SAMPLE_INTERVAL_MS = 1
    # 送信前の画面は3秒以上暗い。短い暗転からの明転は位置合わせやノイズとして無視する。
    MIN_IDLE_DARK_MS = 500
    FRAME_IDLE_TIMEOUT_MS = 1500
    MAX_PAYLOAD_BYTES = 512
    START_MARKER = (1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0)
    END_MARKER = (0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1)

    def __init__(self, photo_transistor):
        self.photo_transistor = photo_transistor
        self.photo_transistor.on_change(self._handle_photo_transistor_change)
        self._start_marker_callback = None
        self._callback = None
        self._failure_callback = None
        self._last_level = 1 if photo_transistor.is_light() else 0
        self._receiving = False
        self._current_level = self._last_level
        self._run_started_at = None
        self._last_transition_at = utime.ticks_ms()
        self._levels = []
        self._run_debug_count = 0
        self._start_marker_consumed = None
        self._payload_length = None
        self._expected_level_count = None
        Runner(self._task).loop(wait_ms=self.SAMPLE_INTERVAL_MS)

    @staticmethod
    def _handle_photo_transistor_change(state):
        if state == 'light':
            print('PhotoTransistor light event.')
        elif state == 'dark':
            print('PhotoTransistor dark event.')

    def on_message(self, callback):
        self._callback = callback
        return self

    def on_start_marker(self, callback):
        self._start_marker_callback = callback
        return self

    def on_failure(self, callback):
        self._failure_callback = callback
        return self

    async def _task(self):
        level = 1 if self.photo_transistor.is_light() else 0
        now = utime.ticks_ms()

        if level != self._last_level:
            previous_transition_at = self._last_transition_at
            self._last_level = level
            self._last_transition_at = now
            if not self._receiving and level == 1:
                idle_duration = utime.ticks_diff(now, previous_transition_at)
                if idle_duration >= self.MIN_IDLE_DARK_MS:
                    self._start_frame(now)
            elif self._receiving:
                self._append_run(now, level)

        if self._receiving:
            current_run_duration = utime.ticks_diff(now, self._run_started_at)
            if current_run_duration >= self.FRAME_IDLE_TIMEOUT_MS:
                print(
                    f'OpticalReceiver: frame timeout '
                    f'(levels={len(self._levels)}, '
                    f'payload_length={self._payload_length}, '
                    f'expected_levels={self._expected_level_count}).'
                )
                if (
                    self._payload_length is None
                    and len(self._levels) <= len(self.START_MARKER)
                ):
                    self._reset()
                else:
                    self._fail('frame timeout')
                return
            self._evaluate_frame()

    def _start_frame(self, now):
        self._receiving = True
        self._current_level = 1
        self._run_started_at = now
        self._levels = []
        self._run_debug_count = 0
        self._start_marker_consumed = None
        self._payload_length = None
        self._expected_level_count = None
        print('OpticalReceiver: start marker candidate.')

    def _append_run(self, now, next_level):
        duration = utime.ticks_diff(now, self._run_started_at)
        bias = (
            self.LIGHT_DURATION_BIAS_MS
            if self._current_level == 1
            else self.DARK_DURATION_BIAS_MS
        )
        corrected_duration = max(1, duration - bias)
        run_count = max(
            1,
            (corrected_duration + self.HALF_BIT_MS // 2) // self.HALF_BIT_MS,
        )
        if self._run_debug_count < 24:
            print(
                f'OpticalReceiver: run level={self._current_level} '
                f'duration={duration}ms corrected={corrected_duration}ms '
                f'slots={run_count}.'
            )
            self._run_debug_count += 1
        for _ in range(run_count):
            self._levels.append(self._current_level)
        self._current_level = next_level
        self._run_started_at = now

    def _evaluate_frame(self):
        start_length = len(self.START_MARKER)
        if self._start_marker_consumed is None:
            if len(self._levels) < start_length:
                return
            marker_end = self._match_start_marker()
            if marker_end == -1:
                return
            if marker_end is None:
                print(
                    f'OpticalReceiver: invalid start marker '
                    f'{tuple(self._levels[:start_length])}.'
                )
                self._fail('invalid start marker')
                return
            self._start_marker_consumed = marker_end
            if self._start_marker_callback:
                self._start_marker_callback()
        else:
            marker_end = self._start_marker_consumed

        data_levels = self._levels[marker_end:]
        if len(data_levels) < 32:
            return

        if self._payload_length is None:
            payload_length, _ = self._decode_uint16(data_levels, 0)
            if payload_length is None:
                self._fail('invalid payload length')
                return
            if payload_length > self.MAX_PAYLOAD_BYTES:
                print(f'OpticalReceiver: payload too large ({payload_length} bytes).')
                self._fail('payload too large')
                return
            self._payload_length = payload_length
            self._expected_level_count = (
                marker_end
                + (2 + payload_length + 2) * 16
                + len(self.END_MARKER)
            )
            print(f'OpticalReceiver: payload length={payload_length} bytes.')
        else:
            payload_length = self._payload_length

        expected_length = self._expected_level_count
        if len(self._levels) < expected_length:
            return

        end_start = expected_length - len(self.END_MARKER)
        end_marker = tuple(self._levels[end_start:expected_length])
        if end_marker != self.END_MARKER:
            print(f'OpticalReceiver: invalid end marker {end_marker}.')
            self._fail('invalid end marker')
            return

        payload = []
        offset = 32
        for _ in range(payload_length):
            value, offset = self._decode_byte(data_levels, offset)
            if value is None:
                self._fail('invalid Manchester data')
                return
            payload.append(value)

        checksum, offset = self._decode_uint16(data_levels, offset)
        if checksum is None:
            self._fail('invalid checksum')
            return

        body = [(payload_length >> 8) & 0xff, payload_length & 0xff]
        body.extend(payload)
        expected_checksum = self._crc16(body)
        if checksum != expected_checksum:
            print(
                f'OpticalReceiver: CRC mismatch '
                f'(expected {expected_checksum}, received {checksum}).'
            )
            self._fail('CRC mismatch')
            return

        try:
            message = bytes(payload).decode('utf-8')
        except UnicodeError:
            print('OpticalReceiver: invalid UTF-8 payload.')
            self._fail('invalid UTF-8 payload')
            return

        print(f"OpticalReceiver: received '{message}'.")
        if self._callback:
            self._callback(message)
        self._reset()

    def _decode_uint16(self, levels, offset):
        high, offset = self._decode_byte(levels, offset)
        if high is None:
            return None, offset
        low, offset = self._decode_byte(levels, offset)
        if low is None:
            return None, offset
        return (high << 8) | low, offset

    def _decode_byte(self, levels, offset):
        value = 0
        for _ in range(8):
            pair_offset = offset
            pair = (levels[offset], levels[offset + 1])
            offset += 2
            if pair == (1, 0):
                bit = 0
            elif pair == (0, 1):
                bit = 1
            else:
                print(
                    f'OpticalReceiver: invalid Manchester pair {pair} '
                    f'at data level {pair_offset}.'
                )
                return None, offset
            value = (value << 1) | bit
        return value, offset

    def _reset(self):
        self._receiving = False
        self._run_started_at = None
        self._levels = []
        self._start_marker_consumed = None
        self._payload_length = None
        self._expected_level_count = None

    def _fail(self, reason):
        if self._failure_callback:
            self._failure_callback(reason)
        self._reset()

    def _match_start_marker(self):
        """開始マーカー中の同一レベル重複を吸収して同期位置を返す。"""
        marker_index = 0
        level_index = 0
        levels = self._levels
        while level_index < len(levels) and marker_index < len(self.START_MARKER):
            if levels[level_index] != self.START_MARKER[marker_index]:
                return None
            marker_index += 1
            current = levels[level_index]
            level_index += 1
            while level_index < len(levels) and levels[level_index] == current:
                level_index += 1
        if marker_index == len(self.START_MARKER):
            return level_index
        return -1

    @staticmethod
    def _crc16(bytes_):
        crc = 0xffff
        for byte in bytes_:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ 0x1021) & 0xffff
                else:
                    crc = (crc << 1) & 0xffff
        return crc
