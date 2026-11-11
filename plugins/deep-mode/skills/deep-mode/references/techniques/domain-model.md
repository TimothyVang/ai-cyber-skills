# domain-model

**Use when:** the project's words are changing, not just being read: naming a new concept, two words for one thing, one word for two things, writing or editing `GLOSSARY.md`, or recording a decision as an ADR ("what do we call this", "add this to the glossary", "write an ADR"). Also runs inside the **grill** technique's With docs mode and inside Triage. Reading `GLOSSARY.md` for vocabulary is a habit every flow has; this technique is for changing it.

Two artifacts, both in the repo, both created only when there is something to put in them:
- **`GLOSSARY.md`** at the repo root: the project's own nouns and verbs, one canonical word each.
- **`docs/adr/NNNN-<slug>.md`**: one file per decision a future reader would question.

## Steps

1. **Load.** Read `GLOSSARY.md` and the ADR titles in `docs/adr/`. A root glossary that lists contexts (a monorepo) points to one `GLOSSARY.md` per context; work in the context the topic belongs to.
2. **Catch drift.** For each domain word in the request, the plan, or the code under discussion:
   - It conflicts with a glossary entry → name the conflict and pick one meaning.
   - It is vague or overloaded ("account", "job", "item") → split it into precise terms and pick the canonical one for each meaning.
   - The code disagrees with how the word is used (the code cancels whole orders, the plan says partial cancel) → read the code, then settle which one is right. A real mismatch is a finding for the plan, not a glossary edit.
3. **Probe with cases.** Invent two or three concrete edge cases that force the boundary between neighboring terms ("an order with one shipped and one unshipped line: is it fulfilled?"). Each case gets an answer, from the code when the code decides it, otherwise by your call (SKILL.md Autonomy).
4. **Write terms as they settle.** Update `GLOSSARY.md` the moment a term is decided, in the format below. Don't batch to the end.
5. **Test each decision for an ADR.** Write one only when all three hold:
   - Undoing it later costs real work (a data shape, a boundary, a vendor, a protocol).
   - A reader of the code would ask "why this way?" without the record.
   - A real alternative existed and lost for a stated reason.

   Fails any test → no ADR; the show-me-your-work trail row is enough.
6. **Report.** List the terms added or changed and the ADRs written, with paths.

## GLOSSARY.md format

```markdown
# <Project or context> glossary

<One sentence: what this part of the system is for.>

## Terms

**<Term>**: <What it is, in one or two sentences. Not what code does with it.>
Not: <rejected synonyms, comma separated>
```

Rules:
- Only words specific to this project. General programming words (cache, retry, timeout) stay out.
- One canonical word per concept; every rejected synonym goes on its `Not:` line so code review can flag it.
- No implementation detail: no file paths, class names, or decisions. Decisions go in ADRs, plans in specs.
- Group terms under `###` headings once clusters appear.

Multi-context repo: the root `GLOSSARY.md` lists each context with a link to its own `GLOSSARY.md` and one line on how the contexts talk (events, shared ids, calls).

## ADR format

Number: the highest `NNNN` in `docs/adr/` plus one, four digits. Slug: the decision in kebab case.

```markdown
# <NNNN>. <The decision as a short statement>

Status: accepted | superseded by <NNNN>
Date: <YYYY-MM-DD>

<Two to four sentences: the situation, what was decided, and the reason it won.>

Rejected: <alternative> because <reason>. (Only when the rejection is not obvious.)
```

A changed decision gets a new ADR; the old one's Status becomes `superseded by <NNNN>`. Never rewrite history in an accepted ADR.

## Done when

Every term this work introduced or disputed has one glossary entry, and every decision that passed the three tests has an ADR. Both ship in the commit of the work that needed them, or in their own commit when there is no code change.
