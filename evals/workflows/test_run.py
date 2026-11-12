"""Synthetic protocol tests, never empirical agent execution evidence."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('workflow_runner', HERE / 'run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
check_spec = importlib.util.spec_from_file_location('workflow_artifact_checks', HERE / 'check_artifacts.py')
artifact_checks = importlib.util.module_from_spec(check_spec)
with patch.dict(sys.modules, {'run': runner}):
    check_spec.loader.exec_module(artifact_checks)


class EvidenceProtocolTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / '.scratch'
        scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='workflow-tests-', dir=scratch)
        self.root = Path(self.temp.name)
        self.home = self.root / 'evals' / 'workflows'
        self.home.mkdir(parents=True)
        for name in ('matrix.json', 'scenarios.json'):
            shutil.copyfile(HERE / name, self.home / name)
        for name in ('sources', 'seeds'):
            shutil.copytree(HERE / name, self.home / name)
        for row in runner.load(HERE / 'matrix.json')['entries']:
            for name in row['routes']:
                path = self.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('Local route fixture\n', encoding='utf-8')
        for scenario in runner.load(HERE / 'scenarios.json')['scenarios']:
            if scenario['runner'] == 'outcome':
                path = self.root / scenario['manifest']
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('Organic request\n', encoding='utf-8')
        self.patch = patch.multiple(runner, ROOT=self.root, HERE=self.home, RUNS=self.root / '.scratch' / 'workflows')
        self.patch.start()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.patch.stop)

    def rewrite(self, path, value):
        path.write_text(json.dumps(value), encoding='utf-8')

    def cli(self, *args):
        with patch.object(sys, 'argv', ['run.py', *args]), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return runner.main()

    def test_all_pinned_named_items_validate(self):
        self.assertEqual(self.cli('validate'), 0)

    def test_missing_mapping_fails(self):
        matrix = runner.load(self.home / 'matrix.json')
        matrix['entries'].pop()
        self.rewrite(self.home / 'matrix.json', matrix)
        self.assertEqual(self.cli('validate'), 2)

    def test_duplicate_mapping_fails(self):
        matrix = runner.load(self.home / 'matrix.json')
        matrix['entries'].append(matrix['entries'][0])
        self.rewrite(self.home / 'matrix.json', matrix)
        self.assertEqual(self.cli('validate'), 2)

    def test_new_upstream_item_requires_mapping(self):
        path = self.home / 'sources' / 'pstack.json'
        source = runner.load(path)
        source['files'].append({'path': 'skills/new-workflow/SKILL.md', 'sha': 'a' * 40, 'size': 1})
        self.rewrite(path, source)
        self.assertEqual(self.cli('validate'), 2)

    def test_asserted_execution_requires_real_evidence_file(self):
        matrix = runner.load(self.home / 'matrix.json')
        row = next(r for r in matrix['entries'] if r['scenarios'])
        row.update(state='executed', evidence=[{'path': 'missing.json', 'sha256': '0' * 64}])
        self.rewrite(self.home / 'matrix.json', matrix)
        self.assertEqual(self.cli('validate'), 2)

    def test_missing_local_route_fails(self):
        matrix = runner.load(self.home / 'matrix.json')
        route = next(r['routes'][0] for r in matrix['entries'] if r['routes'])
        (self.root / route).unlink()
        self.assertEqual(self.cli('validate'), 2)

    def fixture_run(self, scenario_id='review'):
        scenario = runner.scenarios()[scenario_id]
        seed = runner.load(self.home / 'seeds' / (scenario['seed'] + '.json'))
        folder = runner.run_dir('synthetic')
        project = folder / 'project'
        project.mkdir(parents=True)
        for name, text in seed.items():
            path = project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')
        prompt = folder / 'request-1.txt'
        prompt.write_text('Please review this local change.\n', encoding='utf-8')
        runner.save(folder / 'run.json', {'scenario': scenario_id, 'scenario_digest': runner.canonical(scenario),
                    'seed_digest': runner.canonical(seed), 'skill_commit': '1' * 40, 'skill_digest': runner.canonical({}),
                    'prompts': [runner.file_record(prompt)], 'initial_files': runner.project_files(project)})
        return folder

    def capture_fixture(self, code):
        return self.cli('capture', '--id', 'synthetic', '--model', 'synthetic-not-agent', '--',
                        sys.executable, '-c', code, 'synthetic-not-agent')

    def assessment(self, folder, passed=True):
        with patch.object(sys, 'argv', ['check_artifacts.py', '--id', 'synthetic']), contextlib.redirect_stdout(io.StringIO()):
            artifact_checks.main()
        scenario = runner.scenarios()['review']
        raw = (folder / 'phase-1' / 'stdout.txt').relative_to(self.root).as_posix()
        path = folder / 'assessment.json'
        runner.save(path, {'reviewer': 'synthetic protocol fixture, not a workflow evaluation',
                          'checks': [{'id': c['id'], 'passed': passed, 'rationale': 'Synthetic collector test only.', 'evidence': [raw]}
                                     for c in scenario['checks']]})
        return path.relative_to(self.root).as_posix()

    def test_failed_process_cannot_pass_with_positive_assessment(self):
        folder = self.fixture_run()
        self.assertEqual(self.capture_fixture("from pathlib import Path; Path('review.md').write_text('synthetic'); print('synthetic'); raise SystemExit(3)"), 1)
        self.assertEqual(self.cli('collect', '--id', 'synthetic', '--assessment', self.assessment(folder)), 1)
        result = runner.load(folder / 'result.json')
        self.assertEqual(result['status'], 'failed')
        self.assertIn('phase 1: failed', result['errors'])

    def test_missing_artifact_cannot_pass_with_successful_process(self):
        folder = self.fixture_run()
        self.assertEqual(self.capture_fixture("print('synthetic')"), 0)
        self.assertEqual(self.cli('collect', '--id', 'synthetic', '--assessment', self.assessment(folder)), 1)
        self.assertIn('missing artifact: review.md', runner.load(folder / 'result.json')['errors'])

    def test_changed_input_refuses_capture(self):
        folder = self.fixture_run()
        (folder / 'project' / 'ledger.py').write_text('changed before run', encoding='utf-8')
        self.assertEqual(self.capture_fixture("print('synthetic')"), 2)
        self.assertFalse((folder / 'phase-1').exists())

    def test_changed_output_cannot_pass(self):
        folder = self.fixture_run()
        self.assertEqual(self.capture_fixture("from pathlib import Path; Path('review.md').write_text('synthetic'); print('synthetic')"), 0)
        (folder / 'project' / 'review.md').write_text('changed after run', encoding='utf-8')
        self.assertEqual(self.cli('collect', '--id', 'synthetic', '--assessment', self.assessment(folder)), 1)
        self.assertIn('project changed after last capture', runner.load(folder / 'result.json')['errors'])

    def test_missing_assessment_is_failed_not_passed(self):
        folder = self.fixture_run()
        self.capture_fixture("from pathlib import Path; Path('review.md').write_text('synthetic'); print('synthetic')")
        self.assertEqual(self.cli('collect', '--id', 'synthetic'), 1)
        self.assertIn('independent assessment not supplied', runner.load(folder / 'result.json')['errors'])

    def test_missing_raw_evidence_invalidates_asserted_pass(self):
        folder = self.fixture_run()
        self.capture_fixture("from pathlib import Path; Path('review.md').write_text('synthetic'); print('synthetic')")
        self.assertEqual(self.cli('collect', '--id', 'synthetic', '--assessment', self.assessment(folder)), 0)
        result = runner.load(folder / 'result.json')
        runner.verify_result(result)
        (folder / 'phase-1' / 'stdout.txt').unlink()
        with self.assertRaisesRegex(ValueError, 'missing or changed'):
            runner.verify_result(result)

    def test_capture_and_collection_never_overwrite_attempt(self):
        folder = self.fixture_run()
        self.capture_fixture("print('first')")
        before = (folder / 'phase-1' / 'capture.json').read_bytes()
        self.assertEqual(self.capture_fixture("print('second')"), 2)
        self.assertEqual((folder / 'phase-1' / 'capture.json').read_bytes(), before)

    def test_explicit_model_argument_is_required(self):
        self.fixture_run()
        self.assertEqual(self.cli('capture', '--id', 'synthetic', '--model', 'synthetic-not-agent', '--', sys.executable, '-c', "print('synthetic')"), 2)

    def test_pending_and_failed_attempts_remain_in_report(self):
        folder = self.fixture_run()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            runner.report()
        report = json.loads(out.getvalue())
        self.assertEqual(report['local_journeys']['attempts_including_pending'], 1)
        self.assertEqual(report['local_journeys']['outcomes'], {'pending': 1})
        self.assertEqual(report['local_journeys']['passed_per_attempt'], 0)

    def test_changed_scenario_invalidates_old_pass_without_hiding_attempt(self):
        folder = self.fixture_run()
        self.capture_fixture("from pathlib import Path; Path('review.md').write_text('synthetic'); print('synthetic')")
        self.assertEqual(self.cli('collect', '--id', 'synthetic', '--assessment', self.assessment(folder)), 0)
        manifest = runner.load(self.home / 'scenarios.json')
        row = next(s for s in manifest['scenarios'] if s['id'] == 'review')
        row['checks'].append({'id': 'new-obligation', 'requirement': 'A newly required observation'})
        self.rewrite(self.home / 'scenarios.json', manifest)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            runner.report()
        result = json.loads(out.getvalue())['local_journeys']
        self.assertEqual(result['outcomes'], {'invalid': 1})
        self.assertEqual(result['attempts_including_pending'], 1)
        self.assertEqual(result['passed_per_attempt'], 0)
        self.assertIn('stale or incomplete', result['invalid_evidence'][0]['error'])

    def test_escape_path_is_rejected(self):
        with self.assertRaises(ValueError):
            runner.inside(self.root, '../outside.json')

    def planning_fixture(self):
        folder = self.fixture_run('planning') / 'project'
        issues = folder / 'docs' / 'deepmodebot' / 'issues'
        issues.mkdir()
        for identifier, labels, parent, blockers in [('0001', 'spec', 'none', 'none'),
                                                      ('0002', 'ticket', '0001', 'none'),
                                                      ('0003', 'ticket', '0001', '0002')]:
            (issues / (identifier + '-issue.md')).write_text(
                f'# Reservation work\nStatus: open\nLabels: {labels}\nParent: {parent}\nBlocked by: {blockers}\n',
                encoding='utf-8')
        return folder, issues

    def test_local_tracker_graph_resolves(self):
        project, _ = self.planning_fixture()
        self.assertTrue(all(artifact_checks.planning_checks(project).values()))

    def test_local_tracker_cycle_fails(self):
        project, issues = self.planning_fixture()
        (issues / '0002-issue.md').write_text(
            '# Slice\nStatus: open\nLabels: ticket\nParent: 0001\nBlocked by: 0003\n', encoding='utf-8')
        self.assertFalse(artifact_checks.planning_checks(project)['blockers_resolve_without_cycles'])

    def test_local_tracker_missing_parent_fails(self):
        project, issues = self.planning_fixture()
        (issues / '0002-issue.md').write_text(
            '# Slice\nStatus: open\nLabels: ticket\nParent: 0099\nBlocked by: none\n', encoding='utf-8')
        self.assertFalse(artifact_checks.planning_checks(project)['ticket_parents_resolve_to_spec'])


if __name__ == '__main__':
    unittest.main()
