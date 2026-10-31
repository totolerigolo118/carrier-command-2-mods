#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Refresh the MAC-ONLY comment blocks of src/cp_groups.c from part 10 of partage/cc2_reference.txt.

The blocks sit between the markers
    /* BEGIN MAC-ONLY <module> */ ... /* END MAC-ONLY <module> */
and only ever contain comments: the Mac bytes are documentation of what the Mac build looked like,
never data for the Windows build (32-bit code has other encodings and addresses).

    python3 tools/mac_table_to_comments.py            rewrite src/cp_groups.c in place
    python3 tools/mac_table_to_comments.py --check    exit 1 if the file is out of date
"""
import re
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
REFERENCE = REPO / 'partage' / 'cc2_reference.txt'
TARGET = HERE.parent / 'src' / 'cp_groups.c'

SITE_RE = re.compile(r'^  (0x[0-9a-f]+)\s+(.*)$')


def parse_modules(text):
    """module name -> list of site dicts (addr, where, kind, insn, before)"""
    modules = {}
    current = None
    site = None
    in_original = False
    for line in text.splitlines():
        m = re.match(r'^MODULE (\w+) - ', line)
        if m:
            current = m.group(1)
            modules[current] = []
            site = None
            continue
        if current is None:
            continue
        if line.startswith('###'):
            break
        m = SITE_RE.match(line)
        if m and not line.startswith('   '):
            where = m.group(2)
            kind = 'RIP'
            if 'CODE CAVE' in where:
                kind = 'CAVE'
            elif where.startswith('DATA') or ' DATA ' in where:
                kind = 'DATA'
            site = {'addr': m.group(1), 'where': where, 'kind': kind, 'insn': '', 'before': ''}
            modules[current].append(site)
            in_original = False
            continue
        if site is None:
            continue
        s = line.strip()
        if s.startswith('insn   :'):
            site['insn'] = s.split(':', 1)[1].strip()
        elif s.startswith('original code'):
            site['kind'] = 'IMM'
            in_original = True
        elif in_original and re.match(r'^[0-9a-f]+: ', s):
            if not site['insn']:
                site['insn'] = s.split(': ', 1)[1].strip()
        elif s.startswith('before :'):
            site['before'] = s.split(':', 1)[1].strip()
            in_original = False
    return modules


def block(module, sites):
    kinds = {}
    for s in sites:
        kinds[s['kind']] = kinds.get(s['kind'], 0) + 1
    summary = ', '.join('%d %s' % (n, k) for k, n in sorted(kinds.items()))
    out = ['MAC-ONLY (module %s, build_mac, x86-64): %d sites in part 10 (%s).' % (module, len(sites), summary),
           'These bytes are documentation of the Mac encoding. They are NOT data for Windows: a 32-bit',
           'build has other addresses and other encodings. RIP = SSE read of a float constant, IMM = raw',
           'bytes / branch, CAVE = code added to the Mac build (no original bytes), DATA = table entry.',
           '']
    for s in sites:
        before = s['before'] if s['before'] and not s['before'].startswith('not listed') else '(none: added code)'
        what = s['insn'] or s['where']
        what = what.replace('CODE CAVE inside dead code of ImGui::ShowDemoWindow, ', 'added code, ')
        head = '%s %-4s %s' % (s['addr'], s['kind'], what)
        assert '*/' not in head and '/*' not in head
        out.append(head)
        for chunk in textwrap.wrap('before: ' + before, 84):
            out.append('    ' + chunk)
    return out


def render(module, sites):
    lines = ['/* BEGIN MAC-ONLY %s' % module]
    lines += [' * ' + l if l else ' *' for l in block(module, sites)]
    lines.append(' */ /* END MAC-ONLY %s */' % module)
    return '\n'.join(lines)


def main():
    check = '--check' in sys.argv
    modules = parse_modules(REFERENCE.read_text(encoding='utf-8'))
    src = TARGET.read_text(encoding='utf-8')
    new = src
    for module in re.findall(r'/\* BEGIN MAC-ONLY (\w+)', src):
        if module not in modules:
            sys.exit('module %s not found in %s' % (module, REFERENCE))
        pat = re.compile(r'/\* BEGIN MAC-ONLY %s\b.*?/\* END MAC-ONLY %s \*/' % (module, module), re.S)
        new = pat.sub(lambda _m, mod=module: render(mod, modules[mod]), new)
    if check:
        sys.exit(0 if new == src else 1)
    if new != src:
        TARGET.write_text(new, encoding='utf-8')
        print('updated', TARGET)
    else:
        print('already up to date')


if __name__ == '__main__':
    main()
