# File: git_commit_loader.py
# GitCommitLoader: Load and parse Git commit objects into memory using git cat-file --batch

import subprocess
from collections import namedtuple
import os
import argparse

# Extend Commit to include branch names
Commit = namedtuple('Commit', ['sha', 'tree', 'parents', 'author', 'committer', 'message', 'branches'])

class GitCommitLoader:
    """
    A loader class to retrieve Git commit objects from a repository and parse them into Commit tuples.
    """
    def __init__(self, repo_path):
        """
        Initialize the loader with the path to the Git repository.

        :param repo_path: Path to the root of a Git repository
        """
        self.repo_path = repo_path
        self.commit_shas = None
        self.branch_map = None  # maps commit SHA to list of branch names

    def get_commit_shas(self):
        """
        Retrieve and cache all commit SHAs in the repository.

        :return: List of commit SHA strings
        """
        if self.commit_shas is None:
            cmd = ['git', '-C', self.repo_path, 'rev-list', '--all']
            result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
            self.commit_shas = result.stdout.splitlines()
        return self.commit_shas

    def get_branches(self):
        """
        Retrieve and cache a mapping from commit SHA to branch names.

        :return: Dict mapping SHA -> list of branch names
        """
        if self.branch_map is None:
            cmd = [
                'git', '-C', self.repo_path,
                'for-each-ref',
                '--format=%(refname:short) %(objectname)',
                'refs/heads/'
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
            self.branch_map = {}
            for line in result.stdout.splitlines():
                name, sha = line.split(None, 1)
                self.branch_map.setdefault(sha, []).append(name)
        return self.branch_map

    def load_commits(self):
        """
        Load all commits from the repository into memory, including branch annotations.

        :return: List of Commit namedtuples
        """
        shas = self.get_commit_shas()
        branch_map = self.get_branches()
        cmd_cat = ['git', '-C', self.repo_path, 'cat-file', '--batch']

        p_cat = subprocess.Popen(cmd_cat, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        for sha in shas:
            p_cat.stdin.write(f"{sha}\n".encode())
        p_cat.stdin.close()

        commits = []
        while True:
            header = p_cat.stdout.readline()
            if not header:
                break
            sha, obj_type, size_str = header.decode().split()
            size = int(size_str)

            # Read raw object data (already uncompressed)
            raw_data = p_cat.stdout.read(size + 1)[:-1]  # drop trailing newline
            text = raw_data.decode('utf-8', errors='replace')

            # Split header lines and commit message
            lines = text.split('\n')
            tree = ''
            parents = []
            author = ''
            committer = ''
            idx = 0

            # Parse header fields
            while idx < len(lines) and lines[idx]:
                key, value = lines[idx].split(' ', 1)
                if key == 'tree':
                    tree = value
                elif key == 'parent':
                    parents.append(value)
                elif key == 'author':
                    author = value
                elif key == 'committer':
                    committer = value
                idx += 1

            # The rest is the commit message
            message = '\n'.join(lines[idx+1:]).strip()
            # Assign branches for this commit
            branches = branch_map.get(sha, [])

            commits.append(
                Commit(
                    sha=sha,
                    tree=tree,
                    parents=parents,
                    author=author,
                    committer=committer,
                    message=message,
                    branches=branches
                )
            )

        return commits

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Git commit loader utility')
    parser.add_argument('repo_path', nargs='?', default=os.getcwd(),
                        help='Path to the Git repository (default: current directory)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--list-branches', action='store_true',
                       help='List branch names with their corresponding commit SHAs')
    group.add_argument('--list-commits', action='store_true',
                       help='Load and list commit objects')
    args = parser.parse_args()

    loader = GitCommitLoader(repo_path=args.repo_path)

    if args.list_branches:
        branches = loader.get_branches()
        for sha, names in branches.items():
            for name in names:
                print(f"{name}: {sha}")
    else:
        # Default or --list-commits
        commits = loader.load_commits()
        print(f"Loaded {len(commits)} commits from {args.repo_path}")
        for c in commits:
            print(c)
