import os
import subprocess
from typing import Callable

def run_experiment_3(original_dir: str, sandbox_dir: str, sandbox_path: str):
    # Experiment 3: Run git status with both GIT_DIR and GIT_WORK_TREE set
    os.chdir(original_dir) # Go back to original_dir
    os.chdir(sandbox_dir) # Go to sandbox_dir
    target_worktree_exp3 = "branch3" # Define a new target_worktree for this experiment
    os.chdir(target_worktree_exp3) # Change to branch3 directory
    print(f"\nExperiment 3: Running git status with GIT_DIR and GIT_WORK_TREE set for {target_worktree_exp3}")
    print(f"Current directory: {os.getcwd()}")
    env = os.environ.copy()
    env["GIT_DIR"] = os.path.join(sandbox_path, f"bare.git/worktrees/{target_worktree_exp3}")
    env["GIT_WORK_TREE"] = os.getcwd()
    print(f"Command: git status")
    print(f"GIT_DIR: {env["GIT_DIR"]}")
    print(f"GIT_WORK_TREE: {env["GIT_WORK_TREE"]}")
    result = subprocess.run("git status", capture_output=True, text=True, shell=True, env=env)
    print(f"Stdout:\n{result.stdout}")
    print(f"Stderr:\n{result.stderr}")
    print(f"Exit Code: {result.returncode}")

    expected_error_message_both = ""
    expected_exit_code_both = 0

    if result.returncode == expected_exit_code_both and not result.stderr:
        print("\nConfirmation: Received expected successful execution for both GIT_DIR and GIT_WORK_TREE.")
    else:
        print("\nConfirmation: Did NOT receive expected successful execution for both GIT_DIR and GIT_WORK_TREE.")
        print(f"Expected Exit Code: {expected_exit_code_both}")
        print(f"Actual Stderr: {result.stderr}")

    # Display the final current directory
    print("\nFinal current directory:")
    print(os.getcwd())

if __name__ == "__main__":
    import sys
    # Assuming arguments are passed as: original_dir sandbox_dir sandbox_path
    if len(sys.argv) != 4:
        print("Usage: python run_experiment_3.py <original_dir> <sandbox_dir> <sandbox_path>")
        sys.exit(1)
    
    original_dir = sys.argv[1]
    sandbox_dir = sys.argv[2]
    sandbox_path = sys.argv[3]
    
    run_experiment_3(original_dir, sandbox_dir, sandbox_path)
