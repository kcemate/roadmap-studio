#!/usr/bin/env python3
"""Build the offline application from local source fragments."""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'

def build():
    template = (SRC / 'app.html').read_text()
    def include(match):
        name = match.group(1)
        path = SRC / name
        if path.parent != SRC or not path.is_file():
            raise ValueError(f'Invalid local include: {name}')
        return path.read_text()
    return re.sub(r'/\* @include ([\w.-]+) \*/', include, template)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = build()
    if args.check:
        if (ROOT / 'index.html').read_text() != output:
            raise SystemExit('index.html is stale; run python3 tasks/build.py')
        print('Generated application is current')
    else:
        (ROOT / 'index.html').write_text(output)
        print('Built index.html from local source')
