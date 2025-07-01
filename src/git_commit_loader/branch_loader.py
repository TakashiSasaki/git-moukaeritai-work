import subprocess

class BranchLoader:
    """
    A loader class to retrieve Git branch information from a repository.
    """
    def __init__(self, repo_path):
        """
        Initialize the loader with the path to the Git repository.

        :param repo_path: Path to the root of a Git repository
        """
        self.repo_path = repo_path
        self.branch_map = None  # maps commit SHA to list of branch names

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
