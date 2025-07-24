import os
import shutil
import subprocess
import stat

# Define the sandbox directory name
sandbox_dir = "sandbox"

# Get the absolute path for the sandbox directory
base_dir = os.path.abspath(os.getcwd())
sandbox_path = os.path.join(base_dir, sandbox_dir)

# Function to remove read-only files
def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

# If the directory exists, remove it and its contents
if os.path.exists(sandbox_path):
    print(f"Removing existing directory: {sandbox_path}")
    shutil.rmtree(sandbox_path, onerror=remove_readonly)

# Create the sandbox directory
print(f"Creating directory: {sandbox_path}")
os.makedirs(sandbox_path)

original_dir = os.getcwd()


def run_experiment_1(original_dir, sandbox_dir, sandbox_path):
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

def run_experiment_2(original_dir, sandbox_dir, sandbox_path):
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

def run_experiment_3(original_dir, sandbox_dir, sandbox_path):
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

def setup_git_environment(original_dir, sandbox_dir, sandbox_path):
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

try:
    setup_git_environment(original_dir, sandbox_dir, sandbox_path)
    # Call the experiments
    run_experiment_1(original_dir, sandbox_dir, sandbox_path)
    run_experiment_2(original_dir, sandbox_dir, sandbox_path)
    run_experiment_3(original_dir, sandbox_dir, sandbox_path)

finally:
    # Always change back to the original directory
    os.chdir(original_dir)
    print(f"\nChanged back to original directory: {os.getcwd()}")