# GainForge Projects Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Projects" section to the aditf portfolio site showcasing GainForge (a solo-built, full-stack-Rust gamified fitness app) as a full case-study card, matching the site's existing tracking-manifest visual language.

**Architecture:** Static site, no build step — `index.html` (markup) + `styles.css` (styling) + `script.js` (generic scroll-reveal/nav-toggle behavior, unmodified). One new `<section id="projects">` inserted between the existing Skills and Experience sections, one new `.project-card` CSS component reusing existing design tokens.

**Tech Stack:** Plain HTML5/CSS3, no JS framework, no build tooling, no test framework — this repo has none of the above, so verification is structural (grep/brace-balance checks) plus a manual visual pass in a real browser via the gstack `/browse` skill.

## Global Constraints

- Reuse existing design tokens only (`--ink`, `--paper`, `--amber`, `--steel`, `--kraft`, `--ink-line`, `--amber-soft`, fonts) — no new colors or fonts.
- Single project card, no grid layout (spec: "No second project card / grid layout — single card only").
- No changes to `script.js` — it has no section-id-specific logic; the new section only needs the `reveal` class to pick up the existing `IntersectionObserver` behavior.
- Text-only case study — no screenshots or mockups of the GainForge UI.
- CTA / badge links to `https://gainforgeapp.com`, `target="_blank" rel="noopener noreferrer"`.
- Copy is sourced from `~/personal/fitness/PRODUCT.md`, `~/personal/fitness/landing/index.html`, and `~/personal/fitness` git history — reproduce the exact wording specified below verbatim, do not paraphrase.
- Nav renumbering: Projects becomes `03`, Experience/Certs/Contact shift to `04`/`05`/`06`.
- **Working directory:** this task runs inside the git worktree at `/home/adit/personal/aditf/.claude/worktrees/gainforge-projects-section` — all file paths and shell commands below (including any `cd /home/adit/personal/aditf`) target that worktree root, NOT the original `/home/adit/personal/aditf` checkout.

---

### Task 1: Add nav link and Projects section markup to `index.html`

**Files:**
- Modify: `index.html:24-30` (nav links)
- Modify: `index.html` (insert new section between the Skills section's closing `</section>` at line 142 and the `<!-- EXPERIENCE -->` comment at line 144)

**Interfaces:**
- Produces: a new anchor target `id="projects"` that Task 3's visual check navigates to via `#projects`, and CSS class names (`project-card`, `project-card__top`, `project-card__eyebrow`, `project-card__badge`, `project-card__lede`, `project-card__points`, `project-card__stack`, `project-card__actions`) that Task 2's CSS must define.

- [x] **Step 1: Update the nav links block**

Replace the current nav block:

```html
  <nav class="nav__links" id="navLinks">
    <a href="#about"><span class="idx">01</span>About</a>
    <a href="#skills"><span class="idx">02</span>Skills</a>
    <a href="#experience"><span class="idx">03</span>Experience</a>
    <a href="#certifications"><span class="idx">04</span>Certs</a>
    <a href="#contact"><span class="idx">05</span>Contact</a>
  </nav>
```

with:

```html
  <nav class="nav__links" id="navLinks">
    <a href="#about"><span class="idx">01</span>About</a>
    <a href="#skills"><span class="idx">02</span>Skills</a>
    <a href="#projects"><span class="idx">03</span>Projects</a>
    <a href="#experience"><span class="idx">04</span>Experience</a>
    <a href="#certifications"><span class="idx">05</span>Certs</a>
    <a href="#contact"><span class="idx">06</span>Contact</a>
  </nav>
```

- [x] **Step 2: Insert the Projects section**

Immediately before the `<!-- EXPERIENCE -->` comment (right after the Skills section's closing `</section>`), insert:

```html
  <!-- PROJECTS -->
  <section class="section" id="projects">
    <div class="section__head">
      <p class="eyebrow">Cargo Log &mdash; Personal Freight</p>
      <h2>Projects</h2>
    </div>

    <div class="project-card reveal">
      <div class="project-card__top">
        <div>
          <p class="project-card__eyebrow">Solo Build &mdash; Full-Stack Rust</p>
          <h3>GainForge <span>Gamified Fitness RPG</span></h3>
        </div>
        <a class="project-card__badge" href="https://gainforgeapp.com" target="_blank" rel="noopener noreferrer">
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

      <div class="project-card__actions">
        <a class="btn btn--stamp" href="https://gainforgeapp.com" target="_blank" rel="noopener noreferrer">Visit GainForge &rarr;</a>
      </div>
    </div>
  </section>

```

- [x] **Step 3: Verify structure**

Run (from the worktree root):

```bash
grep -c 'id="projects"' index.html          # expect: 1
grep -c '<span class="idx">0[1-6]</span>' index.html  # expect: 6
python3 -c "
import html.parser, sys
class P(html.parser.HTMLParser):
    pass
P().feed(open('index.html', encoding='utf-8').read())
print('parsed ok')
"
```

Expected output: `1`, `6`, then `parsed ok` with no exceptions.

- [x] **Step 4: Commit**

```bash
git add index.html
git commit -m "$(cat <<'EOF'
Add Projects nav entry and GainForge case-study markup

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Add `.project-card` styling to `styles.css`

**Files:**
- Modify: `styles.css` (insert new rule block immediately after the `.crate-grid`/`.crate` rules end at line 271, before the `/* ---------- timeline ---------- */` comment at line 273)

**Interfaces:**
- Consumes: class names produced by Task 1 (`project-card`, `project-card__top`, `project-card__eyebrow`, `project-card__badge`, `project-card__lede`, `project-card__points`, `project-card__stack`, `project-card__actions`), and existing global tokens/classes (`--ink-line`, `--paper`, `--paper-dim`, `--steel`, `--amber`, `--amber-soft`, `--kraft`, `--font-mono`, `.dot`, `.btn`, `.btn--stamp`).

- [x] **Step 1: Insert the CSS block**

Insert after line 271 (the closing `}` of `.crate__items span`) and before the `/* ---------- timeline ---------- */` comment:

```css

/* ---------- projects ---------- */
.project-card{
  border:1px solid var(--ink-line);
  padding:40px;
}
.project-card__top{
  display:flex; flex-wrap:wrap; align-items:flex-start; justify-content:space-between;
  gap:16px; margin-bottom:22px;
}
.project-card__eyebrow{
  font-family:var(--font-mono); font-size:12px; letter-spacing:.08em;
  text-transform:uppercase; color:var(--steel); margin:0 0 8px;
}
.project-card__top h3{
  font-size:22px; text-transform:none; font-weight:600; color:var(--paper); margin:0;
}
.project-card__top h3 span{
  display:block; font-family:var(--font-mono); font-size:13px;
  color:var(--steel); font-weight:400; text-transform:uppercase;
  letter-spacing:.04em; margin-top:4px;
}
.project-card__badge{
  display:flex; align-items:center; gap:8px;
  font-family:var(--font-mono); font-size:12px; letter-spacing:.08em;
  text-transform:uppercase; color:var(--amber);
  text-decoration:none; white-space:nowrap;
  border:1px solid var(--amber); padding:6px 12px; border-radius:2px;
  transition:background .18s ease, color .18s ease;
}
.project-card__badge:hover{background:var(--amber-soft);}
.project-card__lede{
  max-width:640px; font-size:17px; color:var(--paper-dim); margin:0 0 24px;
}
.project-card__points{
  list-style:none; display:flex; flex-direction:column; gap:10px;
  max-width:680px; margin:0 0 28px;
}
.project-card__points li{
  position:relative; padding-left:18px; color:var(--paper-dim); font-size:15px;
}
.project-card__points li::before{
  content:"›"; position:absolute; left:0; color:var(--amber);
}
.project-card__stack{
  display:flex; flex-wrap:wrap; gap:8px; margin-bottom:28px;
}
.project-card__stack span{
  font-family:var(--font-mono); font-size:11.5px;
  color:var(--kraft); background:var(--amber-soft);
  border:1px solid rgba(232,135,30,.35);
  padding:4px 9px; border-radius:2px;
}
.project-card__actions{display:flex; flex-wrap:wrap; gap:16px;}
```

- [x] **Step 2: Verify no CSS syntax errors**

Run (from the worktree root):

```bash
python3 -c "
css = open('styles.css', encoding='utf-8').read()
assert css.count('{') == css.count('}'), f\"brace mismatch: {css.count('{')} open vs {css.count('}')} close\"
print('braces balanced:', css.count('{'))
"
grep -c '\.project-card' styles.css   # expect: at least 9 (one per selector variant above)
```

Expected: `braces balanced: <N>` with no assertion error, and a count ≥ 9.

- [x] **Step 3: Commit**

```bash
git add styles.css
git commit -m "$(cat <<'EOF'
Style the GainForge project-card component

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Visual verification in a real browser

**Files:** none (verification only; fixes if needed land as follow-up commits touching `index.html` / `styles.css`)

**Interfaces:**
- Consumes: the rendered page at `#projects` produced by Tasks 1–2.

- [x] **Step 1: Serve the site locally**

```bash
python3 -m http.server 8792 >/tmp/aditf-preview-worktree.log 2>&1 &
echo $! > /tmp/aditf-preview-worktree.pid
sleep 1
curl -sf http://localhost:8792/index.html >/dev/null && echo "server up"
```

Expected: `server up`. (Port 8792 used instead of 8791 to avoid clashing with any preview server the original checkout might be running.)

- [x] **Step 2: Visually inspect the Projects section**

Use the gstack `/browse` skill to open `http://localhost:8792/#projects` and confirm, at both desktop (~1280px) and mobile (~390px) widths:
- The nav shows `03 Projects` between Skills and Projects, and Experience/Certs/Contact read `04`/`05`/`06`.
- The project card renders with title "GainForge — Gamified Fitness RPG", the amber pulsing `LIVE` badge, lede paragraph, three bullet points, six stack chips (Rust, Leptos (WASM), Axum, PostgreSQL, Docker, Self-hosted VPS), and the "Visit GainForge →" button.
- The card fades/slides in on scroll (same `reveal` animation as other sections) — disable if `prefers-reduced-motion` is on and confirm it's visible immediately instead.
- No layout overflow or text clipping at mobile width.
- The `LIVE` badge and "Visit GainForge →" button both point to `https://gainforgeapp.com` and open in a new tab (check `target="_blank"` in devtools/inspect if the browse skill supports it, otherwise confirm via `grep 'gainforgeapp.com' index.html` that both links are present).

If any issue is found, fix it in `index.html`/`styles.css` and re-run Step 2 until clean, then commit the fix with its own descriptive message.

- [x] **Step 3: Stop the local server**

```bash
kill "$(cat /tmp/aditf-preview-worktree.pid)" 2>/dev/null
rm -f /tmp/aditf-preview-worktree.pid /tmp/aditf-preview-worktree.log
```
