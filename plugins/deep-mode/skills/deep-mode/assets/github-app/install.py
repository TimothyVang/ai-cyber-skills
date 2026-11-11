#!/usr/bin/env python3
"""One-command setup for the bots: checks, the GitHub App, the agents, and autostart.

    python3 install.py                      # interactive; asks before installing anything
    python3 install.py --yes                # accept every default
    python3 install.py --check              # report what is missing, change nothing
    python3 install.py --brand acme-review  # white-label: app, comments, mention, branches, paths

Steps, each skipped when already done:
1. Tools: git, gh (logged in), openssl, node/npm, acpx (installed with npm when missing).
2. Agents: any ACP harness on PATH (omp preferred, then Claude Code, Codex, Gemini CLI, Cursor, Copilot,
   OpenCode), each logged in with its own subscription. No API keys. omp is registered with acpx.
3. A round trip through ACP to the agents the bots will use.
4. Your private GitHub App (`<brand>-<login>`), created in the browser, then installed on the repos you pick.
5. ~/.config/<brand>/bot.json with the agents found, and an autostart entry that runs `bot.py watch` at logon.
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import brand  # noqa: E402


def apply_brand_flag() -> None:
    """Set the brand before ghapp reads it at import, so --brand takes effect on this run. It is written to
    brand.local.json except under --check, which changes nothing."""
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--brand")
    pre.add_argument("--homepage")
    pre.add_argument("--check", action="store_true")
    known, _ = pre.parse_known_args()
    if known.brand:
        if known.check:
            brand.BRAND = brand.derive(known.brand, {"homepage": known.homepage})
        else:
            brand.BRAND = brand.write_local(known.brand, known.homepage)
        brand.CONFIG_DIR = Path.home() / ".config" / brand.BRAND["configDirName"]
        brand.CACHE_DIR = Path.home() / ".cache" / brand.BRAND["configDirName"] / "bot"


apply_brand_flag()
import ghapp  # noqa: E402

ACPX_VERSION = "0.22"
BOT_CONFIG = ghapp.CONFIG_DIR / "bot.json"


def run(cmd: list[str], timeout=120) -> subprocess.CompletedProcess:
    exe = shutil.which(cmd[0]) or cmd[0]
    try:
        return subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as err:
        return subprocess.CompletedProcess(cmd, 1, "", str(err))


def say(mark: str, text: str) -> None:
    print(f"  [{mark}] {text}", flush=True)


def confirm(question: str, args) -> bool:
    if args.check:  # --check changes nothing, even with --yes
        return False
    if args.yes:
        return True
    return input(f"  {question} [Y/n] ").strip().lower() in ("", "y", "yes")


def check_tools(args) -> bool:
    print("1. Tools")
    ok = True
    for tool, hint in [("git", "https://git-scm.com/downloads"), ("gh", "https://cli.github.com"),
                       ("openssl", "ships with Git for Windows; brew/apt install openssl"),
                       ("npm", "https://nodejs.org")]:
        if shutil.which(tool):
            say("ok", tool)
        else:
            say("missing", f"{tool}: install it ({hint})")
            ok = False
    if shutil.which("gh"):
        login = run(["gh", "api", "user", "-q", ".login"]).stdout.strip()
        if login:
            say("ok", f"gh logged in as {login}")
        else:
            say("missing", "gh is not logged in: run `gh auth login`")
            ok = False
    if shutil.which("acpx"):
        say("ok", f"acpx {run(['acpx', '--version']).stdout.strip()}")
    elif shutil.which("npm") and confirm(f"Install acpx@{ACPX_VERSION} (ACP client, MIT) with npm -g?", args):
        result = run(["npm", "install", "-g", f"acpx@{ACPX_VERSION}"], timeout=600)
        if result.returncode == 0 and shutil.which("acpx"):
            say("ok", "acpx installed")
        else:
            say("missing", f"npm install -g acpx failed: {(result.stderr or result.stdout)[-300:]}")
            ok = False
    else:
        say("missing", f"acpx: run `npm install -g acpx@{ACPX_VERSION}`")
        ok = False
    return ok


# Harnesses the bots can run on, in preference order: (acpx agent name, executable on PATH).
# Any other acpx agent works too: name it with --author/--reviewer.
KNOWN_AGENTS = [("omp", "omp"), ("claude", "claude"), ("codex", "codex"), ("gemini", "gemini"),
                ("cursor", "cursor-agent"), ("copilot", "copilot"), ("opencode", "opencode")]
ACPX_CONFIG = Path.home() / ".acpx" / "config.json"


def ensure_acpx_agent(name: str, command: str, args: list[str]) -> None:
    """acpx has no built-in profile for some harnesses (omp); register one without touching other entries."""
    config = json.loads(ACPX_CONFIG.read_text(encoding="utf-8")) if ACPX_CONFIG.is_file() else {}
    agents = config.setdefault("agents", {})
    if name in agents:
        return
    agents[name] = {"command": command, "args": args}
    ACPX_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    ACPX_CONFIG.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    say("ok", f"registered `{name}` in {ACPX_CONFIG}")


def detect_agents(args) -> list[str]:
    print("2. Agents (each harness uses its own subscription login, no API keys)")
    wanted = [a for a in (args.author, args.reviewer) if a]
    found = [name for name, exe in KNOWN_AGENTS if shutil.which(exe)]
    for name in found:
        say("ok", f"{name} found")
    if "omp" in found and not args.check:
        ensure_acpx_agent("omp", "omp", ["acp"])
    return list(dict.fromkeys(wanted + found))


def acp_round_trip(agents: list[str], needed: int) -> list[str]:
    print("3. ACP round trip")
    working = []
    for agent in agents:
        result = run(["acpx", "--deny-all", "--timeout", "240", "--format", "quiet", agent, "exec",
                      "Reply with exactly: acp-ready-7"], timeout=300)
        if "acp-ready-7" in result.stdout:
            working.append(agent)
            say("ok", f"{agent} answered over ACP")
        else:
            say("skip", f"{agent}: not logged in or not ACP-ready: {(result.stderr or result.stdout).strip()[-200:]}")
        if len(working) >= needed:
            break
    return working


def ensure_app(args) -> bool:
    print("4. GitHub App")
    if ghapp.CONFIG_PATH.is_file():
        config = ghapp.load_config()
        say("ok", f"app {config['slug']} already configured")
    elif args.check or not confirm("Create your private deep-mode GitHub App in the browser now?", args):
        say("missing", "no app: rerun without --check")
        return False
    else:
        result = subprocess.run([sys.executable, str(HERE / "ghapp.py"), "setup"])
        if result.returncode != 0:
            say("fail", "app setup did not finish")
            return False
        config = ghapp.load_config()
    installs = ghapp.installations(config)
    if installs:
        say("ok", f"installed on {', '.join(i['account']['login'] for i in installs)}")
        return True
    url = f"{config['html_url']}/installations/new"
    if args.check:
        say("missing", f"not installed on any repo: {url}")
        return False
    say("todo", f"install it on the repos the bots may work in: {url}")
    webbrowser.open(url)
    deadline = time.time() + 900
    while time.time() < deadline:
        time.sleep(5)
        if ghapp.installations(config):
            say("ok", "installed")
            return True
    say("fail", "no installation seen within 15 minutes; rerun once it is installed")
    return False


def write_bot_config(agents: list[str], args) -> None:
    print("5. Bot config and autostart")
    if BOT_CONFIG.is_file():
        say("ok", f"keeping {BOT_CONFIG}")
        return
    author = args.author or agents[0]
    reviewer = args.reviewer or author
    role = lambda agent, model: {"agent": agent, **({"model": model} if model else {})}  # noqa: E731
    config = {"author": role(author, args.author_model), "reviewer": role(reviewer, args.reviewer_model),
              "verifiers": [role(author, args.author_model), role(reviewer, args.reviewer_model),
                            role(author, args.author_model)],
              "autonomousMerge": True, "maxRounds": 3, "interval": 120, "mention": brand.BRAND["mention"]}
    BOT_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    BOT_CONFIG.write_text(json.dumps(config, indent=2), encoding="utf-8")
    say("ok", f"wrote {BOT_CONFIG} (author {author}, reviewer {reviewer})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--yes", action="store_true", help="accept every default")
    parser.add_argument("--check", action="store_true", help="report only; change nothing")
    parser.add_argument("--no-autostart", action="store_true")
    parser.add_argument("--brand", help="white-label name (lowercase, hyphens); written to brand.local.json")
    parser.add_argument("--homepage", help="homepage URL shown on the GitHub App (with --brand)")
    parser.add_argument("--author", help="acpx agent for the author role (default: first found, omp preferred)")
    parser.add_argument("--reviewer", help="acpx agent for the reviewer role (default: same as author)")
    parser.add_argument("--author-model", help="model id passed to the author agent")
    parser.add_argument("--reviewer-model", help="model id for the reviewer; another model family is a stronger review")
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        sys.exit("Python 3.10 or newer is required")

    tools_ok = check_tools(args)
    if not tools_ok:
        sys.exit("Install the missing tools above, then rerun.")
    agents = detect_agents(args)
    if not agents:
        sys.exit("No agent harness found. Install one (omp, Claude Code, Codex, Gemini CLI, ...) and log in.")
    needed = len({a for a in (args.author, args.reviewer) if a}) or 1
    agents = acp_round_trip(agents, needed)
    if not agents:
        sys.exit("No agent answered over ACP; log in to one harness and rerun.")
    if not ensure_app(args):
        sys.exit(1)
    if args.check:
        print("Check passed. Rerun without --check to finish setup.")
        return
    write_bot_config(agents, args)
    bot = [sys.executable, str(HERE / "bot.py")]
    if not args.no_autostart and confirm("Start the bot at every logon (it polls your installed repos)?", args):
        result = subprocess.run([*bot, "install-autostart"])
        say("ok" if result.returncode == 0 else "fail", "autostart")
    print(f"\nDone. {brand.BRAND['name']} bots post as {ghapp.bot_login(ghapp.load_config())}. Useful commands:")
    print(f"  {' '.join(bot)} status")
    print(f"  {' '.join(bot)} once --repo <owner/repo> --dry-run")
    print(f"  {' '.join(bot)} watch")


if __name__ == "__main__":
    main()
