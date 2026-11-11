# questionnaire

**Use when:** a decision depends on knowledge that only a specific other person holds (a client, a domain expert, another team, an ops owner), and neither the repo, the docs, nor the user can supply it. Also "write questions for X", "what should I ask the client", "make a questionnaire". Facts you can look up and calls you can make yourself never become questions (SKILL.md Autonomy). The output is a file the user sends or works through in a meeting; sending it is theirs (a message outside the repo).

**Ask the user only about the send**, which they can always answer: who receives it and what must come back. The questions in the document aim at the gap between what that person knows and what the user needs.

1. **Recipient.** Infer from the conversation, then confirm in one exchange only what is missing: role, expertise, relationship to the user, and what they know that the user does not. This sets tone and how much background the document must carry.
2. **What comes back.** List the decisions or facts the user cannot settle alone, each phrased as "after the answers we can decide/do ...". Drop any item you can resolve now by lookup, prototype, or judgment.
3. **Write it** to `docs/questionnaires/<slug>.md` in a repo, else `questionnaire-<slug>.md` in the current directory, using the layout below. Order questions by importance, since an async reader may answer only once. Group them under themed headings once there are more than five. One idea per question, never two joined by "and". Prefer questions that ask for an example, a number, or a choice between named options over open "thoughts on X?". Add a one-line reason only where a question could be misread or answered lightly. Write through **unslop** (`references/techniques/unslop.md`).
4. **Check coverage.** Every item from step 2 maps to at least one question. Remove questions whose answer would not change any decision.
5. **Report** the path. When answers come back, record each settled decision where it belongs (an ADR in `docs/adr/`, a `GLOSSARY.md` term, the spec, or a decision trail row) and continue the blocked work.

**Layout**

```markdown
# <What we need to decide>

**Why this exists:** <the decision that waits on these answers>
**From:** <user> · **To:** <recipient> · **What happens with your answers:** <where they go>

## Background
<One paragraph that lets someone outside the project answer well.>

## How to answer
<Deadline and rough effort. Partial answers help. "Not sure" with a best guess beats a blank.>

## <Theme>

### 1. <Question>
_Why we ask: <only when needed>_

> 

## Anything we missed?
<What should we have asked?>
```

**Output:** the file path, the recipient, and the decisions each question unblocks.
