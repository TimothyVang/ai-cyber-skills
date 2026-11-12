#!/usr/bin/env bash
# Guided setup for steps only a human can do. Built from the deep-mode wizard template.
# The helper section is shared by every wizard; edit only the steps section at the bottom.
# Re-running is safe: values already in the env file are offered as defaults.
set -euo pipefail

# ---------------------------------------------------------------- helpers (shared)

ENV_FILE="${ENV_FILE:-.env}"
STEPS_TOTAL=0
STEP_NO=0
SAVED_KEYS=()
SET_REMOTE=()
LEFT_FOR_HUMAN=()

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  C_B=$'\e[1m' C_D=$'\e[2m' C_0=$'\e[0m' C_H=$'\e[36m' C_OK=$'\e[32m' C_W=$'\e[33m'
else
  C_B='' C_D='' C_0='' C_H='' C_OK='' C_W=''
fi

wiz_clear() { [[ -t 1 ]] && printf '\e[H\e[2J\e[3J'; return 0; }

# wiz_begin TITLE TOTAL: opening screen.
wiz_begin() {
  STEPS_TOTAL="$2"
  wiz_clear
  printf '\n%s%s%s\n%s%s steps. Ctrl-C stops at any point; run it again to resume.%s\n\n' \
    "$C_B" "$1" "$C_0" "$C_D" "$STEPS_TOTAL" "$C_0"
  wiz_wait "Press Enter to begin."
}

# wiz_step NAME: new screen with progress.
wiz_step() {
  STEP_NO=$((STEP_NO + 1))
  wiz_clear
  printf '\n%s%s[%d/%d] %s%s\n\n' "$C_B" "$C_H" "$STEP_NO" "$STEPS_TOTAL" "$1" "$C_0"
}

wiz_say()  { printf '  %s\n' "$*"; }
wiz_do()   { printf '  %s->%s %s\n' "$C_H" "$C_0" "$*"; }
wiz_hint() { printf '  %s%s%s\n' "$C_D" "$*" "$C_0"; }
wiz_warn() { printf '  %s! %s%s\n' "$C_W" "$*" "$C_0"; }

# wiz_open URL: open in the default browser (macOS, Windows Git Bash, WSL, Linux).
wiz_open() {
  wiz_say "Opening $1"
  case "${OSTYPE:-}" in
    darwin*) open "$1" >/dev/null 2>&1 && return 0 ;;
    msys* | cygwin*) start "" "$1" >/dev/null 2>&1 && return 0 ;;
    *)
      if command -v wslview >/dev/null 2>&1; then
        wslview "$1" >/dev/null 2>&1 && return 0
      elif grep -qi microsoft /proc/version 2>/dev/null && command -v explorer.exe >/dev/null 2>&1; then
        explorer.exe "$1" >/dev/null 2>&1 || true  # explorer.exe exits non-zero even when it opens the page
        return 0
      elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$1" >/dev/null 2>&1 && return 0
      fi
      ;;
  esac
  wiz_warn "Could not open a browser. Visit it yourself: $1"
}

wiz_wait() { printf '  %s%s%s ' "$C_D" "${1:-Press Enter when done.}" "$C_0"; read -r _ || true; }

# wiz_confirm QUESTION: returns 0 only on y or yes.
wiz_confirm() {
  local answer=''
  printf '  %s%s [y/N]%s ' "$C_W" "$1" "$C_0"
  read -r answer || true
  case "$answer" in [yY] | [yY][eE][sS]) return 0 ;; *) return 1 ;; esac
}

# wiz_saved KEY: print the value KEY already has in ENV_FILE, if any.
wiz_saved() {
  [[ -f "$ENV_FILE" ]] || return 1
  local raw sq="'\\''" q="'"
  raw="$(awk -v k="$1" 'index($0, k "=") == 1 { v = substr($0, length(k) + 2) } END { if (v == "") exit 1; print v }' "$ENV_FILE")" || return 1
  case "$raw" in
    \'*\')
      raw="${raw#\'}"
      raw="${raw%\'}"
      raw=${raw//"$sq"/$q}
      ;;
    \"*\")
      raw="${raw#\"}"
      raw="${raw%\"}"
      case "$raw" in *[\\\$\`\"]*) return 1 ;; esac  # escapes or expansions: ask again instead of guessing
      ;;
  esac
  printf '%s' "$raw"
}

# wiz_ask KEY PROMPT [secret]: read a value into the shell variable KEY.
# Enter keeps the saved value. Pass "secret" as the third argument to hide typing.
wiz_ask() {
  local key="$1" prompt="$2" mode="${3:-}" saved='' value='' rc
  saved="$(wiz_saved "$key" || true)"
  [[ -n "$saved" ]] && prompt="$prompt ${C_D}(Enter keeps the saved value)${C_0}"
  while :; do
    rc=0
    printf '  %s%s%s ' "$C_B" "$prompt" "$C_0"
    if [[ "$mode" == secret ]]; then read -rs value || rc=1; printf '\n'; else read -r value || rc=1; fi
    if ((rc)) && [[ -z "$value$saved" ]]; then return 1; fi
    [[ -z "$value" ]] && value="$saved"
    [[ -n "$value" ]] && break
    wiz_warn "A value is required."
  done
  printf -v "$key" '%s' "$value"
}

# wiz_env KEY VALUE: insert or replace KEY in ENV_FILE. New files are created private (0600).
wiz_env() {
  local key="$1" value="$2" quoted tmp sq="'\\''" q="'"
  quoted=${value//"$q"/$sq}
  quoted="'$quoted'"
  [[ -e "$ENV_FILE" ]] || (umask 077; : >"$ENV_FILE")
  tmp="$(mktemp)"
  awk -v k="$1" 'index($0, k "=") != 1' "$ENV_FILE" >"$tmp"
  printf '%s=%s\n' "$key" "$quoted" >>"$tmp"
  cat "$tmp" >"$ENV_FILE"
  rm -f "$tmp"
  case " ${SAVED_KEYS[*]-} " in *" $key "*) ;; *) SAVED_KEYS+=("$key") ;; esac
  printf '  %ssaved%s %s in %s\n' "$C_OK" "$C_0" "$key" "$ENV_FILE"
}

wiz_gh_ready() { command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; }

# wiz_gh_secret NAME VALUE: GitHub Actions secret for the current repo.
wiz_gh_secret() {
  if wiz_gh_ready && printf '%s' "$2" | gh secret set "$1" >/dev/null 2>&1; then
    SET_REMOTE+=("secret $1")
    printf '  %sset%s GitHub secret %s\n' "$C_OK" "$C_0" "$1"
  else
    LEFT_FOR_HUMAN+=("gh secret set $1")
    wiz_warn "GitHub secret $1 not set (gh missing or logged out). Do it later: gh secret set $1"
  fi
}

# wiz_gh_var NAME VALUE: GitHub Actions variable (not secret).
wiz_gh_var() {
  if wiz_gh_ready && gh variable set "$1" --body "$2" >/dev/null 2>&1; then
    SET_REMOTE+=("variable $1")
    printf '  %sset%s GitHub variable %s\n' "$C_OK" "$C_0" "$1"
  else
    LEFT_FOR_HUMAN+=("gh variable set $1 --body <value>")
    wiz_warn "GitHub variable $1 not set. Do it later: gh variable set $1 --body <value>"
  fi
}

# wiz_finish: closing summary.
wiz_finish() {
  wiz_clear
  printf '\n%s%sAll steps done.%s\n' "$C_B" "$C_OK" "$C_0"
  if ((${#SAVED_KEYS[@]})); then wiz_hint "Saved to $ENV_FILE: ${SAVED_KEYS[*]}"; fi
  if ((${#SET_REMOTE[@]})); then wiz_hint "Set on GitHub: ${SET_REMOTE[*]}"; fi
  if ((${#LEFT_FOR_HUMAN[@]})); then
    wiz_warn "Still to do by hand:"
    local item
    for item in "${LEFT_FOR_HUMAN[@]}"; do wiz_hint "  $item"; done
  fi
  printf '\n'
}

# ---------------------------------------------------------------- steps (edit below)
# One wiz_step per screen, in dependency order. The total passed to wiz_begin must match.
# All steps stay inside main so bash reads the whole file before the first prompt.

main() {
  wiz_begin "Example service setup" 1

  wiz_step "Example service: API key"
  wiz_say "This key lets the app call the example service from local dev and CI."
  wiz_open "https://example.com/dashboard/api-keys"
  wiz_do "Click Create key, name it after this repo, and copy the key."
  wiz_ask EXAMPLE_API_KEY "Paste the key:" secret
  wiz_env EXAMPLE_API_KEY "$EXAMPLE_API_KEY"
  wiz_gh_secret EXAMPLE_API_KEY "$EXAMPLE_API_KEY"

  wiz_finish
}

main "$@"
exit
