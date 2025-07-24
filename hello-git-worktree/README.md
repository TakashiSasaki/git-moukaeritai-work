# Git Worktree Experiments

This repository contains a set of Python scripts designed to experiment with Git worktrees and observe their behavior under various scenarios, particularly focusing on directory renaming and the impact of Git environment variables (`GIT_DIR` and `GIT_WORK_TREE`).

## Files

-   `main.py`: This is the main entry point for running all the Git worktree experiments. It handles the initial setup of the Git environment (creating a bare repository, cloning, setting up branches and worktrees) and then sequentially calls the individual experiment scripts.

-   `run_experiment_1.py`: This script performs "Experiment 1", which involves renaming a Git worktree directory and then attempting to perform Git operations (creating a new file, committing, and pushing) within the renamed worktree. It demonstrates how Git continues to track the worktree even after its directory has been moved.

-   `run_experiment_2.py`: This script executes "Experiment 2". It simulates a scenario where the `.git` file (which points to the worktree's internal Git directory) is removed from a worktree. It then attempts to run `git status` while explicitly setting the `GIT_WORK_TREE` environment variable, expecting a specific error related to not being in a worktree.

-   `run_experiment_3.py`: This script carries out "Experiment 3". It tests the behavior of `git status` when both `GIT_DIR` (pointing to the worktree's Git directory within the bare repository) and `GIT_WORK_TREE` (pointing to the current worktree directory) environment variables are explicitly set. It expects a successful execution, demonstrating how these variables can be used to control Git's behavior.

## How to Run

To run all the experiments, execute the `main.py` script from the root directory of this repository:

```bash
python main.py
```

The script will:
1.  Clean up any previous `sandbox` directory.
2.  Set up a fresh Git environment with a bare repository and three worktrees.
3.  Execute Experiment 1 (renaming a worktree).
4.  Execute Experiment 2 (removing `.git` file and testing `git status`).
5.  Execute Experiment 3 (testing `git status` with `GIT_DIR` and `GIT_WORK_TREE`).
6.  Clean up the created `sandbox` directory upon completion.

## Experiments Overview

Each experiment is designed to illustrate a specific aspect of Git worktree functionality:

-   **Experiment 1: Renaming a Worktree Directory**
    -   **Objective**: To show that Git can still track and operate within a worktree even after its directory has been renamed. It also highlights that `git worktree list` might mark such a worktree as 'prunable' because its original path is no longer valid.

-   **Experiment 2: Removing .git File and Testing GIT_WORK_TREE**
    -   **Objective**: To demonstrate the dependency of Git commands on the `.git` file within a worktree. It shows that without this file, Git commands will fail unless `GIT_WORK_TREE` is explicitly set, and even then, certain operations might not behave as expected.

-   **Experiment 3: Using GIT_DIR and GIT_WORK_TREE Together**
    -   **Objective**: To illustrate how `GIT_DIR` and `GIT_WORK_TREE` environment variables can be used to manually specify the Git repository and working tree, respectively. This allows for fine-grained control over Git operations, even in non-standard setups.
