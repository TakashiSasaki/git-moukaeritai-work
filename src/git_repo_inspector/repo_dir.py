import subprocess
import os
from typing import Optional

class RepoDir:
    __slots__ = (
        'absolute_git_dir',
        'toplevel_dir',
        '_is_bare',
        'absolute_git_dir_error',
        'is_bare_error',
        'toplevel_dir_error',
    )

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

        # Initialize members
        self.absolute_git_dir: Optional[str] = None
        self.toplevel_dir: Optional[str] = None
        self._is_bare: Optional[bool] = None
        self.absolute_git_dir_error: Optional[Exception] = None
        self.is_bare_error: Optional[Exception] = None
        self.toplevel_dir_error: Optional[Exception] = None

        try:
            result_git_dir = subprocess.run(
                ['git', 'rev-parse', '--absolute-git-dir'],
                capture_output=True, text=True, check=True
            )
            self.absolute_git_dir = result_git_dir.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.absolute_git_dir_error = e

        try:
            result_is_bare = subprocess.run(
                ['git', 'rev-parse', '--is-bare-repository'],
                capture_output=True, text=True, check=True,
                cwd=target_path
            )
            self._is_bare = result_is_bare.stdout.strip() == 'true'
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.is_bare_error = e

        if self._is_bare is False or self._is_bare is None:
            try:
                result_toplevel = subprocess.run(
                    ['git', 'rev-parse', '--show-toplevel'],
                    capture_output=True, text=True, check=True
                )
                self.toplevel_dir = result_toplevel.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                self.toplevel_dir_error = e

        os.chdir(original_cwd)

    def is_inside_working_tree(self) -> bool:
        """
        Checks if the .git directory is inside a working tree (i.e., not a bare repository).

        :return: True if it's a non-bare repository with a working tree, False otherwise.
        """
        if self._is_bare is None:
            return False
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
