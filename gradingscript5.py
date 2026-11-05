#!/usr/bin/env python3

import subprocess
from pathlib import Path

# Student's project directory
REPO = Path("/home/student/project")

score = 0


def git(*args):
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True,
        text=True
    )


# Check 1: Does .gitignore exist?
if (REPO / ".gitignore").is_file():
    print("PASS: .gitignore file exists")
    score += 1
else:
    print("FAIL: .gitignore file does not exist")


# Check 2: Was the repository initialized?
result = git("rev-parse", "--show-toplevel")

if (
    result.returncode == 0
    and Path(result.stdout.strip()).resolve() == REPO.resolve()
):
    print("PASS: Git repository initialized")
    score += 1
else:
    print("FAIL: Git repository not initialized")


# Check 3: Does .gitignore contain ignore rules?
ignore_file = REPO / ".gitignore"

if ignore_file.is_file():
    rules = [
        line.strip()
        for line in ignore_file.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if rules:
        print("PASS: .gitignore contains ignore rules")
        score += 1
    else:
        print("FAIL: .gitignore has no active rules")
else:
    print("FAIL: Cannot check ignore rules")


# Check 4: Does git status --ignored work?
result = git("status", "--ignored")

if result.returncode == 0:
    print("PASS: git status --ignored executes successfully")
    score += 1
else:
    print("FAIL: git status --ignored failed")


# Final grade
print(f"\nFinal Score: {score}/4")

if score == 4:
    print("SUCCESS: All checks passed")
else:
    print("FAILED: Some checks did not pass")