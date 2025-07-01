# File: load_commits_in_memory.py
# Load all commit objects into memory, parse fields for in-memory use using git cat-file --batch

import subprocess
from collections import namedtuple

Commit = namedtuple('Commit', ['sha', 'tree', 'parents', 'author', 'committer', 'message'])

def load_commits():
    # Start git processes
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

        text = raw.decode('utf-8', errors='replace')

        lines = text.split('\n')
        tree = ''
        parents = []
        author = committer = msg = ''
        idx = 0

        while idx < len(lines) and lines[idx]:
            parts = lines[idx].split(' ', 1)
            if parts[0] == 'tree':
                tree = parts[1]
            elif parts[0] == 'parent':
                parents.append(parts[1])
            elif parts[0] == 'author':
                author = parts[1]
            elif parts[0] == 'committer':
                committer = parts[1]
            idx += 1

        msg = '\n'.join(lines[idx+1:]).strip()

        commits.append(Commit(sha=sha, tree=tree, parents=parents,
                              author=author, committer=committer, message=msg))
    return commits

if __name__ == '__main__':
    commits = load_commits()
    print(f"Loaded {len(commits)} commits")
    if commits:
        print(commits[0])
        print(commits[-1])
