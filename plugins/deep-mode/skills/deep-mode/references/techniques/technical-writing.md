# technical-writing

**Use when:** writing or reviewing docs, RFCs, READMEs, PR descriptions, commit messages. Apply all four layers so a tired engineer gets it on first read.

Above the layers: cut every word that does no work; use the short everyday word; if a rule makes a sentence worse, fix it another way. The codebase is the word list: real symbol, file, flag, command names. Don't invent jargon; define a named pattern on first use. Vary rhythm: mix sentence lengths, have a view where the mode allows, be specific ("a column rename fails the build") over sterile.

1. **Pick the mode (Diátaxis).** One document, one mode.
   Action+learning = **tutorial** (say what they'll build; every step gives a visible result and states expected output; "we", commands; explanation cut to a clause and a link). Action+work = **how-to** (a real user problem, named by task; assume competence; action only; forks "If you want x, do y").
   Understanding+work = **reference** (describe only; dry, complete, sure; mirror the thing's structure; generate from code where possible). Understanding+learning = **explanation** (one bounded topic, title tolerates "About…"; anchored on a real why; context, history, alternatives; opinion allowed only here).
   Don't mix; split and link. Done when the document is labeled with exactly one mode.
2. **Sentences (Google style).** "You", present tense. Name the actor. Instructions as commands. Condition before instruction. Common case first. No buzzwords, "please", "simply/easy/quickly", pre-announcements, or repeated sentence openings. Descriptive link text, never "click here". Headings carry the point, sentence case, one h1, no skipped levels. Numbered lists for sequences, introduced by a full sentence, parallel items. Code font for code, bold for UI, serial commas, no "etc.".
   Done when every heading, link, and list follows these rules.
3. **STE.** One instruction per sentence; split instructions >~20 words, other sentences >~25. Warning before the step. Keep articles. One meaning per word, one word per action. Direct commands, never passive procedures. Avoid -ing words.
   Done when no instruction sentence exceeds about 20 words and none is passive.
4. **Global English.** Keep "only"/"not" next to what they modify. Break noun strings. Every "it/they/this" points at one thing; never "this/which" for a clause. Don't drop verbs. Keep "that". Repeat articles in a series when it prevents misreads. Periods, not semicolons; no em dashes. Parentheses hold full units; no "(s)", no slashes. One name per thing everywhere. No idioms, Latin abbreviations, metaphors.
   Done when every pronoun has one referent and no em dash or semicolon remains.
5. Apply **unslop**. PRs/commits: every layer except Diátaxis; a PR body is a one-minute briefing; link logs and tables, don't paste. UI strings follow product copy guidelines. Real paths; every count or tree claim true at that commit, with the command that regenerates it.
   Done when every path and count is checked against the commit.

Before → after: "Configuration of the proto import ratchet budget script parameters is performed via budget.json…" → "`budget.mjs` reads the committed budget from `budget.json` and counts the files that import protos. If the count exceeds the budget, CI fails. Run `budget.mjs --write` only to lower the budget."

**Done when** each numbered layer's own check holds for the whole document.
