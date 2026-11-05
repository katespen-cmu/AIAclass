#!/usr/bin/env python3
"""
Grading Script (Step 4): Clean up remote branches
Run on coworker-1 after completing Step 4.

Checks that:
  - clean-dev exists and contains no .env file (tree, working dir, or history)
  - the most recent commit on clean-dev is a proper cherry-pick of coworker-1's
    main.py change (commit starting with 980d)
  - the leaky remote development branch has been deleted
  - the old commit has been purged locally (reflog expire + gc)

Only failures and the final score are printed.
"""
import os
import subprocess

REPO = os.path.expanduser("~/project")
NEW_BRANCH = "clean-dev"
BASE_BRANCH = "master"
OLD_REMOTE_BRANCH = "origin/development"
ORIGINAL_COMMIT_PREFIX = "980d"        # coworker-1's main.py commit
EXPECTED_CHANGED_FILES = ["main.py"]   # cherry-picked commit only touches main.py
POINTS_PER_CHECK = 10
NUM_CHECKS = 6
TOTAL_POSSIBLE = POINTS_PER_CHECK * NUM_CHECKS

current_points = 0

def git(*args, input_text=None):
    """Run a git command inside the project repo."""
    return subprocess.run(["git", "-C", REPO, *args],
                          capture_output=True, text=True, input=input_text)

def result(passed, fail_message=""):
    """Add points on pass; print only on failure."""
    global current_points
    if passed:
        current_points += POINTS_PER_CHECK
    else:
        print(f"FAIL: {fail_message}")
    return passed

def check_clean_dev_exists():
    ok = git("rev-parse", "--verify", NEW_BRANCH).returncode == 0
    result(ok, f"Branch '{NEW_BRANCH}' not found")

def check_no_env_file():
    tree = git("ls-tree", "-r", "--name-only", NEW_BRANCH)
    if tree.returncode != 0:
        return result(False, f"Could not read contents of '{NEW_BRANCH}'")

    tracked_env = [f for f in tree.stdout.splitlines() if os.path.basename(f) == ".env"]
    current = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    on_disk = current == NEW_BRANCH and os.path.exists(os.path.join(REPO, ".env"))
    result(not (tracked_env or on_disk), f".env file is still present on '{NEW_BRANCH}'")

def check_no_env_in_history():
    log = git("log", NEW_BRANCH, "--oneline", "--", ".env")
    if log.returncode != 0:
        return result(False, f"Could not read history of '{NEW_BRANCH}'")
    result(not log.stdout.strip(), f"A commit touching .env exists in the history of '{NEW_BRANCH}'")

def get_patch_id(commit):
    show = git("show", commit)
    if show.returncode != 0:
        return None
    pid = subprocess.run(["git", "-C", REPO, "patch-id", "--stable"],
                         capture_output=True, text=True, input=show.stdout)
    parts = pid.stdout.split()
    return parts[0] if parts else None

def check_cherry_pick():
    tip = git("rev-parse", NEW_BRANCH).stdout.strip()
    parent = git("rev-parse", f"{NEW_BRANCH}~1").stdout.strip()
    base = git("rev-parse", BASE_BRANCH).stdout.strip()
    if not tip or not parent or not base:
        return result(False, "Could not resolve commits for cherry-pick check")

    # 1. Commit must sit directly on top of clean master
    if parent != base:
        return result(False, f"Latest commit on '{NEW_BRANCH}' is not directly on top of '{BASE_BRANCH}'")

    # 2. Commit must only change main.py
    files = git("diff-tree", "--no-commit-id", "--name-only", "-r", tip).stdout.split()
    if sorted(files) != sorted(EXPECTED_CHANGED_FILES):
        return result(False, f"Latest commit should change only {EXPECTED_CHANGED_FILES}, found {files}")

    # 3. If the original commit still exists locally, compare patches directly
    original = git("rev-parse", "--verify", f"{ORIGINAL_COMMIT_PREFIX}^{{commit}}")
    if original.returncode == 0:
        orig_hash = original.stdout.strip()
        if orig_hash == tip:
            return result(False, "Latest commit is the original commit, not a new cherry-picked copy")
        if get_patch_id(orig_hash) != get_patch_id(tip):
            return result(False, "Cherry-picked changes do not match the original commit")

    result(True)

def check_remote_development_deleted():
    branches = [b.strip() for b in git("branch", "-r").stdout.splitlines()]
    result(OLD_REMOTE_BRANCH not in branches, f"{OLD_REMOTE_BRANCH} still exists")

def check_old_commit_purged():
    found = git("cat-file", "-e", f"{ORIGINAL_COMMIT_PREFIX}^{{commit}}").returncode == 0
    result(not found,
           "Original commit still exists locally "
           "(run: git reflog expire --expire=now --all && git gc --prune=now)")

if __name__ == "__main__":
    if not os.path.isdir(os.path.join(REPO, ".git")):
        print(f"FAIL: No git repository found at {REPO}")
    else:
        check_clean_dev_exists()
        check_no_env_file()
        check_no_env_in_history()
        check_cherry_pick()
        check_remote_development_deleted()
        check_old_commit_purged()

    print("\n=== Final Result ===")
    print(f"Total Points: {current_points}/{TOTAL_POSSIBLE}")
    raise SystemExit(0 if current_points == TOTAL_POSSIBLE else 1)