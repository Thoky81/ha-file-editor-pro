# File Editor Pro

A modern, multi-tab editor for your Home Assistant configuration.

## Features

- **Multi-tab editing** — open as many files as you like; each tab keeps its own undo history
- **Syntax highlighting** for YAML, Python and JSON with a custom dark palette
- **Fold gutters** — collapse any YAML block
- **Find & replace** (`Ctrl+F` / `Ctrl+H`), **toggle comment** (`Ctrl+/`), **save** (`Ctrl+S`)
- **Cross-file search** across everything you have open
- **Git-style status badges** (M/A/U/D) in the sidebar and a commit panel
- **Live YAML validation** via js-yaml — status bar shows Valid / Error as you type
- **Breadcrumb trail** of the current file path
- **Right-click context menu** with cut/copy/paste/find/replace/save

## Installation

Install via the repository URL — see the [repo README](../README.md).

## Configuration

No options required. The add-on exposes a web UI via **Ingress** and operates on `/config` directly.

## Architecture

- Frontend: single-page HTML using CodeMirror 5
- Backend: FastAPI (Python 3) providing `/api/files/tree`, `/api/files/read`, `/api/files/write`, `/api/files/delete`
- All file operations are scoped to `/config` with path-escape protection

## Development

```bash
cd file_editor_pro
pip install -r requirements.txt
CONFIG_DIR=/path/to/test/config PORT=8099 python3 server.py
# → http://localhost:8099
```

When the backend is not reachable the frontend falls back to built-in demo data, so the HTML is also usable standalone for UI work.
