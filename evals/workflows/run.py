#!/usr/bin/env python3
"""Pinned workflow inventory and operator-run, disposable agent journeys."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RUNS = ROOT / '.scratch' / 'workflows'
API_KEYS = ('ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'CODEX_API_KEY')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def inside(root, name):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or '\\' in str(name):
        raise ValueError(f'unsafe relative path: {name}')
    target = root / path
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'path escapes root: {name}')
    if any(p.is_symlink() for p in [target, *target.parents] if p.is_relative_to(root)):
        raise ValueError(f'symlink path: {name}')
    return target


def scenarios():
    rows = load(HERE / 'scenarios.json')['scenarios']
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('duplicate scenario ID')
    return {r['id']: r for r in rows}


def inventory_paths(source):
    return {f['path'] for f in source['files'] if f['path'].endswith('/SKILL.md')
            or f['path'].startswith('skills/poteto-mode/playbooks/') and f['path'].endswith('.md')
            or f['path'].startswith('agents/') and f['path'].endswith('.md')
            or f['path'] == 'automations/benny/README.md'}


def evidence_file(record):
    path = inside(ROOT, record['path'])
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f'missing/empty evidence: {path}')
    if digest(path.read_bytes()) != record['sha256']:
        raise ValueError(f'evidence digest mismatch: {path}')
    return path


def validate():
    entries = load(HERE / 'matrix.json')['entries']
    suite = scenarios()
    expected = set()
    sources = {}
    for path in sorted((HERE / 'sources').glob('*.json')):
        source = load(path)
        if source['truncated'] or not re.fullmatch('[0-9a-f]{40}', source['commit']):
            raise ValueError(f'incomplete or unpinned inventory: {path}')
        files = [f['path'] for f in source['files']]
        if len(files) != len(set(files)):
            raise ValueError(f'duplicate source paths: {path}')
        sources[path.stem] = source
        expected.update(path.stem + ':' + p for p in inventory_paths(source))
    actual = [row['id'] for row in entries]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError(f'inventory mapping mismatch: missing={sorted(expected-set(actual))}; extra={sorted(set(actual)-expected)}; duplicates={len(actual)-len(set(actual))}')
    for row in entries:
        source = sources[row['upstream']]
        if row['id'] != row['upstream'] + ':' + row['path'] or row['commit'] != source['commit']:
            raise ValueError(f'wrong source binding: {row["id"]}')
        expected_url = f'https://github.com/{source["repository"]}/blob/{source["commit"]}/{source["prefix"]}{row["path"]}'
        if row['source_url'] != expected_url:
            raise ValueError(f'wrong source URL: {row["id"]}')
        if row['disposition'] not in ('mapped', 'missing', 'not-applicable') or not row['limits'].strip():
            raise ValueError(f'invalid disposition/limits: {row["id"]}')
        if row['disposition'] == 'mapped' and not row['routes']:
            raise ValueError(f'mapped item has no route: {row["id"]}')
        for route in row['routes']:
            if not inside(ROOT, route).is_file():
                raise ValueError(f'missing local route: {route}')
        if not set(row['scenarios']) <= suite.keys():
            raise ValueError(f'unknown scenario: {row["id"]}')
        if row['state'] not in ('mapped', 'executed', 'failed', 'blocked'):
            raise ValueError(f'invalid evidence state: {row["id"]}')
        if row['state'] in ('executed', 'failed'):
            if not row['evidence'] or not row['scenarios']:
                raise ValueError(f'asserted run without evidence/scenario: {row["id"]}')
            for reference in row['evidence']:
                result = load(evidence_file(reference))
                verify_result(result)
                wanted = 'passed' if row['state'] == 'executed' else 'failed'
                if result['scenario'] not in row['scenarios'] or result['status'] != wanted:
                    raise ValueError(f'wrong result for mapping: {row["id"]}')
        else:
            for reference in row['evidence']:
                evidence_file(reference)
    for scenario in suite.values():
        if scenario['runner'] == 'outcome':
            if not inside(ROOT, scenario['manifest']).is_file():
                raise ValueError('missing linked outcome task')
        else:
            seed = load(HERE / 'seeds' / (scenario['seed'] + '.json'))
            for name in seed:
                inside(ROOT, name)
            ids = [c['id'] for c in scenario['checks']]
            if not ids or len(ids) != len(set(ids)) or not scenario['artifacts']:
                raise ValueError('invalid scenario checks/artifacts')
    return entries


def run_dir(identifier):
    if not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}', identifier):
        raise ValueError('run ID must be a lowercase slug of at most 64 characters')
    return inside(RUNS, identifier)


def file_record(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(path.read_bytes())}


def project_files(project):
    result = {}
    total = 0
    for path in sorted(project.rglob('*')):
        relative = path.relative_to(project)
        if any(p in ('.git', '.omp', '.scratch', '.worktrees', '__pycache__') for p in relative.parts):
            continue
        inside(project, relative.as_posix())
        if path.is_file():
            total += path.stat().st_size
            if total > 10_000_000:
                raise ValueError('project capture exceeds 10 MB')
            result[relative.as_posix()] = digest(path.read_bytes())
    return result


def prepare(args):
    scenario = scenarios()[args.scenario]
    if scenario['runner'] != 'local':
        raise ValueError(scenario['instructions'])
    folder = run_dir(args.id)
    if folder.exists():
        raise ValueError('run already exists; choose a new ID (evidence is never overwritten)')
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', args.ref + '^{commit}'], cwd=ROOT, text=True).strip()
    brand = json.loads(subprocess.check_output(['git', 'show', commit + ':brand/brand.json'], cwd=ROOT, text=True))
    if any(not isinstance(brand.get(key), str) or not re.fullmatch('[a-z][a-z0-9-]*', brand[key])
           for key in ('slug', 'mainSkillName')):
        raise ValueError('snapshot brand must name a safe plugin and main skill')
    skills = f"plugins/{brand['slug']}/skills/"
    archive = subprocess.check_output(['git', 'archive', commit, skills], cwd=ROOT)
    seed = load(HERE / 'seeds' / (scenario['seed'] + '.json'))
    folder.mkdir(parents=True)
    project = folder / 'project'
    project.mkdir()
    subprocess.run(['git', 'init', '-b', 'main', str(project)], cwd=ROOT, check=True, capture_output=True)
    (project / '.git' / 'info' / 'exclude').write_text(chr(10).join(('.omp/', '.scratch/', '.worktrees/', '')), encoding='utf-8')
    for name, text in seed.items():
        path = inside(project, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    skill_hashes = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        for member in bundle:
            if member.isdir():
                continue
            if not member.isfile() or not member.name.startswith(skills):
                raise ValueError('skill archive contains unsupported member')
            name = member.name[len(skills):]
            path = inside(project / '.omp' / 'skills', name)
            data = bundle.extractfile(member).read()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            skill_hashes[name] = digest(data)
    safety = (f"Use the project-local .omp/skills/{brand['mainSkillName']}/SKILL.md instructions. "
              'This directory is your project root. Keep all writes and temporary files inside it. '
              'No external issue comments, pushes, deployments, purchases, credentials, global configuration changes or installs. '
              'Do not read parent directories or other projects. Do not commit or reset user work.\n\n')
    prompts = []
    for index, text in enumerate(scenario['prompts'], 1):
        path = folder / f'request-{index}.txt'
        path.write_text(safety + text + '\n', encoding='utf-8')
        prompts.append(file_record(path))
    save(folder / 'run.json', {'schema_version': 1, 'scenario': scenario['id'], 'scenario_digest': canonical(scenario),
                             'seed_digest': canonical(seed), 'skill_commit': commit, 'skill_digest': canonical(skill_hashes),
                             'prompts': prompts, 'initial_files': project_files(project)})
    save(folder / 'assessment-template.json', {'reviewer': '', 'checks': [{'id': c['id'], 'passed': None, 'rationale': '', 'evidence': []} for c in scenario['checks']]})
    print(json.dumps({'project': str(project), 'requests': [str(folder / f'request-{i}.txt') for i in range(1, len(prompts)+1)], 'assessment_template': str(folder / 'assessment-template.json')}, indent=2))


def capture(args):
    folder = run_dir(args.id)
    meta = load(folder / 'run.json')
    scenario = scenarios()[meta['scenario']]
    if canonical(scenario) != meta['scenario_digest']:
        raise ValueError('scenario changed since prepare; create a fresh run')
    skill_root = folder / 'project' / '.omp' / 'skills'
    if canonical(project_files(skill_root)) != meta['skill_digest']:
        raise ValueError('installed skills changed since prepare')
    if args.phase == 1 and project_files(folder / 'project') != meta['initial_files']:
        raise ValueError('candidate input changed since prepare')
    if not 1 <= args.phase <= len(scenario['prompts']):
        raise ValueError('invalid phase')
    phase = folder / f'phase-{args.phase}'
    if phase.exists() or (args.phase > 1 and not (folder / f'phase-{args.phase-1}' / 'capture.json').is_file()):
        raise ValueError('phase already attempted or prior phase missing; never overwrite failed attempts')
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or args.model not in command:
        raise ValueError('supply an explicit approved model as a command argument and matching --model label')
    request = evidence_file(meta['prompts'][args.phase - 1]).read_bytes()
    phase.mkdir()
    env = {k: v for k, v in os.environ.items() if k not in API_KEYS}
    temp = folder / 'project' / '.scratch' / 'tmp'
    temp.mkdir(parents=True, exist_ok=True)
    env.update({key: str(temp) for key in ('TEMP', 'TMP', 'TMPDIR')})
    started = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    status, code, error = 'completed', None, None
    with (phase / 'stdout.txt').open('wb') as out, (phase / 'stderr.txt').open('wb') as err:
        try:
            completed = subprocess.run(command, input=request, cwd=folder / 'project', env=env,
                                       stdout=out, stderr=err, timeout=args.timeout, check=False)
            code = completed.returncode
            if code:
                status = 'failed'
        except subprocess.TimeoutExpired:
            status, error = 'timeout', f'process exceeded {args.timeout} seconds; inspect any descendant processes before retrying'
        except OSError as exc:
            status, error = 'launch-error', str(exc)
    snapshot = {}
    try:
        snapshot = project_files(folder / 'project')
        for name in snapshot:
            dest = inside(phase / 'artifacts', name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(inside(folder / 'project', name).read_bytes())
    except (OSError, ValueError) as exc:
        status, error = 'capture-error', str(exc)
    record = {'phase': args.phase, 'scenario': meta['scenario'], 'scenario_digest': meta['scenario_digest'],
              'model': args.model, 'command': command, 'started_at': started,
              'wall_seconds': round(time.monotonic() - start, 3), 'exit_code': code, 'status': status, 'error': error,
              'prompt': meta['prompts'][args.phase - 1], 'stdout': file_record(phase / 'stdout.txt'),
              'stderr': file_record(phase / 'stderr.txt'), 'snapshot': snapshot}
    save(phase / 'capture.json', record)
    print(json.dumps(record, indent=2))
    return 0 if status == 'completed' else 1


def verify_result(result):
    if result['status'] not in ('passed', 'failed', 'blocked') or not result.get('scenario_digest'):
        raise ValueError('invalid collected result')
    if not result.get('evidence'):
        raise ValueError('result has no raw evidence')
    for item in result['evidence']:
        path = inside(ROOT, item['path'])
        if not path.is_file() or digest(path.read_bytes()) != item['sha256']:
            raise ValueError(f'missing or changed result evidence: {path}')
    if result['status'] == 'passed' and (not result.get('checks') or not all(c['passed'] is True for c in result['checks']) or result.get('errors')):
        raise ValueError('passing result has failed/missing checks')
    if result['status'] == 'passed':
        scenario = scenarios()[result['scenario']]
        expected = {c['id'] for c in scenario['checks']}
        ids = [c['id'] for c in result['checks']]
        if canonical(scenario) != result['scenario_digest'] or set(ids) != expected or len(ids) != len(expected):
            raise ValueError('passing result has stale or incomplete scenario checks')
        captures = [load(inside(ROOT, item['path'])) for item in result['evidence']
                    if Path(item['path']).name == 'capture.json']
        if sorted(c['phase'] for c in captures) != list(range(1, len(scenario['prompts']) + 1)):
            raise ValueError('passing result lacks every phase capture')
        for record in captures:
            if record['status'] != 'completed' or record['exit_code'] != 0 or record['scenario_digest'] != result['scenario_digest']:
                raise ValueError('passing result contains failed or mismatched execution')
            evidence_file(record['stdout'])


def collect(args):
    folder = run_dir(args.id)
    meta = load(folder / 'run.json')
    scenario = scenarios()[meta['scenario']]
    errors, evidence, checks = [], [file_record(folder / 'run.json')], []
    if canonical(scenario) != meta['scenario_digest']:
        errors.append('scenario changed since prepare')
    if canonical(load(HERE / 'seeds' / (scenario['seed'] + '.json'))) != meta['seed_digest']:
        errors.append('seed changed since prepare')
    captures = []
    for index in range(1, len(scenario['prompts']) + 1):
        path = folder / f'phase-{index}' / 'capture.json'
        if not path.is_file():
            errors.append(f'missing phase {index}')
            continue
        record = load(path)
        captures.append(record)
        evidence.append(file_record(path))
        if record['scenario_digest'] != meta['scenario_digest'] or record['phase'] != index or record['prompt'] != meta['prompts'][index - 1]:
            errors.append(f'phase {index}: input binding mismatch')
        if not record['model'] or record['model'] not in record['command']:
            errors.append(f'phase {index}: model not explicit in command')
        for key in ('stdout', 'stderr', 'prompt'):
            item = record[key]
            source = inside(ROOT, item['path'])
            if not source.is_file() or digest(source.read_bytes()) != item['sha256']:
                errors.append(f'changed/missing {key} in phase {index}')
            evidence.append(item)
        if record['status'] != 'completed' or record['exit_code'] != 0:
            errors.append(f'phase {index}: {record["status"]}')
        stdout_path = inside(ROOT, record['stdout']['path'])
        if not stdout_path.is_file() or not stdout_path.stat().st_size:
            errors.append(f'phase {index}: empty or missing raw output')
        for name, sha in record['snapshot'].items():
            artifact = inside(path.parent / 'artifacts', name)
            if not artifact.is_file() or digest(artifact.read_bytes()) != sha:
                errors.append(f'missing/changed phase artifact: {name}')
            else:
                evidence.append(file_record(artifact))
    project = folder / 'project'
    current = project_files(project)
    if captures and current != captures[-1]['snapshot']:
        errors.append('project changed after last capture')
    for name in scenario['immutable']:
        if current.get(name) != meta['initial_files'].get(name):
            errors.append(f'protected input changed: {name}')
    for pattern in scenario['artifacts']:
        matches = [p for p in project.glob(pattern) if p.is_file() and p.stat().st_size]
        if not matches:
            errors.append(f'missing artifact: {pattern}')
    probe_path = folder / 'artifact-checks' / 'checks.json'
    if not probe_path.is_file():
        errors.append('independent artifact checks not supplied')
    else:
        probes = load(probe_path)
        evidence.append(file_record(probe_path))
        final_capture = folder / f'phase-{len(scenario["prompts"])}' / 'capture.json'
        if not final_capture.is_file() or probes['capture'] != file_record(final_capture):
            errors.append('artifact checks have wrong capture binding')
        if probes['scenario_digest'] != meta['scenario_digest'] or probes['scenario'] != scenario['id']:
            errors.append('artifact checks have wrong scenario binding')
        if probes['all_artifact_checks_pass'] is not True or not probes['checks'] or not all(value is True for value in probes['checks'].values()):
            errors.append('independent artifact checks failed')
        for item in [probes['capture'], *probes['evidence']]:
            evidence_file(item)
            if item not in evidence:
                evidence.append(item)
    assessment_path = inside(ROOT, args.assessment) if args.assessment else None
    if assessment_path:
        assessment = load(assessment_path)
        evidence.append(file_record(assessment_path))
        checks = assessment['checks']
        ids = [c['id'] for c in checks]
        expected = {c['id'] for c in scenario['checks']}
        if set(ids) != expected or len(ids) != len(set(ids)) or not assessment.get('reviewer', '').strip():
            errors.append('assessment must name reviewer and contain every required check exactly once')
        for check in checks:
            if type(check.get('passed')) is not bool or not check.get('rationale', '').strip() or not check.get('evidence'):
                errors.append(f'incomplete assessment: {check["id"]}')
            for name in check.get('evidence', []):
                path = inside(ROOT, name)
                if not path.is_file() or not path.stat().st_size:
                    errors.append(f'missing assessment evidence: {name}')
                else:
                    evidence.append(file_record(path))
    else:
        errors.append('independent assessment not supplied')
    status = 'passed' if not errors and all(c['passed'] is True for c in checks) else 'failed'
    result = {'schema_version': 1, 'scenario': scenario['id'], 'scenario_digest': meta['scenario_digest'],
              'skill_commit': meta['skill_commit'], 'skill_digest': meta['skill_digest'], 'status': status,
              'checks': checks, 'errors': errors, 'evidence': evidence}
    save(folder / 'result.json', result)
    print(json.dumps(result, indent=2))
    return 0 if status == 'passed' else 1


def report():
    entries = validate()
    local = [s for s in scenarios().values() if s['runner'] == 'local']
    counts = Counter()
    by_scenario = {}
    invalid = []
    for folder in sorted(RUNS.glob('*')) if RUNS.exists() else []:
        if not (folder / 'run.json').is_file():
            continue
        meta = load(folder / 'run.json')
        status = 'pending'
        if (folder / 'result.json').is_file():
            try:
                result = load(folder / 'result.json')
                verify_result(result)
                status = result['status']
            except (ValueError, KeyError, OSError) as exc:
                status = 'invalid'
                invalid.append({'run': folder.name, 'error': str(exc)})
        counts[status] += 1
        by_scenario.setdefault(meta['scenario'], []).append(status)
    attempted = sum(counts.values())
    print(json.dumps({'inventory': {'total': len(entries), 'dispositions': dict(Counter(r['disposition'] for r in entries)),
                                   'states': dict(Counter(r['state'] for r in entries))},
                      'local_journeys': {'defined': len(local), 'attempts_including_pending': attempted, 'outcomes': dict(counts),
                                         'passed_per_attempt': counts['passed'] / attempted if attempted else None,
                                         'by_scenario': by_scenario, 'invalid_evidence': invalid},
                      'linked_outcome_tasks': ['billsplit', 'kitty'],
                      'limits': 'Mapping coverage is not a pass rate. Pending, failed and blocked attempts stay in the denominator. Linked outcome runs are reported by their own collector, not silently pooled here.'}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('validate')
    commands.add_parser('report')
    p = commands.add_parser('prepare')
    p.add_argument('scenario', choices=scenarios())
    p.add_argument('--id', required=True)
    p.add_argument('--ref', required=True)
    p = commands.add_parser('capture')
    p.add_argument('--id', required=True)
    p.add_argument('--phase', type=int, default=1)
    p.add_argument('--model', required=True)
    p.add_argument('--timeout', type=int, default=1200)
    p.add_argument('command', nargs=argparse.REMAINDER)
    p = commands.add_parser('collect')
    p.add_argument('--id', required=True)
    p.add_argument('--assessment')
    args = parser.parse_args()
    try:
        if args.action == 'validate':
            print(f'{len(validate())} upstream items accounted for; evidence references valid')
            return 0
        if args.action == 'report':
            report()
            return 0
        return globals()[args.action](args) or 0
    except (KeyError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
