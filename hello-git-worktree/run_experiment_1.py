import os
import subprocess
from typing import Callable

def run_experiment_1(original_dir: str, sandbox_dir: str, sandbox_path: str):
    # Experiment 1: Rename a worktree directory
    # Rename sandbox/branch1 to sandbox/branch1_moved
    os.chdir(original_dir)
    os.chdir(sandbox_dir)
    old_name = "branch1"
    new_name = "branch1_moved"
    print(f"\nExperiment 1: Renaming {old_name} to {new_name}")
    os.rename(old_name, new_name)

    # Try to create a new file and commit in the renamed worktree
    # Note: Even after renaming the worktree directory, Git can still track it
    # and allow commits/pushes because the worktree's internal Git directory
    # (e.g., .git/worktrees/branch3) still points to the correct bare repository.
    # However, `git worktree list` will show it as 'prunable' because the original
    # path it was added with is no longer valid.
    os.chdir(new_name)
    print(f"Changed current directory to: {os.getcwd()}")
    file_name = "new_file_in_moved_branch.txt"
    print(f"Creating {file_name} in {new_name}")
    with open(file_name, "w") as f:
        f.write(f"This is a new file in {new_name}")
    subprocess.run(f"git add {file_name}", check=True, shell=True)
    try:
        subprocess.run(f'git commit -m "Add {file_name} in moved branch1" --no-verify', check=True, shell=True)
        subprocess.run(f"git push ../bare.git branch1", check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"\nError during commit/push in renamed worktree: {e}")
        print(f"Stderr: {e.stderr.decode()}")

    # Display the final current directory
    print("\nFinal current directory:")
    print(os.getcwd())

if __name__ == "__main__":
    import sys
    # Assuming arguments are passed as: original_dir sandbox_dir sandbox_path
    if len(sys.argv) != 4:
        print("Usage: python run_experiment_1.py <original_dir> <sandbox_dir> <sandbox_path>")
        sys.exit(1)
    
    original_dir = sys.argv[1]
    sandbox_dir = sys.argv[2]
    sandbox_path = sys.argv[3]
    
    run_experiment_1(original_dir, sandbox_dir, sandbox_path)
