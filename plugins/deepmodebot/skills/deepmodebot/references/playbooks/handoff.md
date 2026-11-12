# Handoff

Use when: the work should continue in a fresh context: "hand this off", "write a handoff", "summarize this for another agent", "continue this in a new session", "start a background agent on the rest", or the context is crowded and the next phase is cleanly separable (then start a background agent on the rest: a handoff you start yourself keeps every ledger item open).
Stopping for later in this same repo is Pause safely (`references/playbooks/pause-safely.md`); picking up someone else's handoff is Session pickup (`references/playbooks/session-pickup.md`); parallel work while this session continues is a `task` subagent. You own a document a cold agent, another harness, or a colleague can act on without this conversation.

## Steps

1. Set the focus. The user's words after "handoff" say what the next session is for; tailor the document to that. No focus given → the next unfinished unit of the current goal.
   Done when the focus is one sentence with a done-when check (a command and its expected result).
2. Make the work reachable: commit finished units on the working branch and push it, so the next agent reads the branch instead of a description of it. Half-done edits get a `wip:` commit (say so in the document). Skip pushing only when the repo has no remote.
   Done when `git status --porcelain` prints nothing and the remote branch head equals local `HEAD` (or the repo has no remote).
3. Write `docs/handoffs/<YYYY-MM-DD>-<slug>.md` (outside a repo: the current folder) with these sections, each as short as it can be:
   - **Goal:** the user's goal and the problem, in your own words (**in-your-own-words**, `references/techniques/in-your-own-words.md`).
   - **Next session's focus:** from step 1, with its done-when check (a command and its expected result).
   - **State:** repo, branch, head SHA, open PRs and their status, what is verified and how, what is not.
   - **Decisions:** each choice made and why, or a pointer to the decision trail that holds them.
   - **Open questions and risks.**
   - **Next steps:** ordered, the first one concrete enough to start without reading anything else.
   - **Pointers:** paths and URLs to specs, ADRs, issues, PRs, logs, and trails. Link artifacts; never paste their contents.
   - **Start with:** the deepmodebot route the next agent should take (playbook or technique names and paths), and the skills it should load.
   - Done when the file exists with all eight sections filled.
4. Redact before saving: API keys, tokens, passwords, connection strings, private hostnames that matter for security, personal data about anyone. Replace each with `<redacted: what it was>` and say where the real value lives (`.env`, a secret manager). Scan the file for key-shaped strings (`sk-`, `ghp_`, `AKIA`, `-----BEGIN`, `password=`) before going on.
   Done when every match of that scan is a `<redacted: ...>` placeholder.
5. Decide where it lives. Next agent on this machine → leave the file untracked. Next agent elsewhere or a colleague → commit it to the working branch and push. Print its absolute path.
   Done when the absolute path is printed and, for a remote reader, the pushed branch contains the file.
6. Launch, only when asked for a background or new agent. Pass the file, not pasted text, so the shell never expands `$` or backticks in it:
   - omp, attended: `omp @<file>` in a new terminal (the `@` prefix reads the file as the first message).
   - omp, unattended: `nohup omp -p @<file> > <file>.log 2>&1 &`; the run is saved and shows in `omp -r`.
   - Claude Code: `claude --bg -n "<short task name>" -- "$(cat <file>)"`; `claude agents` lists it.
   - Other harnesses: their headless or background flag with the same file. None → give the user the command to start it themselves.
   Done when the launched name or log path is reported, or no launch was asked for.

## Gates

- Nothing lives only in this context: every fact the next agent needs is in the document, the branch, or a linked artifact.
- No secrets or personal data in the document (step 4 scan done).
- A launched agent follows SKILL.md Autonomy on its own; its hard stops still need the user.

## Evidence

- The handoff path, and whether it is committed.
- Branch and head SHA it describes.
- The launch command and the agent's name or log path, if one was launched.
- What was redacted (kinds, not values).
