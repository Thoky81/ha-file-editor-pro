# Changelog

## 1.11.29 — Find bar: Whole-entity toggle + regex toggle fix

- **New `.id` toggle** on the floating search bar (Alt+E) — *Whole entity* mode that treats letters + digits + `_` + `.` as one identifier, so a search for `sensor.foo` won't match `sensor.foo_bar` or `binary_sensor.foo`. Same matching rule the Find & Replace modal already had; now reachable from Ctrl/Cmd+F too. Takes precedence over Whole-word (`\b`) when both are on.
- **Bug fix**: the regex (`.*`) toggle in the search bar was calling `_esearchToggle('rx', …)` but the option key is `regex`, so clicking it never actually enabled regex mode. Now it does.

## 1.11.28 — Floating Find-in-file bar (Ctrl/Cmd+F)

Replaces CodeMirror's tiny built-in find dialog with a compact floating bar at the top-right of the active editor.

- **Live highlight** of every match in the file (yellow tint via a CodeMirror overlay) as you type. Updates instantly on every keystroke.
- **Match counter** *(`3/12`)* in the input field; turns red when there are zero matches and again when the regex is invalid.
- **Prev / Next navigation** with the arrow buttons or **Enter** / **Shift+Enter**. The current match is selected so the cursor lands there when you close the bar.
- **Three toggles**: *Match case* (`Aa`), *Whole word* (`\b`), *Regex* (`.*`). Active toggle highlights blue. Keyboard shortcuts: **Alt+C / Alt+W / Alt+R** while the input has focus.
- **Pre-fills from the current selection** if you had something selected.
- **Esc** closes the bar and returns focus to the editor.
- Works against **either editor pane** — opens the bar against whichever pane has focus.
- Find & Replace (Ctrl/Cmd+H) is unchanged; this is for the much more common find-only case.

Entry points: **Ctrl/Cmd+F**, right-click → *Find*, FAB → *Find*, or palette → *View: Find in file…*.

## 1.11.27 — Theme editor: every swatch verified against the previews

Audited each of the 21 customisable variables to confirm the previews actually demonstrate them, then tightened two labels that were misleading users:

- **`--syn-def` was labelled "Anchors & aliases"** but it also colours **Python class names and function definition names** via CodeMirror's `cm-def` token (`class MySensor`, `def __init__`). Renamed to *"Definitions (anchors, class & fn names)"* so changing it doesn't surprise Python editors.
- **`--syn-variable` was labelled "Identifiers / variable names"** without indicating which file types use it. Now shows *"... — Py/JS"* alongside Built-ins.
- **Help text** in the modal now lists exactly which preview each swatch type appears in:
  - Keys / Strings / Numbers / Booleans / Punctuation / Comments / Anchors → YAML preview (top)
  - Built-ins / Identifiers / class & fn names → Python preview (bottom)
  - Indent rainbow + Bracket pairs → both
- Verified all 21 swatches (9 syntax + 6 indent rainbow + 6 bracket pair) have at least one visible token in the previews.

## 1.11.26 — Theme editor preview: realistic HA automations

The YAML preview now shows three real-world HA automations (sun trigger + template condition + light action; numeric_state trigger + multi-condition + notify; state trigger + choose-action with nested data) — much closer to what users actually edit in `automations.yaml` than the previous abstract sample. Plus a more comprehensive Python preview using a typical custom_component class with `async`, `@property`, type hints, and built-ins. Every swatch from 1.11.25 still has visible feedback; the previews simply read like things you'd actually see in `/config`.

## 1.11.25 — Theme editor preview: scrollable + every token recolours

Plus three tokeniser fixes from the same release.

Three tokeniser-related issues meant some swatches weren't actually visible in the preview, even though the underlying CSS variable was being applied correctly to real files.

- **Numbers and booleans on commented lines weren't being tokenised.** CodeMirror's YAML mode requires the *value* to be at end-of-line (its number regex is `^\s*-?[0-9\.\,]+\s?$`), so `brightness: 200            # ← 200 is a NUMBER` returned no class for `200`. Moved every inline note above its line so values reach end-of-line cleanly. Numbers and booleans now respond to swatch changes.
- **`offset: -00:30:00` is not a number to YAML mode** — the colons defeat the regex. Removed; the line was misleading.
- **6-level indent + 6-deep bracket nesting in both previews.** Previously the preview only went 3 levels deep, so changing `--rb-3..5` or `--bp-3..5` had nothing to recolour. Now both YAML and Python contain `[1, [2, [3, [4, [5, [6]]]]]]` and matching indent depth, so every rainbow + bracket-pair swatch shows visible feedback.
- **Identifiers swatch now displays its true colour.** `--syn-variable` has no `:root` default — the CSS rule resolves it via `var(--syn-variable, var(--text-primary))` at paint time, but the swatch's `getPropertyValue('--syn-variable')` returned empty and was falling back to `#000000`. Added a fallback map so the swatch reads `--text-primary` when its primary variable is unset.
- **Each preview frame caps at 240 px and CodeMirror handles its own scrollbar** when the content overflows. The YAML preview's bottom no longer cuts off; long previews scroll inside the frame, so the swatches below remain on screen.

## 1.11.24 — Theme editor: scrollable body so the YAML preview is fully visible

The Theme editor body got tall enough that its bottom (the YAML preview's last lines, plus the Python preview, plus the swatches below) was clipping off-screen. The modal is `display:flex; flex-direction:column; max-height:88vh`, but `.te-body` was missing `flex:1; min-height:0` so it didn't bound itself to the modal height — meaning `overflow-y:auto` on the body never engaged. Added those two declarations; the body scrolls properly now and everything is reachable.

## 1.11.23 — Theme editor: indent rainbow + bracket palettes + Python preview

The Theme editor now lets you recolour the indent overlays and bracket-pair colours, and the preview shows them — plus a Python sample so the *Built-ins* and *Identifiers* swatches are visible too. **Twenty-one categories total**, all with live preview.

### Newly customisable
- **Indent rainbow / bars (6 colours).** The base palette previously hard-wired into the CSS as `rgba(255, 92, 92, .14)` etc. is now driven by `--rb-0` through `--rb-5`, and the rules apply the alpha (`color-mix(... 14% / 75% transparent)`) so the rainbow stays translucent and the bars stay solid even when you swap colours. Same six colours feed both overlays.
- **Bracket pair colours (6 colours).** `--bp-0` through `--bp-5` now drive the rainbow brackets overlay (Settings → *Rainbow brackets*).

### Preview improvements
- **Two stacked previews** in the modal: a YAML sample on top (covers keys, strings, numbers, booleans, anchors, punctuation, comments, deeply-nested brackets to demo bracket-pair colours, multi-level indentation to demo rainbow) and a Python sample below (covers built-ins like `print` / `len`, identifiers, keywords like `def` / `import` / `return`).
- **Indent rainbow + bracket-pair overlays force-enabled** on both previews regardless of your editor preferences, so every swatch has something visible to recolour.

### Theme editor UI
- Swatches now group under section headers — *Syntax* / *Indent rainbow / bars* / *Bracket pair colours* — so it's clear what each block controls.
- Reset still works per-theme (resets all sections).

## 1.11.22 — Theme editor: every syntax type is now reachable

The previous swatches were mislabelled relative to what CodeMirror's YAML mode actually emits, so changing one swatch sometimes recoloured a different category in the preview — exactly the *"not everything updates live"* symptom.

Audited against the CodeMirror 5.65.16 YAML mode source and reorganised:

- **Anchors & aliases** (`&workdays`, `*workdays`) — were wrongly labelled "Values after :", routed via `cm-variable-2` → `--syn-def`. Now correctly labelled.
- **Punctuation** (`:`, `-`, `[`, `]`, `{`, `}`, `,`, list dashes) — were wrongly labelled "Anchors / !tags", routed via `cm-meta` → `--syn-meta`. Now correctly labelled.
- **Booleans** label clarified as *"Booleans / language keywords"* since `cm-keyword` covers Python/JS keywords too.
- **Plain unquoted YAML values** (e.g. `sun`, `light.kitchen`) get no class from CodeMirror's YAML mode — documented in the in-modal help text. They render in the editor's text colour and aren't separately recolourable.
- **Two new swatches** for users editing Python / JS files (HA scripts, custom_components):
  - **Built-ins** (`print`, `len`, `range`) → `--syn-builtin`
  - **Identifiers / variable names** → `--syn-variable` (newly customisable; previously hard-wired to `--text-primary`)
- The CSS rule for `cm-variable` now uses `var(--syn-variable, var(--text-primary))` so undefined themes still fall back to the readable default.
- Inline notes in the preview YAML rewritten so each comment correctly identifies its line's token type.

**Total: 9 syntax categories, all live-updating, all editable by colour-picker or hex.**

## 1.11.21 — Theme editor: typeable hex + correct picker placement

Two fixes to the Theme editor.

- **Colour picker now opens next to the swatch** instead of in the bottom-left corner. The hidden `<input type="color">` was `position:absolute` inside the modal but was being placed using viewport-relative coordinates from `getBoundingClientRect()` — different coordinate systems. Switched to `position:fixed` so the coords match.
- **Hex value is now editable.** The hex displayed next to each swatch is a real input — click it and type. Accepts `#rrggbb` and `#rgb` shorthands; auto-prepends `#` if you paste raw digits. Changes apply live as you type a valid value (invalid intermediate values are flagged red but don't apply, so partial typing doesn't flicker the editor). Press Enter to confirm or Escape to cancel.
- Live updates no longer rebuild the whole swatch list, so the input doesn't lose focus while you're typing.

## 1.11.20 — Sidebar header height matches editor tab bar

The sidebar header (Explorer, Source Control, Search, etc.) used asymmetric vertical padding that rendered roughly 28–30 px tall, while the editor tab bar is exactly `var(--tab-height)` = 36 px. The bottom borders didn't line up, which read as a small visual "step" between the sidebar and the editor. The header now uses the same `--tab-height` so the two horizontal lines are perfectly continuous across all panels.

## 1.11.19 — Standalone Theme editor with click-to-recolour

The syntax preview from 1.11.18 graduates into a dedicated **Theme editor** modal you open from the **Theme** button in the bottom status bar (or the command palette → *Theme: Open Theme editor…*). Removed from Settings — one home, not two.

- **Click any swatch** to open the OS colour picker. Pick a colour and it applies live to the editor, the right pane, and the preview.
- **Inline labels in the preview YAML** so each token type is self-documenting — e.g. `# ← THIS WHOLE LINE is a comment`, `# ← 200 is a NUMBER`, `# ← &workdays is an ANCHOR`. No more guessing what's what.
- **Per-theme overrides persist** in `localStorage[fep-theme-overrides]` keyed by theme id. Customise GitHub Light, switch to HA Dark, switch back — your GitHub Light tweaks are still there.
- **Customised tokens are highlighted** with a blue border + dot so you can see at a glance what you've changed.
- **Reset to defaults** button restores the active theme's original colours.
- **Theme dropdown inside the editor** so you can flip themes (and tweak each one) without leaving the modal.
- Boot-time apply: `applyPrefs()` calls `applyThemeOverrides()` so customisations survive page refreshes.

## 1.11.18 — Live syntax preview in Settings

A new **Syntax preview** section in the Settings modal renders a small HA YAML sample using whatever theme is currently active, plus a row of swatches showing each token category's exact hex value. Switch the *Theme* dropdown above and the preview repaints instantly — no more guessing what a theme does to comments vs. anchors vs. booleans.

- Sample covers every category that has its own colour: keys, strings, numbers, booleans, anchors / aliases / `!tags`, comments, and "values after `:`".
- Swatches are labelled with the category name, the hex value, and the underlying CSS variable on hover (e.g. `--syn-atom`).
- Read-only CodeMirror instance with no cursor or gutters, so the preview doesn't interfere with the editor.

## 1.11.17 — Unified Find & Replace with HA entity picker

The previous *Replace* (Ctrl/Cmd+H) used CodeMirror's tiny built-in dialog, while *Rename entity* was a two-step input prompt — different mental models for the same job. Both now open the same proper modal.

- **One Find & Replace modal** with two text fields, two checkboxes (*Whole entity* — `sensor.foo` won't match `sensor.foo_bar`; *Case sensitive*), live match counter (*"4 matches · at 2"*), and three actions: **Find next**, **Replace** (current match), **Replace all**.
- **HA entity picker** next to **both** fields. Click the magnifying-glass icon and a searchable list of every registered HA entity drops below the field — filter by entity ID *or* friendly name (typing "kitchen" finds `light.kitchen_main` even if you don't remember the slug). Click an entry to fill the field. The picker is bias-sorted: prefix matches on `entity_id` first, then prefix matches on friendly name, then everything else.
- **Picking a Find entity** with an empty Replace field auto-toggles *Whole entity* on (matches the rename-entity intent).
- Entry points: right-click in editor → *Find & Replace…* or *Rename entity…*; **Ctrl+H** / **Cmd+H**; the FAB Replace button; command palette (*View: Find & Replace…* and *HA: Rename entity in this file…*).
- All replacements happen inside one CodeMirror operation, so a single Cmd/Ctrl+Z reverts the whole batch.
- **Right-click context menu width bumped** from `170px` to `230px` (with `white-space:nowrap`) so labels like *Find & Replace…* and *Rename entity…* don't get clipped.

## 1.11.16 — Upload fixes + rename-entity helper

### Upload
- **Bug fix**: uploads into folders outside `/config` (e.g. `share/`, `ssl/`, `addons/`, `media/`) were rejected with *"Upload escapes config directory"* even though `resolve_safe()` had already validated the destination. The backend now re-validates against every mapped root, so uploads work in all roots that the add-on has mounted.
- **Default destination follows the Explorer focus.** If you've drilled into a folder via double-click, *Upload File* uploads there. Right-clicking a folder → *Upload* still wins. Previously every upload went to the config root regardless of context.
- **Overwrite confirmation.** When a file with the same name already exists, the backend returns a structured `"exists"` response instead of silently overwriting. The UI shows the existing file's size and asks *"Replace it with the file you're uploading?"*. For multi-file uploads, the first answer applies to the rest of the batch (one prompt, not N).

### Entity rename helper
- New command **Rename entity in this file…** — finds every occurrence of an entity ID (e.g. `sensor.motion_sensor_vzadu_bok_illuminance`) in the active editor and replaces it with another, with **whole-entity-only matching** so `sensor.foo` doesn't accidentally also match `sensor.foo_bar`.
- Available from: the editor right-click menu, the command palette (*HA: Rename entity in this file…*).
- If the cursor is on an entity ID (or the selection is one), the find field is pre-filled. Validates that both old and new follow the `domain.name` shape. The replacement is one undo step, so Cmd/Ctrl+Z reverts the whole rename.

## 1.11.15 — Visible timestamp prefill in the commit box

Follow-up to 1.11.14: the auto-timestamp now appears **inside the commit-message textarea** so you can see it before hitting Commit and edit it if you want. Previously the timestamp only kicked in as a hidden fallback when the box was empty.

- On load and whenever the box is empty and focused, it pre-fills with the current local time in `YYYY-MM-DD HH:MM` form.
- Typing replaces it — the autofill tracker only refreshes the timestamp when the value is still the one we put there, so your in-progress message is never clobbered.
- After a successful commit the box is re-prefilled with a fresh timestamp, ready for the next one.

## 1.11.14 — Auto-timestamped commits

- **Commit with no message.** If the commit box is empty, the message defaults to the current local date and time in `YYYY-MM-DD HH:MM` form (e.g. `2026-04-24 14:32`). Hit the Commit button — or Ctrl+Enter — without typing anything and you get a clean, sortable entry in `git log`. Typing a message still works exactly as before.
- Placeholder updated to make the behavior discoverable.

## 1.11.13 — Instant show/hide hidden-files toggle

The hidden-files toggle used to take a few seconds in either direction — every click triggered a full backend filesystem walk followed by a complete tree re-render. Now it's a single DOM pass.

- **Fetch once, filter on the client.** The tree is always fetched with `?hidden=1`, so dotfiles are present in the client-side model. `renderNodes()` and the Explorer filter drop them when `PREFS.showHidden` is off. Toggling only re-renders — no network round-trip, no backend rewalk.
- **Bigger `SKIP_DIRS` list in the backend** so expensive noise folders are never walked, even when hidden is on: `.venv`, `venv`, `.tox`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.cache`, `.idea`, `.vscode`, plus HA's own `tts/` and `deps/`. Existing skips (`.git`, `.storage`, `.cloud`, `__pycache__`, `node_modules`) are preserved. This also speeds up the initial tree fetch on large `/config`s.

## 1.11.12 — Mac keyboard-shortcut labels

All keyboard shortcuts displayed in the UI are now re-labelled for Mac users automatically. The mapping: `Ctrl → ⌘`, `Alt → ⌥`, `Shift → ⇧`, `Enter → ↵`, `Tab → ⇥`. Windows/Linux users see exactly the same labels as before.

- **Help modal**, **command palette** shortcut column, button **tooltips** (`Save`, `Toggle sidebar`, etc.), the Jinja preview hint, the welcome screen hint line, and dynamic status-bar tooltips all render the correct modifier symbols.
- Detection is a one-shot `navigator.platform` check at load, and a single DOM sweep relabels `<kbd>` elements plus `title`/`placeholder`/`aria-label` attributes. Dynamic strings go through a small `fmtInline()` helper.
- Keybinding logic was already platform-aware (`ctrlKey || metaKey` across the board) — only the displayed labels changed.

## 1.11.11 — Jinja error list is now clickable + far fewer false positives

Two fixes to how Jinja validation surfaces in the UI.

- **Status-bar click finally opens an error list.** The *"N Jinja errors"* indicator in the bottom status bar used to look clickable but did nothing. It now opens a modal that lists every error with line/column, the offending expression, and the underlying message. Click a row to jump the cursor to that expression. There's also a *Re-check* button and an Escape/click-outside close.
- **Far fewer false positives.** The old validator sent each `{{ … }}` and `{% … %}` fragment to HA's template renderer in isolation. That made isolated `{% if %}` / `{% for %}` / `{% macro %}` / `{% set x = y %}` fragments look like syntax errors (no matching close tag, no variable in scope), even though the full template would render fine.
  - **`{% … %}` statements are no longer validated one-by-one.** They almost always participate in a larger block that a per-fragment check can't see.
  - **If a file contains any `{% … %}` statement, per-expression validation is skipped for the whole file** — the status bar shows *"Jinja: skipped (complex template)"* and the tooltip points at Ctrl+Alt+J (template preview) and HA's Check Config for authoritative validation.
  - Simple files with only `{{ expr }}` expressions are still validated expression-by-expression as before.
- **Command palette**: *HA: Show Jinja error list* (opens the same modal directly).

## 1.11.10 — Hidden-files toggle + "nothing to commit" treated as success

- **Show / hide hidden files** toggle in the Explorer toolbar (the eye icon next to Refresh). Flip it to reveal dotfiles and dotdirs (`.gitignore`, `.storage`, `.env`, etc.) on demand — the state persists in preferences and also applies to cross-file search. Runtime toggle, no add-on restart. Command palette: *View: Toggle hidden files (dotfiles) in Explorer*.
  - The add-on's `show_hidden` option still sets the default; the toolbar button overrides it per session.
- **Backend**: `/api/files/tree` and `/api/files/search` now accept a `?hidden=1` query parameter.
- **Commit**: *"nothing to commit, working tree clean"* no longer bubbles up as a red error toast. It's treated as a successful no-op with a neutral *"Nothing to commit — working tree is clean"* message. This often happened after auto-ignoring nested repositories, because `git rm --cached` already resolved the only pending change.

## 1.11.9 — One-click fix for nested git repositories

Fixes *"'ha_vibecode_git/' does not have a commit checked out"* and *"adding embedded git repository: …"* — both symptoms of having folders inside `/config` that are themselves git repositories (cloned add-ons, experimental projects, etc.). Git refuses to add them directly, and if any of them has no commits, it aborts the whole `git add -A`.

- **Automatic detection.** The backend now parses git stderr for both the hard-failure variant (*"does not have a commit checked out"*) and the warning variant (*"adding embedded git repository"*), and returns a structured `409` response listing the offending folders instead of an opaque stderr dump.
- **Commit-time recovery dialog.** When the commit panel sees a nested-repo error, it lists the folders and asks *"Add them to /config/.gitignore and try the commit again?"* One click resolves it.
- **New backend endpoint** `POST /api/git/ignore-paths` — appends `/<path>/` rules to `/config/.gitignore` (skipping any that already exist) and runs `git rm -r --cached` so previously-tracked gitlinks stop showing up as changes.
- Stale-lock errors now also use the structured `409` flow, making the retry logic consistent across failure kinds.

## 1.11.8 — Stale git lock recovery

Fixes *"fatal: Unable to create '/config/.git/index.lock': File exists"* — a recurring failure when a previous git operation was interrupted (container stop, OOM, browser refresh mid-commit) and left its lockfile behind. The add-on couldn't commit again until that file was removed by hand.

- **Auto-clear on the way in.** Every backend git call now checks for `.git/index.lock` first and removes it if it's older than 15 seconds. Live operations the add-on just started (<15 s) are never disturbed, so this is safe even under normal use.
- **Serialized git access.** All git subprocesses now run under a single `asyncio.Lock`, so two panel actions firing at the same instant can't collide into a lockfile conflict of their own making.
- **Commit-time auto-retry.** If a commit still hits a stale-lock error, the panel pops a confirm dialog: *"Clear the lock and retry?"* — one click recovers, no terminal needed.
- **Unlock button in the Source Control header.** Next to Refresh / Pull / Push: a small padlock icon that force-clears `index.lock`. Use it only when the friendly retry dialog doesn't appear but git still refuses to cooperate.
- **Command palette entry**: *Git: Clear stale index.lock*.
- **Clearer error message** — when a stale lock is the cause, the toast now tells you what to click, instead of dumping raw git stderr.

## 1.11.7 — Logs panel: persistent notification history

- **New Logs panel** — every toast notification is now captured in a 500-entry ring buffer so you can re-read messages that disappeared before you finished reading them. Open it from the **Logs** button in the status bar (bottom-right), press **F12**, or use the command palette (*View: Show Logs*).
- **Error toasts linger longer** — 6 seconds instead of 2.2, and they're rendered with a red accent so they're immediately distinguishable from plain info.
- **Unread-error badge** on the status-bar button — a red count appears when an error toast fires and clears when you open the panel.
- **Copy all** button dumps the full log as ISO-timestamped lines to the clipboard; text inside the panel is also **selectable with the mouse** so you can grab a single line. **Clear** wipes the buffer.
- Escape closes the panel; clicking outside the modal does too.

## 1.11.6 — Selective staging in Source Control + fix path mismatch

- **Per-file checkboxes** in the Source Control panel. Every change gets a checkbox (staged by default). Uncheck a file and it won't be part of the next commit. The commit button label updates in real time — *Commit 3/7 to main* when a subset is selected, *Commit 7 files to main* when all are. Commits now only stage + commit the checked paths (`git add --` then `git commit -- paths`). Folders work too (git add recurses).
- **Fixed a long-standing path mismatch.** git worked at `/config`, but the frontend sees paths prefixed with the root name (e.g. `config/configuration.yaml`). `/api/git/status` now prefixes its returned paths with `config/` so the tree git badges light up correctly; `/api/git/commit`, `/api/git/diff`, `/api/git/show` strip the prefix before calling git so partial commits and per-file diffs finally work. (Previously per-path operations silently no-op'd.)

## 1.11.5 — Default .gitignore with secrets excluded by default

- **Checkbox in the init UI** (on by default) seeds a `/config/.gitignore` alongside the repo with HA-appropriate patterns. **Secrets are excluded by default** — `secrets.yaml`, `*.secrets.yaml`, `.env`, `.env.*`, `*.pem`, `*.key`, SSH host keys. Runtime state (`.storage/`, `.cloud/`, `backups/`), databases, logs, Python caches, and OS/editor junk are all excluded too.
- Users who *want* to commit secrets (e.g. encrypted) can delete those lines from `.gitignore` after init.
- **Command palette**: *Git: Create default .gitignore (HA-appropriate patterns)* for existing repos, and an overwrite variant. Backend adds `POST /api/git/seed-gitignore` (with an optional `?overwrite=true`).

## 1.11.4 — Clearer help icon + guided git setup

- Help button in the activity bar swapped from a thin path-drawn `?` (which read as fuzzy at 18 px) to a bold italic `i` rendered as an SVG `<text>` element inside a circle. Same update applied to the Help modal header for consistency.
- **Source Control onboarding.** When the config folder isn't a git repository yet, the Source Control panel now shows an explainer + an **"Initialise git repository"** button and an optional **GitHub URL field** to set up a remote at the same time. No more dropping to the terminal for the first-time setup.
- When a repo exists but has no remote, the panel's header shows "no remote"; when it does, it shows the remote URL (trimmed). New backend endpoints `POST /api/git/remote-add` and `GET /api/git/remote`.

## 1.11.3 — Dropdown actually works + tabs persist across refresh

- **Tab-list dropdown** — moved from `position: absolute` to `position: fixed` with coordinates computed from the trigger button's bounding rect. The old dropdown was being clipped by the tab-bar's `overflow: hidden`, so clicking the icon appeared to do nothing. Now it opens correctly with `z-index: 1200`.
- **Open tabs persist across page refresh.** A `fep-tabs` localStorage snapshot (paths + active path) is saved on every tab open / close / switch and restored on boot. Refreshing the add-on no longer loses your working set.
- **Refreshing with all tabs closed no longer opens a random file.** The boot's fallback used `Object.keys(FILES)[0]` after failing to find `configuration.yaml` at the root — on real HA installs files are prefixed (e.g. `config/…`), so it picked up the first alphabetical automations file instead. Auto-open is removed entirely: refresh restores whatever was open, or shows the empty-state message if nothing was. Predictable.

## 1.11.2 — Squeeze-to-fit tabs with hover-expand

- Tabs now use `flex: 1 1 140px` with `min-width: 42 px` and `max-width: 180 px`, so when many are open they share the available space instead of spilling off-screen. When you hover a tab its width expands (up to 320 px) so the full filename is visible and you can click it to switch. The **active tab always keeps its natural width** (up to 360 px) so the file you're editing is never truncated. 180 ms transition on width so the effect feels smooth rather than twitchy. Filenames truncate with an ellipsis when squeezed.

## 1.11.1 — Tab overflow handling

When many files are open, the tab bar overflowed and the Save button + dropdown scrolled off-screen. Three fixes:

- **Tab-list dropdown** at the right end of the bar showing every open file (with modified dot + directory), click to switch, click `×` to close. Shows the count next to the icon.
- **Save button + dropdown now pinned to the right** (`position: sticky`). They stay visible no matter how far the tabs scroll; a subtle left-shadow hints that there's more content behind.
- **Navigation shortcuts**: `Ctrl+Tab` → next tab, `Ctrl+Shift+Tab` → previous tab, `Ctrl+W` → close active tab, **middle-click** on any tab to close it. Active tab auto-scrolls into view on switch. All listed in the Help modal.

## 1.11.0 — Help panel

- **New `?` icon in the activity bar** (below the sidebar toggle). Opens a Help modal with:
  - Legend for every activity-bar icon (sidebar toggle, Explorer, Search, Source control, Insert, Outline, Sun/Moon theme toggle, Settings gear)
  - File-operation shortcuts (save, quick-open, command palette, terminal, Jinja preview, sidebar toggle)
  - Editing shortcuts (find/replace, toggle comment, autocomplete, multi-cursor, indent/outdent)
  - File-tree actions (expand, drill-in, split-right, create/rename/delete)
  - Source-control shortcuts
- **`F1`** opens the Help modal too. Also in the command palette as *View: Show Help & shortcuts*.

## 1.10.10 — Drop the redundant Explorer-header hide button

- Removed the double-chevron hide-sidebar button from the Explorer header. Now that the activity-bar toggle (top item) does the same thing and is always visible, the header button was duplicated clutter.

## 1.10.9 — Sidebar toggle moved into the activity bar

- The expand chevron added in 1.10.8 overlapped the tab bar. Moved it into the activity bar as a dedicated item at the top (above Explorer), always visible, chevron direction flips with state (`‹` when sidebar is shown, `›` when hidden). No more overlap; re-click on the active activity-bar icon still toggles too.

## 1.10.8 — Discoverable sidebar expand + toggle on re-click

- **Expand chevron when the sidebar is collapsed.** A small `›` button appears at the left edge of the editor area whenever the sidebar is hidden. Clicking it shows the sidebar back. Solves the "where did my files go?" problem after a first-time `Ctrl+B` or the header hide button.
- **Clicking the active activity-bar icon now hides the sidebar.** Explorer / Search / Git / Insert / Outline: pressing the already-active icon toggles the sidebar off (rather than re-showing the same panel). Pressing a different icon opens its panel and brings the sidebar back.

## 1.10.7 — Custom input dialog for create / rename / duplicate

- **New file, New folder, Rename, Duplicate** now use the same custom modal style as the delete confirmation. Title, label, text field, *Cancel* + action button. Enter submits, Esc cancels, input is auto-selected for quick edits.
- **Input field shows only the filename, not the full path.** Creating a new file under `config/packages/` used to pre-fill `config/packages/new_file.yaml`; now it just shows `new_file.yaml` with a hint "*Will be created under config/packages*" below. The app joins the dir + name internally. Same treatment for Rename (only the basename is edited, directory stays).

## 1.10.6 — Preserved expanded state + custom delete confirm

- **Tree no longer collapses on create / delete / rename.** `ingestBackendTree` now snapshots every currently-open directory path and re-applies the expanded flag after the refresh, so you don't have to re-open folders every time you modify the filesystem.
- **Custom delete confirm dialog.** Native `confirm()` put focus on OK or Cancel depending on the browser — inconsistent and sometimes one-Enter-accidental-delete. Replaced with a small modal: Cancel + Delete; **Cancel is the initial focus**, so Enter always cancels; the red Delete button requires a deliberate click.

## 1.10.5 — Default folder on startup

- Settings → Appearance → **Default folder on startup**. Enter a path (e.g. `config` or `config/packages`) and the app drills into that folder automatically on load. Empty = full tree as before. The *Use current* button next to the field fills it with whatever folder you're currently focused on. Also available from the command palette as *View: Set current folder as default startup folder*.

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
