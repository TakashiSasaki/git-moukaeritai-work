import os
import shutil
import subprocess
import stat
from typing import Callable

# Function to remove read-only files
def remove_readonly(func: Callable, path: str, excinfo: tuple):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def initial_setup_and_cleanup(sandbox_path: str):
    # If the directory exists, remove it and its contents
    if os.path.exists(sandbox_path):
        print(f"Removing existing directory: {sandbox_path}")
        shutil.rmtree(sandbox_path, onerror=remove_readonly)

    # Create the sandbox directory
    print(f"Creating directory: {sandbox_path}")
    os.makedirs(sandbox_path)







def setup_git_environment(original_dir: str, sandbox_dir: str, sandbox_path: str):
    # Initial Git setup
    os.chdir(sandbox_path)
    print(f"Changed current directory to: {os.getcwd()}")

    print("Creating bare repository: bare.git")
    subprocess.run("git init --bare bare.git", check=True, shell=True)

    print("Cloning bare.git to bare")
    subprocess.run("git clone bare.git bare", check=True, shell=True)

    os.chdir("bare")
    print(f"Changed current directory to: {os.getcwd()}")

    print("Creating date.txt")
    subprocess.run('cmd /c "date /t > date.txt"', check=True, shell=True)

    print("Configuring local git user")
    subprocess.run('git config user.email "test@example.com"', check=True, shell=True)
    subprocess.run('git config user.name "Test User"', check=True, shell=True)

    print("Committing date.txt")
    subprocess.run("git add date.txt", check=True, shell=True)
    subprocess.run('git commit -m "Add date.txt"', check=True, shell=True)

    print("Pushing to origin")
    subprocess.run("git push origin master", check=True, shell=True)

    for i in range(1, 4):
        branch_name = f"branch{i}"
        print(f"Creating and pushing branch: {branch_name}")
        subprocess.run(f"git branch {branch_name}", check=True, shell=True)
        subprocess.run(f"git push origin {branch_name}", check=True, shell=True)

    os.chdir(original_dir)
    os.chdir(sandbox_dir)
    for i in range(1, 4):
        branch_name = f"branch{i}"
        worktree_path = f"{branch_name}"
        print(f"Creating worktree for {branch_name} at {worktree_path}")
        subprocess.run(f"git --git-dir=bare.git worktree add {worktree_path} {branch_name}", check=True, shell=True)

    for i in range(1, 4):
        branch_name = f"branch{i}"
        worktree_path = f"{branch_name}"
        os.chdir(sandbox_path) # Ensure we are in sandbox_path before changing to worktree
        os.chdir(worktree_path)
        print(f"Changed current directory to: {os.getcwd()}")
        print("Configuring local git user")
        subprocess.run('git config user.email "test@example.com"', check=True, shell=True)
        subprocess.run('git config user.name "Test User"', check=True, shell=True)
        file_name = f"file{i}.txt"
        print(f"Creating {file_name} in {branch_name}")
        with open(file_name, "w") as f:
            f.write(f"This is file {i} in branch {i}")
        subprocess.run(f"git add {file_name}", check=True, shell=True)
        subprocess.run(f'git commit -m "Add {file_name}"', check=True, shell=True)
        subprocess.run(f"git push ../bare.git {branch_name}", check=True, shell=True)

    print("\nFinal current directory:")
    print(os.getcwd())

def main():
    # Define the sandbox directory name
    sandbox_dir = "sandbox"

    # Get the absolute path for the sandbox directory
    base_dir = os.path.abspath(os.getcwd())
    sandbox_path = os.path.join(base_dir, sandbox_dir)

    original_dir = os.getcwd()

    try:
        initial_setup_and_cleanup(sandbox_path)
        setup_git_environment(original_dir, sandbox_dir, sandbox_path)
        # Call the experiments
        subprocess.run(["python", os.path.join(base_dir, "run_experiment_1.py"), original_dir, sandbox_dir, sandbox_path], check=True)
        subprocess.run(["python", os.path.join(base_dir, "run_experiment_2.py"), original_dir, sandbox_dir, sandbox_path], check=True)
        subprocess.run(["python", os.path.join(base_dir, "run_experiment_3.py"), original_dir, sandbox_dir, sandbox_path], check=True)

    finally:
        # Always change back to the original directory
        os.chdir(original_dir)
        print(f"\nChanged back to original directory: {os.getcwd()}")

if __name__ == "__main__":
    main()