# Implement spec

Use when: a spec has tickets (Spec and Tickets playbooks) and the whole spec should be built and land as one reviewed change ("implement the spec", "build spec #N", "build all the tickets on one branch"). Every ticket merges into one **integration branch**, and one PR carries that branch to trunk. When each ticket should land on trunk as its own PR, use the Board playbook (`references/playbooks/board.md`) instead.

You coordinate; ticket owners write the code. The tickets are a graph, not a list: the **frontier** is every open ticket whose blockers are all merged into the integration branch.

## Steps

1. **Load the graph.** Read the spec (issue and `docs/specs/<slug>.md`) and every ticket with its Blocked by lines, per the **tracker** technique (`references/techniques/tracker.md`). Record the graph, the integration branch, and each ticket's owner and state in one notes file a cold start can find, as Orchestrate step 1 describes (`references/playbooks/orchestrate.md`).
2. **Explore once** (optional). Tickets that share unknown code → one `scout` pass that returns file pointers, conventions, and test commands. Save its report beside the notes file and give owners the path, not a pasted copy.
3. **Integration branch.** Use `spec/<slug>` when the Spec playbook created it; else create it off the default branch. When the repo has a remote, push it with an explicit refspec. Without a remote, every push and PR step below is skipped: worktrees share one `.git`, so local branches are enough.
4. **Start the frontier.** One fresh default `task` owner per frontier ticket, each in its own worktree on branch `ticket/<n>-<slug>` cut from the integration branch tip, under the shared-`.git` rules in Orchestrate step 3. At most about ten at once. Each kickoff names the spec path, the ticket, the notes paths, its allowed files, and these duties:
   - Confirm the worktree's base is the current integration tip; reset onto it if not.
   - Build with the Feature or Bug fix playbook's steps (`references/playbooks/feature.md`, `references/playbooks/bug-fix.md`). Write the ticket's Done when as failing checks first per the **tdd** technique (`references/techniques/tdd.md`) where a cheap seam exists.
   - Prove each Done when item on the real surface.
   - Run the **pr-review** technique (`references/techniques/pr-review.md`) in local mode against the integration branch and fix, dismiss with a reason, or escalate each finding.
   - Merge the integration tip into the ticket branch, rerun the checks, push (when there is a remote), and report the head SHA with its evidence.
5. **Merge each finished ticket.** Read the owner's evidence and diff. In a clean worktree of the integration branch: `git merge --no-ff ticket/<n>-<slug>`, rerun the repo's checks, push when there is a remote. A conflict or red check goes back to the owner with the output. No PR exists yet: Opening a PR hands every PR straight to pr-conversation, which would land a partial build.
6. **Move the frontier.** After each merge: comment the merge SHA on the ticket, recompute the frontier, start owners for newly unblocked tickets. A ticket that grows past one session is split with the Tickets playbook's rules and the graph updated.
7. **Close the build.** When every ticket is merged:
   - Run pr-review on the integration branch against the default branch, with the spec as the claim, so its Spec findings check every user story and Done when item.
   - One fresh owner fixes every finding in one pass on the integration branch.
   - Local tracker → set each ticket and the spec to `Status: closed` on the integration branch, so the close lands with the code.
   - With a remote: open one PR from the integration branch to the default branch through Opening a PR (`references/playbooks/opening-a-pr.md`), with `Closes #<spec>` and one `Closes #<ticket>` line per ticket in its body. It lands through the **pr-conversation** technique (`references/techniques/pr-conversation.md`) on a **panel** pass (`references/techniques/panel.md`) at its head.
   - No remote: after a panel pass at the integration tip, run `git merge --no-ff spec/<slug>` in a clean worktree of the default branch and rerun the checks there. A red result is undone with `git revert -m 1 <merge sha>`.
8. **Clean up** the ticket worktrees and merged ticket branches you created, per Worktree cleanup (`references/playbooks/worktree-cleanup.md`).

## Gates

- Only you merge into the integration branch, and only a ticket whose evidence you read.
- The integration branch stays green after every merge. A red merge is reverted on the branch before the next one.
- The final PR (no remote: the final local merge) lands only on a panel pass at its exact head, with no P0 or P1 review finding open.
- Subagent briefs carry pointers (spec, ticket, notes, commits), not copies of them.

## Evidence

- The final PR link (no remote: none), its merge SHA, and the trunk check after the merge.
- Per ticket: owner, merge SHA into the integration branch, and the Done when evidence.
- The closing review line and panel line.
- Decisions made on the user's behalf, each with how to reverse it.
