import subprocess
import os
from typing import Optional

class RepoDir:
    __slots__ = ('absolute_git_dir', 'toplevel_dir')
    """
    A class to represent a Git repository and retrieve its essential paths.
    """
    def __init__(self, repo_path: Optional[str] = None) -> None:
        """
        Initialize the RepoDir with an optional path to the Git repository.
        If a path is provided, the current working directory will be changed to it.

        :param repo_path: Path to the root of a Git repository. If None, uses the current working directory.
        """
        original_cwd = os.getcwd()
        if repo_path:
            try:
                os.chdir(repo_path)
            except FileNotFoundError:
                raise FileNotFoundError(f"Repository path not found: {repo_path}")

        try:
            # Get absolute Git directory (e.g., .git)
            result_git_dir = subprocess.run(
                ['git', 'rev-parse', '--absolute-git-dir'],
                capture_output=True, text=True, check=True
            )
            self.absolute_git_dir: str = result_git_dir.stdout.strip()

            # Get top-level working directory
            result_toplevel = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True, text=True, check=True
            )
            self.toplevel_dir: str = result_toplevel.stdout.strip()

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: {e.stderr}") from e
        except FileNotFoundError:
            raise RuntimeError("Git command not found. Please ensure Git is installed and in your PATH.")
        finally:
            # Always change back to the original working directory
            os.chdir(original_cwd)


def main():
    """Command-line entry point for RepoDir."""
    try:
        loader = RepoDir()
        print(f"Absolute Git Directory: {loader.absolute_git_dir}")
        print(f"Top-level Working Directory: {loader.toplevel_dir}")
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
