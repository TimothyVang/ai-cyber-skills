"""Run one command in a Windows 10+ kill-on-close Job Object, without a spawn race.

The private supervisor assigns the command at creation, rather than relying on
job inheritance from its supervisor. Its sole job handle is not
inherited. This is process lifetime management, not a sandbox.
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
PROC_THREAD_ATTRIBUTE_JOB_LIST = 0x0002000D
EXTENDED_STARTUPINFO_PRESENT = 0x00080000


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


class _StartupInfo(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.c_void_p),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class _StartupInfoEx(ctypes.Structure):
    _fields_ = [("StartupInfo", _StartupInfo), ("lpAttributeList", ctypes.c_void_p)]


class _ProcessInformation(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
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
    api.InitializeProcThreadAttributeList.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                                                      ctypes.POINTER(ctypes.c_size_t)]
    api.InitializeProcThreadAttributeList.restype = wintypes.BOOL
    api.UpdateProcThreadAttribute.argtypes = [ctypes.c_void_p, wintypes.DWORD, ctypes.c_size_t, ctypes.c_void_p,
                                             ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p]
    api.UpdateProcThreadAttribute.restype = wintypes.BOOL
    api.DeleteProcThreadAttributeList.argtypes = [ctypes.c_void_p]
    api.DeleteProcThreadAttributeList.restype = None
    api.GetStdHandle.argtypes = [wintypes.DWORD]
    api.GetStdHandle.restype = wintypes.HANDLE
    api.CreateProcessW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, wintypes.BOOL,
                                  wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
                                  ctypes.POINTER(_StartupInfoEx), ctypes.POINTER(_ProcessInformation)]
    api.CreateProcessW.restype = wintypes.BOOL
    api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    api.WaitForSingleObject.restype = wintypes.DWORD
    api.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    api.GetExitCodeProcess.restype = wintypes.BOOL
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    api.CloseHandle.restype = wintypes.BOOL
    api.ExitProcess.argtypes = [wintypes.UINT]
    api.ExitProcess.restype = None
    return api


def _run_in_job(api, job, argv, shell):
    command = subprocess.list2cmdline(argv) if isinstance(argv, list) else argv
    batch = isinstance(argv, list) and argv and os.path.splitext(argv[0])[1].lower() in (".bat", ".cmd")
    application = None
    if shell or batch:
        application = os.environ.get("ComSpec") or os.path.join(os.environ["SystemRoot"], "System32", "cmd.exe")
        command = f'{subprocess.list2cmdline([application])} /c "{command}"'
    size = ctypes.c_size_t()
    api.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(size))
    if ctypes.get_last_error() != 122 or not size.value:
        raise ctypes.WinError(ctypes.get_last_error())
    attributes = ctypes.create_string_buffer(size.value)
    if not api.InitializeProcThreadAttributeList(attributes, 1, 0, ctypes.byref(size)):
        raise ctypes.WinError(ctypes.get_last_error())
    process = _ProcessInformation()
    try:
        jobs = (wintypes.HANDLE * 1)(job)
        # Assign before any target code runs; job inheritance alone is not reliable
        # across packaged/unpackaged process launches.
        # https://learn.microsoft.com/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute
        if not api.UpdateProcThreadAttribute(attributes, 0, PROC_THREAD_ATTRIBUTE_JOB_LIST,
                                              jobs, ctypes.sizeof(jobs), None, None):
            raise ctypes.WinError(ctypes.get_last_error())
        startup = _StartupInfoEx()
        startup.StartupInfo.cb = ctypes.sizeof(startup)
        startup.StartupInfo.dwFlags = 0x00000100  # STARTF_USESTDHANDLES
        startup.StartupInfo.hStdInput = api.GetStdHandle(-10)
        startup.StartupInfo.hStdOutput = api.GetStdHandle(-11)
        startup.StartupInfo.hStdError = api.GetStdHandle(-12)
        startup.lpAttributeList = ctypes.cast(attributes, ctypes.c_void_p)
        if not api.CreateProcessW(application, ctypes.create_unicode_buffer(command), None, None, True,
                                  EXTENDED_STARTUPINFO_PRESENT, None, None, ctypes.byref(startup), ctypes.byref(process)):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        api.DeleteProcThreadAttributeList(attributes)
    api.CloseHandle(process.hThread)
    try:
        if api.WaitForSingleObject(process.hProcess, 0xFFFFFFFF) != 0:
            raise ctypes.WinError(ctypes.get_last_error())
        exit_code = wintypes.DWORD()
        if not api.GetExitCodeProcess(process.hProcess, ctypes.byref(exit_code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return exit_code.value
    finally:
        api.CloseHandle(process.hProcess)


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
        exit_code = _run_in_job(api, job, argv, shell)
    except BaseException as error:
        print(f"Windows job supervisor: {error}", file=sys.stderr, flush=True)
    finally:
        # ExitProcess preserves the full UINT status and closes the sole job handle,
        # terminating remaining descendants on both success and exceptions.
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
