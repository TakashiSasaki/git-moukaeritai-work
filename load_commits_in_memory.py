#!/usr/bin/env python3
"""
File: load_commits_in_memory.py
Load all commit objects into memory, parse fields for in-memory use.
"""

import subprocess
import zlib
from collections import namedtuple

Commit = namedtuple('Commit', ['sha', 'tree', 'parents', 'author', 'committer', 'message'])

def load_commits():
    p_rev = subprocess.Popen(['git', 'rev-list', '--all'], stdout=subprocess.PIPE)
    p_cat = subprocess.Popen(['git', 'cat-file', '--batch'], stdin=p_rev.stdout, stdout=subprocess.PIPE)
    p_rev.stdout.close()
    commits = []

    while True:
        header = p_cat.stdout.readline()
        if not header:
            break
        sha, typ, size = header.decode().split()
        size = int(size)
        raw = p_cat.stdout.read(size + 1)[:-1]  # drop trailing newline
        data = zlib.decompress(raw) if typ != 'tag' else raw
        text = data.decode('utf-8', errors='replace')

        # ヘッダ部とメッセージ部で分割
        hdr, _, msg = text.partition('\n\n')
        fields = {'parents': []}
        for line in hdr.splitlines():
            key, rest = line.split(' ', 1)
            if key == 'tree':
                fields['tree'] = rest
            elif key == 'parent':
                fields['parents'].append(rest)
            elif key == 'author':
                fields['author'] = rest
            elif key == 'committer':
                fields['committer'] = rest
        fields['message'] = msg.strip()
        commits.append(Commit(sha=sha, **fields))
    return commits

if __name__ == '__main__':
    commits = load_commits()
    print(f"Loaded {len(commits)} commits")
    # 例：最初と最後を表示
    print(commits[0])
    print(commits[-1])
