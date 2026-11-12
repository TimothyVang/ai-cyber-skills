"""Render docs/images/how-it-works.gif: an illustrated PR conversation in a brand's names and colors.

Frames are drawn with Pillow at 2x and encoded with gifski. A branded build shows this GIF where the upstream
shows the capture of its own real PR thread.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from brandlib import font, palette, tool

S = 2
W, H = 960, 540
FPS = 2


def render(brand: dict, out: Path) -> Path:
    p = palette(brand)
    BG, PANEL, EDGE, TEXT, MUTED = p["BG"], p["PANEL"], p["PANEL_EDGE"], p["TEXT"], p["MUTED"]
    thread_bg = p["BG"]
    steps = [("Kickoff", p["SKY"]), ("Conflicts", p["AUTHOR"]), ("Review", p["REVIEWER"]), ("Answer", p["AUTHOR"]),
             ("Re-review", p["REVIEWER"]), ("Panel", p["AMBER"]), ("Merge gate", p["ACCENT"])]
    colors = {"coordinator": p["SKY"], "author": p["AUTHOR"], "reviewer": p["REVIEWER"], "verifier": p["AMBER"], "panel": p["AMBER"]}
    # (step index, role label, agent, color key, body lines)
    cards = [
        (0, "coordinator", "", "coordinator", ["Goal, acceptance criteria, evidence so far.", "Head 3f9c2ab."]),
        (1, "author", "omp", "author", ["Base conflicted: merged origin/main into the head,", "resolved the conflict, checks pass. Pushed."]),
        (2, "reviewer", "codex", "reviewer", ['{"findings":[{"id":"F1","severity":"P1",', '  "file":"cart.py","line":42, ...}]}']),
        (3, "author", "omp", "author", ['{"responses":[{"id":"F1","action":"fixed",', '  "sha":"a91c3f2", ...}]}']),
        (4, "reviewer", "codex", "reviewer", ["Re-reviewed a91c3f2.", "No P0 or P1 open."]),
        (5, "verifier 1", "omp", "verifier", ['{"vote":"PASS","evidence":"..."}']),
        (5, "verifier 2", "codex", "verifier", ['{"vote":"PASS","evidence":"..."}']),
        (5, "verifier 3", "claude", "verifier", ['{"vote":"PASS","evidence":"..."}']),
        (5, "panel", "", "panel", ["3/3 PASS at a91c3f2."]),
        (6, "coordinator", "", "coordinator", ["Same head, required checks green, not conflicting,", "own PR, authorized. Merged a91c3f2."]),
    ]
    head = {0: "3f9c2ab", 1: "7d1e0b4", 2: "7d1e0b4", 3: "a91c3f2", 4: "a91c3f2", 5: "a91c3f2", 6: "a91c3f2"}
    sans, sansb, mono = (lambda s: font("regular", s * S)), (lambda s: font("bold", s * S)), (lambda s: font("mono", s * S))
    bot = f"{brand['slug']}-<login>[bot]"

    def rr(d, box, r, fill=None, outline=None, width=1):
        d.rounded_rectangle([v * S for v in box], r * S, fill=fill, outline=outline, width=width * S)

    def text(d, xy, s, f, fill):
        d.text((xy[0] * S, xy[1] * S), s, font=f, fill=fill)

    def frame(step, ncards):
        im = Image.new("RGB", (W * S, H * S), BG)
        d = ImageDraw.Draw(im)
        text(d, (32, 22), f"{brand['name']}: a PR, talked out by bots", sansb(22), TEXT)
        text(d, (32, 54), "Illustration of the steps. Every turn is a comment in the PR thread.", sans(13), MUTED)
        for i, (name, color) in enumerate(steps):
            y = 100 + i * 56
            active, done = i == step, i < step
            rr(d, (28, y, 268, y + 44), 12, fill=PANEL if active else BG, outline=color if active else EDGE, width=2 if active else 1)
            cx, cy = 52, y + 22
            d.ellipse([(cx - 12) * S, (cy - 12) * S, (cx + 12) * S, (cy + 12) * S], fill=color if (active or done) else EDGE)
            text(d, (cx - 4, cy - 10), str(i + 1), sansb(13), BG if (active or done) else MUTED)
            text(d, (76, y + 10), name, sansb(16) if active else sans(16), TEXT if (active or done) else MUTED)
        px0, py0, px1, py1 = 296, 92, 932, 508
        rr(d, (px0, py0, px1, py1), 16, fill=thread_bg, outline=EDGE)
        text(d, (px0 + 20, py0 + 14), "Fix rounding in coupon totals #42", sansb(16), TEXT)
        merged = step == 6 and ncards == len(cards)
        rr(d, (px1 - 92, py0 + 12, px1 - 18, py0 + 38), 13, fill=p["MERGED"] if merged else "#238636")
        label = "Merged" if merged else "Open"
        text(d, (px1 - 55 - (24 if merged else 16), py0 + 15), label, sansb(13), "#ffffff")
        d.line([(px0 + 1) * S, (py0 + 50) * S, (px1 - 1) * S, (py0 + 50) * S], fill=EDGE, width=S)
        shown = cards[:ncards]
        room, keep = py1 - py0 - 66, []
        for c in reversed(shown):
            h = 62 + 21 * len(c[4]) + 10
            if room - h < 0:
                break
            room -= h
            keep.insert(0, c)
        y = py0 + 62
        name_font = sansb(13.5)
        name_w = d.textlength(bot, font=name_font) / S
        for k, (si, role, agent, ckey, lines) in enumerate(keep):
            h = 62 + 21 * len(lines)
            newest = k == len(keep) - 1 and si == step
            color = colors[ckey]
            rr(d, (px0 + 16, y, px1 - 16, y + h), 12, fill=PANEL, outline=color if newest else EDGE, width=2 if newest else 1)
            d.ellipse([(px0 + 30) * S, (y + 12) * S, (px0 + 54) * S, (y + 36) * S], fill=color)
            text(d, (px0 + 64, y + 13), bot, name_font, TEXT)
            text(d, (px0 + 64 + name_w + 10, y + 14), "commented", sans(13), MUTED)
            sig = f"{brand['slug']} {role}" + (f" · {agent}" if agent else "") + f" · head {head[si]}"
            text(d, (px0 + 64, y + 36), sig, sansb(13), color)
            for j, line in enumerate(lines):
                f = mono(12.5) if line.lstrip().startswith(("{", '"')) else sans(13.5)
                text(d, (px0 + 64, y + 60 + j * 21), line, f, TEXT)
            y += h + 10
        rr(d, (28, 520, 932, 526), 3, fill=PANEL)
        rr(d, (28, 520, 28 + (932 - 28) * (step + 1) / len(steps), 526), 3, fill=steps[step][1])
        return im

    # (step, cards visible, seconds on screen)
    plan = []
    for step in range(len(steps)):
        first = next(i for i, c in enumerate(cards) if c[0] == step)
        last = max(i for i, c in enumerate(cards) if c[0] == step)
        plan.append((step, first, 1.0))
        for k in range(first + 1, last + 2):
            plan.append((step, k, 1.5))
    plan.append((len(steps) - 1, len(cards), 3.0))
    gifski = tool("gifski")
    work = Path(tempfile.mkdtemp(prefix="brand-demo-"))
    try:
        files = []
        for step, n, secs in plan:
            im = frame(step, n)
            for _ in range(round(secs * FPS)):
                path = work / f"f{len(files):03d}.png"
                im.save(path)
                files.append(str(path))
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([gifski, "--quiet", "--fps", str(FPS), "--width", str(W), "--quality", "90", "-o", str(out), *files],
                       check=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return out
