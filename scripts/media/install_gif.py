"""Render docs/images/install.gif from the asciicast docs/images/install.cast with agg, in a brand's colors."""
import subprocess
from pathlib import Path

from brandlib import palette, tool


def theme(brand: dict) -> str:
    """agg's custom theme: background, foreground, then the 8 ANSI colors. The prompt's green takes the accent."""
    p = palette(brand)
    colors = [p["BG"], p["TEXT"], p["PANEL"], p["ROSE"], p["ACCENT"], p["AMBER"], p["SKY"], p["ACCENT"], p["SKY"], p["TEXT"]]
    return ",".join(c.lstrip("#") for c in colors)


def render(brand: dict, cast: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([tool("agg"), "--quiet", "--theme", theme(brand), str(cast), str(out)], check=True)
    return out
