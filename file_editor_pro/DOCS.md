# File Editor Pro — Documentation

A modern, multi-tab editor for your Home Assistant configuration, served via Ingress.

---

## Installation

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**.
2. Click the **⋮** menu (top-right) → **Repositories**.
3. Add `https://github.com/Thoky81/ha-file-editor-pro` and click **Add**.
4. Scroll to the bottom of the store; you'll see **Thoky's Home Assistant Add-ons**. Install **File Editor Pro**.
5. Start the add-on. The sidebar panel appears automatically (Ingress is enabled).

---

## Features

### Editor
- Multi-tab editing with per-tab undo history
- Syntax highlighting for **YAML**, **Python**, **JSON**
- Fold gutters (collapse any YAML block)
- **Indent guides** at every tab stop (toggleable)
- Configurable **tab size** (2 / 4 / 8) and **indent style** (spaces or tabs)
- Preferences persisted in `localStorage`
- Find & replace (`Ctrl+F` / `Ctrl+H`), toggle comment (`Ctrl+/`)
- Live **YAML validation** on every keystroke via `js-yaml`
- Cross-file search across everything open
- Breadcrumb trail + right-click context menu

### HA-aware autocompletion
- Completes **entity IDs** as you type — triggered after a domain-prefixed identifier (`light.` → your lights) or after `entity_id:` / `service:`
- Completes **service calls** (`light.turn_on`, `notify.persistent_notification`, …) with their descriptions
- Cache is loaded on startup from `/api/states` + `/api/services`; press `Ctrl+Space` to force hints anywhere
- Refresh the cache via the command palette after adding new integrations

### Command palette — `Ctrl+Shift+P`
Fuzzy-search across every command in the app:
- File ops (save, new file / folder, upload, refresh)
- View switches (explorer / search / git)
- Editor preferences (tab size, indent style, indent guides)
- Git (pull, push, commit)
- HA actions (check config, restart, reload automations / scripts / scenes / templates / groups)
- Snippets (insert YAML skeletons at cursor)
- Every file currently in the tree

### YAML snippets
Available from the command palette — `Snippet: Insert…`:
- Automation skeleton
- Script skeleton
- Template Sensor / Template Binary Sensor
- REST Sensor
- `input_boolean`
- Trigger blocks: time, state, numeric_state
- Condition block: time
- Action blocks: notify, service call

### Source control
- Real **git integration** against `/config/.git` — backend uses `git` subprocess
- Sidebar **Source Control** panel: branch name, change list, Pull / Push buttons
- **M / A / U / D** badges in the file tree
- Commit via panel or `Git: Commit` command
- Commit author configurable per add-on option

### File management
- **Upload** from the Explorer header or via right-click → Upload File
- **Download** any file via right-click → Download
- **Rename**, **Duplicate**, **Delete** from the tree context menu
- **New File…** / **New Folder…** relative to `/config`

### HA integration
- **Check Config** button in the status bar — calls `/config/core/check_config`
- **Restart HA** — with confirmation
- **Reload** menu — core config, automations, scripts, scenes, templates, groups, input helpers
- **Jinja template preview** (`Ctrl+Alt+J`) — split-pane modal rendering templates via `/api/template`. Seeds from editor selection; `Ctrl+Enter` renders.

---

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+S` | Save current file |
| `Ctrl+F` / `Ctrl+H` | Find / Find & Replace |
| `Ctrl+/` | Toggle line comment |
| `Ctrl+Space` | Trigger autocomplete |
| `Ctrl+Shift+P` | Command palette |
| `Ctrl+Shift+E` | Show Explorer |
| `Ctrl+Shift+F` | Show Search |
| `Ctrl+Alt+J` | Jinja template preview |
| `Ctrl+Enter` (in commit box) | Commit |

---

## Configuration

All options are editable from the **Configuration** tab in the add-on UI.

| Option | Type | Default | Description |
|---|---|---|---|
| `git_user_name` | string | `""` | Name used for git commits made from the editor. |
| `git_user_email` | string | `""` | Email used for git commits made from the editor. |
| `show_hidden` | bool | `false` | Show hidden files (those starting with `.`) in the file tree. |

### Git SSH keys

To push over SSH, drop your private key in `/ssl/` on the host (mounted read-only into the container at `/ssl/`). Then configure your git remote to use SSH. HTTPS remotes with a token work out of the box.

---

## Permissions & what the add-on accesses

- **`/config` read-write** — full file browser, edit and upload files into your HA config.
- **`/ssl` read-only** — to read SSH keys for git push.
- **`homeassistant_api: true`** — enables the Supervisor-issued token for `/api/states`, `/api/services`, `/api/template`, and the `homeassistant.restart` + `*.reload` service calls.
- **Ingress enabled** — the UI is only reachable through the HA sidebar, never exposed on a random port.

File access is strictly scoped to `/config`; paths containing `..` or leading slashes are rejected by the backend.

---

## Troubleshooting

**Autocomplete is empty.** Open the command palette and run *HA: Refresh entity/service cache*. If still empty, check the add-on log: the likely cause is `homeassistant_api` not being granted (it is by default; nothing to configure).

**`Check Config` says "Supervisor token not available".** Make sure the add-on was restarted after installation so the Supervisor token is injected into the environment.

**Git push fails with an auth error.** For HTTPS, embed a personal access token in the remote URL (`https://<token>@github.com/user/repo.git`). For SSH, drop your private key under `/ssl/` — the container will pick it up from `/ssl/`.

**Tree shows no files.** Refresh the tree (button in the Explorer header). If it's still empty, check the log for a path-resolution error — this typically means `/config` isn't mapped, which shouldn't happen with the default add-on config.

**Changes don't persist after restart.** The add-on writes directly to `/config` — if saves succeed (toast appears) but files revert, you're probably editing files that are rewritten by HA itself (for example, `.storage/*` files). Avoid editing anything under `.storage`.

---

## Reporting issues

Open an issue at https://github.com/Thoky81/ha-file-editor-pro/issues. Include:
- Add-on version (shown on the Info tab)
- A snippet of the log (Log tab) around the time of the problem
- What you were doing when it broke
