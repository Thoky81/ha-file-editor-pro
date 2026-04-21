# Changelog

## 1.3.1 — Whitespace dots on by default + sidebar icon match

- **Whitespace rendering now defaults to ON** so spaces show as `·` and tabs as `→`, matching the look of the original HA File Editor out of the box. Still toggleable in Settings → Appearance → Show whitespace.
- Rendering fix: each whitespace span is now an `inline-block` so the pseudo-element reliably centers over the character, fixing a flaky-layout case on some browsers.
- **Sidebar icon** changed from `mdi:file-code` to `mdi:format-list-bulleted` to visually match the add-on's YAML-list logo mark. (HA only accepts MDI icon names for `panel_icon`, not PNG files — `icon.png` is still used for the store tile.)

## 1.3.0 — Themes, Settings, FAB, visible save

- **Settings modal** (gear in the status bar). Groups: Appearance (theme, font size, indent guides, whitespace), Editor (tab size, indent style, line wrapping). All preferences persist in `localStorage`.
- **Eight themes** shipped. Default is now **GitHub Light**. Picker groups Light / Dark:
  - Light: GitHub Light, HA Light, Solarized Light, HA Cream, Nord Light
  - Dark: HA Soft, HA Muted, HA Dark (original)
  - Available via the Settings modal or the command palette under `Theme:`.
- **Editor font size** (10–22 px) with a slider + numeric input in Settings; `View: Font size:` shortcuts in the palette.
- **Visible Save button** in the tab-bar action area, with a highlighted amber state when the active file has unsaved changes (`Save*`).
- **Pencil FAB** at bottom-right of the editor with a menu: undo / redo / toggle comment / indent / outdent / fold (at cursor / all / unfold all) / find / replace.
- **Visible whitespace** option (dots for spaces, arrows for tabs) — matches the original HA File Editor's look.
- **Indent guides default OFF** per user feedback; when on, they're now subtler and tint-aware via the theme's muted color.
- All CSS colors reference a single set of per-theme variables (`--bg-*`, `--text-*`, `--accent*`, `--syn-*`). CodeMirror tokens use `--syn-*` so syntax highlighting re-theme instantly.
- Early theme apply: reads the saved theme from `localStorage` before the editor mounts to avoid a flash of the default theme.

## 1.2.2 — Store-ready branding & docs

- **Icon and logo** — amber YAML-list mark (`icon.png`, `logo.png`) applied across the add-on store tile, sidebar panel, and info tab.
- **`DOCS.md`** — full Documentation tab content in the store: install steps, every feature, keyboard shortcuts, configuration reference, permissions explainer, troubleshooting.

## 1.2.1 — Indent guides & editor prefs

- **Indent guides** in the editor (faint vertical lines at each indent level), toggleable from the command palette.
- **Configurable tab size** (2 / 4 / 8) and **indent style** (spaces / tabs), accessible via the command palette under `View:`.
- Preferences persist in `localStorage` and apply across all open tabs.

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
