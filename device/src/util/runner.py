import asyncio

class Runner:
    # 監視の反応の機敏さと電池持ちのトレードオフなため調節する
    # 0だと最も電池食うが反応は良い。100だと入力系統がモッサリしてしまう
    _LOOP_WAIT_MS = 10

    def __init__(self, func):
        self._func = func
        self._task = None

    def run(self):
        if self._task is None:
            async def coro():
                try:
                    await self._func()
                finally:
                    self._task = None
            self._task = asyncio.create_task(coro())

    def loop(self, wait_ms = _LOOP_WAIT_MS):
        if self._task is None:
            async def coro():
                try:
                    while True:
                        await self._func()
                        await asyncio.sleep_ms(wait_ms)
                finally:
                    self._task = None
            self._task = asyncio.create_task(coro())

    def stop(self):
        if self._task is not None:
            self._task.cancel()
            self._task = None
