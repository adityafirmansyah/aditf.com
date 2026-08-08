# GainForge Projects Section — Design

## Purpose

Add a "Projects" section to the aditf portfolio site (`index.html`) that showcases GainForge — a gamified fitness RPG app the user built solo (Rust/Leptos/Axum) — as a full case study. This is the first project showcased on the site.

## Placement

Insert a new `<section class="section" id="projects">` between the existing **Skills** and **Experience** sections.

Resulting page order: Hero → About → Skills → **Projects** → Experience → Certifications → Contact.

Update the nav (`.nav__links` in `index.html`) to insert a Projects link and renumber the trailing indices:

```
01 About
02 Skills
03 Projects   <- new
04 Experience  (was 03)
05 Certs       (was 04)
06 Contact     (was 05)
```

## Content

Single full-width case-study card (no grid — one project today, but the component should read fine if a second project card is added later).

- **Eyebrow:** "Solo Build — Full-Stack Rust"
- **Title:** "GainForge" with subtitle "Gamified Fitness RPG"
- **Status badge:** `● LIVE` (amber pulse-dot, same visual motif as the hero waybill's "IN TRANSIT" status), linking to the live site
- **Lede (1 short paragraph):** GainForge turns real workouts into RPG quests — users earn XP, level up a character, and grow four stats (STR, END, AGI, FLX) by completing daily strength, cardio, flexibility, and endurance sessions. Built solo end-to-end: product design, schema, API, frontend, and production deployment.
- **Three bullet points** (standout technical/product decisions):
  1. Full Rust stack front-to-back — Leptos (WASM) frontend and an Axum backend share a single DTO crate, keeping types identical across client and server.
  2. Designed the quest/XP/leveling system and a 4-stat character model, plus an admin panel for managing training programs, exercises, and weekly schedules.
  3. Shipped and self-hosted on a VPS with Docker and PostgreSQL — 15 schema migrations, 100+ commits, with iterative mobile-UX polish (drawer navigation, responsive schedule grid).
- **Stack chips:** Rust, Leptos (WASM), Axum, PostgreSQL, Docker, Self-hosted VPS
- **CTA button:** "Visit GainForge →" linking to `https://gainforgeapp.com`, opens in a new tab (`target="_blank" rel="noopener noreferrer"`), styled `btn btn--stamp` to match existing primary CTAs.

All copy is sourced from the project's own `PRODUCT.md` and landing page (`~/personal/fitness/PRODUCT.md`, `~/personal/fitness/landing/index.html`) and its git history (`~/personal/fitness` — 105 commits, 15 migrations under `migrations/`, Cargo workspace with `shared`/`backend`/`frontend` crates using Leptos 0.7 and Axum 0.7).

## Visual Design

Reuse existing design tokens and patterns from `styles.css` — no new colors, fonts, or unrelated components:

- Card background/border styled like `.label-card` (kraft card) is NOT used — instead the card sits on the dark `--ink` background like `.timeline__card`, since Projects sits among dark sections, not the kraft-toned About section.
- New `.project-card` block:
  - `.project-card__top` — flex row: title block on the left, `.project-card__badge` (reuses `.waybill__status` + `.dot` pulse animation, amber) on the right
  - `.project-card__eyebrow` — same treatment as `.eyebrow`
  - Title (`h3`) styled like `.timeline__card h3`, with the subtitle in a `<span>` styled like the existing `h3 span` (steel-colored, mono, uppercase)
  - `.project-card__lede` — body copy, same size/color as `.hero__lede`
  - `.project-card__points` — reuses the `›`-bullet list styling from `.timeline__card ul/li`
  - `.project-card__stack` — reuses `.timeline__stack` chip styling
  - `.project-card__actions` — reuses `.hero__actions` + `.btn btn--stamp`
- Card gets a `1px solid var(--ink-line)` border and generous padding (`40px`) to read as a distinct, contained artifact — similar weight to `.crate-grid` but as a single block rather than a grid.
- `reveal` class applied for the existing scroll-reveal behavior, consistent with every other content block on the page.

## Out of Scope

- No screenshots/mockups of the GainForge UI (text-only case study, per approved design).
- No changes to `script.js`. It has no section-id-specific logic — nav links are plain `#anchor` links, and the reveal-on-scroll `IntersectionObserver` targets any `.reveal` element generically. The new section only needs the `reveal` class on its content block to pick up existing behavior.
- No second project card / grid layout — single card only.
