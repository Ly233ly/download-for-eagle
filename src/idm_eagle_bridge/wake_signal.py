from __future__ import annotations

import ctypes
import os
import threading


EVENT_NAME = "Local\\IdmEagleAutoImportWake"
ERROR_ALREADY_EXISTS = 183


class WakeSignal:
    """跨进程轻量唤醒信号；避免助手为了等新任务频繁轮询数据库。"""

    def __init__(self) -> None:
        self._fallback = threading.Event() if os.name != "nt" else None
        self._handle = None
        self._kernel32 = None
        self.listener_present = False
        if os.name == "nt":
            self._kernel32 = ctypes.windll.kernel32
            self._kernel32.CreateEventW.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_wchar_p,
            ]
            self._kernel32.CreateEventW.restype = ctypes.c_void_p
            self._kernel32.SetEvent.argtypes = [ctypes.c_void_p]
            self._kernel32.WaitForSingleObject.argtypes = [
                ctypes.c_void_p,
                ctypes.c_uint32,
            ]
            self._kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
            self._handle = self._kernel32.CreateEventW(None, False, False, EVENT_NAME)
            if not self._handle:
                raise OSError("无法创建任务唤醒信号")
            self.listener_present = self._kernel32.GetLastError() == ERROR_ALREADY_EXISTS

    def set(self) -> None:
        if self._fallback is not None:
            self._fallback.set()
            return
        self._kernel32.SetEvent(self._handle)

    def wait(self, timeout: float) -> bool:
        if self._fallback is not None:
            signaled = self._fallback.wait(timeout)
            self._fallback.clear()
            return signaled
        milliseconds = max(0, min(int(timeout * 1000), 0xFFFFFFFE))
        return self._kernel32.WaitForSingleObject(self._handle, milliseconds) == 0

    def close(self) -> None:
        if self._handle:
            self._kernel32.CloseHandle(self._handle)
            self._handle = None


def notify_processing_service() -> bool:
    signal = WakeSignal()
    try:
        signal.set()
        return signal.listener_present
    finally:
        signal.close()
