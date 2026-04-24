# Changelog

## 1.10.4 — Visible collapse button, context-aware new file/folder, folder drill-down

- **Hide sidebar button** added to the Explorer header (right-most chevrons icon, next to Collapse All). Complements the existing Ctrl+B shortcut so users who don't know the shortcut can still hide it.
- **New file / New folder now use a real target directory.** Order of preference: right-click target → currently focused tree folder → directory of the active tab → root. The prompt also tells you which directory the new item will land in, so it's not ambiguous.
- **Folder drill-down (focus mode).** Double-click any directory in the tree (or right-click → *Focus here*) to view just that folder's contents. A small breadcrumb appears at the top of the tree (`↑ Root  ›  packages  ›  …`) — click any part to navigate back up. Single-click still expands/collapses as before; the drill-down is purely opt-in.

## 1.10.3 — Split view: equal panes and right-pane minimap

- **Even split.** `.editor-right` changed from `width: 50%` (half the viewport) to `flex: 1`, so the two editor panes divide only the space left over after the activity bar and sidebar. Panes are now visually the same width.
- **Minimap in the right pane.** Minimap code refactored to loop over a `_minimapPanes()` list so every open CodeMirror instance gets its own minimap when the setting is on. Scroll + content changes on the right pane now update its viewport box as well.

## 1.10.2 — No-cache headers on index.html

- The root HTML response now carries `Cache-Control: no-store, no-cache, must-revalidate` + `Pragma: no-cache` + `Expires: 0`. Fixes the case where the add-on upgrades but the user keeps seeing the previous build — e.g. a new tree-context-menu entry that didn't show up because HA ingress or the browser cached the older `index.html`.

## 1.10.1 — Jinja validator, defensive bracket toggle, bluer blue

- **Jinja template validator.** Every `{{…}}` and `{%…%}` expression in the active YAML file is extracted, deduplicated, and validated via HA's `/api/template` endpoint. Errors surface as red markers in the gutter alongside YAML parse errors; status bar shows the count when YAML is otherwise valid. Debounced 1500 ms per edit; aborts in-flight requests when you keep typing. Manual trigger: command palette → *HA: Validate Jinja in current file*.
- **Rainbow brackets toggle** now always updates its visual state. Previous failure mode: the onclick's second statement (`refreshSettingsUI()`) was skipped when the first one's inner `addOverlay` threw. Moved the toggle-class update into `toggleBracketColors()` itself and wrapped the overlay work in try/catch so the pref, the toast, and the UI toggle always stay in sync regardless of what CodeMirror does.
- **Unquoted-value blue** in GitHub Light brightened from `#1e5b8a` → `#2c6ba0` — a touch less slate, a touch more "proper blue".

## 1.10.0 — Hide sidebar, split view, status-bar polish, YAML colors

- **Hide sidebar** — `Ctrl+B` (or `View: Toggle Sidebar` in the command palette) collapses the whole sidebar panel to 0 px. Activity bar stays visible, so clicking any icon (Explorer, Search, Git, …) reopens it. Preference persists.
- **Split view** — right-click any file → *Open to the right*, or use the command palette *File: Open active file to the right*. Opens a second CodeMirror pane alongside the main editor, showing one file at a time. Ctrl+S in the right pane saves through to disk. Close with the × on its header.
- **Status bar** — horizontal padding bumped so text no longer clips on rounded browser corners; on narrow viewports (< 760 px / mobile) the bar now wraps to multiple rows instead of overflowing.
- **GitHub Light YAML colors** rebalanced. Keys and strings are now dark red, unquoted values (`parallel`, `event`, `state_changed`) are blue, and dotted identifiers stay near-black — matching the density and readability of the reference palette the user shared.

## 1.9.8 — No indent markers on comment lines

- Rainbow, gradient, colored-bars and indent-guides overlays now skip lines whose first non-whitespace character is `#`. Comments render clean with just their own color — no background tint, no vertical guide, no bar.

## 1.9.7 — Sidebar resizer no longer overlaps terminal + nano available

- Sidebar resize handle no longer shows a vertical line through the terminal panel when it's open. Root cause: the terminal panel had `z-index:40` and the resizer had `z-index:50`, so the resizer rendered on top. Terminal panel lifted to `z-index:60`.
- **`nano`** added to the add-on image, so you can run `nano somefile.yaml` inside the integrated terminal.

## 1.9.6 — Greener comments in GitHub Light

- `--syn-comment` switched from olive `#6a7c3a` to `#236e25`. Deeper, more saturated green; italic styling unchanged.

## 1.9.5 — Olive comments in GitHub Light

- GitHub Light's `--syn-comment` nudged from gray `#59636e` to olive `#6a7c3a`. Comments remain italic.

## 1.9.4 — Revert the "classic" theme

- Removed the "classic" theme added in 1.9.2. Theme selector is back to the eight originally shipped themes.

## 1.9.3 — Terminal fixed (bundled xterm), defensive settings refresh

- **Terminal was crashing with `ReferenceError: Can't find variable: Terminal`** because the xterm.js CDN URLs I used (cdnjs) 404'd, so the global never loaded. Bundled `xterm.min.js`, `xterm.min.css`, and `xterm-addon-fit.min.js` into `file_editor_pro/vendor/` and served them as static files from the FastAPI backend. CDN dependency removed; terminal now works in ingress with strict CSP.
- **Settings toggles not switching visually** (e.g. Rainbow brackets): `refreshSettingsUI` was doing `document.getElementById(id).classList.toggle(...)` directly — a single missing or renamed id earlier in the function would throw and halt updates to every toggle after it. Rewrote with `_setVal` / `_setText` / `_setToggle` helpers that silently no-op if the element is missing, so every control refreshes independently.

## 1.9.2 — Indent guides in indent area only, rainbow brackets

- **Indent guides no longer paint across whole lines.** Old CSS used a line-width background-gradient that drew vertical lines across every row from top to bottom. Now guides come from an overlay (`_guidesOverlay`) that tags each tab-stop position inside the actual leading whitespace with `cm-ig-line`. CSS renders a 1 px `box-shadow` on those spans only — zero paint on blank lines or the content area.
- **Rainbow style** now combines the indent colors with the new in-indent guide lines (previously it added the whole-line guides class).
- **Rainbow brackets fixed**. The `.cm-s-ha.bp-on .cm-bp-N` CSS gate was too brittle. Removed the `.bp-on` class; color rules now apply as soon as the overlay starts tagging brackets with `cm-bp-N` — and the overlay is added/removed based on `PREFS.bracketColors`.
- **Rainbow/gradient/bars indent levels**: removed the `width: 1ch` clip on marker spans. CodeMirror merges consecutive same-class tokens into one span, so a single `ir-0` span may cover 2+ spaces. The old rule was shrinking it to one character and the visible level looked wrong.
- **Terminal diagnostics**: pre-connect health check against `/api/terminal/available` so failures show an actionable error instead of hanging; logs the WS URL and close codes. `bash` added to the add-on image so the PTY prefers it over `/bin/sh`.

## 1.9.1 — Bug sweep: icons, filter, opacity, indent switch, rainbow gaps

- **Folder icons** now render **filled solid amber** so directories are instantly distinct from (outlined) file icons. YAML files recolored from amber → red/pink to avoid collision with the folder color.
- **Explorer filter** now shows live results. Previous implementation walked the currently-rendered DOM, so files inside collapsed directories never appeared. Rewrote to walk the TREE data and render a flat list of full-path hits.
- **Indent-style transparency** slider actually works now. Switched from per-rule `calc()` in `rgba()` alpha to a single `opacity:` on the marker spans, which is supported by every modern browser. Also bumped the default alpha values so the colored styles are visible even at 100%.
- **Rainbow / gradient / bars** rows now paint edge-to-edge with **no vertical gap** between lines. Root cause: `vertical-align: bottom` introduced a baseline gap on inline-block marker spans. Switched to `vertical-align: top` + `line-height: inherit` + `margin/padding: 0`.
- **Indent "with spaces vs tabs" now works.** Root cause: two functions were both named `setIndentStyle` — the newer visual-style one shadowed the older character-selection one, so the dropdown silently hit the wrong function. Renamed the character selector to `setIndentChar` and wired the dropdown accordingly. Editor refreshes after switch.
- Clarified behaviour of three features in the tooltips/docs:
  - **Line wrapping** — wraps long lines instead of horizontal scroll. Only visible on lines wider than the pane.
  - **Show whitespace** — renders leading spaces as `·` and tabs as `→`.
  - **YAML validation** — runs `js-yaml` (with HA tag extensions) on every keystroke; only flags parse-breaking issues, not stylistic ones like 2-vs-4-space indent.

## 1.9.0 — Integrated terminal, minimap, blueprint snippets

- **Integrated terminal** (`Ctrl+` \` ) — xterm.js frontend over a WebSocket PTY. Spawns a shell in `/config`, respects the ingress URL base, and supports resize via the addon. Drag the top edge to resize. Clear / close buttons in the header. Backend dep: `ptyprocess`; `/api/terminal` WebSocket endpoint + `/api/terminal/available` health check.
- **Minimap** (opt-in) — right-edge document overview. Each line renders as a short grey bar scaled to its text length; a highlighted rectangle shows the current viewport. Click anywhere on the minimap to jump that line into view. Toggle in Settings → Appearance or via `View: Toggle minimap`.
- **Blueprint snippets** — four new insertions in the command palette: automation blueprint skeleton, script blueprint skeleton, entity selector input, time selector input. (`!input` tag was already recognized by the YAML linter.)

## 1.8.0 — Multi-cursor, sticky scroll, diff view, rainbow brackets

- **Multi-cursor**:
  - `Ctrl+D` — select the next occurrence of the selection (or the word at cursor if nothing is selected).
  - `Ctrl+Alt+Down` / `Ctrl+Alt+Up` — add a cursor on the line below / above.
  - `Alt+Click` — add a cursor at the click position (CodeMirror default).
  - `Ctrl+Shift+D` — duplicate line (moved from `Ctrl+D`).
- **Sticky scroll**: as you scroll into a nested YAML block, a pinned row at the top of the editor shows the current parent-key path (e.g. `automation › trigger › platform`). Rebuilds on every scroll; auto-hides at the top of a file.
- **Diff view** (vs git HEAD or vs on-disk content): command palette → `Git: Diff current file vs HEAD` or `File: Diff current file vs on disk`. Opens a side-by-side CodeMirror merge modal with aligned gutters and identical-line collapsing. New backend endpoint `/api/git/show?path=...`.
- **Rainbow brackets** (opt-in): color `()` `[]` `{}` by nesting depth, 6 cycling colors. Useful in YAML flow style (`[1, 2, 3]`, `{a: 1}`) and in Jinja templates. Settings → Appearance → Rainbow brackets.

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
- **Rainbow bands now fill the row vertically**: marker spans switched to `inline-block` with full line-height so the colored backgrounds connect across rows with no white gaps between lines.

## 1.5.2 — Indent transparency actually works, dots under colored styles, rainbow + guides

- **Indent style transparency** now works. Two fixes:
  - The `[class^="cm-ir-"]` opacity selector didn't match spans that also carried `cm-ws-space` (dots), because `^=` only looks at the first class in the attribute. Dropped the blanket-opacity approach in favour of multiplying each marker's alpha directly via `calc(base * var(--indent-opacity))`, which scales cleanly and leaves the dots untouched.
  - Background rules for rainbow / gradient switched from `background:` (shorthand) to `background-color:` so the whitespace-dot `background-image` layer paints on top. **Dots now remain visible under rainbow, gradient, and bars.**
- **Rainbow + grey guide lines** combined: the Indent rainbow style now also draws the faint vertical guide lines at each tab stop.
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
