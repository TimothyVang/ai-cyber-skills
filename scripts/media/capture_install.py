"""Record a real `install.py --check` run of the bots as docs/images/install.cast (asciicast v2).

    py -3 scripts/media/capture_install.py [--brand brand/brand.json]

Run it in a branded copy to record your own run, then render install.gif with render.py.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import brandlib  # noqa: E402

ROOT = HERE.parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--brand", default=str(ROOT / "brand/brand.json"))
    args = parser.parse_args()
    brand = brandlib.load(args.brand)
    skill = ROOT / "plugins" / brand["slug"] / "skills" / brand["mainSkillName"]
    out = ROOT / "docs/images/install.cast"
    command = "py -3 assets/github-app/install.py --check"
    prompt = f"\x1b[32m~/{brand['slug']}/plugins/{brand['slug']}/skills/{brand['mainSkillName']}\x1b[0m $ "
    events, t = [(0.0, "o", prompt)], 0.6
    for ch in command:
        events.append((round(t, 3), "o", ch))
        t += 0.045
    t += 0.3
    events.append((round(t, 3), "o", "\r\n"))
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    start = time.monotonic()
    proc = subprocess.Popen([sys.executable, "-u", "assets/github-app/install.py", "--check"], cwd=skill, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    raw = [(time.monotonic() - start, line.rstrip("\n")) for line in proc.stdout]
    code = proc.wait()
    elapsed = time.monotonic() - start
    events += [(round(t + at, 3), "o", line + "\r\n") for at, line in raw]
    events += [(round(t + elapsed + 0.2, 3), "o", prompt), (round(t + elapsed + 3.0, 3), "o", "")]
    header = {"version": 2, "width": 92, "height": 22, "timestamp": int(time.time()),
              "title": "install.py --check (real run)", "env": {"SHELL": "bash", "TERM": "xterm-256color"}}
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(header) + "\n")
        for e in events:
            f.write(json.dumps(list(e)) + "\n")
    print(f"exit {code}, {len(raw)} lines, {elapsed:.1f}s -> {out}")
    return code


if __name__ == "__main__":
    sys.exit(main())
