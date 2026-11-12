#!/usr/bin/env python3
"""Check captured journey artifacts on a disposable copy; never score skill adherence."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import run as workflow

HANDOFF_PROBE = '''
import copy, json
from reservations import cancel, display_title
rows = {"a": {"owner": "sam", "active": True}}
before = copy.deepcopy(rows)
checks = {}
checks["other_owner_unchanged"] = cancel(rows, "a", "lee") is False and rows == before
checks["absent_id_unchanged"] = cancel(rows, "absent", "sam") is False and rows == before
checks["owner_cancels"] = cancel(rows, "a", "sam") is True and rows["a"]["active"] is False
inactive = copy.deepcopy(rows)
checks["repeat_is_false_unchanged"] = cancel(rows, "a", "sam") is False and rows == inactive
checks["user_title_preserved"] = display_title("drill") == "Tool library: drill"
print(json.dumps(checks))
'''


def planning_checks(project):
    issues = sorted((project / 'docs' / 'deepmodebot' / 'issues').glob('*.md'))
    records, valid_ids = {}, True
    for path in issues:
        match = re.match(r'^(\d{4})-', path.name)
        if not match or match[1] in records:
            valid_ids = False
            continue
        text = path.read_text(encoding='utf-8')
        fields = dict(re.findall(r'^(Status|Labels|Parent|Blocked by):\s*(.+)$', text, re.M))
        records[match[1]] = fields
    specs = {key for key, row in records.items() if 'spec' in [s.strip() for s in row.get('Labels', '').split(',')]}
    tickets = {key for key, row in records.items() if 'ticket' in [s.strip() for s in row.get('Labels', '').split(',')]}
    graph = {key: re.findall(r'\b\d{4}\b', row.get('Blocked by', '')) for key, row in records.items()}
    visited, visiting = set(), set()

    def acyclic(key):
        if key in visiting:
            return False
        if key in visited:
            return True
        visiting.add(key)
        if any(dep not in graph or not acyclic(dep) for dep in graph[key]):
            return False
        visiting.remove(key)
        visited.add(key)
        return True

    return {'unique_four_digit_issue_ids': valid_ids and bool(records),
            'spec_and_vertical_ticket_count': bool(specs) and len(tickets) >= 2,
            'required_tracker_headers': bool(records) and all(set(row) == {'Status', 'Labels', 'Parent', 'Blocked by'} for row in records.values()),
            'ticket_parents_resolve_to_spec': bool(tickets) and all(records[key].get('Parent') in specs for key in tickets),
            'blockers_resolve_without_cycles': bool(records) and all(acyclic(key) for key in graph)}


def main(argv=None, runtime=None):
    workflow = runtime or globals()["workflow"]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--output-name', default='artifact-checks')
    args = parser.parse_args(argv)
    if not re.fullmatch('[a-z0-9-]+', args.output_name):
        parser.error('output-name must be a lowercase slug')
    try:
        folder = workflow.run_dir(args.id)
        meta = workflow.load(folder / 'run.json')
        scenario = workflow.scenarios()[meta['scenario']]
        phase = folder / f'phase-{len(scenario["prompts"])}'
        record = workflow.load(phase / 'capture.json')
        source = phase / 'artifacts'
        if workflow.project_files(source) != record['snapshot']:
            raise ValueError('captured artifacts missing or changed')
        output = folder / args.output_name
        if output.exists():
            raise ValueError('artifact checks already exist; preserve the original evidence')
        output.mkdir()
        project = output / 'project'
        shutil.copytree(source, project)
        checks = {f'artifact:{pattern}': any(p.is_file() and p.stat().st_size for p in project.glob(pattern)) for pattern in scenario['artifacts']}
        checks.update({f'protected:{name}': workflow.project_files(project).get(name) == meta['initial_files'][name] for name in scenario['immutable']})
        evidence = []
        if scenario['id'] == 'planning':
            checks.update(planning_checks(project))
        if scenario['id'] == 'handoff':
            tests = sorted(project.glob("**/test_reservations.py"))
            checks["regression:one_test_file"] = len(tests) == 1
            test_directory = tests[0].parent if len(tests) == 1 else project
            for name, command in [('behavior', [sys.executable, '-c', HANDOFF_PROBE]),
                                  ('regression', [sys.executable, '-B', '-m', 'unittest', 'discover',
                                                  '-s', str(test_directory), '-p', 'test_reservations.py'])]:
                try:
                    result = subprocess.run(command, cwd=project, capture_output=True, text=True, encoding='utf-8', timeout=60)
                    code, stdout, stderr = result.returncode, result.stdout, result.stderr
                except (OSError, subprocess.TimeoutExpired) as exc:
                    code, stdout, stderr = None, '', str(exc)
                path = output / (name + '.json')
                workflow.save(path, {'command': command, 'exit_code': code, 'stdout': stdout, 'stderr': stderr})
                evidence.append(workflow.file_record(path))
                checks[name + ':exit'] = code == 0
                if name == 'behavior':
                    try:
                        observed = json.loads(stdout)
                        expected = {'other_owner_unchanged', 'absent_id_unchanged', 'owner_cancels', 'repeat_is_false_unchanged', 'user_title_preserved'}
                        checks['behavior:observations'] = set(observed) == expected and all(value is True for value in observed.values())
                    except (ValueError, TypeError):
                        checks['behavior:observations'] = False
        result = {'scenario': scenario['id'], 'scenario_digest': meta['scenario_digest'], 'capture': workflow.file_record(phase / 'capture.json'),
                  'checks': checks, 'evidence': evidence, 'all_artifact_checks_pass': all(checks.values()),
                  'limits': 'Artifact checks only. Semantic review and transcript safety/adherence assessment are still required.'}
        workflow.save(output / 'checks.json', result)
        print(json.dumps(result, indent=2))
        return 0 if all(checks.values()) else 1
    except (OSError, KeyError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
