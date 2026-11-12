# blast-radius

**Use when:** "what could this break", "blast radius of X", or a small diff you don't trust. Listing callers is not the job; the breakage grep won't show is.

Proof ladder. Push each load-bearing fact as far as is cheap and say where it stopped: (1) you said so, which is worthless; (2) pointed at a real `file:line` or library source; (3) walked the failure and showed it can't reach; (4) ran a script/test calling the real code that fails loud if wrong; (5) reproduced in the running app.

1. Read the change: diff, symbols added/changed/deleted, what it now does differently incl. what the diff doesn't spell out (pull PR/commits as in **why** step 2).
   Done when every added, changed, and deleted symbol is listed with its new behavior.
2. Find the one fact it's safe because of (e.g. "this call only drops already-dead cache entries"). Spend time here, not on a list of maybes. Done when the fact is one written sentence.
3. Look where grep stops: library source at the pinned version plus local patches; timing (microtasks, teardown, framework semantics); JSON an API returns, DB columns, wire formats, other languages reading the same bytes, feature flags, code three hops downstream.
   Done when each of those places is marked checked with a `file:line` or not applicable.
4. Rate each risk honestly (likelihood, cost). Separate confirmed from checked-and-cleared. Cite real `file:line`; an empty search is an answer; never invent a caller or API.
   Done when every risk has a likelihood, a cost, and a confirmed or cleared label.
5. Prove the one fact: write and run a script/test against real code; paste output. Done when the pasted output shows the script passing, or the fact is marked unproven with the ladder step reached.
6. Big or wide change → run as **arena** (different models catch different bugs).

**Output:** **What it does** · **The one fact** (ladder step reached + proof, or "unproven") · **Risks** (how it breaks, `file:line`, likelihood/severity, how to check, proof for the ones that matter) · **Cleared** · **Before you merge** (cheapest catching test/repro, incl. your script). Through **unslop**; strip private details.

**Done when** every output section is filled and the one fact names the ladder step it reached.
