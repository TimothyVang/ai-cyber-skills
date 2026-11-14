import hashlib, json, pathlib, subprocess, sys, threading, time
ROOT = pathlib.Path(sys.argv[1]).resolve()
OUT = ROOT / '.scratch/current-plugin-race'
OUT.mkdir()
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'plugins/deepmodebot/skills/deepmodebot/assets/github-app'))
import local_updates as updates
home, cache = OUT / 'home', OUT / 'cache'
home.mkdir()
source = updates.prepare_source(home, cache, False)
history = updates.text(source.path, 'log', '--max-count=2', '--format=%H', source.sha, '--', updates.PLUGIN).splitlines()
old = history[1]
marketplace = home / '.omp/plugins/cache/marketplaces/deepmodebot'
marketplace.parent.mkdir(parents=True)
commands = []
def git(*args):
    command = ['git', '-c', 'core.hooksPath=', *map(str, args)]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    commands.append({'argv': command, 'exit': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr})
    if run.returncode:
        raise RuntimeError(run.stderr)
git('clone', '--config', 'core.longpaths=true', '--config', 'core.autocrlf=false', str(source.path), str(marketplace))
git('-C', marketplace, 'remote', 'set-url', 'origin', updates.CANONICAL)
git('-C', marketplace, 'checkout', '-B', 'main', old)
installed = home / 'current-install'
for name, (data, mode) in source.contents(updates.PLUGIN).items():
    dest = installed / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    dest.chmod(mode)
assert updates.inventory(installed) == source.tree(source.sha, updates.PLUGIN)
target = installed / 'skills/deepmodebot/assets/github-app/bot.py'
original = target.read_bytes()
marker = b'\n# CONCURRENT LOCAL EDIT; DO NOT RECORD CANONICAL PROVENANCE\n'
fetch = marketplace / '.git/FETCH_HEAD'
def stamp():
    try:
        return fetch.stat().st_mtime_ns
    except (FileNotFoundError, PermissionError):
        return None
initial_stamp = stamp()
stop = threading.Event()
observations = {'upgrade_called': False, 'initial_complete_canonical_inventory': True}
def editor():
    deadline = time.monotonic() + 120
    while not stop.is_set() and time.monotonic() < deadline:
        observed = stamp()
        if observed is not None and observed != initial_stamp:
            target.write_bytes(original + marker)
            observations['edit_injected_after_marketplace_fetch_started'] = True
            return
        stop.wait(.001)
thread = threading.Thread(target=editor)
thread.start()
def upgrade_boundary():
    observations['upgrade_called'] = True
    raise RuntimeError('No package-manager execution authorized in this probe')
try:
    result = updates.synchronize(home, cache, install={'link': installed, 'marketplace': 'deepmodebot'}, upgrade=upgrade_boundary)
finally:
    stop.set()
    thread.join()
observations['edit_preserved'] = target.read_bytes() == original + marker
observations['edited_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
report = {'source': source.sha, 'marketplace_before': old, 'commands': commands, 'observations': observations,
          'result': result, 'updater_sha256': hashlib.sha256(pathlib.Path(updates.__file__).read_bytes()).hexdigest(),
          'limits': 'Real canonical-network synchronize API and external editor thread; no updater/provider function patched. Installed files began at current canonical contents. No package manager or watcher was invoked.'}
(OUT / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
assert observations.get('edit_injected_after_marketplace_fetch_started') and observations['edit_preserved']
assert not observations['upgrade_called'] and not result['upgraded']
assert str(installed) not in result['manifests'] and str(installed) in result['incomplete']
row = next(row for row in result['targets'] if row['kind'] == 'plugin')
assert row['action'] == 'preserved' and row['marketplace_action'] == 'fast-forwarded'
