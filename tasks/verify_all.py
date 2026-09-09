#!/usr/bin/env python3
"""Run every local release gate and retain the actual combined result."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    ('Generated build', ['tasks/build.py', '--check'], {}),
    ('Existing features', ['tasks/roadmap_feature_tests.py'], {}),
    ('Core Chromium', ['tasks/audit_regression_tests.py'], {'ROADMAP_BROWSER': 'chromium'}),
    ('Core WebKit', ['tasks/audit_regression_tests.py'], {'ROADMAP_BROWSER': 'webkit'}),
    ('Core Firefox', ['tasks/audit_regression_tests.py'], {'ROADMAP_BROWSER': 'firefox'}),
    ('Workspace', ['tasks/audit_workspace_tests.py'], {}),
    ('Selection WebKit', ['tasks/audit_workspace_tests.py', 'WorkspaceAuditTests.test_selection_column_tracks_row_center_and_height', 'WorkspaceAuditTests.test_selection_checkbox_keyboard_and_header_state'], {'ROADMAP_BROWSER': 'webkit'}),
    ('Selection Firefox', ['tasks/audit_workspace_tests.py', 'WorkspaceAuditTests.test_selection_column_tracks_row_center_and_height', 'WorkspaceAuditTests.test_selection_checkbox_keyboard_and_header_state'], {'ROADMAP_BROWSER': 'firefox'}),
    ('Accessibility', ['tasks/audit_accessibility_tests.py'], {}),
    ('Exports', ['tasks/audit_export_tests.py'], {}),
    ('Presentation design', ['tasks/audit_presentation_tests.py'], {}),
    ('Initiative register', ['tasks/audit_register_tests.py'], {}),
    ('Release and rollback', ['tasks/release.py', 'build', '--dry-run'], {}),
]

def main():
    started = time.time()
    source_hash = hashlib.sha256((ROOT / 'index.html').read_bytes()).hexdigest()
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
    unchanged = source_hash == hashlib.sha256((ROOT / 'index.html').read_bytes()).hexdigest()
    success = unchanged and len(results) == len(STEPS) and all(r['exitCode'] == 0 for r in results)
    report = {'startedAt': started, 'applicationSHA256': source_hash,
              'applicationUnchangedDuringVerification': unchanged,
              'passed': success, 'gates': results}
    (ROOT / 'tasks' / 'audit-integration-results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'\nFull verification: {"PASSED" if success else "FAILED"}', flush=True)
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
