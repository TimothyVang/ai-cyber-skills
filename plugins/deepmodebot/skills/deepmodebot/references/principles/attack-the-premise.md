# attack-the-premise

Group: core. When: two or more fixes that share one premise have failed the same gate.
- **Rule.** Suspect the premise, not the fixes. Each failed fix is evidence against the belief it assumed.
- **Steps.** (1) Write the premise down: the one sentence every failed fix assumed. (2) Test it before the next fix: find an observation that would differ if the premise were false, and make it; look at how failures are *distributed*, not only their size; make the check rerunnable (build-the-lever). (3) Follow the evidence: contradicted → look for what the failures share that the premise didn't predict; confirmed → ask the next "why" (fix-root-causes); earlier fixes may have treated a consequence. (4) Remove the condition instead of compensating (laziness-protocol): if one part always lands on the losing side, change what puts it there.
- **Stop.** No next fix until the premise is written down and tested.
- **Anti-patterns.** A third fix on the same premise; a cleanup mechanism that leaves the cause in place and adds work every run.
