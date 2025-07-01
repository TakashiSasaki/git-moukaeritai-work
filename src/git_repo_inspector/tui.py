from pathlib import Path
import os

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, Button, Label, DataTable

from .repo_dir import RepoDir
from .branch_loader import BranchLoader
from .commit_loader import CommitLoader


class GitRepoInspectorTUI(App):
    """A Textual TUI for inspecting Git repositories."""

    CSS_PATH = "tui.css"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, repo_path: str = "."):
        super().__init__()
        self._repo_path = Path(repo_path).resolve()
        self._repo_dir: RepoDir | None = None
        self._branch_loader: BranchLoader | None = None
        self._commit_loader: CommitLoader | None = None
        self._load_repo_data()

    def _load_repo_data(self):
        """Loads repository data based on the current _repo_path."""
        try:
            self._repo_dir = RepoDir(str(self._repo_path))
            self._branch_loader = BranchLoader(str(self._repo_path))
            self._commit_loader = CommitLoader(str(self._repo_path))
            # In a real app, you'd update widgets with this data
            # Update RepoDir info widget
            if hasattr(self, 'repo_info_widget'):
                if self._repo_dir:
                    repo_dir_info = (
                        f"[b]RepoDir Information for:[/b] {self._repo_path}\n"
                        f"  Absolute Git Dir: {self._repo_dir.absolute_git_dir}\n"
                        f"  Is Bare Repository: {self._repo_dir._is_bare}"
                    )
                    if not self._repo_dir._is_bare and self._repo_dir.toplevel_dir:
                        repo_dir_info += f"\n  Top-Level Directory: {self._repo_dir.toplevel_dir}"
                    self.repo_info_widget.update(repo_dir_info)
                else:
                    # This case should ideally be caught by the exception below,
                    # but as a fallback:
                    self.repo_info_widget.update(f"RepoDir could not be initialized for: {self._repo_path}")

            # Update Branch Table
            self._update_branch_table()

            # Update Commit Table
            self._update_commit_table()

        except Exception as e:
            self._repo_dir = None
            self._branch_loader = None
            self._commit_loader = None
            self._commits_data_cache = [] # Clear cache on error
            error_message = f"Error loading repository data for {self._repo_path}:\n[b]{type(e).__name__}:[/b] {e}"

            if hasattr(self, 'repo_info_widget'):
                self.repo_info_widget.update(error_message)

            if hasattr(self, 'branch_table'):
                self.branch_table.clear()
                self.branch_table.add_row("Error loading branches.", type(e).__name__)

            if hasattr(self, 'commit_table'):
                self.commit_table.clear()
                self.commit_table.add_row("Error loading commits.", str(type(e).__name__), "", "")

            if hasattr(self, 'commit_detail_view'):
                self.commit_detail_view.update("Error loading commit details.")


    def _parse_commit_date(self, author_info: str) -> str:
        """Parses the date from the author/committer string."""
        try:
            # Example: "Author Name <email> 1678886400 +0000"
            parts = author_info.split(' ')
            timestamp = int(parts[-2])
            # Convert timestamp to a readable format, e.g., YYYY-MM-DD HH:MM:SS
            from datetime import datetime
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except (IndexError, ValueError):
            return "Unknown Date"

    def _get_author_name(self, author_info: str) -> str:
        """Extracts the author name from the full author string."""
        try:
            return author_info.split('<', 1)[0].strip()
        except: # Broad except as parsing can be tricky
            return "Unknown Author"

    def _update_commit_table(self):
        """Updates the commit table with data from CommitLoader."""
        self.commit_table.clear()
        self.commit_detail_view.update("Select a commit to see details.") # Reset detail view
        if self._commit_loader:
            try:
                # Cache commits if not already loaded to avoid reloading on every UI update
                # that doesn't change the repo path.
                if not self._commits_data_cache: # Simple caching strategy
                    self._commits_data_cache = self._commit_loader.load_commits()

                if self._commits_data_cache:
                    # Sort commits by date (most recent first) - assuming date is parseable from author string
                    # This might be slow for very large repos if done every time.
                    # For simplicity, we'll sort here.
                    # A more robust way would be to parse and store date objects.

                    # For now, let's display in the order they are loaded, often reverse chronological.
                    for commit in self._commits_data_cache:
                        short_sha = commit.sha[:7]
                        author_name = self._get_author_name(commit.author)
                        # Assuming author string contains date info that can be parsed
                        # Example: "User Name <user@example.com> 1625078400 -0700"
                        # We need to extract and format the date.
                        commit_date = self._parse_commit_date(commit.author) # Or commit.committer
                        subject = commit.message.split('\n', 1)[0] # First line of message
                        self.commit_table.add_row(short_sha, author_name, commit_date, subject, key=commit.sha)
                else:
                    self.commit_table.add_row("No commits found.", "", "", "")
            except Exception as e:
                self._commits_data_cache = [] # Clear cache on error
                self.commit_table.add_row(f"Error: {type(e).__name__}", str(e), "", "")
        else:
            self.commit_table.add_row("CommitLoader not available.", "", "", "")

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Populate tables on initial load
        self._load_repo_data()
        # Set cursor type for tables to 'row' to enable row selection
        self.branch_table.cursor_type = "row"
        self.commit_table.cursor_type = "row"


    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        # Directory Input Area
        self.dir_input = Input(value=str(self._repo_path), placeholder="Enter repository path")
        self.change_dir_button = Button("Change Directory", id="change_dir")
        yield Horizontal(
            Label("Repo Path:"),
            self.dir_input,
            self.change_dir_button,
            id="dir_input_bar"
        )

        # Main content area
        self.repo_info_widget = Static("RepoDir Info Will Appear Here", id="repo_info")

        self.branch_table = DataTable(id="branch_table")
        self.branch_table.add_columns("Branch Name", "Commit SHA")

        self.commit_table = DataTable(id="commit_table")
        self.commit_table.add_columns("SHA (short)", "Author", "Date", "Subject")

        self.commit_detail_view = Static("Select a commit to see details.", id="commit_detail")

        yield Vertical(
            self.repo_info_widget,
            Label("[b]Branches:[/b]"),
            self.branch_table,
            Label("[b]Commits:[/b]"),
            self.commit_table,
            Label("[b]Commit Details:[/b]"),
            self.commit_detail_view,
            id="main_content"
        )
        yield Footer()

    def _update_branch_table(self):
        """Updates the branch table with data from BranchLoader."""
        self.branch_table.clear()
        if self._branch_loader:
            try:
                branches = self._branch_loader.get_branches()
                if branches:
                    sorted_branches = []
                    for sha, names in branches.items():
                        for name in names:
                            sorted_branches.append((name, sha))
                    sorted_branches.sort(key=lambda x: x[0])

                    for name, sha in sorted_branches:
                        self.branch_table.add_row(name, sha)
                else:
                    self.branch_table.add_row("No branches found.", "")
            except Exception as e:
                self.branch_table.add_row(f"Error loading branches: {type(e).__name__}", str(e))
        else:
            self.branch_table.add_row("BranchLoader not available.", "")


    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "change_dir":
            new_path_str = self.dir_input.value
            new_path = Path(new_path_str).resolve()
            if new_path.is_dir():
                self._repo_path = new_path
                self.dir_input.value = str(self._repo_path)

                # Clear old data and indicate loading
                self.repo_info_widget.update(f"Attempting to load: {self._repo_path}...")
                self.branch_table.clear()
                self.branch_table.add_row("Loading branches...", "")
                # self.commit_info_widget.update("...") # For commit loader later

                self._load_repo_data() # This will call _update_branch_table via _load_repo_data
            else:
                self.repo_info_widget.update(f"Error: Path '{new_path_str}' is not a valid directory.")


def main():
    """The main entry point for the TUI application."""
    app = GitRepoInspectorTUI()
    app.run()

if __name__ == "__main__":
    main()
