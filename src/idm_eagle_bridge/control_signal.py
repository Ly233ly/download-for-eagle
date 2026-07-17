from __future__ import annotations

import ctypes
from ctypes import wintypes


SHOW_EVENT_NAME = "Local\\IdmEagleAutoImportShow"
RULES_EVENT_NAME = "Local\\IdmEagleAutoImportRules"
QUIT_EVENT_NAME = "Local\\IdmEagleAutoImportQuit"
WAIT_OBJECT_0 = 0


kernel32 = ctypes.windll.kernel32
kernel32.CreateEventW.argtypes = [
    ctypes.c_void_p,
    wintypes.BOOL,
    wintypes.BOOL,
    wintypes.LPCWSTR,
]
kernel32.CreateEventW.restype = wintypes.HANDLE
kernel32.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.OpenEventW.restype = wintypes.HANDLE
kernel32.SetEvent.argtypes = [wintypes.HANDLE]
kernel32.SetEvent.restype = wintypes.BOOL
kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.WaitForSingleObject.restype = wintypes.DWORD
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


class ControlSignals:
    """接收原生托盘宿主发来的显示窗口和退出指令。"""

    def __init__(self) -> None:
        self._show_handle = self._create(SHOW_EVENT_NAME)
        self._rules_handle = self._create(RULES_EVENT_NAME)
        self._quit_handle = self._create(QUIT_EVENT_NAME)

    @staticmethod
    def _create(name: str):
        handle = kernel32.CreateEventW(None, False, False, name)
        if not handle:
            raise OSError(f"无法创建控制信号：{name}")
        return handle

    @staticmethod
    def _poll(handle) -> bool:
        return kernel32.WaitForSingleObject(handle, 0) == WAIT_OBJECT_0

    def poll_show(self) -> bool:
        return self._poll(self._show_handle)

    def poll_quit(self) -> bool:
        return self._poll(self._quit_handle)

    def poll_rules(self) -> bool:
        return self._poll(self._rules_handle)

    def close(self) -> None:
        for attribute in ("_show_handle", "_rules_handle", "_quit_handle"):
            handle = getattr(self, attribute, None)
            if handle:
                kernel32.CloseHandle(handle)
                setattr(self, attribute, None)


def notify_control_event(name: str) -> bool:
    event_modify_state = 0x0002
    handle = kernel32.OpenEventW(event_modify_state, False, name)
    if not handle:
        return False
    try:
        return bool(kernel32.SetEvent(handle))
    finally:
        kernel32.CloseHandle(handle)
