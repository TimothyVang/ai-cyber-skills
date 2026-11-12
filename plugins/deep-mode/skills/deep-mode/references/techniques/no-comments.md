# no-comments

**Use when:** cleaning comments from a diff or files. Scope = caller's files/diff, else current diff against the base branch (default `main`) incl. working tree.

1. Spawn a default `task` agent (not `reviewer`, which can't edit) as **Comment Sicko** with the scope and this brief.
   Delete comments in scope: narration, banners, commented-out code, workaround sermons.
   Only keeps: legal/license headers; non-obvious behavior forced by an external dependency, platform, vendor, or protocol we can't reshape; `prettier-ignore`; lint suppressions whose rule is faulty, pedantic, or style-only; doc comments defining a public API contract; issue/RFC links explaining a constraint code can't express.
   Unsure a keep applies → it dies.
   Surprises in *our* code die and the exact symbol is flagged `MUST KILL` (rename, extract, type, or rearchitect so prose isn't needed). `eslint-disable`/`@ts-ignore`/`@ts-expect-error` on rules that catch real bugs or protect correctness/safety → kill and flag `MUST KILL`.
   `IMPORTANT`, `do not remove`, `too risky`, `fine for now`, long justifications are scent: read nearby code, run **how**/**why** on the symbol; only a foreign keep-list gotcha proven true today on a live path survives.
   Never shorten an alibi. Touches only comments; never writes application code; invents nothing.
   Reports touched files, deletion count, `MUST KILL` flags (one line each), skips.
   Done when its report lists touched files, the deletion count, flags, and skips.
2. Audit its report and diff. Reject application-code edits, scope escapes, deletions protected by an exception, misstated `MUST KILL` reasons, flags against kept intentional code.
   Don't restore reshape-flagged our-code comments. Audit missed scoped lint/TS suppressions; correctness/safety ones stay `MUST KILL`. Restore only with an exact exception and scoped proof.
   Thin `IMPORTANT`/`do not remove` verdicts → run **how**/**why** first. Ambiguous kill → stay deleted; refuted or ambiguous keep → delete.
   One rejected report → revert and rerun with the failure named; a second rejection → report open and fail.
   Done when the diff touches only comments in scope and each restored comment names its exception.
3. Fix trivial accepted flags directly (delete dead path, drop param, use the real API). Any fix needing a shape → run **architect** once for the accepted set, stop at the sketch.
   Done when every accepted flag is fixed or covered by the architect sketch.
4. Implement the smallest in-scope root-cause fix; remove every named workaround. Out-of-scope root cause → smallest in-scope fix, rest reported open. Never widen the fence; never add symptom guards.
   Done when no named workaround remains in scope and each out-of-scope cause is listed as open.
5. Constraint comments (`do not remove`, `do not change wording`, `talk to X first`): keep those about things we can't change.
   Otherwise decide: encode it as the cheapest in-scope type, runtime check, test, or CI lint, then delete the comment; or delete it and report the constraint open. Log the call (SKILL.md Autonomy).
   Done when each constraint comment is kept with a reason, encoded, or reported open.

**Done when** no comment in scope survives without a named keep exception, and every `MUST KILL` flag is fixed, sketched, or reported open.

**Output:** deletion count, restored comments, reruns, architect sketch, fixes, encoding offers, encodings landed, unenforced constraints, other open work.
