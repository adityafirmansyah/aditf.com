# Upwork Proposal Generator — Projects Section Design

## Purpose

Add a second case-study card to the existing Projects section (`index.html`) for the Upwork Proposal Generator — an AI-assisted cover-letter tool for Upwork freelancers, built solo (React/Vite/Tailwind frontend, Express/PostgreSQL backend) and deployed live at `https://uclg.aditf.com`.

## Placement

The Projects section (`#projects`) currently holds a single `.project-card` for GainForge. This change:

1. Wraps both cards in a new `.project-list` container (`display:flex; flex-direction:column; gap:32px`) so there's visible separation between cards — today's CSS has no spacing rule between sibling `.project-card` elements because only one exists.
2. Adds the new Upwork Proposal Generator card as the second child, after GainForge (GainForge stays first — it's the more fully-realized product).

No nav or other section changes — Projects already exists as its own nav entry.

## Content

- **Eyebrow:** "Solo Build — Full-Stack JavaScript"
- **Title:** "Upwork Proposal Generator" with subtitle "AI Cover Letter Tool"
- **Status badge:** `● LIVE` (same amber pulse-dot badge as GainForge's), linking to `https://uclg.aditf.com`
- **Lede (1 short paragraph):** Freelancers on Upwork build a profile (skills, bio, experience), paste a job listing URL, and get a tailored, editable cover letter back — turning "found a job I want" into "submitted a proposal that gets a reply" in the time it takes to read the posting.
- **Three bullet points** (standout technical/product decisions):
  1. Backend scrapes the pasted Upwork listing (Express + cheerio) with SSRF hardening — validates and blocks requests to localhost, private/reserved IP ranges, and cloud metadata endpoints before fetching a user-submitted URL.
  2. Job summary and user profile feed a prompt builder that calls an LLM gateway (Claude Haiku) to draft the cover letter, which the user can edit before saving.
  3. Full auth/profile/letter-history schema in PostgreSQL (users, profiles, projects, cover_letters with draft/saved status) behind JWT auth; self-hosted on a VPS via git-push deploy (bare repo + post-receive hook + systemd + nginx).
- **Stack chips:** React, Vite, Tailwind, Node.js, Express, PostgreSQL, Self-hosted VPS
- **CTA button:** "Visit Upwork Proposal Generator →" linking to `https://uclg.aditf.com`, opens in a new tab (`target="_blank" rel="noopener noreferrer"`), styled `btn btn--stamp` to match GainForge's CTA.

All copy is sourced from the project's own `PRODUCT.md`, backend source (`backend/src/services/jobParser.js`, `aiGenerator.js`, `backend/migrations/001_initial_schema.sql`), and git history (`~/personal/upwork-proposal-generator` — 35 commits) and deploy commit (`0edb2bc`, documenting the VPS git-push pipeline to `uclg.aditf.com`).

## Visual Design

No new CSS components — this card reuses every class already defined for GainForge's card verbatim (`.project-card`, `.project-card__top`, `.project-card__eyebrow`, `.project-card__badge`, `.project-card__lede`, `.project-card__points`, `.project-card__stack`, `.hero__actions`, `.btn btn--stamp`, `.reveal`).

The only new CSS is the `.project-list` wrapper (flex column + `32px` gap), following the same flex+gap convention already used by `.seal-row` and `.lang-row` elsewhere in `styles.css`.

## Out of Scope

- No screenshots/mockups of the Upwork Proposal Generator UI (text-only case study, matching GainForge's treatment).
- No changes to `script.js` — the reveal-on-scroll observer targets `.reveal` generically, and the new card gets the class directly.
- No grid layout — cards stack vertically in the `.project-list` column, not side-by-side.
