import unittest
import os
import subprocess
import tempfile

from git_repo_inspector.repo_dir import RepoDir


class TestRepoDirIntegration(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.original_cwd)

    def test_non_bare_repository(self):
        with tempfile.TemporaryDirectory() as repo_path:
            subprocess.run(["git", "init", repo_path], check=True, capture_output=True)
            loader = RepoDir(repo_path=repo_path)

            self.assertEqual(loader.absolute_git_dir, os.path.join(repo_path, ".git"))
            self.assertTrue(loader.is_inside_working_tree())
            self.assertEqual(loader.get_toplevel_dir(), os.path.abspath(repo_path))
            self.assertEqual(os.getcwd(), self.original_cwd)

    def test_bare_repository(self):
        with tempfile.TemporaryDirectory() as repo_path:
            subprocess.run(["git", "init", "--bare", repo_path], check=True, capture_output=True)
            loader = RepoDir(repo_path=repo_path)

            self.assertEqual(loader.absolute_git_dir, os.path.abspath(repo_path))
            self.assertFalse(loader.is_inside_working_tree())
            self.assertIsNone(loader.toplevel_dir)
            with self.assertRaises(RuntimeError):
                loader.get_toplevel_dir()
            self.assertEqual(os.getcwd(), self.original_cwd)


if __name__ == "__main__":
    unittest.main()
