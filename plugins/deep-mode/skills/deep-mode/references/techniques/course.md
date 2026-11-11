# course

**Use when:** the user wants to learn a topic over several sessions: "teach me Rust over the next month", "make me a course on X", "I want to get good at Y", or they return to a folder that already has `MISSION.md`. One explanation of code or a change is the **teach** technique (`references/techniques/teach.md`). The topic need not be code.

The current directory is the course workspace. Its files are the learner's memory between sessions:

| File | Holds |
|---|---|
| `MISSION.md` | Why they are learning: the real goal, three to five things they will be able to do, constraints (time, budget, preferences), what is out of scope. One screen at most. |
| `RESOURCES.md` | Trusted sources, each with one line on what it covers and when to use it. Two groups: **Sources** (books, docs, papers, courses) and **Communities** (forums, classes, groups where they can test themselves). A **Gaps** list for needs with no good source yet. |
| `GLOSSARY.md` | Terms the learner can already use correctly, one or two sentences each, with the words to avoid. A term enters only after they use it right. |
| `NOTES.md` | Their stated preferences and your working notes. |
| `lessons/NNNN-<slug>.html` | One lesson per file, numbered. |
| `reference/<slug>.html` | Cheat sheets distilled from lessons: syntax, procedures, formulas, sequences. These get revisited; lessons rarely do. |
| `learning-records/NNNN-<slug>.md` | One short record per established fact about the learner (see step 6). |
| `assets/` | Shared stylesheet, quiz widget, and any component a second lesson could reuse. |

Create files when first needed, not up front.

1. **Mission first.** No `MISSION.md`, or one too vague to choose the next lesson ("understand X") → ask why they want this and what they will do with it, in one exchange. Push past abstract answers to an outcome ("ship a CLI to my team", "run a half marathon in October"). Write `MISSION.md`. A changed goal later: confirm with them, update the file, and add a learning record.
2. **Sources before lessons.** Search for high-trust primary sources (official docs, standard texts, recognized experts, well-moderated communities) and fill `RESOURCES.md`. Every factual claim in a lesson cites one. Do not teach from memory where a source exists.
3. **Choose the next lesson.** If they named a target, teach it. Otherwise read `MISSION.md`, every learning record, and `NOTES.md`, then pick the smallest next step the mission needs that sits just past what they have shown they can do: hard enough to stretch, close enough to succeed.
4. **Write the lesson** as one HTML file linking `assets/` (build the shared stylesheet with the first lesson; every later lesson reuses it). It is short enough to finish in one sitting and ends in one concrete win. Shape:
   - the goal in one line, tied to the mission;
   - only the knowledge that skill needs, with citations, kept easy to absorb;
   - practice with immediate feedback: an in-page quiz or exercise that checks the answer, or a checklist of real-world steps for physical skills;
   - links to earlier lessons and reference sheets it builds on;
   - one primary source to read or watch next, and a reminder to bring questions back to you.
   Open it for them (`start`, `open`, or `xdg-open`).
5. **Make it stick.** Practice should be effortful: ask them to recall before they see the answer, revisit earlier material at growing intervals, and for skills mix related problem types. Quick fluency in a session can be an illusion; retention across sessions is the goal. Quiz options have the same length and form, and the correct position varies, so format never gives the answer away. Add or update a `reference/` sheet when a lesson produces something worth looking up later.
6. **Record what is now known.** Write a learning record (`# <title>` plus one to three sentences: what is established and how it changes what to teach next) when they show real command of something non-trivial, state prior knowledge (with the depth they claim), correct a misconception, or shift the mission. Exposure is not learning; don't record material merely covered. A later record that overturns an earlier one marks the old one `Status: superseded by NNNN`; never delete it.
7. **Point outward for judgment.** Questions that need practical wisdom (taste, trade-offs, "is this normal") get your best answer plus a community from `RESOURCES.md` where they can test it. If they decline communities, note it in `NOTES.md` and stop suggesting them.

**Hard rules.** Every lesson traces to the mission. One lesson, one win. Cite sources. Reuse `assets/` instead of duplicating code across lessons. Write through **unslop** (`references/techniques/unslop.md`).

**Output:** the lesson path (opened), what it teaches and why it is next, the sources it cites, and any workspace files created or updated.
