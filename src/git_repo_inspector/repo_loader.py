import subprocess
import os
from typing import Optional

class RepoDir:
    __slots__ = ('absolute_git_dir', 'toplevel_dir', '_is_bare')

    def __init__(self, repo_path: Optional[str] = None) -> None:
        """
        Initialize the RepoDir with an optional path to the Git repository.
        If a path is provided, the current working directory will be changed to it.

        :param repo_path: Path to the root of a Git repository. If None, uses the current working directory.
        """
        original_cwd = os.getcwd()
        target_path = repo_path if repo_path else original_cwd

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

            # Check if it's a bare repository
            result_is_bare = subprocess.run(
                ['git', 'rev-parse', '--is-bare-repository'],
                capture_output=True, text=True, check=True,
                cwd=target_path # Run this command in the context of the target path
            )
            self._is_bare: bool = result_is_bare.stdout.strip() == 'true'

            self.toplevel_dir: Optional[str] = None
            if not self._is_bare:
                # Get top-level working directory only for non-bare repositories
                result_toplevel = subprocess.run(
                    ['git', 'rev-parse', '--show-toplevel'],
                    capture_output=True, text=True, check=True
                )
                self.toplevel_dir = result_toplevel.stdout.strip()

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: {e.stderr}") from e
        except FileNotFoundError:
            raise RuntimeError("Git command not found. Please ensure Git is installed and in your PATH.")
        finally:
            # Always change back to the original working directory
            os.chdir(original_cwd)

    def is_inside_working_tree(self) -> bool:
        """
        Checks if the .git directory is inside a working tree (i.e., not a bare repository).

        :return: True if it's a non-bare repository with a working tree, False otherwise.
        """
        return not self._is_bare


    def get_toplevel_dir(self) -> str:
        """
        Returns the path to the top-level working directory of the Git repository.

        :return: The absolute path to the top-level working directory.
        :raises RuntimeError: If the repository is bare (no working tree).
        """
        if self._is_bare or self.toplevel_dir is None:
            raise RuntimeError("Cannot get top-level directory for a bare repository.")
        return self.toplevel_dir


def main():
    """Command-line entry point for RepoDir."""
    try:
        loader = RepoDir()
        print(f"Absolute Git Directory: {loader.absolute_git_dir}")
        print(f"Is inside working tree: {loader.is_inside_working_tree()}")
        if loader.is_inside_working_tree():
            print(f"Top-level Working Directory: {loader.get_toplevel_dir()}")
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
