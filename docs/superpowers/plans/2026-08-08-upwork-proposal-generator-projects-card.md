# Upwork Proposal Generator Projects Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second case-study card to the Projects section of the aditf portfolio site for the Upwork Proposal Generator (a solo-built, full-stack-JavaScript AI cover-letter tool, live at `https://uclg.aditf.com`), stacked below the existing GainForge card.

**Architecture:** Static site, no build step — `index.html` (markup) + `styles.css` (styling) + `script.js` (generic scroll-reveal/nav-toggle behavior, unmodified). Wrap the existing single `.project-card` in a new `.project-list` container and add the new card as its second child, reusing every existing `.project-card*` class verbatim.

**Tech Stack:** Plain HTML5/CSS3, no JS framework, no build tooling, no test framework — verification is structural (grep/brace-balance checks) plus a manual visual pass in a real browser via the gstack `/browse` skill.

## Global Constraints

- Reuse existing `.project-card*` classes and design tokens only — no new per-card CSS, only the new `.project-list` wrapper.
- No grid layout — cards stack vertically in a flex column (spec: "cards stack vertically in the `.project-list` column, not side-by-side").
- No changes to `script.js` — the new card only needs the `reveal` class to pick up the existing `IntersectionObserver` behavior.
- Text-only case study — no screenshots or mockups of the Upwork Proposal Generator UI.
- CTA / badge link to `https://uclg.aditf.com`, `target="_blank" rel="noopener noreferrer"`.
- Copy is sourced from `~/personal/upwork-proposal-generator`'s `PRODUCT.md`, `backend/src/services/jobParser.js`, `backend/src/services/aiGenerator.js`, `backend/migrations/001_initial_schema.sql`, and git history (35 commits, deploy commit `0edb2bc`) — reproduce the exact wording specified below verbatim, do not paraphrase.
- GainForge stays the first card; the new card is inserted second.

---

### Task 1: Wrap existing card in `.project-list` and add the new card markup to `index.html`

**Files:**
- Modify: `index.html:152-178` (currently the lone `.project-card` for GainForge, sitting directly inside `<section id="projects">`)

**Interfaces:**
- Produces: a `.project-list` wrapper class that Task 2's CSS must define, and reuses existing class names (`project-card`, `project-card__top`, `project-card__eyebrow`, `project-card__badge`, `project-card__lede`, `project-card__points`, `project-card__stack`, `hero__actions`, `btn btn--stamp`, `reveal`) already styled by existing CSS.

- [ ] **Step 1: Replace the Projects section body**

Replace this block (`index.html:152-178`):

```html
    <div class="project-card reveal">
      <div class="project-card__top">
        <div>
          <p class="project-card__eyebrow">Solo Build &mdash; Full-Stack Rust</p>
          <h3>GainForge <span>Gamified Fitness RPG</span></h3>
        </div>
        <a class="project-card__badge" href="https://gainforgeapp.com" target="_blank" rel="noopener noreferrer" aria-label="GainForge — visit live site">
          <i class="dot" aria-hidden="true"></i>LIVE
        </a>
      </div>

      <p class="project-card__lede">GainForge turns real workouts into RPG quests &mdash; users earn XP, level up a character, and grow four stats (STR, END, AGI, FLX) by completing daily strength, cardio, flexibility, and endurance sessions. Built solo end-to-end: product design, schema, API, frontend, and production deployment.</p>

      <ul class="project-card__points">
        <li>Full Rust stack front-to-back &mdash; Leptos (WASM) frontend and an Axum backend share a single DTO crate, keeping types identical across client and server.</li>
        <li>Designed the quest/XP/leveling system and a 4-stat character model, plus an admin panel for managing training programs, exercises, and weekly schedules.</li>
        <li>Shipped and self-hosted on a VPS with Docker and PostgreSQL &mdash; 15 schema migrations, 100+ commits, with iterative mobile-UX polish (drawer navigation, responsive schedule grid).</li>
      </ul>

      <div class="project-card__stack">
        <span>Rust</span><span>Leptos (WASM)</span><span>Axum</span><span>PostgreSQL</span><span>Docker</span><span>Self-hosted VPS</span>
      </div>

      <div class="hero__actions">
        <a class="btn btn--stamp" href="https://gainforgeapp.com" target="_blank" rel="noopener noreferrer">Visit GainForge &rarr;</a>
      </div>
    </div>
```

with (the same GainForge card, now nested inside `.project-list`, plus the new second card):

```html
    <div class="project-list">
      <div class="project-card reveal">
        <div class="project-card__top">
          <div>
            <p class="project-card__eyebrow">Solo Build &mdash; Full-Stack Rust</p>
            <h3>GainForge <span>Gamified Fitness RPG</span></h3>
          </div>
          <a class="project-card__badge" href="https://gainforgeapp.com" target="_blank" rel="noopener noreferrer" aria-label="GainForge — visit live site">
            <i class="dot" aria-hidden="true"></i>LIVE
          </a>
        </div>

        <p class="project-card__lede">GainForge turns real workouts into RPG quests &mdash; users earn XP, level up a character, and grow four stats (STR, END, AGI, FLX) by completing daily strength, cardio, flexibility, and endurance sessions. Built solo end-to-end: product design, schema, API, frontend, and production deployment.</p>

        <ul class="project-card__points">
          <li>Full Rust stack front-to-back &mdash; Leptos (WASM) frontend and an Axum backend share a single DTO crate, keeping types identical across client and server.</li>
          <li>Designed the quest/XP/leveling system and a 4-stat character model, plus an admin panel for managing training programs, exercises, and weekly schedules.</li>
          <li>Shipped and self-hosted on a VPS with Docker and PostgreSQL &mdash; 15 schema migrations, 100+ commits, with iterative mobile-UX polish (drawer navigation, responsive schedule grid).</li>
        </ul>

        <div class="project-card__stack">
          <span>Rust</span><span>Leptos (WASM)</span><span>Axum</span><span>PostgreSQL</span><span>Docker</span><span>Self-hosted VPS</span>
        </div>

        <div class="hero__actions">
          <a class="btn btn--stamp" href="https://gainforgeapp.com" target="_blank" rel="noopener noreferrer">Visit GainForge &rarr;</a>
        </div>
      </div>

      <div class="project-card reveal">
        <div class="project-card__top">
          <div>
            <p class="project-card__eyebrow">Solo Build &mdash; Full-Stack JavaScript</p>
            <h3>Upwork Proposal Generator <span>AI Cover Letter Tool</span></h3>
          </div>
          <a class="project-card__badge" href="https://uclg.aditf.com" target="_blank" rel="noopener noreferrer" aria-label="Upwork Proposal Generator — visit live site">
            <i class="dot" aria-hidden="true"></i>LIVE
          </a>
        </div>

        <p class="project-card__lede">Freelancers on Upwork build a profile (skills, bio, experience), paste a job listing URL, and get a tailored, editable cover letter back &mdash; turning &ldquo;found a job I want&rdquo; into &ldquo;submitted a proposal that gets a reply&rdquo; in the time it takes to read the posting.</p>

        <ul class="project-card__points">
          <li>Backend scrapes the pasted Upwork listing (Express + cheerio) with SSRF hardening &mdash; validates and blocks requests to localhost, private/reserved IP ranges, and cloud metadata endpoints before fetching a user-submitted URL.</li>
          <li>Job summary and user profile feed a prompt builder that calls an LLM gateway (Claude Haiku) to draft the cover letter, which the user can edit before saving.</li>
          <li>Full auth/profile/letter-history schema in PostgreSQL (users, profiles, projects, cover_letters with draft/saved status) behind JWT auth; self-hosted on a VPS via git-push deploy (bare repo + post-receive hook + systemd + nginx).</li>
        </ul>

        <div class="project-card__stack">
          <span>React</span><span>Vite</span><span>Tailwind</span><span>Node.js</span><span>Express</span><span>PostgreSQL</span><span>Self-hosted VPS</span>
        </div>

        <div class="hero__actions">
          <a class="btn btn--stamp" href="https://uclg.aditf.com" target="_blank" rel="noopener noreferrer">Visit Upwork Proposal Generator &rarr;</a>
        </div>
      </div>
    </div>
```

- [ ] **Step 2: Verify structure**

Run (from the repo root):

```bash
grep -c 'class="project-card reveal"' index.html   # expect: 2
grep -c 'project-list' index.html                  # expect: 2 (open + close tag)
grep -c 'uclg.aditf.com' index.html                 # expect: 2 (badge + CTA)
python3 -c "
import html.parser
class P(html.parser.HTMLParser):
    pass
P().feed(open('index.html', encoding='utf-8').read())
print('parsed ok')
"
```

Expected output: `2`, `2`, `2`, then `parsed ok` with no exceptions.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "$(cat <<'EOF'
Add Upwork Proposal Generator project card

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Add `.project-list` spacing rule to `styles.css`

**Files:**
- Modify: `styles.css` (insert immediately before the `.project-card{` rule at line 274)

**Interfaces:**
- Consumes: the `.project-list` class produced by Task 1.
- Produces: vertical `32px` gap between sibling `.project-card` elements, consumed visually by Task 3's browser check.

- [ ] **Step 1: Insert the CSS rule**

Insert directly above `.project-card{` (styles.css:274):

```css
.project-list{display:flex; flex-direction:column; gap:32px;}
```

So the surrounding block reads:

```css
/* ---------- projects ---------- */
.project-list{display:flex; flex-direction:column; gap:32px;}
.project-card{
  border:1px solid var(--ink-line);
  padding:40px;
}
```

- [ ] **Step 2: Verify no CSS syntax errors**

Run (from the repo root):

```bash
python3 -c "
css = open('styles.css', encoding='utf-8').read()
assert css.count('{') == css.count('}'), f\"brace mismatch: {css.count('{')} open vs {css.count('}')} close\"
print('braces balanced:', css.count('{'))
"
grep -c '\.project-list' styles.css   # expect: 1
```

Expected: `braces balanced: <N>` with no assertion error, and a count of `1`.

- [ ] **Step 3: Commit**

```bash
git add styles.css
git commit -m "$(cat <<'EOF'
Add spacing between stacked project cards

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Visual verification in a real browser

**Files:** none (verification only; fixes if needed land as follow-up commits touching `index.html` / `styles.css`)

**Interfaces:**
- Consumes: the rendered page at `#projects` produced by Tasks 1–2.

- [ ] **Step 1: Serve the site locally**

```bash
python3 -m http.server 8793 >/tmp/aditf-preview-upwork.log 2>&1 &
echo $! > /tmp/aditf-preview-upwork.pid
sleep 1
curl -sf http://localhost:8793/index.html >/dev/null && echo "server up"
```

Expected: `server up`. (Port 8793 used to avoid clashing with any other preview server that might already be running on 8791/8792.)

- [ ] **Step 2: Visually inspect the Projects section**

Use the gstack `/browse` skill to open `http://localhost:8793/#projects` and confirm, at both desktop (~1280px) and mobile (~390px) widths:
- Both cards render, GainForge first, Upwork Proposal Generator second, with a clear visible gap between them (not touching borders).
- The second card shows title "Upwork Proposal Generator — AI Cover Letter Tool", the amber pulsing `LIVE` badge, lede paragraph, three bullet points, seven stack chips (React, Vite, Tailwind, Node.js, Express, PostgreSQL, Self-hosted VPS), and the "Visit Upwork Proposal Generator →" button.
- Both cards fade/slide in on scroll independently (same `reveal` animation as GainForge already had) — disable if `prefers-reduced-motion` is on and confirm both are visible immediately instead.
- No layout overflow or text clipping at mobile width, especially the longer title/CTA text on the new card.
- The `LIVE` badge and "Visit Upwork Proposal Generator →" button both point to `https://uclg.aditf.com` and open in a new tab.

If any issue is found, fix it in `index.html`/`styles.css` and re-run Step 2 until clean, then commit the fix with its own descriptive message.

- [ ] **Step 3: Stop the local server**

```bash
kill "$(cat /tmp/aditf-preview-upwork.pid)" 2>/dev/null
rm -f /tmp/aditf-preview-upwork.pid /tmp/aditf-preview-upwork.log
```
