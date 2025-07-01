import unittest
import os
import subprocess
import tempfile
import shutil

from git_repo_inspector.repo_loader import RepoDir

class TestRepoDirIntegration(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for the Git repository
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_path)

        # Initialize a Git repository
        subprocess.run(['git', 'init'], cwd=self.repo_path, check=True)

        # Create a dummy commit
        with open(os.path.join(self.repo_path, "test.txt"), "w") as f:
            f.write("hello world")
        subprocess.run(['git', 'add', "test.txt"], cwd=self.repo_path, check=True)
        subprocess.run(['git', 'commit', '-m', "Initial commit"], cwd=self.repo_path, check=True)

        self.original_cwd = os.getcwd()

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)
        os.chdir(self.original_cwd)

    def test_repo_dir_initialization_and_methods(self):
        # Test with explicit repo_path
        loader = RepoDir(repo_path=self.repo_path)
        self.assertTrue(loader.absolute_git_dir.startswith(self.repo_path))
        self.assertTrue(loader.absolute_git_dir.endswith(".git"))
        self.assertTrue(loader.is_inside_working_tree())
        self.assertEqual(loader.get_toplevel_dir(), self.repo_path)

        # Test with current working directory (chdir to repo_path first)
        os.chdir(self.repo_path)
        loader_cwd = RepoDir()
        self.assertTrue(loader_cwd.absolute_git_dir.startswith(self.repo_path))
        self.assertTrue(loader_cwd.absolute_git_dir.endswith(".git"))
        self.assertTrue(loader_cwd.is_inside_working_tree())
        self.assertEqual(loader_cwd.get_toplevel_dir(), self.repo_path)

    def test_bare_repository(self):
        # Create a bare repository
        bare_repo_path = os.path.join(self.temp_dir, "bare_repo.git")
        subprocess.run(['git', 'init', '--bare', bare_repo_path], check=True)

        loader = RepoDir(repo_path=bare_repo_path)
        self.assertTrue(loader.absolute_git_dir.startswith(bare_repo_path))
        self.assertTrue(loader.is_inside_working_tree() == False)
        with self.assertRaisesRegex(RuntimeError, "Cannot get top-level directory for a bare repository."):
            loader.get_toplevel_dir()

    def test_non_git_directory(self):
        non_git_dir = os.path.join(self.temp_dir, "non_git_dir")
        os.makedirs(non_git_dir)

        with self.assertRaisesRegex(RuntimeError, "Git command failed: not a git repository"): # Adjust regex based on actual git error message
            RepoDir(repo_path=non_git_dir)

if __name__ == '__main__':
    unittest.main()
