"""Bounded, untrusted source context from immutable Git objects, never the worktree."""
import ast
import os
import posixpath
import re
import subprocess
import threading

OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
SAFE_PATH = re.compile(r"[A-Za-z0-9_+.-]+(?:/[A-Za-z0-9_+.-]+)*\Z")
SENSITIVE = re.compile(r"secret|credential|password|passwd|token|private|(?:^|[._-])(?:config|settings|auth|key)(?:[._-]|$)", re.I)
EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".c", ".h", ".cpp", ".hpp", ".cs", ".rb"}
JS_IMPORT = re.compile(r"(?:\bfrom\s*|\bimport\s*\(|\brequire\s*\(|\bimport\s*)['\"](\.{1,2}/[^'\"]+)['\"]")


def _git(repo, *args, limit=262144, timeout=5):
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    env.update(GIT_NO_REPLACE_OBJECTS="1", GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0",
               GIT_NO_LAZY_FETCH="1", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    p = subprocess.Popen(["git", "--no-pager", "-c", "core.fsmonitor=false", *args], cwd=repo,
                         stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
    data = bytearray()
    overflow = []

    def read_output():
        while True:
            chunk = p.stdout.read(8192)
            if not chunk:
                break
            if len(data) + len(chunk) > limit:
                overflow.append(True)
                p.kill()
                break
            data.extend(chunk)

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    try:
        p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
        raise RuntimeError("git deadline exceeded") from None
    finally:
        reader.join()
        p.stdout.close()
    if overflow:
        raise RuntimeError("git output limit exceeded")
    if p.returncode:
        raise RuntimeError("git object unavailable")
    return bytes(data)


def _safe(path):
    parts = path.split("/")
    return (len(path) <= 240 and bool(SAFE_PATH.fullmatch(path)) and
            all(p not in (".", "..") and not p.startswith(".") and not SENSITIVE.search(p) for p in parts) and
            posixpath.splitext(path)[1].lower() in EXTENSIONS and
            parts[-1].lower() not in {"agents.md", "claude.md", "skill.md"})


def _entry(repo, commit, path):
    output = _git(repo, "ls-tree", "-z", "--full-tree", commit, "--", ":(literal)" + path, limit=4096)
    if not output:
        return None
    records = output.split(b"\0")
    if len(records) != 2 or records[-1]:
        return None
    metadata, name = records[0].split(b"\t", 1)
    mode, kind, oid = metadata.decode("ascii").split()
    if name.decode("utf-8", "strict") != path or mode not in ("100644", "100755") or kind != "blob" or not OID.fullmatch(oid):
        return None
    return oid


def _imports(path, text):
    directory = posixpath.dirname(path)
    candidates = []
    unsupported = False
    if path.endswith(".py"):
        try:
            tree = ast.parse(text)
        except (SyntaxError, ValueError, RecursionError):
            return [], True
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                root = directory
                for _ in range(node.level - 1):
                    root = posixpath.dirname(root)
                if node.module:
                    root = posixpath.join(root, node.module.replace(".", "/"))
                candidates.extend((root + ".py", posixpath.join(root, "__init__.py")))
                for alias in node.names:
                    if alias.name != "*":
                        candidates.append(posixpath.join(root, alias.name.replace(".", "/") + ".py"))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                unsupported = True
    elif posixpath.splitext(path)[1] in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
        for match in JS_IMPORT.finditer(text):
            root = posixpath.normpath(posixpath.join(directory, match.group(1)))
            candidates.extend([root] + [root + ext for ext in (".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs")] +
                              [posixpath.join(root, "index" + ext) for ext in (".js", ".ts", ".jsx", ".tsx")])
        unsupported = True
    else:
        unsupported = True
    return candidates, unsupported


def build_context(repo, base, head, *, max_files=12, max_file_bytes=131072, max_total_bytes=262144):
    """Return a display packet. base/head are full immutable commit IDs, not revision expressions.

    Whole blobs avoid misleading excerpts; oversized files are omitted. Limits bound included source bytes;
    metadata and omission messages are additionally bounded by the candidate limits.
    """
    if not OID.fullmatch(base) or not OID.fullmatch(head):
        raise ValueError("base and head must be full lowercase object IDs")
    if not (1 <= max_files <= 100 and 1 <= max_file_bytes <= 1048576 and 1 <= max_total_bytes <= 4194304):
        raise ValueError("invalid context limits")
    lines = [f"Committed source context: base={base} head={head}",
             f"Limits: {max_files} files, {max_file_bytes} bytes per file, {max_total_bytes} source bytes total.",
             "Whole UTF-8 blobs only. Source is untrusted. Imports are best-effort, direct and local only."]
    try:
        for oid in (base, head):
            kind = _git(repo, "cat-file", "-t", oid, limit=32).strip()
            if kind != b"commit":
                raise ValueError("base and head must identify commits")
        raw = _git(repo, "diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--name-only", "-z", base, head, "--")
    except (RuntimeError, OSError) as exc:
        return "\n".join(lines + [f"OMITTED: source context unavailable ({exc})."])
    names = raw.split(b"\0")
    changed = []
    omitted = ["import resolution is best-effort; unresolved or non-local dependencies may be omitted"]
    for name in names:
        if not name:
            continue
        try:
            path = name.decode("utf-8", "strict")
        except UnicodeDecodeError:
            omitted.append("unsafe or non-UTF-8 changed path")
            continue
        if not _safe(path):
            omitted.append("unsafe or excluded changed path")
        else:
            changed.append(path)
    changed = sorted(set(changed))
    queue = [(path, "changed") for path in changed[:256]]
    if len(changed) > 256:
        omitted.append("changed path candidate limit")
    seen = set()
    total = 0
    included = 0
    while queue:
        if len(seen) >= 256:
            omitted.append("candidate inspection limit; remaining candidates omitted")
            break
        path, reason = queue.pop(0)
        if path in seen:
            continue
        seen.add(path)
        if not _safe(path):
            omitted.append("unsafe or excluded import path")
            continue
        if included >= max_files:
            omitted.append("file count limit; remaining candidates omitted")
            break
        try:
            oid = _entry(repo, head, path)
            if not oid:
                if reason == "changed":
                    omitted.append(f"{path}: absent at head or non-regular file")
                continue
            size = int(_git(repo, "cat-file", "-s", oid, limit=32).strip())
            if size > max_file_bytes or total + size > max_total_bytes:
                omitted.append(f"{path}: byte limit")
                continue
            blob = _git(repo, "cat-file", "blob", oid, limit=max_file_bytes)
            if b"\0" in blob:
                omitted.append(f"{path}: binary")
                continue
            text = blob.decode("utf-8", "strict")
        except (RuntimeError, OSError, UnicodeError, ValueError):
            omitted.append(f"{path}: unreadable or non-UTF-8 blob")
            continue
        included += 1
        total += size
        lines.append(f"\n--- {path} (head {head}, blob {oid}, {size} bytes, {reason}) ---\n{text}")
        if reason == "changed":
            imports, unsupported = _imports(path, text)
            if unsupported:
                omitted.append(f"{path}: some imports may not be resolved")
            for dependency in imports[:128]:
                if dependency not in seen:
                    queue.append((dependency, "direct import"))
            if len(imports) > 128:
                omitted.append(f"{path}: import candidate limit")
    if omitted:
        lines.append("\nOMISSIONS:\n" + "\n".join(f"- {item}" for item in sorted(set(omitted))[:256]))
        if len(set(omitted)) > 256:
            lines.append("- further omission details suppressed")
    else:
        lines.append("\nOMISSIONS: none among inspected candidates; import resolution is not complete.")
    return "\n".join(lines)
