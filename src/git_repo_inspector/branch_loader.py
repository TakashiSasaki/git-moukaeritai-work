import subprocess
import argparse
import os
import json

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

    def to_json(self):
        """
        Return the branch-to-SHA mappings as a JSON string.
        """
        branches = self.get_branches()
        output = []
        for sha, names in branches.items():
            for name in names:
                output.append({'branch': name, 'sha': sha})
        return json.dumps(output, indent=2)

def main():
    """Command-line entry point for listing branches."""
    parser = argparse.ArgumentParser(description='List Git branches and their commit SHAs.')
    parser.add_argument('repo_path', nargs='?', default=os.getcwd(),
                        help='Path to the Git repository (default: current directory)')
    parser.add_argument('--json', action='store_true',
                        help='Output in JSON format')
    args = parser.parse_args()

    try:
        loader = BranchLoader(repo_path=args.repo_path)
        if args.json:
            print(loader.to_json())
        else:
            branches = loader.get_branches()
            if not branches:
                print(f"No branches found in {args.repo_path}")
                return
            # Sort for consistent output
            sorted_branches = sorted(branches.items(), key=lambda item: item[1][0])
            for sha, names in sorted_branches:
                # Primary branch name first, then others
                print(f"{sha} {' '.join(sorted(names))}")

    except FileNotFoundError:
        print(f"Error: Repository not found at {args.repo_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing Git command: {e}")

if __name__ == '__main__':
    main()
