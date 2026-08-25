# design-sync notes — @aditf/design-system

## Font resolution

- `--font-display: 'Oswald', 'Arial Narrow', sans-serif` — the shipped CSS references three font families in that stack. `Oswald`, `Inter`, and `IBM Plex Mono` are Google Fonts, loaded at runtime by the consuming host page via a `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=...">` tag — exactly as the live aditf.com `index.html` does (see its `<head>`). No `@font-face` ships in the package by design; resolved via `cfg.runtimeFontPrefixes: ["Oswald", "Inter", "IBM Plex Mono"]`.
- `Arial Narrow` is the system-font fallback in the `--font-display` stack (after Oswald, before the generic `sans-serif`) — not a real font family to source. The `[FONT_MISSING]` warning for it is expected and accepted; no action needed.

## Playwright / render check

- Cached chromium build `1234` was already present at `~/.cache/ms-playwright/`. Installed `playwright@1.62.1` into `.ds-sync/node_modules` (matches that pinned revision) rather than the repo's own default, since no playwright was already a project dependency.

## Preview authoring scope

- User chose "author previews for everything" (all 20 discoverable exports) on the first sync, given the small size of this package.

## Preview authoring — known render notes

- **RouteProgress**: `position: fixed` escapes any wrapper without a new containing block, so its preview wraps content in a `transform: translateZ(0)` box to contain it for the card capture (it correctly spans the full viewport on the real page — this containment is preview-only). 0% amber fill in the screenshot is expected (fresh page load, `scrollY=0`, no props to force a state) — grade it on structural correctness (a full-width `--ink-line` track), not fill amount.
- **Reveal**: fires correctly in the real headless-Chromium render check (not jsdom) — content shows at full opacity, no `prefers-reduced-motion`/no-`IntersectionObserver` fallback needed for the preview.
- **Seal**: the live site ships 3 seals (JavaScript/Course, CSS/Fundamentals, jQuery/Course) — all 3 are real content from `index.html`'s Certifications section, not synthetic.
- StatChip and Crate (co-located exports in `StatRow.tsx`/`CrateGrid.tsx`) import and render standalone from the package with no special wiring; same for ContactRow/TimelineItem.
- No `[GRID_OVERFLOW]` issues beyond Hero (which needed `cardMode: "column"`, applied during the solo set) — CrateGrid, Nav, StatRow, and ContactGrid were all flagged as plausible candidates but none needed an override at the authored content sizes.

- **TimelineItem** must be wrapped in `<ol className="timeline">` when authoring its standalone preview — the dashed rail/node positioning is owned by the parent `.timeline` element, not the item itself; a bare `<TimelineItem />` renders content but silently drops the rail line and node dot.
- **CrateGrid** overflowed its preview card height with all 8 real skill groups (the trailing group got cropped, leaving a blank cell). Fixed by trimming the authored content to 5 groups rather than a `cardMode` override — trimming is the cheaper fix when a component's real content is a variable-length list, vs. `cardMode: "column"` for components whose content is fixed-shape-but-wide (like Hero).
- Nav and CrateGrid were both plausible `[GRID_OVERFLOW]` candidates (like Hero) but neither needed the override — both fit cleanly at default `cardMode` at authored content sizes.

## Re-sync risks

- The two toolchain choices above (`runtimeFontPrefixes`, the pinned `playwright@1.62.1`) are environment-derived, not repo-derived — a future sync on a different machine may need to re-verify the cached chromium revision still matches, or re-pin playwright if the cache changes.
- `dist/` is gitignored in `design-system/` — always re-run `npm run build` inside `design-system/` before re-running the converter; a stale or missing `dist/` will fail with `[NO_DIST]`.
