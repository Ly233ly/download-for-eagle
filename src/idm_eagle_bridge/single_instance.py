from __future__ import annotations

import ctypes
from ctypes import wintypes


ERROR_ALREADY_EXISTS = 183

kernel32 = ctypes.windll.kernel32
kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.GetLastError.restype = wintypes.DWORD
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


class SingleInstance:
    def __init__(self, name: str = "Local_IdmEagleAutoImport") -> None:
        self.handle = kernel32.CreateMutexW(None, False, name)
        self.already_running = kernel32.GetLastError() == ERROR_ALREADY_EXISTS

    def close(self) -> None:
        if self.handle:
            kernel32.CloseHandle(self.handle)
            self.handle = None
