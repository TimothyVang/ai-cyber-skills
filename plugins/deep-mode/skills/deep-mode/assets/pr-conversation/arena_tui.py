"""The arena's terminal view: the battle screen drawn with half-block pixels and box-drawing in any shell.

`frame(ui, width, height, mode)` is pure: it returns the screen as `height` strings of `width` columns
(ANSI colour codes only in the colour modes). `run()` owns the terminal: alternate screen, hidden cursor,
raw keys (msvcrt on Windows, termios + select on POSIX), redraw on resize, live refetch, and restores
everything on exit, Ctrl+C or an exception.
"""

import datetime
import os
import queue
import re
import shutil
import sys
import threading
import time
import unicodedata

FOLD = {"—": "-", "–": "-", "‑": "-", "·": "-", "•": "*", "×": "x", "→": "->", "←": "<-", "⇒": "=>",
        "…": "...", "‘": "'", "’": "'", "“": '"', "”": '"', "≥": ">=", "≤": "<=", "≠": "!=",
        "✓": "v", "✔": "v", "✗": "x", "✘": "x", "°": "o", "\u00a0": " "}


def fold(text: str) -> str:
    """Printable ASCII for the 8x8 font and the terminal: typography mapped, accents stripped, markdown
    ticks and control characters (an ESC in a comment must not reach the terminal) dropped."""
    out = []
    for ch in (text or "").replace("`", ""):
        if ch < " " or ch == "\x7f":
            out.append(" ")
        elif ord(ch) < 128:
            out.append(ch)
        elif ch in FOLD:
            out.append(FOLD[ch])
        else:
            out.append(unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode())
    return re.sub(r" {2,}", " ", "".join(out)).strip()


MIN_W, MIN_H = 60, 20
TYPE_CPS = 60         # typewriter speed, characters per second
LIVE_SECONDS = 15
PAL = [(0xE0, 0xEF, 0xC4), (0xA3, 0xC4, 0x7A), (0x4F, 0x7D, 0x4A), (0x1D, 0x33, 0x24)]  # lightest .. darkest
COLOUR = ("truecolor", "256")
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
# Unicode glyphs are those the Windows console fonts (Consolas, Cascadia) carry: ► not ▶.
GLYPHS = {
    "unicode": dict(h="─", v="│", tl="┌", tr="┐", bl="└", br="┘", H="═", V="║", TL="╔", TR="╗", BL="╚", BR="╝",
                    dot="·", more="▼", pip="●", nopip="○", failpip="×", full="█", empty="░", cursor="►",
                    up="▲", down="▼", left="←", right="→", updown="↑↓"),
    "ascii": dict(h="-", v="|", tl="+", tr="+", bl="+", br="+", H="=", V="|", TL="+", TR="+", BL="+", BR="+",
                  dot="-", more="v", pip="*", nopip="o", failpip="x", full="#", empty=".", cursor=">",
                  up="^", down="v", left="<-", right="->", updown="Up/Down"),
}
SHADES = {"mono": {"full": "█", "dark": "▓", "top": "▀", "bottom": "▄", "light": "░"},
          "ascii": {"full": "#", "dark": "#", "top": '"', "bottom": "_", "light": ":"}}


def glyphs(mode: str) -> dict:
    return GLYPHS["ascii" if mode == "ascii" else "unicode"]


def colour_mode(env, ascii_flag: bool = False) -> str:
    """truecolor, 256, mono (NO_COLOR: no escape codes, Unicode shading) or ascii (7-bit only)."""
    if ascii_flag:
        return "ascii"
    if env.get("NO_COLOR"):
        return "mono"
    if env.get("COLORTERM", "").lower() in ("truecolor", "24bit") or env.get("WT_SESSION"):
        return "truecolor"
    return "256"


def xterm256(rgb) -> int:
    """The nearest xterm-256 colour (6x6x6 cube or grey ramp)."""
    levels = [0, 95, 135, 175, 215, 255]
    best, best_d = 16, None
    for i in range(16, 256):
        if i < 232:
            n = i - 16
            c = (levels[n // 36], levels[n // 6 % 6], levels[n % 6])
        else:
            c = (8 + 10 * (i - 232),) * 3
        d = sum((a - b) ** 2 for a, b in zip(rgb, c))
        if best_d is None or d < best_d:
            best, best_d = i, d
    return best


XTERM = [xterm256(c) for c in PAL]


def sgr(fg: int, bg: int, mode: str) -> str:
    if mode == "truecolor":
        return "\x1b[38;2;{};{};{};48;2;{};{};{}m".format(*PAL[fg], *PAL[bg])
    return f"\x1b[38;5;{XTERM[fg]};48;5;{XTERM[bg]}m"


# ---------- dialog text ----------

def split_long(word: str, n: int) -> list[str]:
    """A word wider than the box, broken after a separator near the end (paths, URLs) or hard at n."""
    out = []
    while len(word) > n:
        head = word[:n]
        k = max(head.rfind(c) for c in "/.:-_,=&?")
        at = k + 1 if k >= n // 2 else n
        out.append(word[:at])
        word = word[at:]
    return out + [word]


def wrap(text: str, n: int) -> list[str]:
    out, line = [], ""
    for word in text.split():
        if len(word) > n:
            if line:
                out.append(line)
                line = ""
            *full, word = split_long(word, n)
            out.extend(full)
        if not line:
            line = word
        elif len(line) + 1 + len(word) <= n:
            line += " " + word
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out or [""]


def pages(text: str, n: int) -> list[tuple[str, str]]:
    """Dialog boxes of two lines each, the whole text: the terminal has no transcript beside it."""
    lines = wrap(text, n)
    return [(lines[i], lines[i + 1] if i + 1 < len(lines) else "") for i in range(0, len(lines), 2)]


def build_boxes(t: dict, n: int) -> list[dict]:
    boxes = []
    for s in t["intro"]:
        boxes += [{"turn": -1, "lines": p} for p in pages(s, n)]
    for i, v in enumerate(t["turns"]):
        for s in v["lines"]:
            boxes += [{"turn": i, "lines": p} for p in pages(s, n)]
    for s in t["outro"]:
        boxes += [{"turn": len(t["turns"]), "lines": p} for p in pages(s, n)]
    return boxes


def text_cols(width: int) -> int:
    return max(10, width - 6)  # border, space, text, space, the ▼, space, border; tiny windows get the message


def box_key(t: dict, boxes: list[dict], i: int):
    """Where box i sits, independent of wrapping width: (turn id or intro/outro, ordinal within it)."""
    tu = boxes[i]["turn"]
    key = "intro" if tu < 0 else "outro" if tu >= len(t["turns"]) else t["turns"][tu]["id"]
    ord_ = 0
    while i - 1 - ord_ >= 0 and boxes[i - 1 - ord_]["turn"] == tu:
        ord_ += 1
    return key, ord_


# ---------- state ----------

class UI:
    """Everything the screen shows; keys and ticks change it, frame() only reads it."""

    def __init__(self, threads: list[dict], live: bool = False, now: float = 0.0):
        self.threads, self.live, self.now = threads, live, now
        self.mode, self.sel, self.th = "menu", 0, None
        self.boxes, self.cols, self.bi, self.typed, self.done_at = [], None, 0, 0.0, None
        self.auto, self.want_refresh = False, False
        self.status, self.error = "", ""  # "live · updated hh:mm" after the last good fetch; the last fetch error
        if len(threads) == 1:
            self.open(0)

    # navigation
    def open(self, i: int) -> None:
        self.th, self.sel, self.mode = self.threads[i], i, "battle"
        self.boxes, self.cols = [], None
        self.go(0, full=False)

    def layout(self, cols: int) -> None:
        """Rewrap the dialog for a new width, keeping the reader on the same text."""
        if self.mode != "battle" or cols == self.cols:
            return
        key = box_key(self.th, self.boxes, self.bi) if self.boxes else ("intro", 0)
        self.boxes, self.cols = build_boxes(self.th, cols), cols
        self.bi = self.locate(key)
        self.typed = min(self.typed, self.box_len())

    def locate(self, key) -> int:
        name, ord_ = key
        t = self.th
        tu = -1 if name == "intro" else len(t["turns"]) if name == "outro" else \
            next((i for i, v in enumerate(t["turns"]) if v["id"] == name), None)
        first = next((i for i, b in enumerate(self.boxes) if b["turn"] == tu), None)
        if first is None:
            return min(self.bi, len(self.boxes) - 1)
        last = max(i for i, b in enumerate(self.boxes) if b["turn"] == tu)
        return min(first + ord_, last)

    def box_len(self) -> int:
        if not self.boxes:
            return 0
        a, b = self.boxes[self.bi]["lines"]
        return len(a) + len(b)

    def go(self, i: int, full: bool) -> None:
        self.bi = max(0, min(len(self.boxes) - 1, i)) if self.boxes else 0
        self.typed = float(self.box_len()) if full else 0.0
        self.done_at = self.now if full else None

    def advance(self) -> None:
        if self.typed < self.box_len():
            self.typed, self.done_at = float(self.box_len()), self.now
        elif self.bi < len(self.boxes) - 1:
            self.go(self.bi + 1, full=False)

    def first_box(self, turn: int) -> int:
        return next((i for i, b in enumerate(self.boxes) if b["turn"] == turn), 0)

    def key(self, k: str):
        """Apply one key; returns "quit" to leave."""
        if k in ("q", "Q", "ctrl-c"):
            return "quit"
        if k in ("r", "R"):
            self.want_refresh = True
            return None
        if self.mode == "menu":
            if k == "up":
                self.sel = max(0, self.sel - 1)
            elif k == "down":
                self.sel = min(len(self.threads) - 1, self.sel + 1)
            elif k in ("enter", "space", "right") and self.threads:
                self.open(self.sel)
            elif k == "esc":
                return "quit"
            return None
        if k in ("enter", "space", "right"):
            self.advance()
        elif k in ("left", "backspace", "b", "B"):
            if self.bi > 0:
                self.go(self.bi - 1, full=True)
        elif k in ("a", "A"):
            self.auto = not self.auto
        elif k in ("l", "L", "end"):
            if self.th["turns"]:
                self.go(self.first_box(len(self.th["turns"]) - 1), full=False)
        elif k == "home":
            self.go(0, full=False)
        elif k == "esc":
            self.mode, self.th, self.boxes, self.cols = "menu", None, [], None
        return None

    def tick(self, now: float) -> None:
        dt, self.now = max(0.0, now - self.now), now
        if self.mode != "battle" or not self.boxes:
            return
        n = self.box_len()
        if self.typed < n:
            self.typed = min(float(n), self.typed + dt * TYPE_CPS)
            if self.typed >= n:
                self.done_at = now
        elif self.auto and self.bi < len(self.boxes) - 1 and now - (self.done_at or now) > 1.0 + n * 0.025:
            self.go(self.bi + 1, full=False)

    def apply(self, threads: list[dict]) -> None:
        """New data from the live refetch: same thread, same text; a reader waiting at the end moves on."""
        if self.mode != "battle":
            self.threads = threads
            self.sel = min(self.sel, max(0, len(threads) - 1))
            return
        was = self.th
        i = next((j for j, t in enumerate(threads) if t["url"] == was["url"]), None)
        if i is None:
            threads = [was, *threads]
            i = 0
        self.threads, self.sel = threads, i
        if threads[i] is was:
            return
        key = box_key(was, self.boxes, self.bi) if self.boxes else ("intro", 0)
        old_turns, typed = len(was["turns"]), self.typed
        self.th = threads[i]
        self.boxes = build_boxes(self.th, self.cols) if self.cols else []
        if not self.boxes:
            return
        if key[0] == "outro" and len(self.th["turns"]) > old_turns:
            self.go(self.first_box(old_turns), full=False)
        else:
            self.bi = self.locate(key)
            self.typed = min(typed, self.box_len())

    # what the screen shows
    def shown_turn(self) -> int:
        return self.boxes[self.bi]["turn"] if self.boxes else -1

    def score(self) -> dict:
        t, tu = self.th, self.shown_turn()
        zero = {"open": 0, "peak": 0, "votes": [None, None, None], "merged": False}
        if tu < 0 or not t["turns"]:
            return {**zero, "merged": tu >= len(t["turns"]) and t["state"] == "merged"}
        if tu >= len(t["turns"]):
            return {**t["turns"][-1]["after"], "merged": t["state"] == "merged"}
        return t["turns"][tu]["after"]

    def speaker(self):
        t, tu = self.th, self.shown_turn()
        return None if tu < 0 or not t["turns"] else t["turns"][min(tu, len(t["turns"]) - 1)]


# ---------- drawing ----------

class Grid:
    """Cells of (char, fg, bg); a pixel cell is (None, top, bottom) with palette indexes or None for clear."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.cells = [[(" ", 3, 0)] * w for _ in range(h)]

    def text(self, x: int, y: int, s: str, fg: int = 3) -> None:
        if 0 <= y < self.h:
            row = self.cells[y]
            for i, ch in enumerate(s):
                if 0 <= x + i < self.w:
                    row[x + i] = (ch, fg, 0)

    def right(self, x_end: int, y: int, s: str, fg: int = 3) -> None:
        self.text(x_end - len(s), y, s, fg)

    def pixels(self, x: int, y: int, top, bottom) -> None:
        if 0 <= y < self.h and 0 <= x < self.w:
            self.cells[y][x] = (None, top, bottom)

    def sprite(self, x: int, y: int, rows: list[str], scale: int) -> None:
        val = lambda p: None if p == "." else int(p)  # noqa: E731
        for r in range(8 * scale):
            top, bottom = rows[(2 * r) // scale], rows[(2 * r + 1) // scale]
            for c in range(16 * scale):
                a, b = val(top[c // scale]), val(bottom[c // scale])
                if a is not None or b is not None:
                    self.pixels(x + c, y + r, a, b)

    def platform(self, cx: int, y: int, half: int) -> None:
        """A light ellipse to stand on: one cell row, its ends on the lower half."""
        for x in range(cx - half, cx + half):
            edge = x in (cx - half, cx + half - 1)
            self.pixels(x, y, None if edge else 1, 1 if edge else None)

    def box(self, x: int, y: int, w: int, h: int, g: dict, double: bool = False) -> None:
        tl, tr, bl, br, hz, vt = (("TL", "TR", "BL", "BR", "H", "V") if double else ("tl", "tr", "bl", "br", "h", "v"))
        self.text(x, y, g[tl] + g[hz] * (w - 2) + g[tr])
        for yy in range(y + 1, y + h - 1):
            self.text(x, yy, g[vt] + " " * (w - 2) + g[vt])
        self.text(x, y + h - 1, g[bl] + g[hz] * (w - 2) + g[br])


def shade(top, bottom, mode: str) -> str:
    s = SHADES[mode]
    t, b = top or 0, bottom or 0
    if t >= 2 and b >= 2:
        return s["full"] if t == b == 3 else s["dark"]
    if t >= 2:
        return s["top"]
    if b >= 2:
        return s["bottom"]
    return s["light"] if t or b else " "


def emit(grid: Grid, mode: str) -> list[str]:
    lines = []
    for row in grid.cells:
        out, cur = [], None
        for ch, a, b in row:
            if ch is None:  # two pixels in one cell
                t, u = a or 0, b or 0
                if mode in COLOUR:
                    ch, fg, bg = ("▀", t, u) if t != u else (" ", 3, t)
                else:
                    ch, fg, bg = shade(a, b, mode), 3, 0
            else:
                fg, bg = a, b
            if mode in COLOUR and (fg, bg) != cur:
                out.append(sgr(fg, bg, mode))
                cur = (fg, bg)
            out.append(ch)
        if mode in COLOUR:
            out.append("\x1b[0m")
        lines.append("".join(out))
    return lines


def cut(s: str, n: int) -> str:
    return s if len(s) <= n else s[:max(0, n - 1)] + "."


def status_of(data: dict, g: dict) -> tuple[str, str]:
    """(live line, error) after a fetch: the error keeps the last good update time beside it."""
    error = "error: " + fold(data["errors"][0])[:200] if data.get("errors") else ""
    when = updated_at(data)
    return (f"live {g['dot']} updated {when}" if when else ""), error


def took(ui, got: dict, g: dict) -> None:
    """A refetch result: threads (with or without per-thread errors) set the time; only a failed fetch keeps the old one."""
    live, ui.error = status_of(got, g)
    if got.get("threads") is not None:
        ui.status = live


def dialog_rows(height: int) -> tuple[int, tuple[int, int]]:
    """The dialog's height and its two text rows (offsets inside it)."""
    if height < 26:
        return 4, (1, 2)
    if height < 32:
        return 5, (1, 3)
    return 7, (2, 4)


def draw_dialog(grid: Grid, g: dict, lines: tuple[str, str], typed: int, more: bool,
                left: str, right: str, bottom: str, bottom_colour: int = 2) -> None:
    w, (h, (r1, r2)) = grid.w, dialog_rows(grid.h)
    y = grid.h - h
    grid.box(0, y, w, h, g, double=True)
    if left:
        grid.text(2, y, f" {left} ")
    if right:
        grid.right(w - 2, y, f" {cut(right, w - 6 - len(left) - 4)} ", 2)
    if bottom:
        grid.text(2, y + h - 1, f" {cut(bottom, w - 6)} ", bottom_colour)
    a, b = lines
    grid.text(2, y + r1, a[:typed])
    grid.text(2, y + r2, b[:max(0, typed - len(a))])
    if more:
        grid.text(w - 3, y + r2, g["more"])


def hints(g: dict, menu: bool, room: int) -> str:
    """The longest key legend that fits in `room` columns."""
    d, L = g["dot"], g["left"]
    if menu:
        options = [f"{g['updown']} pick {d} Enter watch {d} R refetch {d} q quit", f"{g['updown']} Enter R q"]
    else:
        options = [f"Enter next {d} {L} back {d} A auto {d} L latest {d} Esc threads {d} q quit",
                   f"Enter next {d} {L} back {d} A auto {d} L latest {d} Esc {d} q",
                   f"Enter {L} A L Esc q"]
    return next((o for o in options if len(o) <= room), options[-1])


def top_right(ui: UI, g: dict) -> str:
    marks = (["AUTO"] if ui.auto and ui.mode == "battle" else []) + ([ui.status] if ui.live and ui.status else [])
    return f" {g['dot']} ".join(marks)


def bottom_line(ui: UI, g: dict, width: int, menu: bool) -> tuple[str, int]:
    """The last error if there is one (darkest ink), else the key legend (quiet ink)."""
    if ui.error:
        return ui.error, 3
    return hints(g, menu, width - 6), 2


def draw_scene(grid: Grid, g: dict, sprites: dict, t: dict, score: dict, v, final: bool, scene: int) -> None:
    """The battle scene above the dialog, in rows [0, scene): the thread top right with its status bracket,
    the speaker `v` (a turn, or None) bottom left with its own. `final`: past the last turn, so a closed
    thread's state shows."""
    W = grid.w
    scale = 2 if W >= 110 and scene >= 2 * 16 else 1
    sh, sw = 8 * scale, 16 * scale
    plat = 1 if scene - 2 * sh >= 2 else 0
    pad = (scene - 2 * sh - 2 * plat) // 3
    top_y, bot_y = pad, scene - pad - plat - sh

    # the thread: sprite on the right, status bracket on the left
    ox = W - sw - max(2, W // 12)
    if plat:
        grid.platform(ox + sw // 2, top_y + sh, sw // 2 + 2)
    grid.sprite(ox, top_y, sprites["pr" if t["kind"] == "pr" else "issue"], scale)
    bw = min(34, ox - 6)
    y = top_y + max(0, (sh - 4) // 2)
    grid.text(2, y, cut(fold(t["label"]).upper(), bw))
    state = None
    if score["merged"] or (final and t["state"] != "open"):
        state = "MERGED" if score["merged"] else t["state"].upper()
    if state and t["kind"] == "pr":
        grid.right(2 + bw, y, state, 2)
    bar_w = bw - 6
    fill = round(bar_w * score["open"] / score["peak"]) if score["peak"] else 0
    grid.text(2, y + 1, "OPEN ")
    grid.text(7, y + 1, g["full"] * fill, 3)
    grid.text(7 + fill, y + 1, g["empty"] * (bar_w - fill), 2)
    grid.text(2, y + 2, f"{score['open']}/{score['peak']}", 2)
    if t["kind"] == "pr":
        pips = "".join({"PASS": g["pip"], "FAIL": g["failpip"]}.get(v, g["nopip"]) for v in score["votes"])
        grid.right(2 + bw, y + 2, f"VOTE {pips}", 2)
    elif state:
        grid.right(2 + bw, y + 2, state, 2)
    grid.text(0, y + 1, g["v"])
    grid.text(0, y + 2, g["v"])
    grid.text(0, y + 3, g["bl"] + g["h"] * (bw + 1))

    # the speaker: sprite on the left, status bracket on the right
    px = max(2, W // 12)
    if plat:
        grid.platform(px + sw // 2, bot_y + sh, sw // 2 + 2)
    if v:
        grid.sprite(px, bot_y, sprites.get(v["kind"], sprites["author"]), scale)
        pw = min(34, W - (px + sw) - 6)
        x2 = W - pw - 2
        rows = [(v["name"], 3), (v.get("lens") or v.get("agent") or "", 2), ((v.get("model") or "").split("/")[-1], 2)]
        rows = [(fold(s), c) for s, c in rows if s]
        head = v.get("head") or ""
        head = "@" + head[:7] if re.fullmatch(r"[0-9a-f]{7,40}", head) else fold(head)
        bottom = bot_y + sh - 1
        grid.text(x2 + pw, bottom, g["br"])
        grid.text(x2 - 1, bottom, g["h"] * (pw + 1))
        grid.text(x2, bottom - 1, cut(head, pw - 7), 2)
        grid.right(x2 + pw - 1, bottom - 1, (v.get("time") or "")[11:16], 2)
        grid.text(x2 + pw, bottom - 1, g["v"])
        for k, (s, c) in enumerate(reversed(rows)):
            yy = bottom - 2 - k
            grid.text(x2, yy, cut(s, pw - 1), c)
            grid.text(x2 + pw, yy, g["v"])


def draw_battle(grid: Grid, ui: UI, g: dict, sprites: dict) -> None:
    W, H = grid.w, grid.h
    t = ui.th
    draw_scene(grid, g, sprites, t, ui.score(), ui.speaker(), ui.shown_turn() >= len(t["turns"]),
               H - dialog_rows(H)[0])
    n_turns = len(t["turns"])
    turn = f"TURN {max(0, min(ui.shown_turn() + 1, n_turns))}/{n_turns}"
    if ui.boxes:
        box = ui.boxes[ui.bi]
        lines, n = box["lines"], int(ui.typed)
        more = n >= len(lines[0]) + len(lines[1]) and ui.bi < len(ui.boxes) - 1 and int(ui.now * 2.5) % 2 == 0
    else:
        lines, n, more = ("", ""), 0, False
    draw_dialog(grid, g, lines, n, more, turn, top_right(ui, g), *bottom_line(ui, g, W, menu=False))


FRAME_SCENE = 18  # two 8-row sprites, each on a one-row platform: the compact scene of a static frame


def turn_frame(t: dict, i: int, width: int, mode: str, sprites: dict) -> list[str]:
    """Turn i of thread t as one static frame `width` columns wide: the scene after that turn, then a dialog
    box holding every one of its dialog lines, wrapped, in full (the box grows; nothing pages or is cut)."""
    width = max(MIN_W, width)
    v, g = t["turns"][i], glyphs(mode)
    text = [row for line in v["lines"] for row in wrap(line, text_cols(width))]
    grid = Grid(width, FRAME_SCENE + len(text) + 2)
    draw_scene(grid, g, sprites, t, v["after"], v, i == len(t["turns"]) - 1, FRAME_SCENE)
    y = FRAME_SCENE
    grid.box(0, y, width, len(text) + 2, g, double=True)
    left = f"TURN {i + 1}/{len(t['turns'])}"
    grid.text(2, y, f" {left} ")
    where = f"{fold(t['label'])} {g['dot']} #{v['id']}"  # one quote level: nested same-quote f-strings need 3.12
    grid.right(width - 2, y, f" {cut(where, width - len(left) - 10)} ", 2)
    for k, row in enumerate(text):
        grid.text(2, y + 1 + k, row)
    return emit(grid, mode)


FRAMES_LAST = 3  # turns per thread when neither since nor last is given


def frames(threads: list[dict], since: int = 0, last=None, width: int = 80, mode: str = "mono",
           sprites=None) -> list[str]:
    """Static frames for a chat: per thread a header, then a frame for each turn newer than comment
    `since` (only the newest `last` of them; the newest FRAMES_LAST when neither is given), then one
    closing line naming the newest comment id, for the next call's since."""
    if not since and last is None:
        last = FRAMES_LAST
    g, out, newest, shown = glyphs(mode), [], since, 0
    for t in threads:
        picked = [i for i, v in enumerate(t["turns"]) if v["id"] > since]
        if last is not None:
            picked = picked[-last:] if last > 0 else []
        newest = max([newest, *(v["id"] for v in t["turns"])])
        if not picked:
            continue
        out.append(cut(f"{t['label']} {g['dot']} {t['state']} {g['dot']} {fold(t['title'])}", width))
        out.append(fold(t["url"])[:width])
        for i in picked:
            out.extend(turn_frame(t, i, width, mode, sprites))
            out.append("")
            shown += 1
    if not shown:
        out.append(f"arena: no bot turns since {since}" if since else "arena: no bot turns yet")
    out.append(f"arena: newest comment {newest} (next: --since {newest})" if newest else "arena: no comments yet")
    return out


def draw_menu(grid: Grid, ui: UI, g: dict) -> None:
    W, H = grid.w, grid.h
    dlg_h = dialog_rows(H)[0]
    grid.box(0, 0, W, 3, g, double=True)
    grid.text(2, 1, "CONVERSATIONS")
    grid.right(W - 2, 1, str(len(ui.threads)), 2)
    list_h = H - dlg_h - 3
    grid.box(0, 3, W, list_h, g, double=True)
    per = 3 if list_h >= 2 + 3 * 4 else 2
    rows = max(1, (list_h - 2) // per)
    top = max(0, ui.sel - rows + 1)
    many_repos = len({t["repo"] for t in ui.threads}) > 1
    for k, t in enumerate(ui.threads[top:top + rows]):
        i, y = top + k, 4 + k * per
        if i == ui.sel:
            grid.text(2, y, g["cursor"])
        label = fold(t["label"]).upper()
        grid.text(4, y, label)
        grid.text(4 + len(label) + 2, y, f"{len(t['turns'])} TURN{'' if len(t['turns']) == 1 else 'S'}", 2)
        grid.right(W - 3, y, t["state"].upper())
        title = (t["repo"].split("/")[1] + ": " if many_repos else "") + t["title"]
        grid.text(4, y + 1, cut(fold(title), W - 8), 2)
    if top > 0:
        grid.text(W - 5, 3 + list_h - 2, g["up"])
    if top + rows < len(ui.threads):
        grid.text(W - 3, 3 + list_h - 2, g["down"])
    prompt = ("Which conversation?", "") if ui.threads else ("No conversations yet.", "")
    draw_dialog(grid, g, prompt, 999, False, "", top_right(ui, g), *bottom_line(ui, g, W, menu=True))


def frame(ui: UI, width: int, height: int, mode: str, sprites: dict) -> list[str]:
    """The whole screen as `height` lines, each `width` columns once ANSI codes are stripped."""
    if width < MIN_W or height < MIN_H:
        msg = cut(f"make the window larger (at least {MIN_W}x{MIN_H}, now {width}x{height})", width)
        return [msg.ljust(width)] + [" " * width] * (height - 1)
    grid = Grid(width, height)
    g = glyphs(mode)
    if ui.mode == "menu":
        draw_menu(grid, ui, g)
    else:
        draw_battle(grid, ui, g, sprites)
    return emit(grid, mode)


# ---------- keys ----------

POSIX_KEYS = {"[A": "up", "[B": "down", "[C": "right", "[D": "left", "[H": "home", "[F": "end",
              "OA": "up", "OB": "down", "OC": "right", "OD": "left", "OH": "home", "OF": "end",
              "[1~": "home", "[4~": "end", "[7~": "home", "[8~": "end"}
SINGLE = {"\r": "enter", "\n": "enter", " ": "space", "\x7f": "backspace", "\x08": "backspace",
          "\x03": "ctrl-c", "\x1b": "esc"}
WIN_EXT = {"H": "up", "P": "down", "K": "left", "M": "right", "G": "home", "O": "end"}


def parse_posix(data: str) -> list[str]:
    """Key names from a burst of terminal input; a lone ESC is the Esc key."""
    keys, i = [], 0
    while i < len(data):
        ch = data[i]
        if ch == "\x1b" and i + 1 < len(data) and data[i + 1] in "[O":
            j = i + 2
            while j < len(data) and not (data[j].isalpha() or data[j] == "~"):
                j += 1
            seq = data[i + 1:j + 1]
            keys.append(POSIX_KEYS.get(seq, "unknown"))
            i = j + 1
            continue
        keys.append(SINGLE.get(ch, ch))
        i += 1
    return keys


def parse_windows(chars: list[str]) -> list[str]:
    """Key names from msvcrt.getwch() results: '\\x00' or '\\xe0' prefixes an arrow or Home/End code."""
    keys, i = [], 0
    while i < len(chars):
        ch = chars[i]
        if ch in ("\x00", "\xe0") and i + 1 < len(chars):
            keys.append(WIN_EXT.get(chars[i + 1], "unknown"))
            i += 2
            continue
        keys.append(SINGLE.get(ch, ch))
        i += 1
    return keys


# ---------- terminal ----------

class Terminal:
    """Full-screen session: VT output (enabled on Windows), raw keys, all restored on exit."""

    ENTER = "\x1b[?1049h\x1b[?25l\x1b[?7l\x1b[2J"
    LEAVE = "\x1b[0m\x1b[?7h\x1b[?25h\x1b[?1049l"

    def __init__(self):
        self.win = os.name == "nt"
        self.saved = None

    def __enter__(self):
        if self.win:
            self.saved = enable_vt()
            if self.saved is None:
                raise OSError("this console can't process VT escape codes")
        else:
            import termios
            fd = sys.stdin.fileno()
            self.saved = termios.tcgetattr(fd)
            raw = termios.tcgetattr(fd)
            raw[3] &= ~(termios.ICANON | termios.ECHO)  # lflags; ISIG stays, so Ctrl+C is SIGINT
            raw[6][termios.VMIN], raw[6][termios.VTIME] = 0, 0
            termios.tcsetattr(fd, termios.TCSANOW, raw)
        self.write(self.ENTER)
        return self

    def __exit__(self, *exc):
        try:
            self.write(self.LEAVE)
        finally:
            if self.win:
                restore_vt(self.saved)
            else:
                import termios
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.saved)
        return False

    @staticmethod
    def write(s: str) -> None:
        sys.stdout.write(s)
        sys.stdout.flush()

    @staticmethod
    def size() -> tuple[int, int]:
        size = shutil.get_terminal_size((80, 24))
        return size.columns, size.lines

    def keys(self, timeout: float) -> list[str]:
        if self.win:
            import msvcrt
            end = time.monotonic() + timeout
            while not msvcrt.kbhit() and time.monotonic() < end:
                time.sleep(0.01)
            chars = []
            while msvcrt.kbhit():
                chars.append(msvcrt.getwch())
                if chars[-1] in ("\x00", "\xe0"):  # kbhit can be false before the key code that must follow
                    chars.append(msvcrt.getwch())
            return parse_windows(chars)
        import select
        fd = sys.stdin.fileno()
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            return []
        data = os.read(fd, 1024)
        while select.select([fd], [], [], 0.02)[0]:  # the rest of an escape sequence
            more = os.read(fd, 1024)
            if not more:
                break
            data += more
        return parse_posix(data.decode("utf-8", "replace"))


def enable_vt():
    """Turn on VT processing and UTF-8 output for this Windows console; None when it can't."""
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = k32.GetStdHandle(-11)
    mode = wintypes.DWORD()
    if not k32.GetConsoleMode(handle, ctypes.byref(mode)):
        return None
    if not k32.SetConsoleMode(handle, mode.value | 0x0004):  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        return None
    cp = k32.GetConsoleOutputCP()
    k32.SetConsoleOutputCP(65001)
    return handle, mode.value, cp


def restore_vt(saved) -> None:
    import ctypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle, mode, cp = saved
    k32.SetConsoleMode(handle, mode)
    k32.SetConsoleOutputCP(cp)


def updated_at(data: dict) -> str:
    try:
        when = datetime.datetime.fromisoformat(data["generated"]).astimezone()
    except (KeyError, ValueError):
        return ""
    return when.strftime("%H:%M")


def run(source, data: dict, mode: str, sprites: dict) -> None:
    """The interactive session; `source.get(force)` refetches (cached) in a background thread."""
    ui = UI(data["threads"], live=True, now=time.monotonic())
    ui.status, ui.error = status_of(data, glyphs(mode))

    updates, wake, stop = queue.Queue(), threading.Event(), threading.Event()

    def refetch():
        while not stop.is_set():
            forced = wake.wait(LIVE_SECONDS)
            wake.clear()
            if stop.is_set():
                return
            try:
                updates.put(source.get(force=forced))
            except Exception as err:  # the screen keeps the last good threads and says why
                updates.put({"errors": [str(err)]})

    threading.Thread(target=refetch, daemon=True).start()
    try:
        with Terminal() as term:
            size, shown = None, None
            while True:
                for k in term.keys(1 / 30):
                    if ui.key(k) == "quit":
                        return
                if ui.want_refresh:
                    ui.want_refresh, ui.status = False, "refreshing..."
                    wake.set()
                try:
                    while True:
                        got = updates.get_nowait()
                        if got.get("threads") is not None:
                            ui.apply(got["threads"])
                        took(ui, got, glyphs(mode))
                except queue.Empty:
                    pass
                w, h = term.size()
                if (w, h) != size:
                    size, shown = (w, h), None
                    term.write("\x1b[0m\x1b[2J")
                ui.layout(text_cols(w))
                ui.tick(time.monotonic())
                lines = frame(ui, w, h, mode, sprites)
                out = [f"\x1b[{i + 1};1H{line}" for i, line in enumerate(lines) if shown is None or shown[i] != line]
                if out:
                    term.write("".join(out))
                shown = lines
    finally:
        stop.set()
        wake.set()
