import unittest
from unittest.mock import patch, MagicMock
import json
import hashlib
from typing import List, Dict, Optional, Tuple, Any

from git_repo_inspector.commit_loader import CommitLoader, Commit
from git_repo_inspector.branch_loader import BranchLoader

class TestCommitLoader(unittest.TestCase):

    def setUp(self):
        self.mock_repo_path = "/tmp/test_repo"
        self.loader = CommitLoader(self.mock_repo_path)

    def test_init(self):
        self.assertEqual(self.loader.repo_path, self.mock_repo_path)
        self.assertIsNone(self.loader.commit_shas)
        self.assertIsInstance(self.loader.branch_loader, BranchLoader)
        self.assertEqual(self.loader.branch_loader.repo_path, self.mock_repo_path)

    @patch('subprocess.run')
    def test_get_commit_shas(self, mock_run):
        mock_run.return_value = MagicMock(stdout="sha1\nsha2\nsha3\n")
        shas = self.loader.get_commit_shas()
        self.assertEqual(shas, ["sha1", "sha2", "sha3"])
        mock_run.assert_called_once_with(
            ['git', '-C', self.mock_repo_path, 'rev-list', '--all'],
            stdout=subprocess.PIPE, text=True, check=True
        )
        # Test caching
        shas_cached = self.loader.get_commit_shas()
        self.assertEqual(shas_cached, ["sha1", "sha2", "sha3"])
        mock_run.assert_called_once() # Should not be called again

    @patch('git_repo_inspector.branch_loader.BranchLoader.get_branches')
    def test_get_branches(self, mock_get_branches):
        mock_get_branches.return_value = {"sha1": ["main", "master"]}
        branches = self.loader.get_branches()
        self.assertEqual(branches, {"sha1": ["main", "master"]})
        mock_get_branches.assert_called_once()

    @patch('git_repo_inspector.commit_loader.CommitLoader.get_commit_shas')
    @patch('git_repo_inspector.commit_loader.CommitLoader.get_branches')
    @patch('subprocess.Popen')
    def test_load_commits(self, mock_popen, mock_get_branches, mock_get_commit_shas):
        mock_get_commit_shas.return_value = ["commit_sha_1", "commit_sha_2"]
        mock_get_branches.return_value = {
            "commit_sha_1": ["main"],
            "commit_sha_2": ["feature"]
        }

        # Mock subprocess.Popen behavior
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        # Simulate git cat-file --batch output
        commit_raw_1 = b"tree tree_sha_1\nparent parent_sha_1\nauthor Author Name <author@example.com> 1234567890 +0000\ncommitter Committer Name <committer@example.com> 1234567890 +0000\n\nCommit message 1\n"
        commit_raw_2 = b"tree tree_sha_2\nparent parent_sha_2\nauthor Author Name <author@example.com> 1234567890 +0000\ncommitter Committer Name <committer@example.com> 1234567890 +0000\n\nCommit message 2\n"

        mock_proc.stdout.readline.side_effect = [
            f"commit_sha_1 commit {len(commit_raw_1)}\n".encode(),
            f"commit_sha_2 commit {len(commit_raw_2)}\n".encode(),
            b"" # End of output
        ]
        mock_proc.stdout.read.side_effect = [
            commit_raw_1 + b"\n", # +1 for newline, then [:-1] removes it
            commit_raw_2 + b"\n"
        ]

        commits = self.loader.load_commits()

        self.assertEqual(len(commits), 2)

        self.assertEqual(commits[0].sha, "commit_sha_1")
        self.assertEqual(commits[0].tree, "tree_sha_1")
        self.assertEqual(commits[0].parents, ["parent_sha_1"])
        self.assertEqual(commits[0].author, "Author Name <author@example.com> 1234567890 +0000")
        self.assertEqual(commits[0].committer, "Committer Name <committer@example.com> 1234567890 +0000")
        self.assertEqual(commits[0].message, "Commit message 1")
        self.assertEqual(commits[0].branches, ["main"])
        self.assertEqual(commits[0].raw, commit_raw_1.decode('utf-8'))

        self.assertEqual(commits[1].sha, "commit_sha_2")
        self.assertEqual(commits[1].tree, "tree_sha_2")
        self.assertEqual(commits[1].parents, ["parent_sha_2"])
        self.assertEqual(commits[1].author, "Author Name <author@example.com> 1234567890 +0000")
        self.assertEqual(commits[1].committer, "Committer Name <committer@example.com> 1234567890 +0000")
        self.assertEqual(commits[1].message, "Commit message 2")
        self.assertEqual(commits[1].branches, ["feature"])
        self.assertEqual(commits[1].raw, commit_raw_2.decode('utf-8'))

        mock_popen.assert_called_once_with(
            ['git', '-C', self.mock_repo_path, 'cat-file', '--batch'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        mock_proc.stdin.write.assert_any_call(b"commit_sha_1\n")
        mock_proc.stdin.write.assert_any_call(b"commit_sha_2\n")
        mock_proc.stdin.close.assert_called_once()

    def test_verify_commit_valid(self):
        # Create a dummy commit with known raw content and SHA
        raw_content = "tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904\nauthor Test User <test@example.com> 1678886400 +0000\ncommitter Test User <test@example.com> 1678886400 +0000\n\nInitial commit\n"
        body_bytes = raw_content.encode('utf-8')
        header = f"commit {len(body_bytes)}\0".encode('utf-8')
        computed_sha = hashlib.sha1(header + body_bytes).hexdigest()

        valid_commit = Commit(
            sha=computed_sha,
            tree="4b825dc642cb6eb9a060e54bf8d69288fbee4904",
            parents=[],
            author="Test User <test@example.com> 1678886400 +0000",
            committer="Test User <test@example.com> 1678886400 +0000",
            message="Initial commit",
            branches=[],
            raw=raw_content
        )
        self.assertTrue(self.loader.verify_commit(valid_commit))

    def test_verify_commit_invalid(self):
        # Create a dummy commit with incorrect SHA
        raw_content = "tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904\nauthor Test User <test@example.com> 1678886400 +0000\ncommitter Test User <test@example.com> 1678886400 +0000\n\nInitial commit\n"
        invalid_commit = Commit(
            sha="incorrect_sha", # This SHA is intentionally wrong
            tree="4b825dc642cb6eb9a060e54bf8d69288fbee4904",
            parents=[],
            author="Test User <test@example.com> 1678886400 +0000",
            committer="Test User <test@example.com> 1678886400 +0000",
            message="Initial commit",
            branches=[],
            raw=raw_content
        )
        self.assertFalse(self.loader.verify_commit(invalid_commit))

    @patch('git_repo_inspector.commit_loader.CommitLoader.load_commits')
    def test_verify_all_commits(self, mock_load_commits):
        # Setup mock commits: one valid, one invalid
        valid_raw = "tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904\nauthor Test User <test@example.com> 1678886400 +0000\ncommitter Test User <test@example.com> 1678886400 +0000\n\nValid commit\n"
        valid_body_bytes = valid_raw.encode('utf-8')
        valid_header = f"commit {len(valid_body_bytes)}\0".encode('utf-8')
        valid_computed_sha = hashlib.sha1(valid_header + valid_body_bytes).hexdigest()

        valid_commit = Commit(
            sha=valid_computed_sha, raw=valid_raw, tree="", parents=[], author="", committer="", message="", branches=[]
        )

        invalid_raw = "tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904\nauthor Test User <test@example.com> 1678886400 +0000\ncommitter Test User <test@example.com> 1678886400 +0000\n\nInvalid commit\n"
        invalid_body_bytes = invalid_raw.encode('utf-8')
        invalid_header = f"commit {len(invalid_body_bytes)}\0".encode('utf-8')
        # This SHA will be intentionally wrong
        invalid_commit = Commit(
            sha="wrong_sha_for_invalid_commit", raw=invalid_raw, tree="", parents=[], author="", committer="", message="", branches=[]
        )
        
        mock_load_commits.return_value = [valid_commit, invalid_commit]

        mismatches = self.loader.verify_all_commits()
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0][0], "wrong_sha_for_invalid_commit")
        # Recompute the correct SHA for the invalid commit to compare
        recomputed_invalid_sha = hashlib.sha1(invalid_header + invalid_body_bytes).hexdigest()
        self.assertEqual(mismatches[0][1], recomputed_invalid_sha)

    @patch('git_repo_inspector.commit_loader.CommitLoader.get_branches')
    def test_list_branches_json(self, mock_get_branches):
        mock_get_branches.return_value = {
            "sha1": ["main", "master"],
            "sha2": ["feature"]
        }
        expected_json = json.dumps([
            {'branch': 'main', 'sha': 'sha1'},
            {'branch': 'master', 'sha': 'sha1'},
            {'branch': 'feature', 'sha': 'sha2'}
        ], indent=2)
        
        # Sort the expected output to match the non-deterministic order of dict.items()
        # in older Python versions, or if the order of branches for a SHA is not guaranteed.
        # For Python 3.7+, dict.items() insertion order is preserved, but for safety,
        # sorting the list of dicts by 'branch' and then 'sha' ensures consistent test results.
        parsed_output = json.loads(self.loader.list_branches_json())
        parsed_output.sort(key=lambda x: (x['branch'], x['sha']))
        expected_parsed = json.loads(expected_json)
        expected_parsed.sort(key=lambda x: (x['branch'], x['sha']))

        self.assertEqual(parsed_output, expected_parsed)
        mock_get_branches.assert_called_once()

    @patch('git_repo_inspector.commit_loader.CommitLoader.load_commits')
    def test_list_commits_json(self, mock_load_commits):
        mock_load_commits.return_value = [
            Commit(sha="sha1", tree="tree1", parents=[], author="A", committer="A", message="Msg1", branches=["main"], raw="raw1"),
            Commit(sha="sha2", tree="tree2", parents=["sha1"], author="B", committer="B", message="Msg2", branches=[], raw="raw2")
        ]
        expected_json = json.dumps([
            {'sha': 'sha1', 'tree': 'tree1', 'parents': [], 'author': 'A', 'committer': 'A', 'message': 'Msg1', 'branches': ['main'], 'raw': 'raw1'},
            {'sha': 'sha2', 'tree': 'tree2', 'parents': ['sha1'], 'author': 'B', 'committer': 'B', 'message': 'Msg2', 'branches': [], 'raw': 'raw2'}
        ], indent=2)
        
        self.assertEqual(self.loader.list_commits_json(), expected_json)
        mock_load_commits.assert_called_once()

if __name__ == '__main__':
    unittest.main()
