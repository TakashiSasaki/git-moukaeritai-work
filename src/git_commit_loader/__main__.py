import os
import argparse
from . import GitCommitLoader


def main():
    parser = argparse.ArgumentParser(description='Git commit loader utility')
    parser.add_argument('repo_path', nargs='?', default=os.getcwd(),
                        help='Path to the Git repository (default: current directory)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--list-branches', action='store_true',
                       help='List branch names with their corresponding commit SHAs')
    group.add_argument('--list-commits', action='store_true',
                       help='Load and list commit objects')
    parser.add_argument('--json', action='store_true',
                        help='Output in JSON format')
    parser.add_argument('--verify', action='store_true',
                        help='Verify commit SHAs against raw content')
    args = parser.parse_args()

    loader = GitCommitLoader(repo_path=args.repo_path)

    if args.verify:
        mismatches = loader.verify_all_commits()
        if mismatches:
            print("Mismatched commits:")
            for sha, rec in mismatches:
                print(f"{sha} != {rec}")
        else:
            print("All commits verified successfully.")
    elif args.list_branches:
        if args.json:
            print(loader.list_branches_json())
        else:
            branches = loader.get_branches()
            for sha, names in branches.items():
                for name in names:
                    print(f"{name}: {sha}")
    else:
        # Default or --list-commits
        if args.json:
            print(loader.list_commits_json())
        else:
            commits = loader.load_commits()
            print(f"Loaded {len(commits)} commits from {args.repo_path}")
            for c in commits:
                print(c)


if __name__ == '__main__':
    main()
