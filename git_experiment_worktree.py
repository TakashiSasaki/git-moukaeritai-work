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

try:
    # Change into the sandbox directory
    os.chdir(sandbox_path)
    print(f"Changed current directory to: {os.getcwd()}")

    # Create a bare git repository
    print("Creating bare repository: bare.git")
    subprocess.run("git init --bare bare.git", check=True, shell=True)

    # Clone the bare repository
    print("Cloning bare.git to bare")
    subprocess.run("git clone bare.git bare", check=True, shell=True)

    # Change into the cloned repository
    os.chdir("bare")
    print(f"Changed current directory to: {os.getcwd()}")

    # Create a new file with the date
    print("Creating date.txt")
    # Using 'date /t' for Windows compatibility
    subprocess.run('cmd /c "date /t > date.txt"', check=True, shell=True)

    # Configure git user for the commit (to avoid errors if not set globally)
    print("Configuring local git user")
    subprocess.run('git config user.email "test@example.com"', check=True, shell=True)
    subprocess.run('git config user.name "Test User"', check=True, shell=True)

    # Add and commit the new file
    print("Committing date.txt")
    subprocess.run("git add date.txt", check=True, shell=True)
    subprocess.run('git commit -m "Add date.txt"', check=True, shell=True)

    # Push the commit to the bare repository. Using 'master' as the branch name.
    print("Pushing to origin")
    subprocess.run("git push origin master", check=True, shell=True)

    # Create and push new branches
    for i in range(1, 4):
        branch_name = f"branch{i}"
        print(f"Creating and pushing branch: {branch_name}")
        subprocess.run(f"git branch {branch_name}", check=True, shell=True)
        subprocess.run(f"git push origin {branch_name}", check=True, shell=True)

    # Create worktrees for each branch
    os.chdir(original_dir)
    os.chdir(sandbox_dir)
    for i in range(1, 4):
        branch_name = f"branch{i}"
        worktree_path = f"{branch_name}"
        print(f"Creating worktree for {branch_name} at {worktree_path}")
        subprocess.run(f"git --git-dir=bare.git worktree add {worktree_path} {branch_name}", check=True, shell=True)

    # Create a new file in each worktree and push to bare.git
    for i in range(1, 4):
        branch_name = f"branch{i}"
        worktree_path = f"{branch_name}"
        os.chdir(worktree_path)
        print(f"Changed current directory to: {os.getcwd()}")
        # Configure git user for the commit (to avoid errors if not set globally)
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
        os.chdir("..")

    # Display the final current directory
    print("\nFinal current directory:")
    print(os.getcwd())

    # Rename sandbox/branch3 to sandbox/branch3_moved
    os.chdir(original_dir)
    os.chdir(sandbox_dir)
    old_name = "branch1"
    new_name = "branch1_moved"
    print(f"Renaming {old_name} to {new_name}")
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

finally:
    # Always change back to the original directory
    os.chdir(original_dir)
    print(f"\nChanged back to original directory: {os.getcwd()}")