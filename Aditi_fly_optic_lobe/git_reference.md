# Git Quick Reference

## About this file

This is a Markdown (`.md`) file. Markdown is a plain text format that uses simple symbols to add formatting — `#` for headings, `**text**` for bold, `-` for bullet points. It looks like plain text in a basic editor, but renders as a nicely formatted document on GitHub or in VS Code. To preview it in VS Code press `Ctrl+Shift+V`. All your git notes are kept here so they're versioned alongside your code.

---

## Connecting a Local Folder to a Remote Repository

```bash
# 1. Navigate to your project folder
cd "path/to/your/folder"

# 2. Initialize git (only needed if no .git folder exists yet)
git init

# 3. Connect to your GitHub repo
git remote add origin https://github.com/USERNAME/REPO_NAME.git

# 4. Check what remote is connected (verify it worked)
git remote -v

# 5. Stage all files
git add .

# 6. Commit with a message
git commit -m "your message here"

# 7. Set branch to main and push
git branch -M main
git push -u origin main
```

After the first push, future pushes are just:
```bash
git add .
git commit -m "your message"
git push
```

---

## Changing or Removing a Remote

```bash
# See current remote
git remote -v

# Change remote URL
git remote set-url origin https://github.com/USERNAME/NEW_REPO.git

# Remove remote entirely
git remote remove origin
```

---

## .gitignore Cheatsheet

A `.gitignore` file tells git which files/folders to ignore. Create it in the same folder as your `.git` folder.

### Basic syntax

```
# This is a comment

# Ignore a specific file
secrets.txt

# Ignore all .npy files
*.npy

# Ignore a specific folder
__pycache__/

# Ignore everything inside a folder but not the folder itself
logs/*

# Ignore a file in a specific location only
SimulationCode/Models/big_file.npy
```

### Negation (!) — include something you previously excluded

```
# Ignore everything
*

# But keep this folder
!Aditi/

# But keep everything inside it
!Aditi/**
```

The order matters — rules are read top to bottom. You must un-ignore parent folders
before you can un-ignore their contents, which is why the pattern above has three lines.

### Common patterns for this project

```
# Ignore pre-built binary files (large, not your work)
*.npy

# Ignore Python cache
__pycache__/
*.pyc

# Ignore VS Code settings
.vscode/

# Ignore OS junk
.DS_Store
Thumbs.db
```

---

## Useful everyday commands

```bash
# See what files have changed
git status

# See what changed inside files
git diff

# See commit history
git log --oneline

# Undo changes to a file (before committing)
git checkout -- filename.py

# Pull latest changes from GitHub
git pull
```

---

## Branches

A branch is a version of your code. Every repo has one default branch created automatically when you run `git init`.

**master vs main** — they mean the same thing, just different default names. Older git versions named it `master`, GitHub now defaults to `main` for new repos. This mismatch is common — just be consistent when pushing.

**`--set-upstream origin main`** — run once on your first push to introduce your local branch to its GitHub counterpart. `origin` is the nickname for your GitHub repo URL, `main` is the branch name. After this git remembers the connection and future pushes are just `git push`.

```bash
# Rename local branch to main (for consistency with GitHub)
git branch -M main

# First push — links local main to GitHub main
git push --set-upstream origin main

# Every push after that
git add .
git commit -m "your message"
git push
```

---

## GitHub credentials

GitHub no longer accepts your account password via terminal.
You need a **Personal Access Token (PAT)**:

1. GitHub → Settings → Developer Settings
2. Personal Access Tokens → Tokens (classic)
3. Generate new token → check `repo` scope → copy it
4. Use it as your password when the terminal prompts you

To avoid entering it every time:
```bash
git config --global credential.helper store
```
This saves your token locally after the first use.
