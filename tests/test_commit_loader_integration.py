import unittest
import subprocess
import tempfile
import os
import json

from git_repo_inspector.commit_loader import CommitLoader

class TestCommitLoaderIntegration(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.original_cwd)

    def _create_repo(self):
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

    def test_load_commits(self):
        repo_dir, repo_path, sha_main, sha_feature = self._create_repo()
        try:
            loader = CommitLoader(repo_path=repo_path)
            commits = loader.load_commits()
            self.assertEqual(len(commits), 2)
            commit_map = {c.sha: c for c in commits}
            self.assertEqual(commit_map[sha_main].message, "initial")
            self.assertEqual(commit_map[sha_main].branches, ["main"])
            self.assertEqual(commit_map[sha_main].parents, [])
            self.assertEqual(commit_map[sha_feature].message, "feature")
            self.assertEqual(commit_map[sha_feature].branches, ["feature"])
            self.assertEqual(commit_map[sha_feature].parents, [sha_main])
        finally:
            repo_dir.cleanup()

    def test_verify_all_commits(self):
        repo_dir, repo_path, *_ = self._create_repo()
        try:
            loader = CommitLoader(repo_path=repo_path)
            mismatches = loader.verify_all_commits()
            self.assertEqual(mismatches, [])
        finally:
            repo_dir.cleanup()

    def test_list_commits_json(self):
        repo_dir, repo_path, sha_main, sha_feature = self._create_repo()
        try:
            loader = CommitLoader(repo_path=repo_path)
            json_output = loader.list_commits_json()
            data = json.loads(json_output)
            commit_map = {d['sha']: d for d in data}
            self.assertEqual(commit_map[sha_main]['message'], 'initial')
            self.assertEqual(commit_map[sha_main]['branches'], ['main'])
            self.assertEqual(commit_map[sha_feature]['message'], 'feature')
            self.assertEqual(commit_map[sha_feature]['branches'], ['feature'])
        finally:
            repo_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
