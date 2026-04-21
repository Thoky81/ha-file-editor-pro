import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

CONFIG_ROOT = Path(os.environ.get("CONFIG_DIR", "/config")).resolve()
APP_DIR = Path(__file__).parent
INDEX_HTML = APP_DIR / "index.html"
PORT = int(os.environ.get("PORT", "8099"))

SKIP_DIRS = {".git", ".storage", "__pycache__", "node_modules", ".cloud"}
MAX_READ_BYTES = 2 * 1024 * 1024

app = FastAPI(title="File Editor Pro", docs_url=None, redoc_url=None)


def resolve_safe(relpath: str) -> Path:
    relpath = (relpath or "").lstrip("/\\")
    target = (CONFIG_ROOT / relpath).resolve()
    try:
        target.relative_to(CONFIG_ROOT)
    except ValueError:
        raise HTTPException(400, "Path escapes config directory")
    return target


def build_tree(root: Path) -> list[dict]:
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
            rel = f"{relbase}/{p.name}" if relbase else p.name
            if p.is_dir():
                out.append({
                    "name": p.name,
                    "type": "dir",
                    "path": rel,
                    "children": walk(p, rel),
                })
            elif p.is_file():
                out.append({
                    "name": p.name,
                    "type": "file",
                    "path": rel,
                    "size": p.stat().st_size,
                })
        return out

    return walk(root, "")


@app.get("/")
async def index():
    return FileResponse(INDEX_HTML)


@app.get("/api/health")
async def health():
    return {"ok": True, "root": str(CONFIG_ROOT)}


@app.get("/api/files/tree")
async def tree():
    return {"root": str(CONFIG_ROOT), "tree": build_tree(CONFIG_ROOT)}


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
        raise HTTPException(400, "Refusing to delete directories")
    target.unlink()
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
