import asyncio
import json
import mimetypes
import os
import re
import shutil
import struct
import subprocess
import time
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    import ptyprocess  # type: ignore
    _HAS_PTY = True
    _PTY_ERROR = ""
except ImportError as _pty_err:
    _HAS_PTY = False
    _PTY_ERROR = str(_pty_err)

APP_DIR = Path(__file__).parent
INDEX_HTML = APP_DIR / "index.html"
PORT = int(os.environ.get("PORT", "8099"))

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
HA_API_BASE = "http://supervisor/core/api"

SKIP_DIRS = {".git", ".storage", "__pycache__", "node_modules", ".cloud"}
MAX_READ_BYTES = 2 * 1024 * 1024
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

OPTIONS_FILE = Path("/data/options.json")

# Multi-root: each name corresponds to an HA folder that the add-on
# may have mapped in config.yaml. Only roots that actually exist at
# start-up are exposed. "config" is primary (editor also operates on
# paths without a root prefix for backward compat).
_ROOT_CANDIDATES = {
    "config":  Path(os.environ.get("CONFIG_DIR", "/config")),
    "ssl":     Path("/ssl"),
    "share":   Path("/share"),
    "addons":  Path("/addons"),
    "media":   Path("/media"),
    "backup":  Path("/backup"),
}
ROOTS = {name: p.resolve() for name, p in _ROOT_CANDIDATES.items() if p.exists()}
# Ensure config is always present (even for local dev without HA mounts)
if "config" not in ROOTS:
    ROOTS["config"] = _ROOT_CANDIDATES["config"].resolve()
CONFIG_ROOT = ROOTS["config"]


def load_options() -> dict:
    try:
        return json.loads(OPTIONS_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


OPTIONS = load_options()
SHOW_HIDDEN = bool(OPTIONS.get("show_hidden", False))

app = FastAPI(title="File Editor Pro", docs_url=None, redoc_url=None)

# Mount the bundled third-party assets (xterm.js etc.). HA ingress
# plus a strict CSP means loading from external CDNs isn't reliable,
# so we ship these files with the image and serve them locally.
_VENDOR_DIR = APP_DIR / "vendor"
if _VENDOR_DIR.exists():
    app.mount("/vendor", StaticFiles(directory=str(_VENDOR_DIR)), name="vendor")


# ─────────────────────────────── Paths ────────────────────────────────

def resolve_safe(relpath: str) -> Path:
    """Resolve a client-supplied path to an absolute filesystem path.
    Paths may be prefixed with a root name ("config/foo.yaml",
    "ssl/cert.pem"). Paths without a known root prefix fall back to
    CONFIG_ROOT for backward compatibility."""
    relpath = (relpath or "").lstrip("/\\")
    first, sep, rest = relpath.partition("/")
    if first in ROOTS:
        root = ROOTS[first]
        target = (root / rest).resolve()
    else:
        root = CONFIG_ROOT
        target = (root / relpath).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise HTTPException(400, "Path escapes root directory")
    return target


def build_tree(root: Path, prefix: str = "") -> list[dict]:
    """Walk `root`, returning nodes whose `path` includes `prefix` so
    the client sends us back the same path and we can resolve it."""
    def walk(dirpath: Path, relbase: str) -> list[dict]:
        out: list[dict] = []
        try:
            entries = sorted(
                dirpath.iterdir(),
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except (FileNotFoundError, PermissionError):
            return out
        for p in entries:
            if p.name in SKIP_DIRS:
                continue
            if not SHOW_HIDDEN and p.name.startswith("."):
                continue
            rel = f"{relbase}/{p.name}" if relbase else p.name
            full = f"{prefix}/{rel}" if prefix else rel
            if p.is_dir():
                out.append({
                    "name": p.name,
                    "type": "dir",
                    "path": full,
                    "children": walk(p, rel),
                })
            elif p.is_file():
                out.append({
                    "name": p.name,
                    "type": "file",
                    "path": full,
                    "size": p.stat().st_size,
                })
        return out

    return walk(root, "")


# ──────────────────────────── Index + health ──────────────────────────

@app.get("/")
async def index():
    # Aggressive no-cache: HA ingress + browsers sometimes cache the
    # shell HTML and miss UI updates after an add-on upgrade.
    return FileResponse(
        INDEX_HTML,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "root": str(CONFIG_ROOT),
        "ha_api": bool(SUPERVISOR_TOKEN),
        "git": has_git(),
    }


# ──────────────────────────── File ops ────────────────────────────────

@app.get("/api/roots")
async def list_roots():
    return {"roots": [{"name": name, "path": str(p)} for name, p in ROOTS.items()]}


@app.get("/api/files/tree")
async def tree():
    """Top-level nodes are one per mapped root; children are that
    root's contents. The `path` on every node is root-prefixed so
    all /api/files/* calls resolve unambiguously."""
    nodes = []
    for name, root in ROOTS.items():
        nodes.append({
            "name": name,
            "type": "dir",
            "path": name,
            "children": build_tree(root, prefix=name),
        })
    return {"tree": nodes, "root": str(CONFIG_ROOT), "roots": list(ROOTS.keys())}


@app.get("/api/files/read")
async def read_file(path: str):
    target = resolve_safe(path)
    if not target.is_file():
        raise HTTPException(404, "File not found")
    if target.stat().st_size > MAX_READ_BYTES:
        raise HTTPException(413, "File too large to open in editor")
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(415, "Binary files are not supported")
    return {"path": path, "content": content}


class WriteBody(BaseModel):
    path: str
    content: str


@app.post("/api/files/write")
async def write_file(body: WriteBody):
    target = resolve_safe(body.path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.content, encoding="utf-8")
    return {"ok": True, "path": body.path, "size": target.stat().st_size}


class PathBody(BaseModel):
    path: str


@app.post("/api/files/delete")
async def delete_file(body: PathBody):
    target = resolve_safe(body.path)
    if not target.exists():
        raise HTTPException(404, "Not found")
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    return {"ok": True}


class RenameBody(BaseModel):
    path: str
    new_path: str


@app.post("/api/files/rename")
async def rename_path(body: RenameBody):
    src = resolve_safe(body.path)
    dst = resolve_safe(body.new_path)
    if not src.exists():
        raise HTTPException(404, "Source not found")
    if dst.exists():
        raise HTTPException(409, "Destination already exists")
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return {"ok": True, "path": body.new_path}


@app.post("/api/files/mkdir")
async def mkdir(body: PathBody):
    target = resolve_safe(body.path)
    target.mkdir(parents=True, exist_ok=False)
    return {"ok": True, "path": body.path}


@app.get("/api/files/search")
async def search_files(q: str, max_files: int = 100, max_per_file: int = 10):
    """Cross-file case-insensitive substring search under /config.
    Skips SKIP_DIRS and binary files. Returns matches with surrounding
    line context so the sidebar can highlight them."""
    if not q:
        return {"results": []}
    q_lower = q.lower()
    results = []
    for root_name, root in ROOTS.items():
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            rel_parts = p.relative_to(root).parts
            if any(part in SKIP_DIRS or (part.startswith(".") and not SHOW_HIDDEN)
                   for part in rel_parts):
                continue
            try:
                if p.stat().st_size > MAX_READ_BYTES:
                    continue
            except OSError:
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            matches = []
            for i, line in enumerate(text.splitlines(), 1):
                low = line.lower()
                idx = low.find(q_lower)
                if idx >= 0:
                    matches.append({
                        "line": i,
                        "before": line[:idx],
                        "match":  line[idx:idx + len(q)],
                        "after":  line[idx + len(q):],
                    })
                    if len(matches) >= max_per_file:
                        break
            if matches:
                rel = f"{root_name}/{p.relative_to(root).as_posix()}"
                results.append({"path": rel, "matches": matches})
                if len(results) >= max_files:
                    return {"results": results}
    return {"results": results}


@app.get("/api/files/download")
async def download_file(path: str):
    target = resolve_safe(path)
    if not target.is_file():
        raise HTTPException(404, "File not found")
    mime, _ = mimetypes.guess_type(target.name)
    return FileResponse(target, media_type=mime or "application/octet-stream",
                        filename=target.name)


@app.post("/api/files/upload")
async def upload_file(path: str, file: UploadFile = File(...)):
    # `path` is a directory (relative to /config) to upload into
    dest_dir = resolve_safe(path)
    dest_dir.mkdir(parents=True, exist_ok=True)
    if not dest_dir.is_dir():
        raise HTTPException(400, "Upload path is not a directory")
    target = (dest_dir / Path(file.filename).name).resolve()
    try:
        target.relative_to(CONFIG_ROOT)
    except ValueError:
        raise HTTPException(400, "Upload escapes config directory")
    written = 0
    with target.open("wb") as fp:
        while chunk := await file.read(1024 * 64):
            written += len(chunk)
            if written > MAX_UPLOAD_BYTES:
                fp.close()
                target.unlink(missing_ok=True)
                raise HTTPException(413, "Upload too large")
            fp.write(chunk)
    return {"ok": True, "path": str(target.relative_to(CONFIG_ROOT)), "size": written}


# ──────────────────────────── Git ─────────────────────────────────────

def has_git() -> bool:
    return shutil.which("git") is not None and (CONFIG_ROOT / ".git").is_dir()


# Serialize git operations so two requests from the UI can't race each
# other into .git/index.lock conflicts.
_GIT_LOCK = asyncio.Lock()

# Age above which .git/index.lock is treated as abandoned and removed.
# A real git process rarely holds the lock for more than a couple of
# seconds; keeping a conservative 15 s window means we never step on a
# live operation the add-on launched itself.
_STALE_LOCK_SECS = 15


def _clear_stale_index_lock(cwd: Path = CONFIG_ROOT) -> bool:
    """Remove .git/index.lock if it looks abandoned.

    Returns True if a lock file was actually cleared. The usual cause is
    an earlier git process being killed mid-operation (container stop,
    OOM, etc.), which leaves the lock behind and then blocks every
    subsequent commit with "File exists".
    """
    lock = cwd / ".git" / "index.lock"
    try:
        if not lock.exists():
            return False
        age = time.time() - lock.stat().st_mtime
        if age >= _STALE_LOCK_SECS:
            lock.unlink(missing_ok=True)
            return True
    except OSError:
        pass
    return False


async def run_git(*args: str, cwd: Path = CONFIG_ROOT) -> tuple[int, str, str]:
    async with _GIT_LOCK:
        # Best-effort: if a prior run crashed and left a stale lock,
        # clear it so the next command isn't permanently broken.
        _clear_stale_index_lock(cwd)
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        out, err = await proc.communicate()
        return proc.returncode or 0, out.decode(errors="replace"), err.decode(errors="replace")


@app.get("/api/git/status")
async def git_status():
    if not has_git():
        return {"repo": False, "changes": [], "branch": None}
    code, out, _ = await run_git("status", "--porcelain=v1", "-b")
    if code != 0:
        return {"repo": False, "changes": [], "branch": None}
    lines = out.splitlines()
    branch = None
    changes = []
    for ln in lines:
        if ln.startswith("## "):
            branch = ln[3:].split("...")[0]
            continue
        if len(ln) < 3:
            continue
        xy = ln[:2]
        path = ln[3:]
        status = "M"
        if "A" in xy or xy.strip() == "A":
            status = "A"
        elif "D" in xy:
            status = "D"
        elif "?" in xy:
            status = "U"
        elif "M" in xy:
            status = "M"
        # Prefix with the root name so frontend keys match
        # (tree uses root-prefixed paths like "config/…").
        changes.append({"path": f"config/{path}", "status": status, "xy": xy})
    return {"repo": True, "branch": branch, "changes": changes}


def _strip_config_prefix(p: str) -> str:
    """Strip leading 'config/' from a path so it matches a git-repo-
    relative path (our repo is /config)."""
    if p.startswith("config/"):
        return p[len("config/"):]
    return p


@app.get("/api/git/diff")
async def git_diff(path: str | None = None):
    if not has_git():
        raise HTTPException(400, "Not a git repository")
    args = ["diff", "--no-color"]
    if path:
        args += ["--", _strip_config_prefix(path)]
    code, out, err = await run_git(*args)
    return {"ok": code == 0, "diff": out, "error": err}


class CommitBody(BaseModel):
    message: str
    paths: list[str] | None = None


@app.post("/api/git/commit")
async def git_commit(body: CommitBody):
    if not has_git():
        raise HTTPException(400, "Not a git repository")
    if not body.message.strip():
        raise HTTPException(400, "Commit message required")

    name = OPTIONS.get("git_user_name") or ""
    email = OPTIONS.get("git_user_email") or ""
    if name:
        await run_git("config", "user.name", name)
    if email:
        await run_git("config", "user.email", email)

    if body.paths:
        # Strip the "config/" prefix the frontend uses; git works
        # relative to CONFIG_ROOT so it needs plain paths.
        gp = [_strip_config_prefix(p) for p in body.paths]
        code, _, err = await run_git("add", "--", *gp)
    else:
        code, _, err = await run_git("add", "-A")
    if code != 0:
        _raise_git_error("git add", err)

    # Commit only the specified paths when given — otherwise commit
    # everything that was just staged.
    if body.paths:
        gp = [_strip_config_prefix(p) for p in body.paths]
        code, out, err = await run_git("commit", "-m", body.message, "--", *gp)
    else:
        code, out, err = await run_git("commit", "-m", body.message)
    if code != 0:
        _raise_git_error("git commit", err or out)
    return {"ok": True, "output": out}


_NESTED_NO_COMMIT_RE = re.compile(r"error:\s*'([^']+)' does not have a commit checked out")
_EMBEDDED_REPO_RE = re.compile(r"adding embedded git repository:\s*(\S+)")


def _raise_git_error(action: str, err: str) -> None:
    """Raise HTTPException with a detail payload the UI can act on.

    For well-known failure patterns we attach structured fields
    (`kind`, and e.g. `nested_repos`) so the frontend can offer a
    one-click recovery instead of just showing stderr. For anything
    else we fall back to a plain string.
    """
    e = (err or "").strip()

    if "index.lock" in e and "File exists" in e:
        raise HTTPException(409, {
            "kind": "stale_lock",
            "message": (f"{action} failed: a stale .git/index.lock is "
                        "blocking git. Click the Source Control header → "
                        "padlock icon to clear it, then retry."),
            "raw": e,
        })

    # Nested git repositories — two variants git may emit:
    # 1) "error: 'path' does not have a commit checked out"  (hard failure)
    # 2) "warning: adding embedded git repository: path"     (would be added as gitlink)
    # If either appears, offer to gitignore them and retry.
    nested = sorted(set(
        _NESTED_NO_COMMIT_RE.findall(e) + _EMBEDDED_REPO_RE.findall(e)
    ))
    if nested:
        raise HTTPException(409, {
            "kind": "nested_repos",
            "message": (f"{action} failed: {len(nested)} nested git "
                        "repositor" + ("y is" if len(nested) == 1 else "ies are") +
                        " blocking the commit. Add "
                        + ("it" if len(nested) == 1 else "them")
                        + " to .gitignore and retry?"),
            "nested_repos": nested,
            "raw": e,
        })

    raise HTTPException(500, f"{action} failed: {e}")


class IgnorePathsBody(BaseModel):
    paths: list[str]


@app.post("/api/git/ignore-paths")
async def git_ignore_paths(body: IgnorePathsBody):
    """Append the given paths to /config/.gitignore as directory rules.

    Also runs `git rm -r --cached` for any that were already tracked, so
    a previous index entry doesn't keep the path showing up as a change.
    Paths are expected to be repo-relative (the frontend strips its
    "config/" prefix before calling).
    """
    if not has_git():
        raise HTTPException(400, "Not a git repository")
    paths = [_strip_config_prefix(p).rstrip("/") for p in body.paths if p.strip()]
    paths = [p for p in paths if p]  # drop empties
    if not paths:
        raise HTTPException(400, "No paths supplied")

    gi = CONFIG_ROOT / ".gitignore"
    existing_lines = gi.read_text().splitlines() if gi.exists() else []
    existing = {ln.strip() for ln in existing_lines}

    added: list[str] = []
    for p in paths:
        rule = f"/{p}/"
        if rule not in existing and p not in existing and f"/{p}" not in existing:
            existing_lines.append(rule)
            added.append(rule)

    if added:
        # Preserve the trailing newline convention.
        text = "\n".join(existing_lines)
        if not text.endswith("\n"):
            text += "\n"
        gi.write_text(text)

    # If any of these paths were already tracked (e.g. as gitlinks from a
    # prior commit), un-track them so the ignore rule actually takes effect.
    removed: list[str] = []
    for p in paths:
        code, _, _ = await run_git("rm", "-r", "--cached", "--ignore-unmatch", "--", p)
        if code == 0:
            removed.append(p)

    return {"ok": True, "added": added, "removed": removed}


@app.post("/api/git/clear-lock")
async def git_clear_lock():
    """Force-remove .git/index.lock regardless of age.

    Exposed so the UI can recover from a fresh lock that the automatic
    15-second window hasn't yet treated as stale. Safe in this add-on
    because git calls are serialized through `_GIT_LOCK` and no other
    process in the container writes to the repo.
    """
    if not has_git():
        raise HTTPException(400, "Not a git repository")
    lock = CONFIG_ROOT / ".git" / "index.lock"
    existed = lock.exists()
    try:
        lock.unlink(missing_ok=True)
    except OSError as e:
        raise HTTPException(500, f"Could not remove lock: {e}")
    return {"ok": True, "cleared": existed}


@app.post("/api/git/push")
async def git_push():
    if not has_git():
        raise HTTPException(400, "Not a git repository")
    code, out, err = await run_git("push")
    if code != 0:
        raise HTTPException(500, err or out)
    return {"ok": True, "output": out or err}


@app.post("/api/git/pull")
async def git_pull():
    if not has_git():
        raise HTTPException(400, "Not a git repository")
    code, out, err = await run_git("pull", "--ff-only")
    if code != 0:
        raise HTTPException(500, err or out)
    return {"ok": True, "output": out}


@app.get("/api/git/show")
async def git_show(path: str, ref: str = "HEAD"):
    """Return `git show ref:path` so the frontend can diff it."""
    if not has_git():
        raise HTTPException(400, "Not a git repository")
    # Paths may be root-prefixed (e.g. "config/foo.yaml"). Git works
    # relative to CONFIG_ROOT — strip the "config/" prefix if present.
    rel = _strip_config_prefix(path)
    code, out, err = await run_git("show", f"{ref}:{rel}", cwd=CONFIG_ROOT)
    if code != 0:
        return {"ok": False, "error": err.strip() or out.strip()}
    return {"ok": True, "content": out, "ref": ref}


HA_GITIGNORE_TEMPLATE = """\
# ──── Secrets — sensitive by default ────
# Comment these out if you store secrets encrypted and want them in git.
secrets.yaml
*.secrets.yaml
.env
.env.*
*.pem
*.key
known_hosts
ssh_host_*

# ──── Home Assistant runtime state ────
.HA_VERSION
.storage/
.cloud/
deps/
tts/
backups/

# Databases and logs
home-assistant_v2.db
home-assistant_v2.db-shm
home-assistant_v2.db-wal
*.db
*.db-shm
*.db-wal
*.log
*.log.*

# Python caches
__pycache__/
*.pyc
*.pyo

# OS / editor junk
.DS_Store
.vscode/
.idea/
Thumbs.db
"""


def _write_default_gitignore(overwrite: bool = False) -> bool:
    """Create /config/.gitignore with HA-appropriate patterns.
    Returns True if written, False if it already existed and
    overwrite=False."""
    target = CONFIG_ROOT / ".gitignore"
    if target.exists() and not overwrite:
        return False
    target.write_text(HA_GITIGNORE_TEMPLATE, encoding="utf-8")
    return True


class InitBody(BaseModel):
    branch: str = "main"
    seed_gitignore: bool = True   # also drop a sensible .gitignore


@app.post("/api/git/init")
async def git_init(body: InitBody):
    if not shutil.which("git"):
        raise HTTPException(500, "git is not installed")
    code, out, err = await run_git("init", "-b", body.branch)
    if code != 0:
        raise HTTPException(500, err or out)
    gitignore_written = False
    if body.seed_gitignore:
        gitignore_written = _write_default_gitignore(overwrite=False)
    return {"ok": True, "output": out, "gitignore_written": gitignore_written}


@app.post("/api/git/seed-gitignore")
async def git_seed_gitignore(overwrite: bool = False):
    """Drop (or overwrite) /config/.gitignore with the default
    HA-appropriate patterns. Safe to call when no repo exists."""
    written = _write_default_gitignore(overwrite=overwrite)
    return {"ok": True, "written": written,
            "exists_already": not written and (CONFIG_ROOT / ".gitignore").exists()}


class RemoteBody(BaseModel):
    url: str
    name: str = "origin"


@app.post("/api/git/remote-add")
async def git_remote_add(body: RemoteBody):
    if not has_git():
        raise HTTPException(400, "Not a git repository")
    # If the remote already exists, swap its URL instead of erroring.
    code, out, _ = await run_git("remote")
    existing = {line.strip() for line in out.splitlines() if line.strip()}
    if body.name in existing:
        code, out, err = await run_git("remote", "set-url", body.name, body.url)
    else:
        code, out, err = await run_git("remote", "add", body.name, body.url)
    if code != 0:
        raise HTTPException(500, err or out)
    return {"ok": True, "output": out or err}


@app.get("/api/git/remote")
async def git_remote_list():
    if not has_git():
        return {"remotes": []}
    code, out, _ = await run_git("remote", "-v")
    seen = set()
    remotes = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] not in seen:
            seen.add(parts[0])
            remotes.append({"name": parts[0], "url": parts[1]})
    return {"remotes": remotes}


# ──────────────────────────── HA API ──────────────────────────────────

async def ha_call(method: str, path: str, json_body: dict | None = None) -> dict:
    if not SUPERVISOR_TOKEN:
        raise HTTPException(503, "Supervisor token not available — is homeassistant_api enabled?")
    url = f"{HA_API_BASE}{path}"
    headers = {"Authorization": f"Bearer {SUPERVISOR_TOKEN}",
               "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.request(method, url, headers=headers, json=json_body)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, f"HA API error: {r.text}")
    try:
        return r.json() if r.content else {}
    except ValueError:
        return {"raw": r.text}


@app.post("/api/ha/check_config")
async def ha_check_config():
    # Supervisor exposes a dedicated check endpoint that returns structured results
    if not SUPERVISOR_TOKEN:
        raise HTTPException(503, "Supervisor token not available")
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            "http://supervisor/core/api/config/core/check_config",
            headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()


@app.post("/api/ha/restart")
async def ha_restart():
    return await ha_call("POST", "/services/homeassistant/restart")


@app.get("/api/ha/states")
async def ha_states():
    """Slim list of entities for autocomplete: [{entity_id, name, domain}]."""
    if not SUPERVISOR_TOKEN:
        raise HTTPException(503, "Supervisor token not available")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{HA_API_BASE}/states",
            headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    out = []
    for s in r.json():
        eid = s.get("entity_id", "")
        out.append({
            "entity_id": eid,
            "domain": eid.split(".", 1)[0] if "." in eid else "",
            "name": (s.get("attributes") or {}).get("friendly_name") or eid,
        })
    return out


@app.get("/api/ha/services")
async def ha_services():
    """Flatten services to [{domain, service, name, description}] for autocomplete."""
    if not SUPERVISOR_TOKEN:
        raise HTTPException(503, "Supervisor token not available")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{HA_API_BASE}/services",
            headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    out = []
    for domain_obj in r.json():
        domain = domain_obj.get("domain", "")
        services = domain_obj.get("services") or {}
        for svc, meta in services.items():
            out.append({
                "domain": domain,
                "service": svc,
                "full": f"{domain}.{svc}",
                "name": (meta or {}).get("name") or svc,
                "description": (meta or {}).get("description") or "",
            })
    return out


class TemplateBody(BaseModel):
    template: str


@app.post("/api/ha/template")
async def ha_template(body: TemplateBody):
    """Render a Jinja template through HA. Returns {result} or {error}."""
    if not SUPERVISOR_TOKEN:
        raise HTTPException(503, "Supervisor token not available")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{HA_API_BASE}/template",
            headers={
                "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"template": body.template},
        )
    if r.status_code >= 400:
        return {"ok": False, "error": r.text, "status": r.status_code}
    return {"ok": True, "result": r.text}


class ReloadBody(BaseModel):
    domain: str  # automation, script, scene, template, input_* etc.


@app.post("/api/ha/reload")
async def ha_reload(body: ReloadBody):
    allowed = {
        "automation", "script", "scene", "template", "rest", "rest_command",
        "group", "input_boolean", "input_number", "input_select", "input_text",
        "input_datetime", "timer", "homeassistant",
    }
    if body.domain not in allowed:
        raise HTTPException(400, f"Domain '{body.domain}' not supported")
    service = "reload_core_config" if body.domain == "homeassistant" else "reload"
    return await ha_call("POST", f"/services/{body.domain}/{service}")


@app.get("/api/terminal/available")
async def terminal_available():
    """Tell the frontend whether the terminal feature is usable."""
    return {
        "available": _HAS_PTY,
        "error": _PTY_ERROR,
        "shell": os.environ.get("SHELL", "/bin/sh"),
    }


@app.websocket("/api/terminal")
async def terminal_ws(ws: WebSocket):
    """Bidirectional PTY bridge."""
    await ws.accept()
    if not _HAS_PTY:
        await ws.send_json({"type": "output",
            "data": f"PTY support unavailable: {_PTY_ERROR}\r\n"})
        await ws.close()
        return

    shell = os.environ.get("SHELL", "/bin/sh")
    # Prefer bash if available — Alpine ships /bin/ash but /bin/bash
    # is installed in our image. bashio loads there too.
    for candidate in ("/bin/bash", shell, "/bin/ash", "/bin/sh"):
        if os.path.exists(candidate):
            shell = candidate
            break
    try:
        proc = ptyprocess.PtyProcessUnicode.spawn(
            [shell, "-l"], cwd=str(CONFIG_ROOT), dimensions=(24, 80),
            env={**os.environ, "TERM": "xterm-256color"},
        )
    except Exception as e:
        await ws.send_json({"type": "output",
            "data": f"Failed to spawn shell ({shell}): {e}\r\n"})
        await ws.close()
        return
    await ws.send_json({"type": "output", "data": f"\x1b[90m[{shell}] \x1b[0m"})

    loop = asyncio.get_event_loop()

    async def pty_to_ws():
        while proc.isalive():
            try:
                chunk = await loop.run_in_executor(None, proc.read, 4096)
            except (EOFError, OSError):
                break
            if not chunk:
                break
            try:
                await ws.send_json({"type": "output", "data": chunk})
            except Exception:
                break

    reader_task = asyncio.create_task(pty_to_ws())
    try:
        while True:
            msg = await ws.receive_json()
            if msg.get("type") == "input":
                try:
                    proc.write(msg.get("data", ""))
                except OSError:
                    break
            elif msg.get("type") == "resize":
                cols = int(msg.get("cols", 80))
                rows = int(msg.get("rows", 24))
                try:
                    proc.setwinsize(rows, cols)
                except Exception:
                    pass
    except WebSocketDisconnect:
        pass
    finally:
        reader_task.cancel()
        try:
            proc.terminate(force=True)
        except Exception:
            pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
