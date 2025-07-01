# File: git_commit_loader.py
# GitCommitLoader: Load and parse Git commit objects into memory using git cat-file --batch

import subprocess
from collections import namedtuple
import os

Commit = namedtuple('Commit', ['sha', 'tree', 'parents', 'author', 'committer', 'message'])

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

    def load_commits(self):
        """
        Load all commits from the repository into memory.

        :return: List of Commit namedtuples
        """
        shas = self.get_commit_shas()
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

            commits.append(
                Commit(
                    sha=sha,
                    tree=tree,
                    parents=parents,
                    author=author,
                    committer=committer,
                    message=message
                )
            )

        return commits

if __name__ == '__main__':
    # Example usage
    repo = os.getcwd()  # Default to current directory
    loader = GitCommitLoader(repo_path=repo)
    shas = loader.get_commit_shas()
    print(f"Found {len(shas)} commit SHAs in {repo}")
    commits = loader.load_commits()
    print(f"Loaded {len(commits)} commits from {repo}")
    if commits:
        print(commits[0])
        print(commits[-1])
