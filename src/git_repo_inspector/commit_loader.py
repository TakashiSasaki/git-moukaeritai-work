# File: commit_loader.py
# CommitLoader: Load and parse Git commit objects into memory using git cat-file --batch

import subprocess

from .env_utils import clean_git_env
import json
import hashlib
from typing import List, Dict, Optional, Tuple, NamedTuple, Any

from .branch_loader import BranchLoader

class Commit(NamedTuple):
    sha: str
    tree: str
    message: str
    raw: str

class CommitLoader:
    """
    A loader class to retrieve Git commit objects from a repository and parse them into Commit tuples.
    """
    def __init__(self, repo_path: str) -> None:
        """
        Initialize the loader with the path to the Git repository.

        :param repo_path: Path to the root of a Git repository
        """
        self.repo_path: str = repo_path
        self.commit_shas: Optional[List[str]] = None
        self.branch_loader: BranchLoader = BranchLoader(repo_path)

    def get_commit_shas(self) -> List[str]:
        """
        Retrieve and cache all commit SHAs in the repository.

        :return: List of commit SHA strings
        """
        if self.commit_shas is None:
            cmd: List[str] = ['git', '-C', self.repo_path, 'rev-list', '--all']
            result: subprocess.CompletedProcess = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                text=True,
                check=True,
                env=clean_git_env(),
            )
            self.commit_shas = result.stdout.splitlines()
        return self.commit_shas

    def get_branches(self) -> Dict[str, List[str]]:
        return self.branch_loader.get_branches()

    def load_commits(self) -> List[Commit]:
        """
        Load all commits from the repository into memory.

        :return: List of Commit namedtuples
        """
        shas: List[str] = self.get_commit_shas()
        cmd_cat: List[str] = ['git', '-C', self.repo_path, 'cat-file', '--batch']

        p_cat: subprocess.Popen = subprocess.Popen(
            cmd_cat,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            env=clean_git_env(),
        )
        for sha in shas:
            p_cat.stdin.write(f"{sha}\n".encode())
        p_cat.stdin.close()

        commits: List[Commit] = []
        while True:
            header_line: bytes = p_cat.stdout.readline()
            if not header_line:
                break
            sha, obj_type, size_str = header_line.decode().split()
            size: int = int(size_str)

            # Read raw object data (already uncompressed)
            raw_data: bytes = p_cat.stdout.read(size + 1)[:-1]  # drop trailing newline
            text: str = raw_data.decode('utf-8', errors='replace')

            # Store raw content before parsing
            raw_content: str = text

            # Split header lines and commit message
            lines: List[str] = text.split('\n')
            tree: str = ''
            idx: int = 0

            # Parse header fields
            while idx < len(lines) and lines[idx]:
                key, value = lines[idx].split(' ', 1)
                if key == 'tree':
                    tree = value
                idx += 1

            # The rest is the commit message
            message: str = '\n'.join(lines[idx+1:]).strip()

            commits.append(
                Commit(
                    sha=sha,
                    tree=tree,
                    message=message,
                    raw=raw_content
                )
            )

        return commits

    def verify_commit(self, commit: Commit) -> bool:
        """
        Recompute the SHA-1 of a commit from its raw content and verify against the stored SHA.

        :param commit: Commit namedtuple
        :return: True if recomputed SHA matches, False otherwise
        """
        body_bytes: bytes = commit.raw.encode('utf-8')
        header: bytes = f"commit {len(body_bytes)}\0".encode('utf-8')
        computed: str = hashlib.sha1(header + body_bytes).hexdigest()
        return computed == commit.sha

    def verify_all_commits(self) -> List[Tuple[str, str]]:
        """
        Verify all loaded commits, returning a list of mismatched SHAs.

        :return: List of tuples (commit_sha, recomputed_sha) for mismatches
        """
        mismatches: List[Tuple[str, str]] = []
        for commit in self.load_commits():
            if not self.verify_commit(commit):
                # Recompute for reporting
                body_bytes: bytes = commit.raw.encode('utf-8')
                header: bytes = f"commit {len(body_bytes)}\0".encode('utf-8')
                recomputed: str = hashlib.sha1(header + body_bytes).hexdigest()
                mismatches.append((commit.sha, recomputed))
        return mismatches

    def list_branches_json(self) -> str:
        """
        List branch names with their corresponding commit SHAs as JSON.

        :return: JSON string of branch-to-SHA mappings
        """
        branches: Dict[str, List[str]] = self.get_branches()
        output: List[Dict[str, str]] = []
        for sha, names in branches.items():
            for name in names:
                output.append({'branch': name, 'sha': sha})
        return json.dumps(output, indent=2)

    def list_commits_json(self) -> str:
        """
        List all commits as JSON, including raw content.

        :return: JSON string of commits
        """
        commits: List[Commit] = self.load_commits()
        output: List[Dict[str, Any]] = []
        for c in commits:
            d: Dict[str, Any] = c._asdict()
            output.append(d)
        return json.dumps(output, indent=2)


