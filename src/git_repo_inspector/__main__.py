import os
import argparse
import sys
from .commit_loader import CommitLoader # Corrected import
from .tui import GitRepoInspectorTUI # Import the TUI application


def main():
    parser = argparse.ArgumentParser(description='Git Repository Inspector Utility. Can show data in CLI or TUI.')
    parser.add_argument('repo_path', nargs='?', default=os.getcwd(),
                        help='Path to the Git repository (default: current directory)')

    # Group for existing CLI output actions
    cli_action_group = parser.add_argument_group(title='CLI Output Options')
    group = cli_action_group.add_mutually_exclusive_group()
    group.add_argument('--list-branches', action='store_true',
                       help='List branch names with their corresponding commit SHAs (CLI output)')
    group.add_argument('--list-commits', action='store_true',
                       help='Load and list commit objects (CLI output)')
    cli_action_group.add_argument('--json', action='store_true',
                                  help='Output in JSON format (for --list-branches or --list-commits)')
    cli_action_group.add_argument('--verify', action='store_true',
                                  help='Verify commit SHAs against raw content (CLI output)')

    # Argument for launching TUI
    parser.add_argument('--tui', action='store_true',
                        help='Launch the Textual TUI for repository inspection. If no other CLI action is specified, this is the default.')

    args = parser.parse_args()

    # Determine if any specific CLI action was requested
    is_cli_action_requested = args.list_branches or args.list_commits or args.verify

    if is_cli_action_requested:
        # Handle existing CLI functionalities
        try:
            loader = CommitLoader(repo_path=args.repo_path) # Use corrected CommitLoader

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
                    # Sort for consistent output, primary branch name first
                    output_lines = []
                    for sha, names in branches.items():
                        for name in sorted(names): # Sort names for consistency
                             output_lines.append(f"{name}: {sha}")
                    output_lines.sort() # Sort lines by branch name
                    for line in output_lines:
                        print(line)

            elif args.list_commits: # This is also the default if no exclusive group member is chosen
                if args.json:
                    print(loader.list_commits_json())
                else:
                    commits = loader.load_commits()
                    print(f"Loaded {len(commits)} commits from {args.repo_path}")
                    for c in commits: # Consider a more summarized output or limit
                        print(f"SHA: {c.sha}, Author: {c.author}, Message: {c.message.splitlines()[0] if c.message else ''}")
            else:
                # This part of the 'else' might be unreachable if --list-commits is the default
                # for the mutually exclusive group.
                # However, if no action from the group is specified, and --verify isn't either,
                # it implies we might want to default to TUI or print help.
                # Given the new --tui flag, if no CLI action is specified, we'll default to TUI later.
                pass # Let TUI logic handle it

        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except RuntimeError as e: # Catching broader Git execution errors
            print(f"Runtime Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected CLI error occurred: {e}", file=sys.stderr)
            sys.exit(1)

    else: # No specific CLI action requested, or --tui was explicitly passed
        # Launch the TUI application
        try:
            app = GitRepoInspectorTUI(repo_path=args.repo_path)
            app.run()
        except Exception as e:
            print(f"Failed to run GitRepoInspectorTUI: {e}", file=sys.stderr)
            print("Ensure the repository path is valid, Git is installed, and all dependencies (like textual) are installed.", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()
