import unittest
import subprocess
import tempfile
import json
import os

from git_repo_inspector.branch_loader import BranchLoader

class TestBranchLoaderIntegration(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.original_cwd)

    def _create_repo_with_branches(self):
        repo_dir = tempfile.TemporaryDirectory()
        repo_path = repo_dir.name
        subprocess.run(["git", "init", "-b", "main", repo_path], check=True, capture_output=True)
        subprocess.run(["git", "-C", repo_path, "config", "user.name", "Tester"], check=True)
        subprocess.run(["git", "-C", repo_path, "config", "user.email", "tester@example.com"], check=True)
        subprocess.run(["git", "-C", repo_path, "commit", "--allow-empty", "-m", "initial"], check=True, capture_output=True)
        sha_main = subprocess.run(["git", "-C", repo_path, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        subprocess.run(["git", "-C", repo_path, "checkout", "-b", "feature"], check=True, capture_output=True)
        subprocess.run(["git", "-C", repo_path, "commit", "--allow-empty", "-m", "feature"], check=True, capture_output=True)
        sha_feature = subprocess.run(["git", "-C", repo_path, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        return repo_dir, repo_path, sha_main, sha_feature

    def test_get_branches(self):
        repo_dir, repo_path, sha_main, sha_feature = self._create_repo_with_branches()
        try:
            loader = BranchLoader(repo_path=repo_path)
            branches = loader.get_branches()
            expected = {sha_main: ["main"], sha_feature: ["feature"]}
            self.assertEqual(branches, expected)
        finally:
            repo_dir.cleanup()

    def test_to_json(self):
        repo_dir, repo_path, sha_main, sha_feature = self._create_repo_with_branches()
        try:
            loader = BranchLoader(repo_path=repo_path)
            json_output = loader.to_json()
            data = json.loads(json_output)
            data.sort(key=lambda x: (x["branch"], x["sha"]))
            expected = [
                {"branch": "feature", "sha": sha_feature},
                {"branch": "main", "sha": sha_main},
            ]
            expected.sort(key=lambda x: (x["branch"], x["sha"]))
            self.assertEqual(data, expected)
        finally:
            repo_dir.cleanup()

if __name__ == "__main__":
    unittest.main()
