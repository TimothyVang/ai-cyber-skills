"""Run one command in a Windows kill-on-close Job Object, without a spawn race.

The private supervisor joins its job before spawning the command. Its sole job
handle is not inherited, so even an orphan holding stdout dies when the
supervisor exits or is killed. This is process lifetime management, not a sandbox.
"""
import base64
import ctypes
from ctypes import wintypes
import json
import os
import subprocess
import sys

JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


def wrap_command(argv, shell=False):
    """Return helper argv for Popen(shell=False), preserving the original command.

    argv is a list of strings or an already-authored command string. cwd, env and
    standard handles belong on the outer Popen and are inherited unchanged.
    """
    payload = json.dumps([argv, shell], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return [sys.executable, "-B", os.path.abspath(__file__), base64.b64encode(payload).decode("ascii")]


def _kernel32():
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    api.CreateJobObjectW.restype = wintypes.HANDLE
    api.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    api.SetInformationJobObject.restype = wintypes.BOOL
    api.GetCurrentProcess.argtypes = []
    api.GetCurrentProcess.restype = wintypes.HANDLE
    api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    api.AssignProcessToJobObject.restype = wintypes.BOOL
    api.ExitProcess.argtypes = [wintypes.UINT]
    api.ExitProcess.restype = None
    return api


def _supervise(argv, shell):
    api = _kernel32()
    # NULL security attributes make this sole, unnamed handle non-inheritable.
    job = api.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    exit_code = 1
    try:
        limits = _ExtendedLimitInformation()
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not api.SetInformationJobObject(job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                                          ctypes.byref(limits), ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not api.AssignProcessToJobObject(job, api.GetCurrentProcess()):
            raise ctypes.WinError(ctypes.get_last_error())
        process = subprocess.Popen(argv, shell=shell)
        exit_code = process.wait()
    except BaseException as error:
        print(f"Windows job supervisor: {error}", file=sys.stderr, flush=True)
    finally:
        # Closing the job explicitly would also kill this supervisor and lose the
        # command's exit status. ExitProcess preserves the full UINT exit code and
        # closes every handle, triggering job cleanup on success and exceptions.
        # https://learn.microsoft.com/windows/win32/api/processthreadsapi/nf-processthreadsapi-exitprocess
        api.ExitProcess(exit_code)


if __name__ == "__main__":
    try:
        if os.name != "nt":
            raise OSError("Windows Job Objects require Windows")
        command, use_shell = json.loads(base64.b64decode(sys.argv[1], validate=True))
        _supervise(command, use_shell)
    except Exception as error:
        print(f"Windows job supervisor: {error}", file=sys.stderr, flush=True)
        raise SystemExit(1)
