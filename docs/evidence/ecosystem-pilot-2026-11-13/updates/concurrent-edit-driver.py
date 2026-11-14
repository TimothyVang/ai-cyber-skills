import hashlib, json, pathlib, subprocess, sys, threading, time
ROOT = pathlib.Path(sys.argv[1]).resolve()
OUT = ROOT / '.scratch/updater-race-fixed'
resume = sys.argv[2:] == ['--resume']
OUT.mkdir(exist_ok=resume)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'plugins/deepmodebot/skills/deepmodebot/assets/github-app'))
import local_updates as updates
home, cache = OUT / 'home', OUT / 'cache'
home.mkdir(exist_ok=resume)
source = updates.prepare_source(home, cache, False)
history = updates.text(source.path, 'log', '--max-count=2', '--format=%H', source.sha, '--', updates.PLUGIN).splitlines()
old = history[1]
marketplace = home / '.omp/plugins/cache/marketplaces/deepmodebot'
marketplace.parent.mkdir(parents=True, exist_ok=resume)
commands = []
def git(*args):
    command = ['git', '-c', 'core.hooksPath=', *map(str, args)]
    run = subprocess.run(command, capture_output=True, cwd=ROOT, text=True, encoding='utf-8', errors='replace')
    commands.append({'argv': command, 'exit': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr})
    if run.returncode:
        raise RuntimeError(run.stderr)
    return run.stdout.strip()
installed = home / 'isolated-install'
if not resume:
    git('clone', '--config', 'core.longpaths=true', '--config', 'core.autocrlf=false', str(source.path), str(marketplace))
    git('-C', marketplace, 'remote', 'set-url', 'origin', updates.CANONICAL)
    git('-C', marketplace, 'checkout', '-B', 'main', old)
    for name, (data, mode) in updates.Source(source.path, old).contents(updates.PLUGIN).items():
        dest = installed / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        dest.chmod(mode)
else:
    previous = (OUT / 'receipt.json').read_bytes()
    (OUT / 'initial-receipt.json').write_bytes(previous)
    old = json.loads(previous)['old']
    assert updates.inventory(installed) == source.tree(old, updates.PLUGIN)
target = installed / 'skills/deepmodebot/SKILL.md'
original = target.read_bytes()
marker = b'\nLOCAL EDIT ARRIVED AFTER BACKUP; MUST NOT ENTER UPGRADE\n'
stop = threading.Event()
observations = {'upgrade_called': False}
existing_backups = set((cache / 'backups').glob('*/skills/deepmodebot/SKILL.md'))
def editor():
    deadline = time.monotonic() + 120
    while not stop.is_set() and time.monotonic() < deadline:
        backups = [path for path in (cache / 'backups').glob('*/skills/deepmodebot/SKILL.md')
                   if path not in existing_backups]
        try:
            complete = backups and backups[0].read_bytes() == original
        except PermissionError:
            complete = False  # Windows may deny reads until the backup writer closes its handle.
        if complete:
            target.write_bytes(original + marker)
            observations['edit_injected'] = True
            observations['backup_sha256'] = hashlib.sha256(backups[0].read_bytes()).hexdigest()
            observations['edited_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
            return
        stop.wait(.001)
thread = threading.Thread(target=editor)
thread.start()
def upgrade_boundary():
    observations['upgrade_called'] = True
    raise RuntimeError('Observation-only boundary: package-manager execution is not authorized')
try:
    result = updates.synchronize(home, cache, install={'link': installed, 'marketplace': 'deepmodebot'}, upgrade=upgrade_boundary)
finally:
    stop.set()
    thread.join()
observations['edit_preserved'] = target.read_bytes() == original + marker
report = {'source': source.sha, 'old': old, 'commands': commands, 'observations': observations, 'result': result,
          'updater_sha256': hashlib.sha256(pathlib.Path(updates.__file__).read_bytes()).hexdigest(),
          'limits': 'Real synchronize API, canonical network/Git and concurrent scratch-only editor. No updater/provider function patched. The callback is an observation-only stop; no package manager or production installation was invoked.'}
(OUT / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
assert observations.get('edit_injected') and observations['edit_preserved']
assert not observations['upgrade_called'] and not result['upgraded']
assert str(installed) not in result['manifests']
assert next(row for row in result['targets'] if row['kind'] == 'plugin')['action'] == 'preserved'
