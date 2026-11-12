"""The bots' white-label identity: every name a user or a repo sees comes from here.

`brand.json` beside this file holds the shipped brand. A fork rebrands by editing it, or by running
`install.py --brand <name>`, which writes `brand.local.json` beside it. `DEEP_MODE_BRAND_FILE` points at
another file. Missing keys are derived from `name`, so a one-key file is a complete brand.
"""
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHIPPED = HERE / "brand.json"
LOCAL = HERE / "brand.local.json"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,22}$")  # leaves room for "-<login>" in a 34-char app name


def derive(name: str, overrides: dict | None = None) -> dict:
    if not NAME_RE.match(name):
        raise ValueError(f"brand name {name!r}: use 1-23 lowercase letters, digits or hyphens")
    brand = {
        "name": name,
        "description": f"{name} bots: review, fix, verify and merge in the PR and issue threads.",
        "homepage": "https://github.com/TimothyVang/deep-mode",
        "mention": f"/{name}",
        "branchPrefix": name,
        "repoConfigFile": f".{name}.json",
        "configDirName": name,
        "autostartId": f"{name}-bot",
    }
    brand.update({k: v for k, v in (overrides or {}).items() if v})
    return brand


def load() -> dict:
    path = Path(os.environ["DEEP_MODE_BRAND_FILE"]) if os.environ.get("DEEP_MODE_BRAND_FILE") else (
        LOCAL if LOCAL.is_file() else SHIPPED)
    data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    return derive(data.get("name", "deep-mode"), data)


def write_local(name: str, homepage: str | None = None) -> dict:
    overrides = {"homepage": homepage} if homepage else {}
    brand = derive(name, overrides)
    LOCAL.write_text(json.dumps({"name": name, **overrides}, indent=2) + "\n", encoding="utf-8")
    return brand


BRAND = load()
CONFIG_DIR = Path(os.environ.get("DEEP_MODE_CONFIG_DIR") or Path.home() / ".config" / BRAND["configDirName"])
CACHE_DIR = Path.home() / ".cache" / BRAND["configDirName"] / "bot"
