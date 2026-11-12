"""Load a brand file and derive what the media generators and the white-label build need from it.

A brand file is JSON. `brand/brand.json` is the default; `brand/examples/acme.json` is a complete reseller.
`logo` and `favicon` are paths relative to the brand file.
"""
import json
import os
import re
import sys
from pathlib import Path

FIELDS = ("name", "displayName", "slug", "commandName", "mainSkillName", "stackSkillName", "envPrefix",
          "botTrigger", "tagline", "description", "author", "homepage", "repo", "supportUrl", "colors", "logo",
          "favicon")
COLOR_FIELDS = ("primary", "accent", "background", "surface", "text", "muted")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,22}$")  # brand.py's limit: room for "-<login>" in a 34-char app name
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

# Role colors in the diagrams and GIFs. They mean the same thing in every brand: author, reviewer, panel.
SKY, AUTHOR, REVIEWER, AMBER, ROSE, MERGED = "#38bdf8", "#f08a5d", "#34d399", "#fbbf24", "#fb7185", "#8957e5"


class BrandError(ValueError):
    pass


def load(path) -> dict:
    """Read and validate a brand file. Returns the fields plus `owner`, `dir`, `logoPath` and `faviconPath`."""
    path = Path(path).resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        raise BrandError(f"{path}: {err}") from err
    missing = [k for k in FIELDS if not data.get(k)]
    if missing:
        raise BrandError(f"{path}: missing {', '.join(missing)}")
    if not SLUG_RE.match(data["slug"]):
        raise BrandError(f"slug {data['slug']!r}: use 1-23 lowercase letters, digits or hyphens")
    for key in ("commandName", "mainSkillName", "stackSkillName"):
        if not NAME_RE.match(data[key]):
            raise BrandError(f"{key} {data[key]!r}: use lowercase letters, digits or hyphens")
    if not re.match(r"^[A-Z][A-Z0-9_]*$", data["envPrefix"]):
        raise BrandError(f"envPrefix {data['envPrefix']!r}: use uppercase letters, digits or underscores")
    if not re.match(r"^/[a-z0-9][a-z0-9-]*$", data["botTrigger"]):
        raise BrandError(f"botTrigger {data['botTrigger']!r}: a slash and a lowercase word, like /acme-review")
    if not re.match(r"^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$", data["repo"]):
        raise BrandError(f"repo {data['repo']!r}: use owner/name")
    if not isinstance(data["author"], dict) or not data["author"].get("name") or not data["author"].get("url"):
        raise BrandError("author: an object with name and url")
    for key in ("homepage", "supportUrl"):
        if not re.match(r"^https?://", data[key]):
            raise BrandError(f"{key} {data[key]!r}: a full http(s) URL")
    for key in COLOR_FIELDS:
        if not HEX_RE.match(str(data["colors"].get(key, ""))):
            raise BrandError(f"colors.{key}: a #rrggbb color")
    brand = {k: data[k] for k in FIELDS}
    brand["homepage"] = data["homepage"].rstrip("/") + "/"
    brand["author"] = {"name": data["author"]["name"], "url": data["author"]["url"].rstrip("/")}
    brand["owner"] = data["repo"].split("/")[0]
    brand["dir"] = path.parent
    for key in ("logo", "favicon"):
        file = (path.parent / data[key]).resolve()
        if not file.is_file():
            raise BrandError(f"{key}: {file} not found")
        brand[key + "Path"] = file
    return brand


def to_json(brand: dict) -> dict:
    """The brand as a brand file, with logo and favicon beside it."""
    out = {k: brand[k] for k in FIELDS}
    out["logo"], out["favicon"] = "logo.svg", "favicon.svg"
    return out


def rgb(color: str) -> tuple:
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def mix(a: str, b: str, t: float) -> str:
    """`t` of the way from color a to color b."""
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(rgb(a), rgb(b)))


def palette(brand: dict) -> dict:
    c = brand["colors"]
    return {"BG": c["background"], "PANEL": c["surface"], "TEXT": c["text"], "MUTED": c["muted"],
            "EDGE": mix(c["surface"], c["muted"], 0.13), "PANEL_EDGE": mix(c["surface"], c["muted"], 0.22),
            "ACCENT": c["accent"], "PRIMARY": c["primary"], "SKY": SKY, "AUTHOR": AUTHOR, "REVIEWER": REVIEWER,
            "AMBER": AMBER, "ROSE": ROSE, "MERGED": MERGED}


# Fonts for the PNG and GIF renders: the first file found wins, then Pillow's built-in font.
FONT_FILES = {
    "bold": ["segoeuib.ttf", "Arial Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
    "regular": ["segoeui.ttf", "Arial.ttf", "arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"],
    "light": ["segoeuisl.ttf", "segoeuil.ttf", "Arial.ttf", "arial.ttf", "DejaVuSans-ExtraLight.ttf", "DejaVuSans.ttf",
              "LiberationSans-Regular.ttf"],
    "mono": ["CascadiaMono.ttf", "consola.ttf", "Menlo.ttc", "DejaVuSansMono.ttf", "LiberationMono-Regular.ttf"],
}
_font_index = None


def _font_dirs():
    if sys.platform == "win32":
        yield Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        yield Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts"
    elif sys.platform == "darwin":
        yield from (Path("/System/Library/Fonts"), Path("/Library/Fonts"), Path.home() / "Library/Fonts")
    else:
        yield from (Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), Path.home() / ".local/share/fonts",
                    Path.home() / ".fonts")


def font(style: str, size: float):
    from PIL import ImageFont
    global _font_index
    if _font_index is None:
        _font_index = {}
        for root in _font_dirs():
            if root.is_dir():
                for f in root.rglob("*"):
                    if f.suffix.lower() in (".ttf", ".ttc", ".otf"):
                        _font_index.setdefault(f.name.lower(), f)
    for name in FONT_FILES[style]:
        if name.lower() in _font_index:
            return ImageFont.truetype(str(_font_index[name.lower()]), size)
    return ImageFont.load_default(size)


def tool(name: str) -> str:
    """Path of an external encoder, or a clear error naming where to get it."""
    import shutil
    found = shutil.which(name)
    if not found:
        hints = {"agg": "https://github.com/asciinema/agg (cargo install --git https://github.com/asciinema/agg)",
                 "gifski": "https://gif.ski (cargo install gifski, brew install gifski, or winget install gifski)"}
        raise BrandError(f"{name} is not on PATH; install it from {hints.get(name, name)}")
    return found
