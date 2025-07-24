import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path

# TUIの実行や実際のGit操作を避けるため、依存関係をモック化します
with patch('src.git_repo_inspector.tui.RepoDir'), \
     patch('src.git_repo_inspector.tui.BranchLoader'), \
     patch('src.git_repo_inspector.tui.CommitLoader'), \
     patch('textual.app.App.run'):
    from src.git_repo_inspector.tui import GitRepoInspectorTUI, datetime
    from textual.widgets import Static, DataTable, Input, Button


# テスト用のモックコミットオブジェクト
class MockCommit:
    def __init__(self, sha, author, message):
        self.sha = sha
        self.author = author
        self.message = message
        self.committer = ""


@pytest.fixture
def app():
    """
    テスト用のTUIアプリケーションインスタンスを生成するフィクスチャ。
    __init__内の_load_repo_dataの自動実行を抑制し、
    UIウィジェットやローダーを手動でモックに置き換えます。
    """
    with patch.object(GitRepoInspectorTUI, '_load_repo_data', lambda self: None):
        app_instance = GitRepoInspectorTUI()

        # UIウィジェットをモック化
        app_instance.repo_info_widget = MagicMock(spec=Static)
        app_instance.branch_table = MagicMock(spec=DataTable)
        app_instance.commit_table = MagicMock(spec=DataTable)
        app_instance.commit_detail_view = MagicMock(spec=Static)
        app_instance.dir_input = MagicMock(spec=Input)

        # データローダーをモック化
        app_instance._repo_dir = MagicMock()
        app_instance._branch_loader = MagicMock()
        app_instance._commit_loader = MagicMock()

        # 必要な属性を初期化
        app_instance._repo_path = Path('/fake/repo')
        app_instance._commits_data_cache = []

        yield app_instance


# --- ヘルパー関数のテスト ---

def test_get_author_name(app):
    assert app._get_author_name("John Doe <john.doe@example.com>") == "John Doe"
    assert app._get_author_name(" Some Name  <name@mail.com> 123 +0900") == "Some Name"
    assert app._get_author_name("InvalidName") == "Unknown Author"
    assert app._get_author_name("") == "Unknown Author"


def test_parse_commit_date(app):
    date_str = "Author Name <email> 1678886400 +0000"
    with patch('src.git_repo_inspector.tui.datetime') as mock_dt:
        mock_datetime_instance = MagicMock()
        mock_datetime_instance.strftime.return_value = "2023-03-15 13:20:00"
        mock_dt.fromtimestamp.return_value = mock_datetime_instance

        result = app._parse_commit_date(date_str)

        assert result == "2023-03-15 13:20:00"
        mock_dt.fromtimestamp.assert_called_once_with(1678886400)
        mock_datetime_instance.strftime.assert_called_once_with('%Y-%m-%d %H:%M:%S')

    assert app._parse_commit_date("Invalid String") == "Unknown Date"


# --- データ更新ロジックのテスト ---

def test_update_branch_table_success(app):
    mock_branches = {'sha1': ['main', 'feature/a'], 'sha2': ['develop']}
    app._branch_loader.get_branches.return_value = mock_branches

    app._update_branch_table()

    app.branch_table.clear.assert_called_once()
    # ブランチ名でソートされることを確認
    expected_calls = [
        call('develop', 'sha2'),
        call('feature/a', 'sha1'),
        call('main', 'sha1'),
    ]
    app.branch_table.add_row.assert_has_calls(expected_calls, any_order=False)


def test_update_branch_table_no_branches(app):
    app._branch_loader.get_branches.return_value = {}
    app._update_branch_table()
    app.branch_table.add_row.assert_called_once_with("No branches found.", "")


def test_update_branch_table_exception(app):
    app._branch_loader.get_branches.side_effect = Exception("Git error")
    app._update_branch_table()
    app.branch_table.add_row.assert_called_with(f"Error loading branches: Exception", "Git error")


def test_update_commit_table_success(app):
    mock_commits = [
        MockCommit("sha1", "Author 1 <a1@x.c> 100", "feat: one"),
        MockCommit("sha2", "Author 2 <a2@x.c> 200", "fix: two\nMore details."),
    ]
    app._commit_loader.load_commits.return_value = mock_commits
    app._commits_data_cache = []  # キャッシュをクリア

    with patch.object(app, '_get_author_name', side_effect=["Author 1", "Author 2"]), \
         patch.object(app, '_parse_commit_date', side_effect=["Date 1", "Date 2"]):
        app._update_commit_table()

        app.commit_table.clear.assert_called_once()
        app.commit_detail_view.update.assert_called_once_with("Select a commit to see details.")
        assert app._commits_data_cache == mock_commits  # キャッシュが更新されたか
        expected_calls = [
            call('sha1', 'Author 1', 'Date 1', 'feat: one', key='sha1'),
            call('sha2', 'Author 2', 'Date 2', 'fix: two', key='sha2'),
        ]
        app.commit_table.add_row.assert_has_calls(expected_calls)


def test_update_commit_table_uses_cache(app):
    app._commits_data_cache = [MockCommit("sha1", "Author 1", "feat: one")]
    app._update_commit_table()
    # キャッシュがある場合、load_commitsは呼ばれない
    app._commit_loader.load_commits.assert_not_called()


def test_update_commit_table_exception(app):
    app._commit_loader.load_commits.side_effect = Exception("Load error")
    app._commits_data_cache = []
    app._update_commit_table()
    assert app._commits_data_cache == [] # エラー時にキャッシュがクリアされるか
    app.commit_table.add_row.assert_called_with("Error: Exception", "Load error", "", "")


# --- コアイベントハンドラのテスト ---

@pytest.mark.asyncio
async def test_on_button_pressed_change_dir_success(app):
    event = MagicMock()
    event.button = MagicMock()
    event.button.id = "change_dir"
    app.dir_input.value = "/new/valid/path"

    with patch('src.git_repo_inspector.tui.Path') as mock_path:
        mock_path.return_value.resolve.return_value = mock_path.return_value
        mock_path.return_value.is_dir.return_value = True
        app._load_repo_data = MagicMock() # _load_repo_dataの呼び出しを監視

        await app.on_button_pressed(event)

        assert app._repo_path == mock_path.return_value
        app.repo_info_widget.update.assert_called_once()
        app.branch_table.clear.assert_called_once()
        app._load_repo_data.assert_called_once()


@pytest.mark.asyncio
async def test_on_button_pressed_change_dir_invalid(app):
    event = MagicMock()
    event.button = MagicMock()
    event.button.id = "change_dir"
    app.dir_input.value = "/invalid/path"

    with patch('src.git_repo_inspector.tui.Path') as mock_path:
        mock_path.return_value.resolve.return_value = mock_path.return_value
        mock_path.return_value.is_dir.return_value = False
        app._load_repo_data = MagicMock()

        await app.on_button_pressed(event)

        app.repo_info_widget.update.assert_called_with(f"Error: Path '{app.dir_input.value}' is not a valid directory.")
        app._load_repo_data.assert_not_called()


# --- _load_repo_data の直接的なテスト ---

@patch('src.git_repo_inspector.tui.CommitLoader')
@patch('src.git_repo_inspector.tui.BranchLoader')
@patch('src.git_repo_inspector.tui.RepoDir')
def test_load_repo_data_success(MockRepoDir, MockBranchLoader, MockCommitLoader):
    # __init__を一時的に無力化してインスタンスを作成
    with patch.object(GitRepoInspectorTUI, '__init__', lambda *args, **kwargs: super(GitRepoInspectorTUI, args[0]).__init__()):
        app = GitRepoInspectorTUI(repo_path=".")

    # 必要な属性とモックを手動で設定
    app._repo_path = Path("/fake/repo")
    app.repo_info_widget = MagicMock(spec=Static)
    app._update_branch_table = MagicMock()
    app._update_commit_table = MagicMock()
    MockRepoDir.return_value._is_bare = False
    MockRepoDir.return_value.toplevel_dir = "/fake/repo"
    MockRepoDir.return_value.absolute_git_dir = "/fake/repo/.git"

    app._load_repo_data()

    MockRepoDir.assert_called_once_with(str(app._repo_path))
    MockBranchLoader.assert_called_once_with(str(app._repo_path))
    MockCommitLoader.assert_called_once_with(str(app._repo_path))
    app.repo_info_widget.update.assert_called_once()
    app._update_branch_table.assert_called_once()
    app._update_commit_table.assert_called_once()


@patch('src.git_repo_inspector.tui.RepoDir', side_effect=ValueError("Not a git repository"))
def test_load_repo_data_failure(MockRepoDir):
    with patch.object(GitRepoInspectorTUI, '__init__', lambda *args, **kwargs: super(GitRepoInspectorTUI, args[0]).__init__()):
        app = GitRepoInspectorTUI(repo_path=".")

    app._repo_path = Path("/invalid/path")
    app._commits_data_cache = ["old data"]
    app.repo_info_widget = MagicMock(spec=Static)
    app.branch_table = MagicMock(spec=DataTable)
    app.commit_table = MagicMock(spec=DataTable)
    app.commit_detail_view = MagicMock(spec=Static)

    app._load_repo_data()

    assert app._repo_dir is None
    assert app._branch_loader is None
    assert app._commit_loader is None
    assert app._commits_data_cache == []
    app.repo_info_widget.update.assert_called_once()
    assert "Error loading repository data" in app.repo_info_widget.update.call_args[0][0]
    app.branch_table.add_row.assert_called_once_with("Error loading branches.", "ValueError")
    app.commit_table.add_row.assert_called_once_with("Error loading commits.", "ValueError", "", "")
    app.commit_detail_view.update.assert_called_once_with("Error loading commit details.")
