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
    parser.add_argument('--init-source', action='store_true')
    args = parser.parse_args()
    if args.init_source:
        if (SRC / 'app.html').exists():
            raise SystemExit('Source already initialized')
        source = (ROOT / 'index.html').read_text()
        start = source.index("$('pngBtn').onclick=")
        end = source.index('/* ============ PERSISTENCE ============ */')
        SRC.mkdir(exist_ok=True)
        (SRC / 'exports.js').write_text(source[start:end])
        source = source[:start] + '/* @include exports.js */\n' + source[end:]
        source = source.replace('</style>', '/* @include workspace.css */\n</style>', 1)
        source = source.replace('(function init(){', '/* @include workspace.js */\n(function init(){', 1)
        (SRC / 'app.html').write_text(source)
        (SRC / 'workspace.js').write_text('')
        (SRC / 'workspace.css').write_text('')
    output = build()
    if args.check:
        if (ROOT / 'index.html').read_text() != output:
            raise SystemExit('index.html is stale; run python3 tasks/build.py')
        print('Generated application is current')
    else:
        (ROOT / 'index.html').write_text(output)
        print('Built index.html from local source')
