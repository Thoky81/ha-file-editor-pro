import asyncio
import json
import mimetypes
import os
import shutil
import subprocess
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

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
    return FileResponse(INDEX_HTML)


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


async def run_git(*args: str, cwd: Path = CONFIG_ROOT) -> tuple[int, str, str]:
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
        changes.append({"path": path, "status": status, "xy": xy})
    return {"repo": True, "branch": branch, "changes": changes}


@app.get("/api/git/diff")
async def git_diff(path: str | None = None):
    if not has_git():
        raise HTTPException(400, "Not a git repository")
    args = ["diff", "--no-color"]
    if path:
        args += ["--", path]
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
        code, _, err = await run_git("add", "--", *body.paths)
    else:
        code, _, err = await run_git("add", "-A")
    if code != 0:
        raise HTTPException(500, f"git add failed: {err}")

    code, out, err = await run_git("commit", "-m", body.message)
    if code != 0:
        raise HTTPException(500, f"git commit failed: {err or out}")
    return {"ok": True, "output": out}


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
    rel = path
    if rel.startswith("config/"):
        rel = rel[len("config/"):]
    code, out, err = await run_git("show", f"{ref}:{rel}", cwd=CONFIG_ROOT)
    if code != 0:
        return {"ok": False, "error": err.strip() or out.strip()}
    return {"ok": True, "content": out, "ref": ref}


class InitBody(BaseModel):
    branch: str = "main"


@app.post("/api/git/init")
async def git_init(body: InitBody):
    if not shutil.which("git"):
        raise HTTPException(500, "git is not installed")
    code, out, err = await run_git("init", "-b", body.branch)
    if code != 0:
        raise HTTPException(500, err or out)
    return {"ok": True, "output": out}


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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
