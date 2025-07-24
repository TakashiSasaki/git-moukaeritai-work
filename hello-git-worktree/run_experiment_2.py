import os
import subprocess
from typing import Callable

def run_experiment_2(original_dir: str, sandbox_dir: str, sandbox_path: str):
    # Experiment 2: Remove .git file from sandbox/branch2 and run git status
    os.chdir(original_dir)
    os.chdir(sandbox_dir)
    target_worktree = "branch2"
    git_file_path = os.path.join(target_worktree, ".git")
    print(f"\nExperiment 2: Removing {git_file_path} and running git status")
    if os.path.exists(git_file_path):
        os.remove(git_file_path)
        print(f"Removed {git_file_path}")
    else:
        print(f"{git_file_path} does not exist.")

    os.chdir(target_worktree)
    print(f"Changed current directory to: {os.getcwd()}")
    print(f"\nExperiment: Running git status with GIT_WORK_TREE set for {target_worktree}")
    env = os.environ.copy()
    env["GIT_WORK_TREE"] = os.path.abspath(target_worktree)
    result = subprocess.run("git status", capture_output=True, text=True, shell=True, env=env)
    print(f"Stdout:\n{result.stdout}")
    print(f"Stderr:\n{result.stderr}")
    print(f"Exit Code: {result.returncode}")

    expected_error_message = "fatal: this operation must be run in a work tree"
    expected_exit_code = 128

    if expected_error_message in result.stderr and result.returncode == expected_exit_code:
        print("\nConfirmation: Received expected error message and exit code.")
    else:
        print("\nConfirmation: Did NOT receive expected error message or exit code.")
        print(f"Expected Stderr: '{expected_error_message}'")
        print(f"Expected Exit Code: {expected_exit_code}")

    # Display the final current directory
    print("\nFinal current directory:")
    print(os.getcwd())

if __name__ == "__main__":
    import sys
    # Assuming arguments are passed as: original_dir sandbox_dir sandbox_path
    if len(sys.argv) != 4:
        print("Usage: python run_experiment_2.py <original_dir> <sandbox_dir> <sandbox_path>")
        sys.exit(1)
    
    original_dir = sys.argv[1]
    sandbox_dir = sys.argv[2]
    sandbox_path = sys.argv[3]
    
    run_experiment_2(original_dir, sandbox_dir, sandbox_path)
