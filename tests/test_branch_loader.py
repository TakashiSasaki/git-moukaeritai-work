
import unittest
from unittest.mock import patch, MagicMock
from git_repo_inspector.branch_loader import BranchLoader
import subprocess

class TestBranchLoader(unittest.TestCase):

    def setUp(self):
        """Set up a BranchLoader instance for testing."""
        self.repo_path = '/fake/repo'
        self.loader = BranchLoader(self.repo_path)

    @patch('subprocess.run')
    def test_get_branches_success(self, mock_subprocess_run):
        """Test successful retrieval and parsing of branch information."""
        # Mock the return value of subprocess.run
        mock_output = (
            "main a1b2c3d4e5f6\n"
            "feature/new-thing 9f8e7d6c5b4a\n"
            "hotfix/bug-123 a1b2c3d4e5f6\n"
        )
        mock_result = MagicMock()
        mock_result.stdout = mock_output
        mock_result.check_returncode.return_value = None
        mock_subprocess_run.return_value = mock_result

        # Call the method
        branches = self.loader.get_branches()

        # Define expected git command
        expected_cmd = [
            'git', '-C', self.repo_path,
            'for-each-ref',
            '--format=%(refname:short) %(objectname)',
            'refs/heads/'
        ]

        # Assert that subprocess.run was called correctly
        mock_subprocess_run.assert_called_once_with(
            expected_cmd,
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )

        # Assert the parsed branch map is correct
        expected_branches = {
            'a1b2c3d4e5f6': ['main', 'hotfix/bug-123'],
            '9f8e7d6c5b4a': ['feature/new-thing']
        }
        self.assertEqual(branches, expected_branches)

    @patch('subprocess.run')
    def test_get_branches_caching(self, mock_subprocess_run):
        """Test that branch information is cached after the first call."""
        # Mock the return value for the first call
        mock_output = "main a1b2c3d4e5f6\n"
        mock_result = MagicMock()
        mock_result.stdout = mock_output
        mock_subprocess_run.return_value = mock_result

        # First call to populate cache
        self.loader.get_branches()
        self.assertIsNotNone(self.loader.branch_map)
        
        # Second call
        self.loader.get_branches()

        # Assert that subprocess.run was only called once
        self.assertEqual(mock_subprocess_run.call_count, 1)

    @patch('subprocess.run')
    def test_get_branches_no_branches(self, mock_subprocess_run):
        """Test behavior when the repository has no branches."""
        # Mock an empty output
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_subprocess_run.return_value = mock_result

        # Call the method
        branches = self.loader.get_branches()

        # Assert the branch map is empty
        self.assertEqual(branches, {})

    @patch('subprocess.run')
    def test_get_branches_subprocess_error(self, mock_subprocess_run):
        """Test that an exception from subprocess.run is propagated."""
        # Configure the mock to raise an exception
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "git")

        # Assert that the exception is raised
        with self.assertRaises(subprocess.CalledProcessError):
            self.loader.get_branches()

if __name__ == '__main__':
    unittest.main()
