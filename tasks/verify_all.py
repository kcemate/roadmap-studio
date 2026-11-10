#!/usr/bin/env python3
"""Run every local release gate and record the combined result under tasks/test-artifacts/results/.

The gate fails if any suite fails or if running the suites changed any tracked file (the application, its source,
the tests, the tracker, or the docs). Suites read the committed build; they never rebuild it."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'tasks' / 'test-artifacts' / 'results'
STEPS = [
    ('Generated build', ['tasks/build.py', '--check'], {}),
    ('Existing features', ['tasks/roadmap_feature_tests.py'], {}),
    ('Core Chromium', ['tasks/audit_regression_tests.py'], {'ROADMAP_BROWSER': 'chromium'}),
    ('Core WebKit', ['tasks/audit_regression_tests.py'], {'ROADMAP_BROWSER': 'webkit'}),
    ('Core Firefox', ['tasks/audit_regression_tests.py'], {'ROADMAP_BROWSER': 'firefox'}),
    ('Audit fixes Chromium', ['tasks/audit_fixes_tests.py'], {'ROADMAP_BROWSER': 'chromium'}),
    ('Audit fixes WebKit', ['tasks/audit_fixes_tests.py'], {'ROADMAP_BROWSER': 'webkit'}),
    ('Audit fixes Firefox', ['tasks/audit_fixes_tests.py'], {'ROADMAP_BROWSER': 'firefox'}),
    ('Consistency and features', ['tasks/audit_consistency_tests.py'], {}),
    ('Workspace', ['tasks/audit_workspace_tests.py'], {}),
    ('Selection WebKit', ['tasks/audit_workspace_tests.py', 'WorkspaceAuditTests.test_selection_column_tracks_row_center_and_height', 'WorkspaceAuditTests.test_selection_checkbox_keyboard_and_header_state'], {'ROADMAP_BROWSER': 'webkit'}),
    ('Selection Firefox', ['tasks/audit_workspace_tests.py', 'WorkspaceAuditTests.test_selection_column_tracks_row_center_and_height', 'WorkspaceAuditTests.test_selection_checkbox_keyboard_and_header_state'], {'ROADMAP_BROWSER': 'firefox'}),
    ('Accessibility', ['tasks/audit_accessibility_tests.py'], {}),
    ('Exports', ['tasks/audit_export_tests.py'], {}),
    ('Presentation design', ['tasks/audit_presentation_tests.py'], {}),
    ('Initiative register', ['tasks/audit_register_tests.py'], {}),
    ('Release and rollback', ['tasks/release.py', 'build', '--dry-run'], {}),
]


def tracked_files():
    try:
        listed = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, check=True, capture_output=True).stdout
        return sorted(name for name in listed.decode().split('\0') if name)
    except (OSError, subprocess.CalledProcessError):
        skip = {'.git', 'release'}
        return sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob('*')
                      if p.is_file() and not set(p.relative_to(ROOT).parts) & skip and 'test-artifacts' not in p.parts)


def fingerprint():
    out = {}
    for name in tracked_files():
        path = ROOT / name
        out[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return out


def main():
    started = time.time()
    before = fingerprint()
    results = []
    for label, args, env in STEPS:
        print(f'\n{label}', flush=True)
        tick = time.monotonic()
        result = subprocess.run([sys.executable, *args], cwd=ROOT,
                                env={**os.environ, **env}, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout, end='', flush=True)
        results.append({'gate': label, 'exitCode': result.returncode,
                        'seconds': round(time.monotonic() - tick, 2), 'output': result.stdout})
        if result.returncode:
            break
    after = fingerprint()
    changed = sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))
    success = not changed and len(results) == len(STEPS) and all(r['exitCode'] == 0 for r in results)
    report = {'startedAt': started, 'applicationSHA256': before.get('index.html'),
              'trackedFilesUnchanged': not changed, 'changedTrackedFiles': changed,
              'passed': success, 'gates': results}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / 'audit-integration-results.json').write_text(json.dumps(report, indent=2) + '\n')
    if changed:
        print('\nTracked files changed during verification: ' + ', '.join(changed), flush=True)
    print(f'\nFull verification: {"PASSED" if success else "FAILED"}', flush=True)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
