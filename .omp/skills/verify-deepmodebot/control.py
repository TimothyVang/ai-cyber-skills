#!/usr/bin/env python3
"""Read-only prerequisites and captured invocations of deepmodebot's real evaluation CLIs."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
TARGETS = {"outcome": "evals/outcome/run.py", "review": "evals/review/run.py",
           "workflows": "evals/workflows/run.py"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    capture = commands.add_parser("run")
    capture.add_argument("--id", required=True)
    capture.add_argument("target", choices=TARGETS)
    capture.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command == "doctor":
        tools = {name: shutil.which(name) for name in ("git", "node", "omp")}
        result = {"root": str(ROOT), "python": sys.version.split()[0], "tools": tools,
                  "ready": all(tools.values()) and sys.version_info >= (3, 12),
                  "auth": "checked by the model runner before any model call"}
        print(json.dumps(result, indent=2))
        return 0 if result["ready"] else 1
    if not re.fullmatch(r"[a-z][a-z0-9-]*", args.id):
        parser.error("id must be a lowercase project slug")
    destination = ROOT / ".scratch/evidence" / args.id
    destination.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(ROOT / TARGETS[args.target]), *args.args]
    if command[2:3] == ["--"]:
        del command[2]
    temp = ROOT / ".scratch/tmp"
    temp.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TMP=str(temp), TEMP=str(temp), TMPDIR=str(temp))
    (destination / "command.json").write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")
    with (destination / "stdout.txt").open("w", encoding="utf-8") as out, (destination / "stderr.txt").open("w", encoding="utf-8") as err:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=out, stderr=err)
    (destination / "result.json").write_text(json.dumps({"exit": result.returncode}) + "\n", encoding="utf-8")
    print(json.dumps({"exit": result.returncode, "evidence": str(destination)}))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
