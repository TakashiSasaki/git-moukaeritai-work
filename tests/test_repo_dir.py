import unittest
from unittest.mock import patch, MagicMock
import os
import subprocess

from git_repo_inspector.repo_loader import RepoDir

class TestRepoDir(unittest.TestCase):

    def setUp(self):
        self.original_cwd = os.getcwd()
        self.mock_git_dir = "/mock/repo/.git"
        self.mock_toplevel_dir = "/mock/repo"

    def tearDown(self):
        os.chdir(self.original_cwd)

    @patch('subprocess.run')
    @patch('os.chdir')
    def test_init_success_no_path(self, mock_chdir, mock_subprocess_run):
        # Mock git rev-parse --absolute-git-dir, --is-bare-repository, --show-toplevel
        mock_subprocess_run.side_effect = [
            MagicMock(stdout=self.mock_git_dir + "\n"), # --absolute-git-dir
            MagicMock(stdout="false\n"), # --is-bare-repository
            MagicMock(stdout=self.mock_toplevel_dir + "\n") # --show-toplevel
        ]

        loader = RepoDir()

        self.assertEqual(loader.absolute_git_dir, self.mock_git_dir)
        self.assertFalse(loader._is_bare)
        self.assertEqual(loader.toplevel_dir, self.mock_toplevel_dir)

        # Verify chdir was called to restore original_cwd
        mock_chdir.assert_called_with(self.original_cwd)

    @patch('subprocess.run')
    @patch('os.chdir')
    def test_init_success_with_path(self, mock_chdir, mock_subprocess_run):
        mock_repo_path = "/path/to/test/repo"
        # Mock git rev-parse --absolute-git-dir, --is-bare-repository, --show-toplevel
        mock_subprocess_run.side_effect = [
            MagicMock(stdout=self.mock_git_dir + "\n"), # --absolute-git-dir
            MagicMock(stdout="false\n"), # --is-bare-repository
            MagicMock(stdout=self.mock_toplevel_dir + "\n") # --show-toplevel
        ]

        loader = RepoDir(repo_path=mock_repo_path)

        self.assertEqual(loader.absolute_git_dir, self.mock_git_dir)
        self.assertFalse(loader._is_bare)
        self.assertEqual(loader.toplevel_dir, self.mock_toplevel_dir)

        # Verify chdir was called to the repo_path and then to restore original_cwd
        mock_chdir.assert_any_call(mock_repo_path)
        mock_chdir.assert_called_with(self.original_cwd)

    @patch('os.chdir', side_effect=FileNotFoundError("Path not found"))
    def test_init_file_not_found_error(self, mock_chdir):
        with self.assertRaisesRegex(FileNotFoundError, "Repository path not found"): 
            RepoDir(repo_path="/non/existent/path")
        mock_chdir.assert_called_once()

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'git', stderr="git error"))
    @patch('os.chdir')
    def test_init_git_command_failure(self, mock_chdir, mock_subprocess_run):
        with self.assertRaisesRegex(RuntimeError, "Git command failed"): 
            RepoDir()
        mock_subprocess_run.assert_called_once()
        mock_chdir.assert_called_with(self.original_cwd) # Ensure chdir is restored

    @patch('subprocess.run')
    @patch('os.chdir')
    def test_is_inside_working_tree_non_bare(self, mock_chdir, mock_subprocess_run):
        mock_subprocess_run.side_effect = [
            MagicMock(stdout=self.mock_git_dir + "\n"), # --absolute-git-dir
            MagicMock(stdout="false\n"), # --is-bare-repository
            MagicMock(stdout=self.mock_toplevel_dir + "\n") # --show-toplevel
        ]
        loader = RepoDir()
        self.assertTrue(loader.is_inside_working_tree())

    @patch('subprocess.run')
    @patch('os.chdir')
    def test_is_inside_working_tree_bare(self, mock_chdir, mock_subprocess_run):
        mock_subprocess_run.side_effect = [
            MagicMock(stdout=self.mock_git_dir + "\n"), # --absolute-git-dir
            MagicMock(stdout="true\n"), # --is-bare-repository
        ]
        loader = RepoDir()
        self.assertFalse(loader.is_inside_working_tree())
        self.assertIsNone(loader.toplevel_dir)

    @patch('subprocess.run')
    @patch('os.chdir')
    def test_get_toplevel_dir_non_bare(self, mock_chdir, mock_subprocess_run):
        mock_subprocess_run.side_effect = [
            MagicMock(stdout=self.mock_git_dir + "\n"), # --absolute-git-dir
            MagicMock(stdout="false\n"), # --is-bare-repository
            MagicMock(stdout=self.mock_toplevel_dir + "\n") # --show-toplevel
        ]
        loader = RepoDir()
        self.assertEqual(loader.get_toplevel_dir(), self.mock_toplevel_dir)

    @patch('subprocess.run')
    @patch('os.chdir')
    def test_get_toplevel_dir_bare(self, mock_chdir, mock_subprocess_run):
        mock_subprocess_run.side_effect = [
            MagicMock(stdout=self.mock_git_dir + "\n"), # --absolute-git-dir
            MagicMock(stdout="true\n"), # --is-bare-repository
        ]
        loader = RepoDir()
        with self.assertRaisesRegex(RuntimeError, "Cannot get top-level directory for a bare repository."): 
            loader.get_toplevel_dir()

if __name__ == '__main__':
    unittest.main()
