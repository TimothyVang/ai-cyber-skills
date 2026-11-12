"""Compose docs/images/pr-19-thread.gif from screenshots of the upstream's real PR #19 thread.

    py -3 scripts/media/pr19_thread.py --raw <dir of captures>

The captures are not in the repo: one PNG per comment, named by its comment id, plus header.png and
merged-event.png. This GIF records the upstream's own run, so a branded build drops it and this script, and
shows the illustrated how-it-works.gif instead.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import brandlib  # noqa: E402

ROOT = HERE.parent.parent
W, H, STRIP, PAD, FPS = 1600, 1000, 112, 40, 2
DARK, TEXT, MUTED, PAGE = "#0b1220", "#e6edf3", "#9fb0c8", "#f6f8fa"
ACCENT = {"author": "#f08a5d", "reviewer": "#34d399", "coord": "#38bdf8", "owner": "#a78bfa",
          "fail": "#fb7185", "pass": "#34d399", "merged": "#8957e5"}
# (comment id, caption, accent, seconds on screen)
STEPS = [
    ("6807669836", "Conflict: the author merges main into the PR", "author", 3.5),
    ("6807689989", "Review: findings with severity and evidence", "reviewer", 3.0),
    ("6807842109", "Answer: the author fixes each finding", "author", 3.5),
    ("6808023857", "Not converged after 3 rounds: blocked, with the open findings", "coord", 3.5),
    ("6808029006", "The owner replies: continue", "owner", 2.5),
    ("6808356255", "Panel 1: a verifier votes FAIL with evidence", "fail", 3.0),
    ("6808356905", "Panel 1: 1/3 PASS, so no merge", "fail", 2.5),
    ("6808477000", "Panel 2 after more fixes: 1/3 PASS again", "fail", 2.5),
    ("6808592285", "The owner names the last fix", "owner", 2.5),
    ("6808644712", "Re-review: no open findings", "reviewer", 2.5),
    ("6808721491", "Panel 3: verifier 3 votes PASS", "pass", 3.0),
    ("6808721238", "Panel 3: verifier 2 still FAILs, with evidence", "fail", 3.0),
    ("6808721728", "Panel PASS at 839703f: 2/3", "pass", 3.0),
    ("6808724808", "Every merge gate holds: squash merged", "merged", 3.0),
    ("final", "Merged by the bots, on their own", "merged", 4.0),
]


def content(raw: Path, shot: str) -> Image.Image:
    if shot != "final":
        return Image.open(raw / f"{shot}.png").convert("RGB")
    header = Image.open(raw / "header.png").convert("RGB")
    header = header.crop((0, 0, min(header.width, 2120), header.height - 96))  # drop the tab bar
    header = header.resize((1600, round(header.height * 1600 / header.width)), Image.LANCZOS)
    event = Image.open(raw / "merged-event.png").convert("RGB")
    combo = Image.new("RGB", (1600, header.height + 40 + event.height), "#ffffff")
    combo.paste(header, (0, 0))
    combo.paste(event, (0, header.height + 40))
    return combo


def frame(raw: Path, repo: str, i: int, shot: str, caption: str, accent: str) -> Image.Image:
    bold, reg = brandlib.font("bold", 40), brandlib.font("regular", 26)
    im = Image.new("RGB", (W, H), PAGE)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, STRIP], fill=DARK)
    d.rectangle([0, STRIP - 6, W, STRIP], fill=ACCENT[accent])
    d.text((PAD, 18), caption, font=bold, fill=TEXT)
    d.text((PAD, 66), f"Real thread: github.com/{repo}/pull/19   ·   {i + 1}/{len(STEPS)}", font=reg, fill=MUTED)
    shot_im = content(raw, shot)
    box_w, box_h = W - 2 * PAD, H - STRIP - 2 * PAD + 10
    scale = box_w / shot_im.width
    max_src_h = int(box_h / scale)
    cropped = shot_im.height > max_src_h
    shot_im = shot_im.crop((0, 0, shot_im.width, min(shot_im.height, max_src_h)))
    shot_im = shot_im.resize((box_w, round(shot_im.height * scale)), Image.LANCZOS)
    y0 = STRIP + PAD - 6
    im.paste(shot_im, (PAD, y0))
    d.rectangle([PAD - 1, y0 - 1, PAD + shot_im.width, y0 + shot_im.height], outline="#d0d7de", width=2)
    if cropped:  # fade the cut edge into the page so it reads as "continues"
        for k in range(120):
            y = y0 + shot_im.height - 120 + k
            row = im.crop((PAD, y, PAD + shot_im.width, y + 1))
            im.paste(Image.blend(row, Image.new("RGB", row.size, PAGE), k / 120), (PAD, y))
    if shot == "final":  # facts from the thread: panels at 1d7c818, 1bdcf1d, 839703f; merge commit 52d2886
        y = y0 + shot_im.height + 70
        for line, fnt, color in [("Three panels: 1/3, 1/3, then 2/3 PASS at 839703f.", bold, "#1f2328"),
                                 ("bot.py squash-merged 52d2886 through the owner's gh.", bold, "#1f2328"),
                                 ("The owner steered with \"continue\" comments; no human approved or merged.", reg, "#59636e")]:
            d.text((PAD, y), line, font=fnt, fill=color)
            y += 64
    return im


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", required=True, help="folder with the thread captures")
    parser.add_argument("--brand", default=str(ROOT / "brand/brand.json"))
    args = parser.parse_args()
    brand, raw = brandlib.load(args.brand), Path(args.raw)
    work = Path(tempfile.mkdtemp(prefix="pr19-"))
    try:
        files = []
        for i, (shot, caption, accent, secs) in enumerate(STEPS):
            img = frame(raw, brand["repo"], i, shot, caption, accent)
            for _ in range(round(secs * FPS)):
                path = work / f"f{len(files):03d}.png"
                img.save(path)
                files.append(str(path))
        out = ROOT / "docs/images/pr-19-thread.gif"
        subprocess.run([brandlib.tool("gifski"), "--quiet", "--fps", str(FPS), "--width", "960", "-o", str(out), *files],
                       check=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
