"""Write the three docs diagrams as hand-laid-out SVG in a brand's names and colors."""
from pathlib import Path
from xml.sax.saxutils import escape

from brandlib import palette

SANS = "ui-sans-serif, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'Cascadia Mono', Consolas, Menlo, monospace"


def render(brand: dict, out: Path) -> list:
    out.mkdir(parents=True, exist_ok=True)
    p = palette(brand)
    BG, EDGE, PANEL, PANEL_EDGE, TEXT, MUTED = p["BG"], p["EDGE"], p["PANEL"], p["PANEL_EDGE"], p["TEXT"], p["MUTED"]
    VIOLET, SKY, CLAUDE, CODEX, AMBER, MERGED = p["ACCENT"], p["SKY"], p["AUTHOR"], p["REVIEWER"], p["AMBER"], p["MERGED"]
    slug, trigger = brand["slug"], brand["botTrigger"]

    def doc(w, h, title, desc, body):
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">
<title id="t">{escape(title)}</title>
<desc id="d">{escape(desc)}</desc>
<defs>
<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{MUTED}"/></marker>
<marker id="ahA" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{AMBER}"/></marker>
<marker id="ahV" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{VIOLET}"/></marker>
<marker id="ahS" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{SKY}"/></marker>
</defs>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="24" fill="{BG}" stroke="{EDGE}" stroke-width="2"/>
{body}
</svg>
"""

    def t(x, y, s, size=15, fill=TEXT, weight=400, anchor="start", font=SANS, extra=""):
        return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
                f'fill="{fill}" text-anchor="{anchor}"{extra}>{escape(s)}</text>')

    def box(x, y, w, h, accent, title, mono=None, note=None, fill=PANEL, rx=14):
        parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{PANEL_EDGE}" stroke-width="1.5"/>',
                 f'<rect x="{x}" y="{y+14}" width="4" height="{h-28}" rx="2" fill="{accent}"/>',
                 t(x + 20, y + 32, title, 17, TEXT, 600)]
        yy = y + 32
        if mono:
            yy += 26
            parts.append(t(x + 20, yy, mono, 14, accent, 500, font=MONO))
        if note:
            yy += 24
            parts.append(t(x + 20, yy, note, 13.5, MUTED))
        return "\n".join(parts)

    def arrow(x1, y1, x2, y2, color=MUTED, marker="ah", both=False, dash=None, width=2):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        s = f' marker-start="url(#{marker})"' if both else ""
        return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{d}'
                f'{s} marker-end="url(#{marker})"/>')

    def chip(x, y, label, color):
        w = 24 + 7.1 * len(label)
        return (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="30" rx="15" fill="{PANEL}" stroke="{color}" stroke-width="1.5"/>'
                + t(x + w / 2, y + 20, label, 13.5, TEXT, 500, "middle")), w

    def panel(x, y, w, h, color, label):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="none" stroke="{color}" stroke-width="1.5" stroke-dasharray="6 6" opacity="0.8"/>'
                + f'<rect x="{x+20}" y="{y-13}" width="{8.6*len(label)+24:.0f}" height="26" rx="13" fill="{BG}"/>'
                + t(x + 32, y + 5, label, 14, color, 700, extra=' letter-spacing="1.2"'))

    written = []

    def save(name, text):
        (out / name).write_text(text, encoding="utf-8", newline="\n")
        written.append(out / name)

    # 1. how it works
    b = [t(40, 58, "How the bots work", 26, TEXT, 700),
         t(40, 86, "A private GitHub App gives them a name. A poller on your machine does the work. Any ACP agent, on your own subscription logins.", 15, MUTED),
         panel(30, 130, 360, 440, VIOLET, "GITHUB"),
         box(50, 160, 320, 100, VIOLET, "Your private GitHub App", f"{slug}-<login>", "installing it on a repo is the opt-in"),
         box(50, 296, 320, 100, VIOLET, "PR and issue threads", f"{slug}-<login>[bot]", "every agent turn, signed by its role"),
         box(50, 432, 320, 100, VIOLET, "Branches, checks, merges", "gh pr merge --match-head-commit", "your own PRs only, checks green"),
         panel(500, 130, 670, 440, SKY, "YOUR MACHINE"),
         box(520, 160, 290, 100, SKY, f"~/.config/{slug}/", "app key, bot.json, state", "never in prompts, logs or repos"),
         box(520, 296, 290, 100, SKY, "bot.py watch", "polls every 120 s", "the coordinator; gates in code"),
         box(520, 432, 290, 100, SKY, "Your gh and git", "push, open PR, merge", "never rebase or force-push"),
         box(860, 160, 290, 100, CLAUDE, "Author agent", "omp (default)", "or Claude Code, Codex, Gemini CLI, ..."),
         box(860, 296, 290, 100, SKY, "acpx", "Agent Client Protocol", "one session per PR or issue"),
         box(860, 432, 290, 100, CODEX, "Reviewer agent", "omp, another model", "cross-family review on one harness"),
         arrow(390, 210, 500, 210, VIOLET, "ahV", both=True), t(445, 200, "1-hour token", 12.5, MUTED, anchor="middle"),
         arrow(390, 346, 500, 346, VIOLET, "ahV", both=True), t(445, 336, "read, post", 12.5, MUTED, anchor="middle"),
         arrow(390, 482, 500, 482, VIOLET, "ahV", both=True), t(445, 472, "push, merge", 12.5, MUTED, anchor="middle"),
         arrow(665, 262, 665, 294, SKY, "ahS", both=True),
         arrow(665, 398, 665, 430, SKY, "ahS"),
         arrow(810, 346, 860, 346, SKY, "ahS", both=True),
         arrow(1005, 262, 1005, 294, SKY, "ahS", both=True), arrow(1005, 398, 1005, 430, SKY, "ahS", both=True),
         t(1016, 283, "ACP", 12.5, MUTED), t(1005, 151, "ACP agents (omp, Claude Code, Codex, ...)", 12.5, MUTED, 600, "middle"), t(1016, 419, "ACP", 12.5, MUTED)]
    x = 40
    for label, color in [("No webhooks", VIOLET), ("No server", SKY), ("Subscription logins, no API keys", CODEX),
                         ("Agents return text; the coordinator posts it", CLAUDE), ("Merges only on a panel pass", AMBER)]:
        s, w = chip(x, 596, label, color)
        b.append(s)
        x += w + 12
    save("how-it-works.svg", doc(1200, 650, f"How the {slug} bots work",
         f"A private GitHub App named {slug}-<login> posts to PR and issue threads. On your machine, bot.py polls the "
         "installed repos, runs ACP agents through acpx (omp by default, or Claude Code, Codex and others) on your subscription logins, "
         "and pushes and merges with your own gh and git.", "\n".join(b)))

    # 2. PR conversation sequence
    W, H = 1200, 940
    lanes = [("PR thread", "as [bot]", 120, VIOLET), ("Coordinator", "bot.py", 360, SKY), ("Author", "omp (default)", 600, CLAUDE),
             ("Reviewer", "omp, other model", 840, CODEX), ("Verifiers x3", "one-shot, own worktree", 1070, AMBER)]
    b = [t(40, 58, "A PR, talked out by bots", 26, TEXT, 700),
         t(40, 86, "Agents talk over ACP. The coordinator mirrors every turn to the PR thread. It merges only when every gate holds.", 15, MUTED)]
    for name, sub, lx, color in lanes:
        b.append(f'<line x1="{lx}" y1="172" x2="{lx}" y2="{H-40 if lx <= 360 else 660}" stroke="{color}" stroke-width="1.5" stroke-dasharray="3 7" opacity="0.55"/>')
        b.append(f'<rect x="{lx-95}" y="112" width="190" height="60" rx="14" fill="{PANEL}" stroke="{color}" stroke-width="1.5"/>')
        b.append(t(lx, 138, name, 16, TEXT, 700, "middle"))
        b.append(t(lx, 159, sub, 13, color, 500, "middle", MONO if name != "Verifiers x3" else SANS))

    def step(n, y, color=SKY):
        return f'<circle cx="34" cy="{y-5}" r="13" fill="{color}"/>' + t(34, y, str(n), 13.5, BG, 800, "middle")

    def msg(y, x1, x2, label, color=MUTED, marker="ah", mirror=False, dash=None):
        parts = [arrow(x1, y, x2, y, color, marker, dash=dash), t((x1 + x2) / 2, y - 9, label, 13.5, TEXT, 500, "middle")]
        if mirror:
            src = x2 if x2 != 360 else x1
            parts.append(f'<line x1="120" y1="{y+14}" x2="{src}" y2="{y+14}" stroke="{VIOLET}" stroke-width="1.2" stroke-dasharray="2 5" opacity="0.8"/>')
            parts.append(f'<circle cx="120" cy="{y+14}" r="5.5" fill="{VIOLET}"/>')
        return "\n".join(parts)

    rows = [
        (210, 1, [msg(210, 360, 120, "kickoff: goal, acceptance, head sha", VIOLET, "ahV")]),
        (262, 2, [msg(262, 360, 600, "conflicting? merge base into head, push", mirror=True)]),
        (330, 3, [msg(330, 360, 840, "review the diff at this head", mirror=False),
                  msg(372, 840, 360, "findings JSON: P0 / P1 / P2, with evidence", CODEX, mirror=True, dash="0")]),
        (430, 4, [msg(430, 360, 600, "answer every finding", mirror=False),
                  msg(472, 600, 360, "fixed (new sha) or dismissed (with proof)", CLAUDE, mirror=True, dash="0")]),
    ]
    for y, n, parts in rows:
        b.append(step(n, y))
        b.extend(parts)
    b.append(f'<rect x="250" y="300" width="700" height="196" rx="14" fill="none" stroke="{AMBER}" stroke-width="1.3" stroke-dasharray="5 5"/>')
    b.append(step(5, 524, AMBER))
    b.append(t(260, 524, "loop 3-4: re-review each new head until no P0 or P1 is open (maxRounds 3)", 13.5, AMBER, 600))
    b.append(step(6, 584))
    b.append(msg(584, 360, 1070, "run the change at the final head, vote", mirror=False))
    b.append(msg(626, 1070, 360, "three sealed votes: PASS / FAIL + evidence", AMBER, "ahA", mirror=True))
    b.append(t(140, 662, "votes, then the tally (2 of 3 PASS)", 12.5, VIOLET, 500))
    b.append(step(7, 712))
    gx, gy = 405, 690
    b.append(f'<rect x="{gx}" y="{gy}" width="460" height="196" rx="14" fill="{PANEL}" stroke="{AMBER}" stroke-width="1.6"/>')
    b.append(t(gx + 20, gy + 30, "Merge gate (enforced in code)", 17, AMBER, 700))
    for i, line in enumerate(["same head the panel voted on", "every required check reported and green",
                              "not conflicting with the base", "your own PR: your commits, no fork",
                              "merge authorized (autonomousMerge, base branch)"]):
        yy = gy + 62 + i * 26
        b.append(f'<path d="M{gx+24} {yy-5} l5 5 l10 -11" fill="none" stroke="{CODEX}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>')
        b.append(t(gx + 48, yy, line, 14.5, TEXT))
    b.append(arrow(360, 700, 360, 860, SKY, "ahS"))
    b.append(arrow(360, 878, 128, 878, VIOLET, "ahV"))
    b.append(t(244, 868, "squash merge at that sha", 13, TEXT, 500, "middle"))
    b.append(f'<rect x="40" y="862" width="80" height="32" rx="16" fill="{MERGED}"/>' + t(80, 883, "Merged", 14, "#ffffff", 700, "middle"))
    b.append(t(gx + 480, gy + 40, "Not a pass, or a gate fails:", 14, TEXT, 600))
    b.append(t(gx + 480, gy + 64, "back to step 4 with the failures,", 13.5, MUTED))
    b.append(t(gx + 480, gy + 86, "or stop at merge-ready and say why.", 13.5, MUTED))
    b.append(t(gx + 480, gy + 122, "Others' PRs and forks:", 14, TEXT, 600))
    b.append(t(gx + 480, gy + 146, "review comments only. Never merged.", 13.5, MUTED))
    save("pr-conversation.svg", doc(W, H, f"The {slug} PR conversation",
         "Sequence: the coordinator posts a kickoff, the author agent merges the base on conflicts, the reviewer agent returns "
         "findings, the author fixes or dismisses each, they loop until no P0 or P1 is open, three verifiers "
         "vote, and a code-enforced merge gate squash-merges at the voted head. Every turn is mirrored to the PR thread.",
         "\n".join(b)))

    # 3. Issue flow
    b = [t(40, 58, "An issue, from report to merged PR", 26, TEXT, 700),
         t(40, 86, "Every turn is posted on the issue as [bot]. Only the owner's issues get built.", 15, MUTED)]
    row1 = [("Trigger", "new issue, or a comment", trigger, VIOLET), ("Read as data", "untrusted, delimited,", "@path defanged", SKY),
            ("Plan", "author, read-only:", "files, check, risks", CLAUDE), ("Critique", "reviewer, read-only:", "premise, cases, path", CODEX),
            ("Answer", "author revises or", "answers with proof", CLAUDE)]
    xs = [40, 270, 500, 730, 960]
    for (title, a, c, color), x0 in zip(row1, xs):
        b.append(f'<rect x="{x0}" y="150" width="200" height="104" rx="14" fill="{PANEL}" stroke="{PANEL_EDGE}" stroke-width="1.5"/>')
        b.append(f'<rect x="{x0}" y="150" width="200" height="5" rx="2" fill="{color}"/>')
        b.append(t(x0 + 18, 186, title, 17, TEXT, 600))
        b.append(t(x0 + 18, 213, a, 13.5, MUTED))
        b.append(t(x0 + 18, 234, c, 13.5, MUTED, font=MONO if c.startswith(("@", "/")) else SANS))
    for x0 in xs[:-1]:
        b.append(arrow(x0 + 200, 202, x0 + 230, 202))
    b.append(f'<path d="M1060 150 C1060 112 600 112 600 146" fill="none" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="5 5" marker-end="url(#ah)"/>')
    b.append(t(830, 116, "the next human comment starts another round", 13, MUTED, anchor="middle"))
    b.append(arrow(1060, 254, 1060, 316))
    cx, cy = 1060, 400
    b.append(f'<path d="M{cx} {cy-84} L{cx+110} {cy} L{cx} {cy+84} L{cx-110} {cy}z" fill="{PANEL}" stroke="{AMBER}" stroke-width="1.8"/>')
    for i, line in enumerate(["Owner opened it,", "or owner said", trigger, "implement?"]):
        b.append(t(cx, cy - 22 + i * 18, line, 13.5, TEXT, 600 if i < 2 else 500, "middle", MONO if i >= 2 else SANS))
    row2 = [("Implement", "worktree, branch", f"{slug}/issue-<n>", CLAUDE), ("Open a ready PR", "body has", "Closes #<n>", SKY),
            ("pr-conversation", "review, fixes, panel,", "merge gate", VIOLET), ("Issue closes", "on merge, by the", "Closes link", MERGED)]
    xs2 = [730, 500, 270, 40]
    for (title, a, c, color), x0 in zip(row2, xs2):
        b.append(f'<rect x="{x0}" y="348" width="200" height="104" rx="14" fill="{PANEL}" stroke="{PANEL_EDGE}" stroke-width="1.5"/>')
        b.append(f'<rect x="{x0}" y="348" width="200" height="5" rx="2" fill="{color}"/>')
        b.append(t(x0 + 18, 384, title, 17, TEXT, 600))
        b.append(t(x0 + 18, 411, a, 13.5, MUTED))
        b.append(t(x0 + 18, 432, c, 13.5, color if color != MERGED else VIOLET, 500, font=MONO))
    b.append(arrow(cx - 110, 400, 932, 400, AMBER, "ahA"))
    b.append(t(940, 388, "yes", 13.5, AMBER, 700))
    for x0 in xs2[:-1]:
        b.append(arrow(x0, 400, x0 - 28, 400))
    b.append(arrow(cx, cy + 84, cx, 520, AMBER, "ahA"))
    b.append(t(cx + 10, 506, "no", 13.5, AMBER, 700))
    b.append(f'<rect x="580" y="524" width="580" height="74" rx="14" fill="{PANEL}" stroke="{PANEL_EDGE}" stroke-width="1.5"/>')
    b.append(t(600, 554, "The thread keeps the plan and its critique.", 15, TEXT, 600))
    b.append(t(600, 580, "The bots never build, label, assign or close anyone else's issue.", 13.5, MUTED))
    b.append(t(40, 520, "Gates", 15, TEXT, 700))
    for i, line in enumerate(["One branch per issue; a second turn joins its open PR.",
                              "Not a bug, can't reproduce, or too risky: answered with evidence.",
                              "Only the merge closes the issue. Never by hand."]):
        b.append(f'<circle cx="46" cy="{541+i*24}" r="3.5" fill="{AMBER}"/>' + t(58, 546 + i * 24, line, 13.5, MUTED))
    save("issue-flow.svg", doc(1200, 630, f"The {slug} issue conversation",
         "A new issue or mention is read as untrusted data. The author plans, the reviewer critiques, the author answers. "
         f"If the owner opened the issue or said {trigger} implement, the author builds it on branch {slug}/issue-<n>, "
         "opens a PR with Closes #<n>, and the PR conversation lands it. Otherwise the bots stop at the discussion.",
         "\n".join(b)))
    return written
