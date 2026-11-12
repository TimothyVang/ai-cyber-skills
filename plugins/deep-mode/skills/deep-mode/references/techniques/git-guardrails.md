# git-guardrails

**Use when:** "block dangerous git commands", "add git safety hooks", "stop the agent from force-pushing / resetting", or a retro found an agent ran or nearly ran a destructive git command. It turns SKILL.md's git hard stops from prose into a hook the harness enforces before the command runs.

Three files in `assets/git-guardrails/` do the work:
- `git-guard-patterns.txt`: the blocked commands, one regular expression per line. Both hooks read it, so the list has one home.
- `git-guard.sh`: Claude Code `PreToolUse` hook for the Bash tool. Exit 2 blocks the call and returns the reason to the agent.
- `git-guard.ts`: omp pre-tool hook. Blocks matching `bash` commands and `eval` cells.

**Blocked by default:** `reset --hard`, `clean -f`, `checkout .` and `restore .`, `stash clear` and `stash drop`, `worktree remove --force`, `branch -D`, `filter-branch`/`filter-repo`, `update-ref -d`, `reflog expire`, `gc --prune=now`, pushes with `--force`, `-f`, `+ref`, `--mirror`, `--delete`, `--prune` or `:ref`, pushes that name `main`, `master`, or `trunk` as the destination, and `push --all`.

**Blocked on the default branch:** while `main`, `master`, or `trunk` is checked out, a push that names no destination (`git push`, `git push origin`) or pushes `HEAD`. These are the `@branch` lines in the pattern file; the hooks check the branch in the command's working directory.

**Allowed:** everything deep-mode does in normal work: branches, commits, pushes to feature branches, `--force-with-lease` to a feature branch, `gh pr merge`. Two playbook commands match the patterns and are blocked too: `git worktree remove --force` (Worktree cleanup) and `git restore ... -- .` (Autopilot's revert). Drop `--force` for a clean worktree and use `git revert` for the revert; anything else is the user's to run. **Strict mode** (only the human pushes): uncomment the last line of the pattern file.

1. **Scope.** Default to the project: the hook files are committed, so every agent working in the repo gets them. User scope (every repo on this machine) only when asked.
2. **Install for the harnesses in use** (both when unsure):
   - **Claude Code.** Copy `git-guard.sh` and `git-guard-patterns.txt` to `.claude/hooks/` (user scope: `~/.claude/hooks/`). Merge this into `.claude/settings.json` (user scope: `~/.claude/settings.json`, command path `~/.claude/hooks/git-guard.sh`), appending to any existing `hooks.PreToolUse` array instead of replacing it:
     ```json
     { "hooks": { "PreToolUse": [ { "matcher": "Bash", "hooks": [ { "type": "command", "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/git-guard.sh\"" } ] } ] } }
     ```
   - **omp.** Copy `git-guard.ts` and `git-guard-patterns.txt` to `.omp/hooks/pre/` (user scope: `~/.omp/agent/hooks/pre/`). omp loads hooks only from the `pre/` and `post/` folders, at session start.
   - Other harnesses with a pre-command hook: call `git-guard.sh --check "<command>"` from it and block on exit code 2.
3. **Tailor the list.** Ask nothing; read the repo. A default branch with another name (`develop`, `production`) gets added to the named-destination push line and to both `@branch` lines. Commands the repo's own scripts legitimately run get removed, with a comment saying why.
4. **Prove it.**
   - Claude Code script: `echo '{"tool_input":{"command":"git reset --hard"}}' | bash .claude/hooks/git-guard.sh; echo $?` prints the block reason and `2`. `--check 'git push --force-with-lease origin feat'` exits `0`. On the default branch, `--check 'git push'` exits `2`; on a feature branch it exits `0`.
   - Live, in a new session of each harness: have the agent run `mkdir -p .scratch/tmp && d=$(mktemp -d -p .scratch/tmp) && cd "$d" && git init -q && git reset --hard` from the project root. It must be blocked before running (an empty scratch repo of its own inside the self-ignored `.scratch/`, so nothing is lost if the hook fails; the `&&` chain stops before `git reset` if the folder was not created).
5. **Land it** through the Opening a PR playbook (`references/playbooks/opening-a-pr.md`), and add one line to `AGENTS.md` naming the guard and the pattern file, so an agent that gets blocked knows where the rule lives.

**Limits.** The patterns match command text, so an alias, a script that runs git inside it, or another tool that shells out can get past them. The `@branch` lines read the branch in the tool call's working directory, so `cd other && git push` or `git -C other push` is judged by the wrong repo, and `push.default=matching` can push the default branch from a feature branch. Some harmless commands look destructive and are blocked too (`git restore --staged .`); use the safe form (`git reset` to unstage). The guard is a seatbelt; the hard stops in SKILL.md still apply.

**Output:** harnesses and scope installed, any pattern changes and why, the two proof results, and the PR.
