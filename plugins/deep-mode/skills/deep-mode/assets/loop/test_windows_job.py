"""Windows process-tree regressions; run with TMP/TEMP/TMPDIR in repo-local scratch.

Use -B (or a scratch PYTHONPYCACHEPREFIX) when discovering these tests. The
fixtures run in isolated interpreters and use events, not sleeps, to coordinate.
"""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

import windows_job

HERE = Path(__file__).resolve()
REPO = next(parent for parent in HERE.parents if (parent / ".git").exists())
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258
SYNCHRONIZE = 0x00100000
PROCESS_TERMINATE = 0x0001
EVENT_MODIFY_STATE = 0x0002
FIXTURE_LIFETIME_MS = 8000
DEADLINE_SECONDS = 2


def _api():
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "CreateEventW": ([ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR], wintypes.HANDLE),
        "OpenEventW": ([wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR], wintypes.HANDLE),
        "SetEvent": ([wintypes.HANDLE], wintypes.BOOL),
        "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
        "WaitForSingleObject": ([wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
        "TerminateProcess": ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
        "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        "ExitProcess": ([wintypes.UINT], None),
    }
    for name, (argtypes, restype) in signatures.items():
        function = getattr(api, name)
        function.argtypes = argtypes
        function.restype = restype
    return api


def _checked(result):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result


def _wait(api, handle, milliseconds):
    result = api.WaitForSingleObject(handle, milliseconds)
    if result not in (WAIT_OBJECT_0, WAIT_TIMEOUT):
        raise ctypes.WinError(ctypes.get_last_error())
    return result


def _fixture(role, mode, root, token):
    root = Path(root)
    api = _api()

    def event(name):
        return _checked(api.OpenEventW(SYNCHRONIZE | EVENT_MODIFY_STATE, False, token + name))

    if role == "leaf":
        print("descendant-ready", flush=True)
        _checked(api.SetEvent(event("leaf")))
        _wait(api, event("finish"), FIXTURE_LIFETIME_MS)
        return 0
    if role == "parent":
        leaf = subprocess.Popen([sys.executable, "-B", str(HERE), "--fixture", "leaf", mode, str(root), token])
        (root / "processes.json").write_text(json.dumps([os.getpid(), leaf.pid]), encoding="utf-8")
        if _wait(api, event("leaf"), 3000) != WAIT_OBJECT_0:
            return 91
        _checked(api.SetEvent(event("ready")))
        if mode == "orphan":
            if _wait(api, event("release"), FIXTURE_LIFETIME_MS) != WAIT_OBJECT_0:
                return 92
            os._exit(23)
        _wait(api, event("finish"), FIXTURE_LIFETIME_MS)
        return 0
    if role == "deadline":
        import loop
        argv = [sys.executable, "-B", str(HERE), "--fixture", "parent", "live", str(root), token]
        started = time.monotonic()
        code, output = loop.run_limited(argv, DEADLINE_SECONDS / 60,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(json.dumps({"code": code, "output": output, "elapsed": time.monotonic() - started}), flush=True)
        return 0
    raise ValueError(role)


@unittest.skipUnless(os.name == "nt", "Windows Job Objects only")
class WindowsJobCase(unittest.TestCase):
    def setUp(self):
        scratch = Path(os.environ.get("TMP", tempfile.gettempdir())).resolve()
        self.assertTrue(scratch.is_relative_to(REPO), "Set TMP/TEMP/TMPDIR to repo-local scratch")
        temporary = tempfile.TemporaryDirectory(prefix="windows-job-", dir=scratch)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.env = {**os.environ, "TMP": str(self.root), "TEMP": str(self.root), "TMPDIR": str(self.root),
                    "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
        self.api = _api()
        self.token = "Local\\deep-mode-test-" + uuid.uuid4().hex + "-"
        self.events = {}
        self.handles = {}
        self.processes = []
        self.addCleanup(self.cleanup_processes)
        for name in ("leaf", "ready", "release", "finish"):
            self.events[name] = _checked(self.api.CreateEventW(None, True, False, self.token + name))

    def cleanup_processes(self):
        try:
            for name in ("finish", "release"):
                if name in self.events:
                    _checked(self.api.SetEvent(self.events[name]))
            # Recover handles even when readiness failed, so failed assertions do
            # not leave benign fixtures running until their finite safety limit.
            record = self.root / "processes.json"
            if record.exists():
                for pid in json.loads(record.read_text(encoding="utf-8")):
                    if pid not in self.handles:
                        handle = self.api.OpenProcess(SYNCHRONIZE | PROCESS_TERMINATE, False, pid)
                        if handle:
                            self.handles[pid] = handle
                        elif ctypes.get_last_error() != 87:  # already gone
                            raise ctypes.WinError(ctypes.get_last_error())
            for handle in self.handles.values():
                if _wait(self.api, handle, 1000) == WAIT_TIMEOUT:
                    _checked(self.api.TerminateProcess(handle, 99))
                    self.assertEqual(_wait(self.api, handle, 1000), WAIT_OBJECT_0)
            for process in self.processes:
                if process.poll() is None:
                    process.kill()
                process.communicate(timeout=2)
        finally:
            for handle in (*self.handles.values(), *self.events.values()):
                _checked(self.api.CloseHandle(handle))
            for process in self.processes:
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None:
                        stream.close()

    def start(self, argv, **kwargs):
        process = subprocess.Popen(argv, cwd=self.root, env=self.env, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding="utf-8", **kwargs)
        self.processes.append(process)
        return process

    def watch_tree(self):
        self.assertEqual(_wait(self.api, self.events["ready"], 3000), WAIT_OBJECT_0,
                         "fixture tree did not become ready")
        for pid in json.loads((self.root / "processes.json").read_text(encoding="utf-8")):
            handle = _checked(self.api.OpenProcess(SYNCHRONIZE | PROCESS_TERMINATE, False, pid))
            self.handles[pid] = handle
            self.assertEqual(_wait(self.api, handle, 0), WAIT_TIMEOUT, "fixture was not alive")
        self.assertEqual(len(self.handles), 2)

    def assert_tree_stopped(self):
        for pid, handle in self.handles.items():
            self.assertEqual(_wait(self.api, handle, 500), WAIT_OBJECT_0, f"process {pid} survived")

    def test_output_stdin_arguments_environment_cwd_and_exit_propagate(self):
        arguments = ["", "two words", 'a"quote', "trailing\\", "&|<>^%!", "snowman-\u2603"]
        code = (
            "import json, os, sys; "
            "print(json.dumps({'argv': sys.argv[1:], 'stdin': sys.stdin.read(), "
            "'cwd': os.getcwd(), 'marker': os.environ['JOB_TEST_MARKER']})); "
            "print('stderr-marker', file=sys.stderr); sys.exit(37)"
        )
        self.env["JOB_TEST_MARKER"] = "inherited-value"
        process = self.start(windows_job.wrap_command([sys.executable, "-B", "-c", code, *arguments]))
        out, err = process.communicate("stdin-value\n", timeout=3)
        self.assertEqual(process.returncode, 37, err)
        self.assertEqual(json.loads(out), {"argv": arguments, "stdin": "stdin-value\n",
                                          "cwd": str(self.root), "marker": "inherited-value"})
        self.assertEqual(err, "stderr-marker\n")

    def test_shell_string_is_not_requoted(self):
        process = self.start(windows_job.wrap_command("echo shell-marker&exit /b 29", shell=True))
        out, err = process.communicate(timeout=3)
        self.assertEqual(process.returncode, 29, err)
        self.assertEqual(out.strip(), "shell-marker")
        self.assertEqual(err, "")

    def test_unsigned_windows_exit_code_propagates(self):
        code = ("import ctypes; from ctypes import wintypes; "
                "exit_process = ctypes.WinDLL('kernel32').ExitProcess; "
                "exit_process.argtypes = [wintypes.UINT]; exit_process.restype = None; "
                "exit_process(0x80000007)")
        process = self.start(windows_job.wrap_command([sys.executable, "-B", "-c", code]))
        out, err = process.communicate(timeout=3)
        self.assertEqual(process.returncode, 0x80000007, err)
        self.assertEqual(out, "")
        self.assertEqual(err, "")

    def test_exited_intermediate_cannot_leave_descendant_holding_stdout(self):
        argv = [sys.executable, "-B", str(HERE), "--fixture", "parent", "orphan", str(self.root), self.token]
        process = self.start(windows_job.wrap_command(argv))
        self.watch_tree()
        started = time.monotonic()
        _checked(self.api.SetEvent(self.events["release"]))
        out, err = process.communicate(timeout=2)
        self.assertLess(time.monotonic() - started, 2)
        self.assertEqual(process.returncode, 23, err)
        self.assertEqual(out, "descendant-ready\n")
        self.assertEqual(err, "")
        self.assert_tree_stopped()

    def test_loop_deadline_stops_live_parent_and_descendant(self):
        # Isolate run_limited itself: an unbounded post-kill communicate must fail
        # this test's outer timeout, rather than hanging the unittest process.
        argv = [sys.executable, "-B", str(HERE), "--fixture", "deadline", "live", str(self.root), self.token]
        process = self.start(argv)
        self.watch_tree()
        out, err = process.communicate(timeout=4)
        self.assertEqual(process.returncode, 0, err)
        self.assertEqual(err, "")
        result = json.loads(out)
        self.assertIsNone(result["code"])
        self.assertIn("descendant-ready", result["output"])
        self.assertLess(result["elapsed"], DEADLINE_SECONDS + 1.5)
        self.assert_tree_stopped()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fixture":
        raise SystemExit(_fixture(*sys.argv[2:]))
    unittest.main()
