# wizard

**Use when:** the work needs steps only a human can do: creating accounts or API keys in a third-party dashboard, pasting credentials into `.env` or CI secrets, approving an OAuth app, a one-off migration or cutover with irreversible clicks. Also "make me a setup script", "walk me through setting up X". Steps the agent can run itself are not wizard steps; run them. A wizard turns the hard stop "needs a credential only the user has" into one command the user runs.

The output is a bash script built from `assets/wizard/wizard.sh`. Its helper section handles screens, progress, browser opening, hidden input, `.env` upserts, GitHub secrets and variables, and the closing summary. You write only the steps section.

1. **Scope.** Read before asking: `.env.example`, `.env*`, README setup sections, `docker-compose*`, framework config, and every `secrets.*` and `vars.*` reference in `.github/workflows/*` (each one is a value the wizard must produce). For a migration, read the current state, the target state, and which actions between them cannot be undone. List the steps in dependency order. For each captured value record where the human finds it, where it goes (`.env`, a GitHub secret or variable, both, or nowhere), and whether it is secret.
   Done when every value has its source, destination, and secret flag recorded.
2. **Map each step.** Write the exact path a stranger would follow: the URL, what to click, where the value appears ("Settings → API → Create key → copy"). Check the provider's current docs for UI paths you have not seen this session (**prior-art** or a fetch of the docs page). A path you cannot confirm is written as such in the step ("the menu may be named Keys or Tokens") instead of guessed.
   Done when every step has a URL and click path, each confirmed or marked unconfirmed.
   Integrations: distinguish user consent, app installation/resource scope, provider-side connection, and usable status; reuse completed stages rather than repeating setup.
   Done when each required stage has an observable check and the final check proves the intended resource is reachable, not merely that login or consent succeeded.
3. **Write the script.** Copy the template to `scripts/setup-<thing>.sh` (kept, when the setup will repeat) or a scratch path (one-off). Replace the example in `main` with one `wiz_step` per screen and set the total in `wiz_begin`.
   Per step: `wiz_say` the purpose in one line, `wiz_open` the URL before asking for anything on it, `wiz_do` each click, `wiz_ask KEY "prompt"` (add `secret` for anything secret), `wiz_env` every value the app reads, `wiz_gh_secret`/`wiz_gh_var` only for names CI references, and `wiz_confirm` before any irreversible action (skip the action on no).
   One task per step: each step clears the screen. Leave the helper section unchanged. Done when every mapped step is a `wiz_step` and the total in `wiz_begin` matches their count.
4. **Check it statically.** `bash -n <script>`; `shellcheck <script>` when installed; `chmod +x <script>`. Trace it: every value from step 1 is asked for and lands where step 1 said; every `wiz_gh_secret` name matches a `secrets.` name in the workflows; nothing secret goes through `wiz_ask` without `secret`. Do not run it end to end: it opens browsers and waits on a human.
   Done when `bash -n` exits 0, shellcheck (when installed) reports nothing, and every trace check holds.
5. **Hand off.** Give the user the one command to run. A kept setup script gets a line in the README's setup section and lands with the rest of the change. After the user runs it, check the result yourself where you can (the app starts with the new `.env`, `gh secret list` shows the names).
   Done when the user has the command, and after their run each checkable result is confirmed.

**Hard rules.** Secrets never echo, never land in the transcript, never go in git (`.env` stays ignored; check `.gitignore`). Never invent a dashboard path. The script must be safe to re-run.

**Output:** the script path, its steps with the values each captures and where they go, the static checks run, and the command for the user.

Connection example: [AWS GitHub connections](https://docs.aws.amazon.com/dtconsole/latest/userguide/connections-create-github.html) require installation and final connection completion; a CLI-created `PENDING` connection is not `AVAILABLE`.
