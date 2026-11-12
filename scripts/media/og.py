"""Render docs/images/og.png, the 1280x640 social card, in a brand's name, tagline and colors."""
from pathlib import Path

from PIL import Image, ImageDraw

from brandlib import font, palette

S = 2  # draw at 2x, then downsample


def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and draw.textlength(trial, font=fnt) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line] if line else lines


def render(brand: dict, out: Path, own_run: bool = False) -> Path:
    """`own_run` names the upstream's real merged PR; a reseller's card shows the generic panel line."""
    p = palette(brand)
    im = Image.new("RGB", (1280 * S, 640 * S), p["BG"])
    d = ImageDraw.Draw(im)

    def tx(x, y, s, fnt, fill):
        d.text((x * S, y * S), s, font=fnt, fill=fill)

    for i, c in enumerate([p["ACCENT"], p["SKY"], p["REVIEWER"], p["AMBER"], p["AUTHOR"]]):
        d.rounded_rectangle([(64 + i * 52) * S, 70 * S, (104 + i * 52) * S, 78 * S], 4 * S, fill=c)
    size = 88  # the product name, shrunk until it fits the card's width
    while size > 36 and d.textlength(brand["name"], font=font("bold", size * S)) > 1152 * S:
        size -= 4
    d.text((64 * S, 196 * S), brand["name"], font=font("bold", size * S), fill=p["TEXT"], anchor="ls")
    tag_font = font("light", 38 * S)
    tag_lines = wrap(d, brand["tagline"], tag_font, 1150 * S)[:2]
    for i, line in enumerate(tag_lines):
        tx(64, 216 + i * 50, line, tag_font, p["TEXT"])
    tx(64, 234 + len(tag_lines) * 50, "Open source (MIT). Runs on your machine and your own subscription. No API keys.",
       font("regular", 24 * S), p["MUTED"])
    x = 64
    for label, c in [("any ACP agent, omp by default", p["SKY"]), ("3-agent verifier panel", p["AMBER"]),
                     ("merge gate in code", p["ACCENT"]), ("spec to tickets to PR", p["REVIEWER"])]:
        fo = font("bold", 21 * S)
        w = d.textlength(label, font=fo) / S + 36
        d.rounded_rectangle([x * S, 404 * S, (x + w) * S, 450 * S], 23 * S, fill=p["PANEL"], outline=c, width=2 * S)
        tx(x + 18, 413, label, fo, p["TEXT"])
        x += w + 14
    d.rounded_rectangle([64 * S, 498 * S, 1216 * S, 584 * S], 18 * S, fill=p["PANEL"], outline=p["PANEL_EDGE"], width=2 * S)
    d.ellipse([88 * S, 520 * S, 130 * S, 562 * S], fill=p["REVIEWER"])
    login = brand["owner"].lower() if own_run else "<login>"
    tx(148, 512, f"{brand['slug']}-{login}[bot]", font("bold", 21 * S), p["TEXT"])
    line = ("Panel PASS at 839703f: 2/3 · Merged 839703f (squash) · PR #19" if own_run
            else "Panel PASS 2/3 · required checks green · squash merged")
    tx(148, 542, line, font("regular", 20 * S), p["AMBER"])
    site_font = font("regular", 19 * S)
    site = brand["homepage"].split("://", 1)[1].rstrip("/")
    tx(1196 - d.textlength(site, font=site_font) / S, 512, site, site_font, p["MUTED"])
    out.parent.mkdir(parents=True, exist_ok=True)
    im.resize((1280, 640), Image.LANCZOS).save(out, optimize=True)
    return out
