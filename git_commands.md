# Git Commands Cheat Sheet

## Basic Commands
```bash
# Check status of your repository
git status

# Add files to staging area
git add filename.py           # Add specific file
git add .                     # Add all files

# Commit changes
git commit -m "Your message"

# Push changes to remote
git push origin main
```

## Reverting Changes
```bash
# Discard changes in working directory for a specific file
git checkout -- filename.py

# Discard all changes in working directory
git checkout -- .

# Reset to last commit (keeps changes in working directory)
git reset HEAD^

# Reset to last commit (discards changes)
git reset --hard HEAD

# Go back to specific commit
git reset --hard commit_hash

# Create new commit that undoes previous commit
git revert HEAD

# Temporarily save changes without committing
git stash
git stash pop               # Apply stashed changes later
```

## Branch Management
```bash
# List branches
git branch

# Create new branch
git branch branch_name

# Switch to branch
git checkout branch_name

# Create and switch in one command
git checkout -b new_branch_name

# Merge branch into current branch
git merge branch_name

# Delete branch
git branch -d branch_name
```

## History and Differences
```bash
# View commit history
git log
git log --oneline           # Compact view
git log --graph --oneline   # Graphical view

# Show changes between commits
git diff
git diff commit1 commit2

# Show changes in staged files
git diff --staged
```

## Remote Repository
```bash
# Show remote repositories
git remote -v

# Add remote repository
git remote add origin https://github.com/username/repo.git

# Fetch latest changes from remote
git fetch origin

# Pull changes from remote
git pull origin main
```

## Config
```bash
# Set username and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set default editor
git config --global core.editor "vim"
```
