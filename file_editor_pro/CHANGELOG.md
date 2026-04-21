# Changelog

## 1.2.0 — Sprint 2: the differentiator

- **HA-aware autocomplete**: entity IDs and service names complete as you type. Auto-triggers after `service:` / `entity_id:` and when typing a domain-prefixed identifier; Ctrl+Space anywhere to force. Cache pulled from `/api/states` and `/api/services` on load, refreshable via command palette.
- **Command palette** (Ctrl+Shift+P): fuzzy-filter across file ops, view panels, git, HA actions, snippets, and every open file.
- **YAML snippets**: Automation, Script, Template Sensor, Template Binary Sensor, REST Sensor, input_boolean, and trigger/condition/action blocks — insert at cursor from the palette.
- **Jinja template preview** (Ctrl+Alt+J): split-pane modal that renders via HA's `/api/template`. Ctrl+Enter to render, seeds from the current editor selection.
- Backend: new `/api/ha/states`, `/api/ha/services`, `/api/ha/template` endpoints.

## 1.1.0 — Sprint 1: parity with File Editor

- **Real git integration**: status, diff, commit, pull, push via backend subprocess. Sidebar git panel now reflects the real `/config` repo; file tree shows live M/A/U/D badges.
- **Upload / download**: drag-and-drop upload button in the explorer header; right-click → Download on any file.
- **Tree context menu**: right-click any item for Rename, Duplicate, New File, New Folder, Upload, Download, Delete.
- **HA actions in the status bar**: Check Config, Restart HA, and a Reload menu (core config / automations / scripts / scenes / templates / groups).
- **Config check** surfaces invalid configuration via toast + console.
- **Add-on options**: `git_user_name`, `git_user_email`, `show_hidden`.
- **Permissions**: `homeassistant_api: true`, `ssl:ro` mount for SSH keys.
- Backend: `git`, `openssh-client` baked into the image; `httpx` + `python-multipart` added.

## 1.0.0

- Initial release.
- Multi-tab CodeMirror editor with YAML / Python / JSON highlighting.
- FastAPI backend with read / write / delete scoped to `/config`.
- Ingress-enabled sidebar panel.
