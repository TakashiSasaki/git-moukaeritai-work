# Git Repo Inspector

A Python package to inspect Git repositories. This tool provides both a command-line interface (CLI) for specific data retrieval and a Textual TUI (Text User Interface) for interactive exploration of repository information, including directory details, branches, and commit history.

## Features

*   **Interactive TUI:** Browse repository information, branches, and commits visually in your terminal.
*   **Directory Information:** View details about the Git repository structure (`.git` directory, working tree).
*   **Branch Listing:** List all local branches and the commits they point to.
*   **Commit History:** View a list of commits with their author, date, and subject.
*   **Commit Details:** Select a commit to see its full information, including parents, tree, message, and raw content.
*   **CLI Access:** (Optional) Retains some command-line flags for direct data extraction (e.g., listing commits or branches in JSON).

## Installation

This project uses Poetry for dependency management and packaging.

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd git-repo-inspector
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    poetry install
    ```
    This will create a virtual environment and install all necessary packages, including Textual for the TUI.

## Usage

### Launching the TUI

The primary way to use `git-repo-inspector` is via its Textual TUI.

*   **To inspect the current directory (if it's a Git repository):**
    ```bash
    poetry run git-repo-inspector
    ```
    Alternatively, if you have activated the Poetry shell (`poetry shell`):
    ```bash
    git-repo-inspector
    ```

*   **To inspect a specific Git repository:**
    ```bash
    poetry run git-repo-inspector /path/to/your/git/repository
    ```
    Or from within the Poetry shell:
    ```bash
    git-repo-inspector /path/to/your/git/repository
    ```

### Navigating the TUI

*   **Repository Path Input:** At the top, you'll find an input field showing the current repository path. You can type a new path here and press the "Change Directory" button to load a different repository.
*   **Information Panels:**
    *   **RepoDir Information:** Shows details about the repository's structure.
    *   **Branches:** A table listing branch names and their corresponding commit SHAs.
    *   **Commits:** A table listing commits (short SHA, author, date, subject).
    *   **Commit Details:** Displays comprehensive information about the commit selected in the "Commits" table.
*   **Selection:** Use the arrow keys (Up/Down) to navigate and select rows in the "Branches" and "Commits" tables.
*   **Key Bindings:**
    *   `d` or `Ctrl+D`: Toggle dark/light mode.
    *   `q` or `Ctrl+Q`: Quit the application.
*   **Scrolling:** If content overflows, you can usually scroll with the mouse wheel or arrow keys/Page Up/Page Down within focused widgets.

### (Optional) Command-Line Interface (CLI)

While the TUI is the main interface, some of the original CLI flags are still available for scripting or quick data checks:

*   `--list-branches`: List branches and their SHAs to the console.
*   `--list-commits`: List basic commit information to the console.
*   `--json`: Use with `--list-branches` or `--list-commits` to get output in JSON format.
*   `--verify`: Verify commit SHAs (can be slow).

**Example (CLI):**
```bash
poetry run git-repo-inspector --list-branches --json
```

If you run `poetry run git-repo-inspector --help`, you will see all available options. If no specific CLI output option is chosen, the TUI will launch by default.

## Development

(Information about setting up a development environment, running tests, and contributing can be added here if applicable.)

---

*This README was last updated to reflect the addition of the Textual TUI.*
