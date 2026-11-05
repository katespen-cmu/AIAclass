#!/usr/bin/env python3
"""
Grading check for the "leaked secret in git" lab (Steps 1-3).

Nothing here depends on commit hashes. It inspects CONTENT:
  - is a file named .env present anywhere in history (all branches, tags, reflog)?
  - does any blob still contain the fake secret strings?
  - are leftover unreachable objects still holding the secret?
  - is the legitimate project history preserved (not just wiped)?
  - is origin pointed at the shared GitLab repo?
  - does the SHARED repo (cloned fresh) also lack the secret, and do its
    branch tips match the student's local branch tips (i.e. they force-pushed)?

Usage (run on coworker-2 as the student, after the student finishes Step 3):
    GL_USER=coworker2 GL_PASS='tartans@1' python3 grade_check2.py

Options:
    --repo PATH            local repo (default ~/project)
    --remote-url URL       shared repo URL (default http://10.9.8.60/aiaclass/project.git)
    --skip-server          only grade the local repo
    --skip-revert-check    don't require evidence of the Step 1 revert commit
    --token TOKEN          optional GitLab API token; also checks master was re-protected
Exit code 0 = all checks passed, 1 = at least one failed.
"""
import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

# ---- Edit these if the lab content changes -------------------------------
SECRET_FILENAME = ".env"
SECRET_MARKERS = [b"NotARealPassword123", b"AIAFAKEDBPASS", b"super-secret-key-123456789"]
EXPECTED_REMOTE = "http://10.9.8.60/aiaclass/project.git"
GITLAB_PROJECT_PATH = "aiaclass/project"
REQUIRED_BRANCH = "master"
# Legit files that must survive the rewrite (proves history wasn't just wiped).
EXPECTED_FILES = ["README.md", "models.py", "database.py", "utils.py", "main.py"]
MAX_BLOB_BYTES = 2_000_000
# ---------------------------------------------------------------------------


def git(repo, *args, env=None, input_bytes=None):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True,
                          input=input_bytes, env=env)


def out(repo, *args, env=None):
    r = git(repo, *args, env=env)
    return r.stdout.decode(errors="replace").strip()


def object_listing(repo):
    """(sha, path) for every object reachable from any ref or the reflog."""
    r = git(repo, "rev-list", "--all", "--reflog", "--objects")
    items = []
    for line in r.stdout.decode(errors="replace").splitlines():
        parts = line.split(" ", 1)
        items.append((parts[0], parts[1] if len(parts) > 1 else ""))
    return items


def blobs_with_markers(repo, shas):
    """Return shas of blobs whose content contains any secret marker."""
    if not shas:
        return []
    r = git(repo, "cat-file", "--batch", input_bytes=("\n".join(shas) + "\n").encode())
    data, pos, hits = r.stdout, 0, []
    while pos < len(data):
        nl = data.find(b"\n", pos)
        if nl == -1:
            break
        header = data[pos:nl].split()
        if len(header) < 3 or header[1] == b"missing":
            pos = nl + 1
            continue
        sha, typ, size = header[0].decode(), header[1], int(header[2])
        body = data[nl + 1: nl + 1 + size]
        pos = nl + 1 + size + 1
        if typ == b"blob" and size <= MAX_BLOB_BYTES and any(m in body for m in SECRET_MARKERS):
            hits.append(sha)
    return hits


def history_checks(repo, label):
    results = []
    objs = object_listing(repo)

    env_paths = sorted({p for _, p in objs if p and os.path.basename(p) == SECRET_FILENAME})
    results.append((f"{label}: no '{SECRET_FILENAME}' file anywhere in history",
                    not env_paths, f"found paths: {env_paths}" if env_paths else ""))

    hits = blobs_with_markers(repo, [s for s, _ in objs])
    results.append((f"{label}: no reachable file content contains the secret",
                    not hits, f"{len(hits)} blob(s) still contain it" if hits else ""))
    return results


def unreachable_check(repo):
    r = git(repo, "fsck", "--unreachable", "--no-reflogs", "--no-progress")
    shas = [l.split()[2] for l in r.stdout.decode(errors="replace").splitlines()
            if l.startswith("unreachable blob")]
    hits = blobs_with_markers(repo, shas)
    return ("local: no leftover unreachable objects contain the secret",
            not hits, "old secret objects remain in .git (rewrite not completed?)" if hits else "")


def normalize_url(u):
    u = re.sub(r"^(https?://)[^@/]+@", r"\1", u.strip())
    u = u.rstrip("/")
    if u.endswith(".git"):
        u = u[:-4]
    return u.lower()


def make_askpass(tmpdir):
    path = os.path.join(tmpdir, "askpass.sh")
    with open(path, "w") as f:
        f.write('#!/bin/sh\ncase "$1" in *sername*) echo "$GL_USER";; *) echo "$GL_PASS";; esac\n')
    os.chmod(path, stat.S_IRWXU)
    return path


def heads(repo, env=None):
    res = {}
    for line in out(repo, "for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", env=env).splitlines():
        name, sha = line.split()
        res[name] = sha
    return res


def local_checks(repo, require_revert):
    results = []
    if not os.path.isdir(os.path.join(repo, ".git")):
        return [(f"local: {repo} is a git repository", False, "not found")]

    results += history_checks(repo, "local")
    results.append(unreachable_check(repo))

    # Legit history preserved
    count = out(repo, "rev-list", "--count", "--all")
    count = int(count) if count.isdigit() else 0
    results.append(("local: project history preserved (more than one commit)",
                    count > 1, f"{count} commit(s)"))
    files = set(out(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines())
    missing = [f for f in EXPECTED_FILES if f not in files]
    results.append(("local: project files still present at HEAD", not missing,
                    f"missing: {missing}" if missing else ""))

    # Step 1 evidence: a revert commit exists
    if require_revert:
        subjects = out(repo, "log", "--all", "--format=%s").splitlines()
        has_revert = any(s.startswith("Revert") for s in subjects)
        results.append(("local: Step 1 revert commit present in history", has_revert,
                        "no commit with a 'Revert ...' subject" if not has_revert else ""))

    # Step 3: remote re-added
    url = out(repo, "remote", "get-url", "origin")
    ok = bool(url) and normalize_url(url) == normalize_url(EXPECTED_REMOTE)
    results.append(("local: origin points to the shared GitLab repo", ok,
                    f"origin = {url or '(not set)'}" if not ok else ""))
    return results


def server_checks(repo, remote_url, token):
    results = []
    user, pw = os.environ.get("GL_USER"), os.environ.get("GL_PASS")
    if not user or not pw:
        return [("server: credentials provided (set GL_USER and GL_PASS)", False, "missing")]

    tmp = tempfile.mkdtemp(prefix="gradecheck_")
    try:
        env = dict(os.environ, GIT_ASKPASS=make_askpass(tmp), GIT_TERMINAL_PROMPT="0",
                   GL_USER=user, GL_PASS=pw)
        mirror = os.path.join(tmp, "server.git")
        r = subprocess.run(["git", "-c", "credential.helper=", "clone", "--bare", "-q",
                            remote_url, mirror], capture_output=True, env=env)
        if r.returncode != 0:
            return [("server: could clone the shared repo", False,
                     r.stderr.decode(errors="replace").strip()[-200:])]

        results += history_checks(mirror, "server")

        srv = heads(mirror)
        results.append((f"server: branch '{REQUIRED_BRANCH}' exists",
                        f"refs/heads/{REQUIRED_BRANCH}" in srv, ""))

        # Server tips must equal the student's local tips (proves the force push happened)
        if repo and os.path.isdir(os.path.join(repo, ".git")):
            loc = heads(repo)
            mismatched = [b.replace("refs/heads/", "") for b, sha in loc.items()
                          if b in srv and srv[b] != sha]
            only_local = [b.replace("refs/heads/", "") for b in loc if b not in srv]
            bad = mismatched + only_local
            results.append(("server: branch tips match local (force push completed)",
                            not bad, f"out of sync: {bad}" if bad else ""))

        # Optional: re-protection (needs API token)
        if token:
            base = remote_url.split("/" + GITLAB_PROJECT_PATH)[0]
            api = (f"{base}/api/v4/projects/{GITLAB_PROJECT_PATH.replace('/', '%2F')}"
                   f"/protected_branches/{REQUIRED_BRANCH}")
            req = urllib.request.Request(api, headers={"PRIVATE-TOKEN": token})
            try:
                urllib.request.urlopen(req, timeout=10)
                protected, detail = True, ""
            except urllib.error.HTTPError as e:
                protected, detail = False, f"HTTP {e.code} (branch not protected)" if e.code == 404 else f"HTTP {e.code}"
            except Exception as e:  # noqa
                protected, detail = False, str(e)
            results.append((f"server: '{REQUIRED_BRANCH}' re-protected after the push", protected, detail))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.path.expanduser("~/project"))
    ap.add_argument("--remote-url", default=EXPECTED_REMOTE)
    ap.add_argument("--skip-server", action="store_true")
    ap.add_argument("--skip-revert-check", action="store_true")
    ap.add_argument("--token", default=os.environ.get("GL_TOKEN"))
    args = ap.parse_args()

    results = local_checks(args.repo, not args.skip_revert_check)
    if not args.skip_server:
        results += server_checks(args.repo, args.remote_url, args.token)

    failed = 0
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  -> {detail}" if detail and not ok else ""))
        failed += (not ok)
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
