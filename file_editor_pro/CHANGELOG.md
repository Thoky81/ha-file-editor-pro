# Changelog

## 1.7.0 — Multi-root access, Outline panel, Quick open

- **Multi-root access**: the editor now exposes `/config`, `/ssl`, `/share`, `/addons`, `/media`, `/backup` as browsable top-level folders in the file tree (when HA has mounted them — `/ssl` and `/backup` are read-only). The backend walks a `ROOTS` dict, API paths are root-prefixed (e.g. `ssl/cert.pem`), and unknown prefixes fall back to `/config` for backward compatibility. Cross-file search also spans all roots.
- **Outline panel** (new sidebar activity-bar entry, three-bullet icon): lists top-level keys and notable list items (YAML entries with `alias`/`name`/`id`/`platform`/`service`) from the active document. Click any entry to jump the cursor to that line. Refreshes automatically as you edit (debounced).
- **Quick open** (`Ctrl+P`): a fuzzy file picker that searches every file in the tree. Under the hood it opens the command palette pre-filtered to `Open ` entries, so every file (not just the ones currently loaded) is reachable with a few keystrokes.

## 1.6.0 — Insert panel, Explorer filter, backend cross-file search

- **Insert panel** (new activity-bar entry, lightning icon). Tabs for **Entities · Services · Triggers · Conditions · Events**, each with a filter search. Entities and services draw from the same live `/api/ha/states` and `/api/ha/services` cache used by autocomplete. Click an item → a ready-made YAML snippet inserts at the cursor. Triggers include state / numeric_state / time / time_pattern / sun / template / event / zone / webhook / device / homeassistant / mqtt; Conditions include state / numeric_state / time / template / and / or / not / trigger / sun / zone / device.
- **Explorer inline filter**: a "Filter files…" input at the top of the tree filters by filename in real time, auto-expanding parent directories whose descendants match. No need to switch to the Search tab for a simple name lookup.
- **Cross-file search now hits the backend**: `/api/files/search?q=` endpoint walks `/config` server-side and returns matches with surrounding line context. Live results now work for files that haven't been opened (previously the panel only searched the in-memory cache, so fresh installs showed no results until a file was opened). Falls back to the local cache when the backend isn't available.

## 1.5.3 — Resizable sidebar, close-confirm, Settings gear, continuous rainbow bands

- **Drag-resizable sidebar**: grab the right edge to resize between 180 and 600 px, double-click to reset to 260 px. Width persists in `localStorage`.
- **Unsaved-changes close dialog**: closing a modified tab now opens a three-button confirm — Save / Don't save / Cancel — instead of discarding silently. Save saves the file first, then closes.
- **Settings modal gear icon** matches the sidebar gear (same 6-tooth cog — was still the old 8-spoke icon).
- **Rainbow bands now fill the row vertically**: marker spans switched to `inline-block` with full line-height so the colored backgrounds connect across rows with no white gaps between lines, matching the VS Code Indent Rainbow look.

## 1.5.2 — Indent transparency actually works, dots under colored styles, rainbow + guides

- **Indent style transparency** now works. Two fixes:
  - The `[class^="cm-ir-"]` opacity selector didn't match spans that also carried `cm-ws-space` (dots), because `^=` only looks at the first class in the attribute. Dropped the blanket-opacity approach in favour of multiplying each marker's alpha directly via `calc(base * var(--indent-opacity))`, which scales cleanly and leaves the dots untouched.
  - Background rules for rainbow / gradient switched from `background:` (shorthand) to `background-color:` so the whitespace-dot `background-image` layer paints on top. **Dots now remain visible under rainbow, gradient, and bars.**
- **Rainbow + grey guide lines** combined: the Indent rainbow style now also draws the faint vertical guide lines at each tab stop, matching the look of the VS Code Indent Rainbow extension.
- Removed a duplicate `.indent-guides` CSS rule that was still using the old 45% alpha.

## 1.5.1 — Theme toggle, proper gear, default light/dark, indent opacity, sidebar font size

- **Sidebar gear** now uses a proper 6-tooth cog icon.
- **Theme toggle** button added above the gear — click to swap between your default light and default dark themes. Icon flips between sun (currently dark) and moon (currently light).
- **Default light theme** and **Default dark theme** added to Settings — pick which themes the sun/moon toggle swaps to. Defaults: GitHub Light and HA Dark.
- **Indent style transparency** — 0–150 % slider under Indent style; multiplies opacity of all level markers (guides, rainbow, bars, gradient).
- **Sidebar font size** — independent 10–18 px slider for the file-tree font; the editor font size stays in its own control.

## 1.5.0 — Indent-style picker, sidebar Settings button, softer guides

- **Indent style** pref consolidated into a single dropdown with 5 options:
  - **None** — plain (no level markers)
  - **Indent guides** — faint vertical lines at each tab stop
  - **Indent rainbow** — tint per level, cycles 6 colors
  - **Colored level bars** — 2 px solid colored bars per indent step
  - **Gradient ramp** — accent tint deepens progressively per level
  Selectable in Settings → Appearance → Indent style, or via `Indent:` entries in the command palette.
- **Sidebar Settings button** (the gear at the bottom of the activity bar) was hardcoded as disabled in the original design. Wired to `openSettings()` and enabled.
- **Indent-guides lines** softened from 45 % → 20 % of `--text-muted` so they read as hints, not strokes.
- Migration: old `indentGuides` / `indentRainbow` bools in `localStorage` are mapped onto the new `indentStyle` pref automatically.

## 1.4.0 — Indent rainbow, open-file highlight, mark-only logo

- **Indent rainbow** (opt-in): each indent level tinted with a different faint background color, cycling on `level % 6`. Toggle in Settings → Appearance or via the command palette.
- **Open files highlighted in the tree**: any file currently open in a tab gets its name rendered in a brighter weight plus a small accent dot next to it. The active tab still gets the full highlighted background + accent edge. Tree re-renders automatically on open/close/switch.
- **Info-page banner** (`logo.png`): removed the wordmark so the HA add-on Info tab shows just the logo mark on a dark tile, with no repeated "File Editor Pro" text.

## 1.3.8 — Defensive Settings, crisper gear icon

- `openSettings()` now shows the modal *first* and wraps the inner setup (`buildSettingsUI` / `refreshSettingsUI`) in try/catch, so an error in one of them can't silently prevent the modal from appearing. Errors are logged to the browser console for diagnosis.
- Swapped the Feather-style compound-path gear for a simple 8-spoke gear SVG. Renders crisper at the 12 × 12 size used in the status bar.

## 1.3.7 — HA-aware YAML validation + inline error markers

- **HA YAML tags recognised**: `!include`, `!include_dir_list`, `!include_dir_merge_list`, `!include_dir_named`, `!include_dir_merge_named`, `!secret`, `!env_var`, `!input` now parse without error. Previously every `configuration.yaml` showed a spurious "YAML Error" because `js-yaml` doesn't know those tags by default.
- **Inline error markers**: CodeMirror's lint addon is wired, so a real syntax error now shows a red marker in the gutter at the failing line; hover it for the parser's message.
- **Status bar shows the error message**: the YAML indicator now reads `Line 47: mapping values are not allowed here` instead of just "YAML Error". Click it to jump to the bad line.
- Whitespace dot intensity raised from 15% → 25%.

## 1.3.6 — Restore dark icon and logo

- Reverted `icon.png` and `logo.png` to the original dark ha-palette look (navy tile, amber dashes, light-grey rows) while keeping the 320 px-wide logo canvas from 1.3.4 so the "Pro" wordmark still fits on HA's Info tab.

## 1.3.5 — Softer indent dots

- Whitespace dots toned down from 55 % → 15 % of `--text-muted` so they sit quietly in the background and read as faint guides instead of strokes of their own. Same intensity applied to the tab arrow.

## 1.3.4 — Whitespace dots only on indentation + lighter icon/logo

- Whitespace dots now render for **leading whitespace only** (indentation). Inline spaces between tokens — for example the mandatory space after a YAML list dash in `- value` — are no longer dotted, so the indent count stays easy to read without visual noise in the content area.
- **icon.png** repainted on a light background with a subtle 1 px border so it sits cleanly on the add-on store Info tab.
- **logo.png** widened (250 → 320 px) with a smaller wordmark so "Pro" is no longer cropped when HA scales the banner.

## 1.3.3 — One dot per space

- Whitespace indicator now paints **one dot per space**. The editor overlay merges consecutive space tokens into one `span`, so a pseudo-element `::before` was rendering the dot only once per run. Switched to a tiled background (radial-gradient, `background-size: 1ch 1em`) that repeats one dot for every 1ch of span width, independent of how many characters the span wraps. Tabs use a similar 4px background tile for the arrow.

## 1.3.2 — Status bar readability, centered whitespace dots, window title

- **Status bar readability**: fixed a CSS regression where all status-bar text (Check Config, Restart HA, Settings, Reload, Ln/Col, UTF-8, theme env) rendered with a hardcoded dark color that looked disabled on light themes. Now uses the theme's `--status-text` variable, so text is always high-contrast against the bar.
- **Whitespace dots** are now vertically centered in the line box (previously sat near the baseline) and rendered in a lighter grey so they guide the eye without fighting the content.
- **Browser tab title** updated to "File Editor Pro".

## 1.3.1 — Whitespace dots on by default + sidebar icon match

- **Whitespace rendering now defaults to ON** so spaces show as `·` and tabs as `→`. Still toggleable in Settings → Appearance → Show whitespace.
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
- **Visible whitespace** option (dots for spaces, arrows for tabs).
- **Indent guides default OFF**; when on, they're now subtler and tint-aware via the theme's muted color.
- All CSS colors reference a single set of per-theme variables (`--bg-*`, `--text-*`, `--accent*`, `--syn-*`). CodeMirror tokens use `--syn-*` so syntax highlighting re-themes instantly.
- Early theme apply: reads the saved theme from `localStorage` before the editor mounts to avoid a flash of the default theme.

## 1.2.2 — Store-ready branding & docs

- **Icon and logo** — amber YAML-list mark (`icon.png`, `logo.png`) applied across the add-on store tile, sidebar panel, and info tab.
- **`DOCS.md`** — full Documentation tab content in the store: install steps, every feature, keyboard shortcuts, configuration reference, permissions explainer, troubleshooting.

## 1.2.1 — Indent guides & editor prefs

- **Indent guides** in the editor (faint vertical lines at each indent level), toggleable from the command palette.
- **Configurable tab size** (2 / 4 / 8) and **indent style** (spaces / tabs), accessible via the command palette under `View:`.
- Preferences persist in `localStorage` and apply across all open tabs.

## 1.2.0 — Autocomplete, command palette, snippets, Jinja preview

- **HA-aware autocomplete**: entity IDs and service names complete as you type. Auto-triggers after `service:` / `entity_id:` and when typing a domain-prefixed identifier; Ctrl+Space anywhere to force. Cache pulled from `/api/states` and `/api/services` on load, refreshable via command palette.
- **Command palette** (Ctrl+Shift+P): fuzzy-filter across file ops, view panels, git, HA actions, snippets, and every open file.
- **YAML snippets**: Automation, Script, Template Sensor, Template Binary Sensor, REST Sensor, input_boolean, and trigger/condition/action blocks — insert at cursor from the palette.
- **Jinja template preview** (Ctrl+Alt+J): split-pane modal that renders via HA's `/api/template`. Ctrl+Enter to render, seeds from the current editor selection.
- Backend: new `/api/ha/states`, `/api/ha/services`, `/api/ha/template` endpoints.

## 1.1.0 — Git, uploads, HA actions, tree ops

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
