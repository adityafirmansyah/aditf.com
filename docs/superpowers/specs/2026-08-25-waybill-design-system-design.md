# Waybill Design System — extraction spec

Status: approved (visual plan reviewed via artifact, 2026-08-25)

## Purpose

`aditf.com` is a static HTML/CSS/JS personal site with a distinctive,
cohesive visual language — a "shipping manifest / logistics" theme
(waybills, kraft-paper cards, freight crates, a tracking timeline, wax-seal
certifications, a barcode divider, stamp-style buttons). This spec covers
extracting that visual language into a standalone, prop-driven React
component package so it can be synced into Claude Design (via the
`design-sync` skill) — after which the design agent builds with these real
components instead of generic ones.

This spec covers building the component package only. Running
`design-sync` against the finished package is the follow-on step once the
package exists and builds cleanly.

## Non-goals

- No changes to the live site (`index.html`, `styles.css`, `script.js`,
  `assets/`) or its deploy flow. The new package lives in a directory the
  deploy hook's `git archive` never touches.
- No Storybook. The package has no existing Storybook, so `design-sync`'s
  "package shape" applies, not the storybook shape.
- No redesign. Fidelity target is 1:1 visual match to the live site, not a
  simplified or reinterpreted version.
- No CMS/data-fetching layer. Components take content via props; nothing
  fetches or hardcodes personal content beyond example usage.

## Location & tooling

- New directory: `design-system/` at repo root (sibling to `index.html`,
  independent `package.json`).
- React + TypeScript, built with esbuild to `design-system/dist/`,
  matching the shape the `design-sync` skill's package converter expects
  (`package-build.mjs` / `package-validate.mjs`).
- Node version: no `.nvmrc`/`engines` pin exists elsewhere in this repo,
  so `design-system/package.json` pins `"engines": {"node": ">=20"}`
  (current Node LTS) as the working assumption.
- Styling: a single `styles.css` exporting the token custom properties and
  component classes (mirrors the live site's approach — plain CSS custom
  properties, not CSS-in-JS or a utility framework), so the styling idiom
  documented for the design agent later matches what's actually shipped.

## Token system

Extracted verbatim from `styles.css`'s `:root` block:

| Token | Value | Role |
|---|---|---|
| `--ink` | `#14181B` | page background |
| `--ink-soft` | `#1B2023` | raised surface |
| `--ink-line` | `#2B3236` | hairline borders |
| `--paper` | `#EDE6D6` | primary text on ink |
| `--paper-dim` | `#9CA3A0` | secondary text |
| `--kraft` | `#D9C8A8` | label-card surface |
| `--kraft-line` | `#B8A47D` | kraft borders / dashed rules |
| `--kraft-ink` | `#2A2116` | text on kraft surfaces |
| `--amber` | `#E8871E` | accent / call-to-action |
| `--amber-soft` | `rgba(232,135,30,.14)` | tag backgrounds |
| `--steel` | `#7FA9C4` | secondary accent (subtitles, labels) |
| `--stamp-red` | `#C24B3B` | reserved accent (unused on current site; carried through for design-agent flexibility) |
| `--font-display` | Oswald | headings, stat numbers |
| `--font-body` | Inter | running text |
| `--font-mono` | IBM Plex Mono | labels, tags, dates, nav |
| `--max` | `1080px` | content max-width |
| `--edge` | `clamp(20px, 6vw, 64px)` | page horizontal padding |

Shipped as `design-system/src/tokens/index.css` (custom properties, same
names) plus a `design-system/src/tokens/index.ts` re-export of the same
values as typed JS constants for components/consumers that need them in
JS (e.g. computing a style prop).

## Component inventory

All components accept content via props — nothing is hardcoded to
Aditya's specific bio/projects/timeline. Internal behavior (scroll reveal,
scroll-progress tracking, mobile nav toggle) moves from the site's global
`script.js` into component-local hooks.

| Component | Source pattern | Key props |
|---|---|---|
| `Button` | `.btn--stamp` / `.btn--ghost` | `variant: 'stamp' \| 'ghost'`, `href`, `children`, `download?` |
| `Nav` | `.nav`, mobile toggle | `mark`, `links: {label, href, index}[]` |
| `RouteProgress` | `.route-progress` | none — internal `useScrollProgress` hook |
| `SectionHead` | `.section__head`, `.eyebrow` | `eyebrow`, `title` |
| `Hero` | `.hero` | `trackingLabel`, `trackingValue`, `status`, `name`, `nameAccent`, `role`, `origin`, `dest`, `lede`, `actions: ReactNode` |
| `Waybill` | `.waybill` | `label`, `value`, `status?` |
| `LabelCard` | `.label-card` (kraft + tape) | `children` |
| `StatRow` / `StatChip` | `.stat-row` / `.stat-chip` | `stats: {num, label}[]` |
| `CrateGrid` / `Crate` | `.crate-grid` / `.crate` | `groups: {label, items: string[]}[]` |
| `ProjectCard` | `.project-card` | `eyebrow`, `title`, `subtitle`, `badge?: {label, href}`, `lede`, `points: string[]`, `stack: string[]`, `cta?: {label, href}` |
| `Timeline` / `TimelineItem` | `.timeline` | `items: {date, status, statusVariant?, role, org, bullets: string[], stack?: string[]}[]` |
| `Seal` | `.seal` | `label`, `sublabel` |
| `LangChip` | `.lang-chip` | `name`, `level` |
| `ContactGrid` / `ContactRow` | `.contact-grid` / `.contact-row` | `rows: {label, value, href?}[]` |
| `Barcode` | `.barcode` | none — decorative |
| `Reveal` | `.reveal` / `IntersectionObserver` scroll-in | `children` — internal `useReveal` hook, respects `prefers-reduced-motion` |

16 components total (matches the reviewed artifact).

## Architecture

```
design-system/
  package.json
  tsconfig.json
  src/
    tokens/
      index.css
      index.ts
    components/
      Button/{Button.tsx, index.ts}
      Nav/...
      RouteProgress/...
      SectionHead/...
      Hero/...
      Waybill/...
      LabelCard/...
      StatRow/... (StatChip co-located)
      CrateGrid/... (Crate co-located)
      ProjectCard/...
      Timeline/... (TimelineItem co-located)
      Seal/...
      LangChip/...
      ContactGrid/... (ContactRow co-located)
      Barcode/...
      Reveal/...
    styles.css          // imports tokens/index.css + each component's CSS
    index.ts             // re-exports every component
  examples/
    portfolio-demo.tsx   // composes all 16 components using the real
                          // aditf.com content, for visual verification
                          // against the live site and as the usage
                          // reference design-sync's converter reads from
```

Each component directory holds its own scoped CSS file (BEM-style class
names carried over from `styles.css`, e.g. `.project-card__top`) imported
by `styles.css`, keeping the "real compiled CSS, real class vocabulary"
property the sync depends on.

## Behavior extraction

- `Reveal`: wraps children, adds `opacity/translateY` transition, uses
  `IntersectionObserver` to add a visible class on first intersection,
  short-circuits to always-visible when `prefers-reduced-motion` is set or
  `IntersectionObserver` is unavailable. Used internally by section-level
  components that currently rely on the site's global `.reveal` class.
- `RouteProgress`: internal scroll listener computing `scrollY / (scrollHeight
  - innerHeight)`, no props.
- `Nav`: internal `useState` for mobile-menu open/close (replaces the
  site's manual `classList.toggle('is-open')`), closes on link click.

## Verification plan

1. `tsc --noEmit` clean.
2. `esbuild` bundle builds without error, produces `dist/` matching
   `design-sync`'s package-shape expectations.
2. `examples/portfolio-demo.tsx` rendered and screenshot-compared against
   the live `aditf.com` sections it mirrors — each of the 16 components
   checked for visual match (spacing, color, type) against its source
   CSS rule.
3. Each component's props exercised with at least one example value in
   `examples/portfolio-demo.tsx` (doubles as the usage reference
   `design-sync` reads for `.prompt.md` generation).

## Follow-on (not part of this spec)

Once `design-system/` builds and passes verification, invoke the
`design-sync` skill (package shape) against it to sync into a new Claude
Design project, per that skill's own process (config, token/style
verification, incremental upload).
