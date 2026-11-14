"""Conservative synchronization from pinned canonical Git objects, never a user's worktree."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import uuid

CANONICAL = "https://github.com/TimothyVang/deepmodebot.git"
CANONICAL_REPOSITORY_ID = 1449516491
PLUGIN = "plugins/deepmodebot"
SKILLS = PLUGIN + "/skills"
TIMEOUT = 120
HISTORY_LIMIT = 2000
CACHES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


class GitCommandError(RuntimeError):
    """A checked Git command failed, rather than deliberately preserving an ineligible copy."""


def canonical(url):
    return bool(re.fullmatch(r"(?:https://github\.com/|ssh://git@github\.com/|git@github\.com:)"
                             r"TimothyVang/(?:deepmodebot|deep-mode)(?:\.git)?/?", url, re.I))


def git(path, *args, check=True, data=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    proc = subprocess.run(["git", "-c", "core.hooksPath=", "-C", str(path), *args],
                          input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=TIMEOUT, env=env)
    if check and proc.returncode:
        raise GitCommandError(proc.stderr.decode("utf-8", "replace").strip() or "git failed")
    return proc


def text(path, *args):
    return git(path, *args).stdout.decode("utf-8").strip()


def origin_problem(path):
    urls = text(path, "remote", "get-url", "--all", "origin").splitlines()
    if len(urls) != 1 or not canonical(urls[0]):
        return "origin is a fork or unknown source (canonical upstream does not override origin)"
    return None


def linked(path):
    return any(p.is_symlink() or (p.exists() and getattr(p.lstat(), "st_file_attributes", 0) & 0x400)
               for p in (path, *path.parents))


def generated(name):
    return bool(set(PurePosixPath(name).parts) & CACHES)


def signature(path):
    if linked(path) or not path.is_file():
        raise RuntimeError(f"not an unlinked regular file: {path}")
    data = path.read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    mode = "100755" if os.name != "nt" and path.stat().st_mode & 0o100 else "100644"
    return blob, mode


def inventory(path):
    files = {}
    for root, dirs, names in os.walk(path, followlinks=False):
        base = Path(root)
        for name in dirs + names:
            child = base / name
            if linked(child):
                raise RuntimeError(f"linked file or directory: {child}")
        dirs[:] = [name for name in dirs if name not in CACHES]
        for name in names:
            child = base / name
            if not child.is_file():
                raise RuntimeError(f"not a regular file: {child}")
            files[child.relative_to(path).as_posix()] = signature(child)
    return files


class Source:
    def __init__(self, path, sha):
        self.path, self.sha = path, sha
        self.trees = {}

    def tree(self, sha, prefix):
        key = sha, prefix
        if key not in self.trees:
            files = {}
            for row in git(self.path, "ls-tree", "-rz", sha, "--", prefix + "/").stdout.split(b"\0"):
                if not row:
                    continue
                info, raw_name = row.split(b"\t", 1)
                mode, kind, blob = info.decode().split()
                name = raw_name.decode("utf-8")[len(prefix) + 1:]
                if mode not in ("100644", "100755") or kind != "blob":
                    raise RuntimeError(f"unsupported canonical entry: {prefix}/{name}")
                if "\\" in name or ":" in name or any(p in ("", ".", "..", ".git") for p in name.split("/")):
                    raise RuntimeError("unsafe canonical filename")
                files[name] = (blob, "100644" if os.name == "nt" else mode)
            self.trees[key] = files
        return self.trees[key]

    def historical(self, prefix, files):
        history = text(self.path, "log", f"--max-count={HISTORY_LIMIT}", "--format=%H", self.sha,
                       "--", prefix).splitlines()
        for sha in history:
            if self.tree(sha, prefix) == files:
                return sha
        raise RuntimeError(f"no complete canonical snapshot matches (searched {len(history)} historical revisions); "
                           "unknown provenance or local modifications")

    def ancestor(self, sha):
        return isinstance(sha, str) and bool(re.fullmatch(r"[0-9a-f]{40}", sha)) and git(
            self.path, "merge-base", "--is-ancestor", sha, self.sha, check=False).returncode == 0

    def contents(self, prefix):
        entries = self.tree(self.sha, prefix)
        request = "".join(blob + "\n" for blob, _ in entries.values()).encode()
        data = git(self.path, "cat-file", "--batch", data=request).stdout
        contents, offset = {}, 0
        for name, (blob, mode) in entries.items():
            end = data.index(b"\n", offset)
            actual, kind, size = data[offset:end].decode().split()
            if actual != blob or kind != "blob":
                raise RuntimeError("canonical blob response does not match its tree")
            offset = end + 1
            contents[name] = (data[offset:offset + int(size)], int(mode, 8) & 0o777)
            offset += int(size) + 1
        return contents


def repository_metadata():
    """One network identity observation per update; the numeric authority survives rebranding."""
    proc = subprocess.run(
        ["gh", "api", "repos/TimothyVang/deepmodebot", "--jq",
         "{id: .id, fork: .fork, default_branch: .default_branch}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=TIMEOUT)
    if proc.returncode:
        raise RuntimeError("canonical repository identity unavailable: "
                           + proc.stderr.decode("utf-8", "replace").strip())
    return json.loads(proc.stdout)


def prepare_source(home, cache, dry):
    """Dry runs only read existing objects; missing objects are an explicit unavailable result."""
    identity = repository_metadata()
    if not isinstance(identity, dict) or identity.get("id") != CANONICAL_REPOSITORY_ID \
            or identity.get("fork") is not False or identity.get("default_branch") != "main":
        raise RuntimeError("fork or unsupported source: repository identity does not match canonical "
                           f"GitHub repository {CANONICAL_REPOSITORY_ID} on main")
    path = cache / "canonical.git"
    if linked(path):
        raise RuntimeError("canonical source cache is linked; preserved")
    if dry:
        choices = [path, home / ".omp/plugins/cache/marketplaces/deepmodebot"]
        path = next((p for p in choices if p.is_dir() and not origin_problem(p)), None)
        if path is None:
            raise RuntimeError("canonical source unavailable locally; a real update must fetch it first")
    elif not path.exists():
        cache.mkdir(parents=True, exist_ok=True)
        git(cache, "clone", "--bare", CANONICAL, str(path))
    if linked(path) or origin_problem(path):
        raise RuntimeError("canonical source cache has a linked path or noncanonical origin")
    remote = text(path, "ls-remote", CANONICAL, "refs/heads/main").split()
    if len(remote) != 2 or not re.fullmatch(r"[0-9a-f]{40}", remote[0]):
        raise RuntimeError("canonical main is unavailable")
    sha = remote[0]
    if not dry:
        git(path, "fetch", "--no-tags", CANONICAL, "refs/heads/main")
    if git(path, "cat-file", "-e", sha + "^{commit}", check=False).returncode:
        raise RuntimeError(f"canonical snapshot {sha} unavailable locally; a real update must fetch it first")
    return Source(path, sha)


def marketplace_metadata(path, source):
    """Recognize OMP's root manifest from tracked HEAD bytes, never from a worktree."""
    metadata = path / "marketplace.json"
    if linked(metadata) or not metadata.is_file():
        return False
    normalized = metadata.read_bytes().replace(b"\r\n", b"\n").removesuffix(b"\n")
    for name in (".omp-plugin/marketplace.json", ".claude-plugin/marketplace.json"):
        entry = git(path, "ls-tree", "-z", "HEAD", "--", name).stdout
        if not entry:
            continue
        info, _ = entry.rstrip(b"\0").split(b"\t", 1)
        mode, kind, blob = info.decode().split()
        if mode not in ("100644", "100755") or kind != "blob":
            continue
        canonical_data = git(path, "cat-file", "blob", blob).stdout
        if normalized != canonical_data.replace(b"\r\n", b"\n").removesuffix(b"\n"):
            continue
        if git(source.path, "ls-tree", "-z", source.sha, "--", "marketplace.json").stdout:
            raise RuntimeError("canonical path collides with generated marketplace.json; preserved")
        return True
    return False


def checkout_problem(path, marketplace_source=None):
    if linked(path):
        return "linked checkout is not managed"
    if problem := origin_problem(path):
        return problem
    if text(path, "rev-parse", "--show-toplevel").replace("\\", "/").lower() != path.resolve().as_posix().lower():
        return "path is inside another checkout"
    branch = git(path, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if branch.returncode:
        return "detached HEAD; no branch switch is permitted"
    if branch.stdout.decode().strip() != "main":
        return "not on main; feature branches are preserved"
    if any(row[0] != "H" for row in text(path, "ls-files", "-v").splitlines()):
        return "index has sparse, skip-worktree, or assume-unchanged entries"
    status = git(path, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    for row in status.split(b"\0"):
        if not row or (row.startswith(b"?? ") and generated(row[3:].decode("utf-8"))):
            continue
        if row == b"?? marketplace.json" and marketplace_source is not None \
                and marketplace_metadata(path, marketplace_source):
            continue
        return "dirty checkout; tracked edits or unknown untracked files are preserved"
    ignored = git(path, "ls-files", "--others", "--ignored", "--exclude-standard", "-z").stdout
    if any(row and not generated(row.decode("utf-8")) for row in ignored.split(b"\0")):
        return "checkout has unknown ignored files; preserved"
    return None


def sync_checkout(path, source, dry, marketplace_source=None):
    problem = checkout_problem(path, marketplace_source)
    if problem:
        raise RuntimeError(problem)
    before = text(path, "rev-parse", "HEAD")
    if not source.ancestor(before):
        raise RuntimeError("local commits or diverged history; no reset, stash, or branch switch")
    if before == source.sha:
        return "current", {"kind": "checkout", "sha": before, "origin": CANONICAL}
    if not dry:
        git(path, "fetch", "--no-tags", CANONICAL, "refs/heads/main")
        if checkout_problem(path, marketplace_source) or text(path, "rev-parse", "HEAD") != before:
            raise RuntimeError("checkout changed during update; preserved")
        git(path, "merge", "--ff-only", source.sha)
    return "would fast-forward" if dry else "fast-forwarded", {
        "kind": "checkout", "sha": source.sha, "origin": CANONICAL}


def copy_plan(path, prefix, source, manifest):
    if linked(path):
        raise RuntimeError("linked copy is not managed")
    if git(path, "rev-parse", "--show-toplevel", check=False).returncode == 0:
        raise RuntimeError("copy belongs to a Git checkout; register its repository root instead")
    current = inventory(path)
    if manifest:
        if not isinstance(manifest, dict) or manifest.get("origin") != CANONICAL \
                or manifest.get("prefix") != prefix or not source.ancestor(manifest.get("sha")):
            raise RuntimeError("provenance manifest is not a canonical historical snapshot")
        previous = source.tree(manifest["sha"], prefix)
        base = manifest["sha"]
        if not previous or any(current.get(name) != blob for name, blob in previous.items()):
            raise RuntimeError("managed files were locally edited or removed; preserved")
    else:
        base = source.historical(prefix, current)
        previous = source.tree(base, prefix)
    desired = source.tree(source.sha, prefix)
    if not desired:
        raise RuntimeError("copy no longer exists in canonical main; preserved")
    unknown = set(current) - set(previous)
    if unknown & set(desired):
        raise RuntimeError("new canonical files collide with unknown local files; preserved")
    # A local directory where upstream needs a file must never be replaced, even if empty.
    for name in desired:
        dest = path / name
        if dest.is_dir() or any(p.is_file() for p in dest.parents if p != path and path in p.parents):
            raise RuntimeError(f"canonical file collides with a local path: {name}")
    return current, previous, desired, base


def backup(path, files, cache):
    folder = cache / "backups" / uuid.uuid4().hex
    for name in files:
        dest = folder / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path / name, dest)
    return str(folder)


def pending_path(cache, path):
    key = hashlib.sha256(os.path.normcase(str(path.absolute())).encode("utf-8")).hexdigest()
    return cache / "pending" / (key + ".json")


def temporary_path(path, name, token):
    dest = path / name
    return dest.with_name("." + dest.name + ".update-" + token)


def read_pending(journal, path, prefix, source):
    if linked(journal):
        raise RuntimeError("linked update journal; preserved")
    data = json.loads(journal.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("path") != str(path.absolute()) \
            or data.get("origin") != CANONICAL or data.get("prefix") != prefix \
            or not source.ancestor(data.get("base")) or not source.ancestor(data.get("sha")) \
            or not isinstance(data.get("token"), str) or not re.fullmatch(r"[0-9a-f]{32}", data["token"]) \
            or not isinstance(data.get("backup"), str):
        raise RuntimeError("invalid pending update provenance; preserved")
    return data


def save_pending(journal, data):
    journal.parent.mkdir(parents=True, exist_ok=True)
    temp = journal.with_suffix(".tmp")
    with temp.open("wb") as stream:
        stream.write(json.dumps(data, sort_keys=True).encode("utf-8"))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, journal)


def resume_plan(path, prefix, source, pending):
    if linked(path) or git(path, "rev-parse", "--show-toplevel", check=False).returncode == 0:
        raise RuntimeError("pending copy is linked or now belongs to a checkout; preserved")
    current = inventory(path)
    previous = source.tree(pending["base"], prefix)
    desired = source.tree(pending["sha"], prefix)
    if not previous or not desired:
        raise RuntimeError("pending update names an absent canonical skill")
    for name in set(previous) | set(desired):
        allowed = {previous.get(name), desired.get(name)}
        if current.get(name) not in allowed:
            raise RuntimeError(f"pending update conflicts with a local edit: {name}; backup: {pending['backup']}")
    for name in desired:
        dest = path / name
        if dest.is_dir() or any(p.is_file() for p in dest.parents if p != path and path in p.parents):
            raise RuntimeError(f"pending update collides with a local path: {name}")
        temp = temporary_path(path, name, pending["token"])
        if temp.exists() and (linked(temp) or not temp.is_file()):
            raise RuntimeError(f"pending temporary path is not a regular file: {temp}")
    return current, previous, desired


def sync_copy(path, prefix, source, manifest, cache, dry):
    journal = pending_path(cache, path)
    if linked(journal):
        raise RuntimeError("linked update journal; preserved")
    pending = read_pending(journal, path, prefix, source) if journal.exists() else None
    # Only a manifest supplied by the caller's persisted receipt acknowledges completion.
    if pending and isinstance(manifest, dict) and all(
            manifest.get(k) == pending[k] for k in ("origin", "prefix", "sha")):
        if not dry:
            journal.unlink()
        pending = None
    if pending:
        current, previous, desired = resume_plan(path, prefix, source, pending)
        target = Source(source.path, pending["sha"])
    else:
        current, previous, desired, base = copy_plan(path, prefix, source, manifest)
        target = source
    record = {"kind": "copy", "origin": CANONICAL, "sha": target.sha, "prefix": prefix}
    if pending:
        record["backup"] = pending["backup"]
    complete = all(current.get(name) == blob for name, blob in desired.items()) \
        and not any(name in current for name in set(previous) - set(desired))
    if complete and not pending:
        if inventory(path) != current:
            raise RuntimeError("copy changed during verification; preserved")
        return "current" if manifest else "would adopt" if dry else "adopted", record
    if dry:
        return "would recover" if pending else "would synchronize", record
    contents = target.contents(prefix)
    if inventory(path) != current:
        raise RuntimeError("copy changed during update; preserved")
    if not pending:
        record["backup"] = backup(path, previous, cache)
        if inventory(path) != current:
            raise RuntimeError("copy changed during backup; preserved")
        pending = {**record, "path": str(path.absolute()), "base": base, "token": uuid.uuid4().hex}
        if any(temporary_path(path, name, pending["token"]).exists() for name in desired):
            raise RuntimeError("update temporary filename collision; preserved")
        save_pending(journal, pending)
    for name, (data, mode) in contents.items():
        dest = path / name
        tmp = temporary_path(path, name, pending["token"])
        observed = signature(dest) if dest.exists() else None
        if linked(dest) or observed != current.get(name):
            raise RuntimeError(f"copy changed during update: {name}; pending recovery retained")
        if observed != desired[name]:
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(data)
            tmp.chmod(mode & 0o777)
            if (signature(dest) if dest.exists() else None) != observed or linked(dest):
                raise RuntimeError(f"copy changed before replacement: {name}; pending recovery retained")
            os.replace(tmp, dest)
        elif tmp.exists():
            # This exact path was reserved by this transaction before any copy mutation.
            tmp.unlink()
    for name in set(previous) - set(desired):
        dest = path / name
        observed = signature(dest) if dest.exists() else None
        if linked(dest) or observed != current.get(name):
            raise RuntimeError(f"copy changed before removal: {name}; pending recovery retained")
        if observed is not None:
            dest.unlink()
    verified = inventory(path)
    if any(verified.get(name) != blob for name, blob in desired.items()) or any(
            name in verified for name in set(previous) - set(desired)):
        raise RuntimeError("copy changed during update; pending recovery retained")
    # Retain the journal through receipt persistence (including process termination).
    return "recovered" if target.sha != source.sha or complete else "synchronized", record


def discover(home, registered, source=None):
    targets = {}
    for parent in (home, home / "code", home / "repos", home / "projects", home / "src"):
        for name in ("deep-mode", "deepmodebot"):
            path = parent / name
            if path.exists():
                targets[str(path.absolute())] = (path, "checkout", "")
    for value in registered:
        path = Path(value).expanduser().absolute()
        targets[str(path)] = (path, "checkout", "")
    for root in (home / ".omp/agent/skills", home / ".claude/skills", home / ".agents/skills"):
        if not root.is_dir():
            continue
        # Only direct skill children, never recursive disk discovery. Names select candidates, not trust.
        names = {PurePosixPath(name).parts[0] for name in source.tree(source.sha, SKILLS)} if source else set()
        for path in root.iterdir():
            if path.is_dir() and (path.name in names or (path / "SKILL.md").is_file()):
                targets[str(path.absolute())] = (path, "copy", SKILLS + "/" + path.name)
    return list(targets.values())


def synchronize(home, cache, registered=(), manifests=None, dry=False, install=None, upgrade=None):
    """Public update seam. Every candidate returns an action or a precise refusal reason."""
    manifests = manifests or {}
    result = {"remote": None, "targets": [], "manifests": dict(manifests), "upgraded": False, "incomplete": []}
    try:
        source = prepare_source(home, cache, dry)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as err:
        result["error"] = str(err)
        for path, kind, _ in discover(home, registered):
            result["targets"].append({"path": str(path), "kind": kind, "action": "preserved", "reason": str(err)})
        if install:
            result["targets"].append({"path": str(install["link"]), "kind": "plugin", "action": "preserved", "reason": str(err)})
        return result
    result["remote"] = source.sha
    for path, kind, prefix in discover(home, registered, source):
        key = str(path.absolute())
        row = {"path": key, "kind": kind}
        try:
            if not path.is_dir():
                raise RuntimeError("registered checkout is missing")
            if kind == "checkout":
                action, record = sync_checkout(path, source, dry)
            else:
                action, record = sync_copy(path, prefix, source, manifests.get(key), cache, dry)
            row["action"] = action
            if not dry:
                result["manifests"][key] = record
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as err:
            row.update(action="failed" if isinstance(err, (OSError, subprocess.SubprocessError, GitCommandError))
                       else "preserved", reason=str(err))
            if kind == "copy" and pending_path(cache, path).exists():
                result["incomplete"].append(key)
        result["targets"].append(row)
    if install:
        row = {"path": str(install["link"]), "kind": "plugin"}
        try:
            marketplace = home / ".omp/plugins/cache/marketplaces" / install["marketplace"]
            marketplace_source = source if marketplace == home / ".omp/plugins/cache/marketplaces/deepmodebot" else None
            if problem := checkout_problem(marketplace, marketplace_source):
                raise RuntimeError("marketplace: " + problem)
            if not source.ancestor(text(marketplace, "rev-parse", "HEAD")):
                raise RuntimeError("marketplace has local commits or diverged history")
            actual = install["link"].resolve()
            files = inventory(actual)
            source.historical(PLUGIN, files)
            desired = source.tree(source.sha, PLUGIN)
            if files == desired:
                row["marketplace_action"], _ = sync_checkout(marketplace, source, dry, marketplace_source)
                row["action"] = "current"
            elif dry:
                row["action"] = "would upgrade"
            else:
                row["backup"] = backup(actual, files, cache)
                sync_checkout(marketplace, source, False, marketplace_source)
                if install["link"].resolve() != actual or inventory(actual) != files:
                    raise RuntimeError("installed copy changed during update; preserved")
                row["action"] = "updating"
                upgrade()
            if not dry:
                if inventory(install["link"].resolve()) != desired:
                    raise RuntimeError("installed contents do not match the pinned canonical SHA; not recorded")
                if row["action"] == "updating":
                    row["action"] = "upgraded"
                    result["upgraded"] = True
                result["manifests"][str(install["link"])] = {
                    "kind": "plugin", "origin": CANONICAL, "sha": source.sha, "prefix": PLUGIN}
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as err:
            failed = row.get("action") == "updating" or isinstance(
                err, (OSError, subprocess.SubprocessError, GitCommandError))
            row.update(action="failed" if failed else "preserved", reason=str(err))
            # Refusal must remain a handover barrier on later retries too: a partial
            # manager upgrade is no longer a recognizable historical snapshot.
            result["incomplete"].append(str(install["link"].resolve()))
        result["targets"].append(row)
    return result
