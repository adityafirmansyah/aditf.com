#!/usr/bin/env python3
"""Static blog generator for aditf.com — waybill design, bilingual EN/ID.

Reads markdown posts from blog/posts/<slug>.en.md and blog/posts/<slug>.id.md,
emits static HTML into blog/ (committed to the repo — deploy is a plain push).

Frontmatter (minimal YAML subset, one `key: value` per line between --- fences):
    title, slug, date (YYYY-MM-DD), excerpt, tags (comma-separated)

Output:
    blog/index.html              post listing (EN-first, ID badge when present)
    blog/<slug>/index.html       EN post
    blog/<slug>/id/index.html    ID post (when .id.md exists)
    blog/rss.xml                 EN feed (last 20)
"""
import html as h
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import markdown

BLOG_DIR = Path(__file__).resolve().parent          # .../blog
REPO_DIR = BLOG_DIR.parent                          # repo root
POSTS_DIR = BLOG_DIR / "posts"
SITE_URL = "https://aditf.com"
BLOG_URL = SITE_URL + "/blog/"
WORDS_PER_MIN = 200

# ---------------------------------------------------------------- frontmatter

def parse_frontmatter(text):
    """Return (meta dict, body markdown). Tolerates missing fences."""
    meta = {}
    body = text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if m:
        body = text[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip()
    tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    meta["tags"] = tags
    return meta, body


def load_posts():
    """Pair <slug>.en.md with optional <slug>.id.md. Sorted newest first."""
    posts = {}
    for f in sorted(POSTS_DIR.glob("*.md")):
        m = re.match(r"^(.+)\.(en|id)\.md$", f.name)
        if not m:
            print(f"SKIP (name must be <slug>.en.md / <slug>.id.md): {f.name}", file=sys.stderr)
            continue
        slug, lang = m.group(1), m.group(2)
        meta, body = parse_frontmatter(f.read_text(encoding="utf-8"))
        meta.setdefault("slug", slug)
        if not meta.get("title") or not meta.get("date"):
            print(f"SKIP (missing title/date frontmatter): {f.name}", file=sys.stderr)
            continue
        entry = posts.setdefault(slug, {"slug": slug})
        entry[lang] = {"meta": meta, "body": body, "file": f}
    for slug, e in posts.items():
        if "en" not in e:
            print(f"SKIP (no EN version): {slug}", file=sys.stderr)
            del posts[slug]
    return sorted(posts.values(), key=lambda e: e["en"]["meta"]["date"], reverse=True)

# ------------------------------------------------------------------- templates

def esc(s):
    return h.escape(str(s), quote=True)


def head(title, description, extra=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%2314181B'/%3E%3Ctext x='50' y='68' font-size='58' font-family='monospace' font-weight='700' fill='%23E8871E' text-anchor='middle'%3EAF%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">
<link rel="stylesheet" href="/blog/blog.css">
<link rel="alternate" type="application/rss+xml" title="Aditya Firmansyah — Field Notes" href="{BLOG_URL}rss.xml">
<script>document.documentElement.classList.add('js');</script>
{extra}
</head>
<body>
"""


NAV = """<div class="route-progress" aria-hidden="true"><span id="routeFill"></span></div>

<header class="nav" id="siteNav">
  <a href="/" class="nav__mark" aria-label="Home">AF</a>
  <button class="nav__toggle" id="navToggle" aria-expanded="false" aria-controls="navLinks" aria-label="Toggle navigation">
    <span></span><span></span><span></span>
  </button>
  <nav class="nav__links" id="navLinks">
    <a href="/#about"><span class="idx">01</span>About</a>
    <a href="/#skills"><span class="idx">02</span>Skills</a>
    <a href="/#projects"><span class="idx">03</span>Projects</a>
    <a href="/#experience"><span class="idx">04</span>Experience</a>
    <a href="/#certifications"><span class="idx">05</span>Certs</a>
    <a href="/#contact"><span class="idx">06</span>Contact</a>
    <a href="/blog/" class="is-current"><span class="idx">07</span>Blog</a>
  </nav>
</header>
"""

FOOTER = """<footer class="footer">
  <span>&copy; 2026 Aditya Firmansyah</span>
  <span class="footer__id">MANIFEST REF. AF&middot;SWE&middot;2026</span>
</footer>
<script src="/script.js"></script>
</body>
</html>
"""


def fmt_date(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d %b %Y")
    except ValueError:
        return iso


def reading_time(body):
    words = len(re.findall(r"\S+", body))
    return max(1, round(words / WORDS_PER_MIN))

# ---------------------------------------------------------------------- pages

def build_listing(posts):
    cards = []
    for e in posts:
        meta = e["en"]["meta"]
        slug = e["slug"]
        tags = "".join(f"<span>{esc(t)}</span>" for t in meta["tags"][:5])
        id_badge = ('<span class="post-card__lang" title="Bahasa Indonesia version available">ID</span>'
                    if "id" in e else "")
        cards.append(f"""    <a class="post-card reveal" href="/blog/{esc(slug)}/">
      <div class="post-card__date">
        <span class="post-card__day">{esc(fmt_date(meta['date']))}</span>
        <span class="post-card__rt">{reading_time(e['en']['body'])} min read</span>
      </div>
      <div class="post-card__body">
        <h3>{esc(meta['title'])} {id_badge}</h3>
        <p>{esc(meta.get('excerpt', ''))}</p>
        <div class="post-card__tags">{tags}</div>
      </div>
      <span class="post-card__go" aria-hidden="true">&rarr;</span>
    </a>""")
    if not cards:
        cards.append("""    <div class="label-card reveal">
      <span class="label-card__tape" aria-hidden="true"></span>
      <p>No shipments logged yet. Field notes are on their way.</p>
    </div>""")
    page = head("Field Notes — Aditya Firmansyah",
                "Practitioner notes on software engineering, AI agents, e-commerce, and self-hosting by Aditya Firmansyah.")
    page += NAV
    page += f"""<main id="top">
  <section class="section blog-hero">
    <div class="section__head">
      <p class="eyebrow">Cargo Log &mdash; Field Notes</p>
      <h2>Blog</h2>
    </div>
    <div class="label-card reveal">
      <span class="label-card__tape" aria-hidden="true"></span>
      <p>Practitioner notes from 13+ years of shipping software &mdash; logistics platforms, e-commerce, AI agents, and the self-hosted infrastructure underneath. English and Bahasa Indonesia.</p>
    </div>
    <div class="post-list">
{chr(10).join(cards)}
    </div>
  </section>
</main>
"""
    page += FOOTER
    (BLOG_DIR / "index.html").write_text(page, encoding="utf-8")

# keep FOOTER definition above usable (module order fix)
FOOTER = FOOTER  # noqa


def build_post(e, lang):
    entry = e[lang]
    meta, body = entry["meta"], entry["body"]
    slug = e["slug"]
    other = "id" if lang == "en" else "en"
    lang_href = (f"/blog/{slug}/id/" if lang == "en"
                 else f"/blog/{slug}/") if other in e or lang == "id" else None
    if lang == "id" and "en" in e:
        lang_href = f"/blog/{slug}/"
    if lang == "en" and "id" not in e:
        lang_href = None
    url = BLOG_URL + (f"{slug}/" if lang == "en" else f"{slug}/id/")
    extra = [f'<link rel="canonical" href="{url}">']
    if lang_href:
        label = "Bahasa Indonesia" if lang == "en" else "English"
        extra.append(f'<link rel="alternate" hreflang="{other if lang=="en" else "en"}" href="{lang_href}">')
    extra.append(f'<link rel="alternate" hreflang="{lang}" href="{url}">')
    title = f"{meta['title']} — Field Notes"
    page = head(title, meta.get("excerpt", title), "\n".join(extra))
    page += f'<html lang="{lang}"'  # placeholder replaced below
    page = page.replace('<html lang="en">', f'<html lang="{lang}">', 1)
    page += NAV
    tags = "".join(f"<span>{esc(t)}</span>" for t in meta["tags"])
    switch = ""
    if lang_href:
        label = "Baca dalam Bahasa Indonesia" if lang == "en" else "Read in English"
        switch = f'<a class="btn btn--ghost post-lang-switch" href="{lang_href}">{label}</a>'
    body_html = markdown.markdown(
        body, extensions=["fenced_code", "tables", "sane_lists", "attr_list"])
    page += f"""<main id="top">
  <article class="section post">
    <div class="post__waybill">
      <span class="waybill__field">FILED <b>{esc(fmt_date(meta['date']))}</b></span>
      <span class="waybill__divider" aria-hidden="true">&middot;</span>
      <span class="waybill__field">{reading_time(entry['body'])} MIN READ</span>
      <span class="waybill__divider" aria-hidden="true">&middot;</span>
      <span class="waybill__status"><i class="dot" aria-hidden="true"></i>{'EN' if lang == 'en' else 'ID'}</span>
    </div>
    <h1 class="post__title">{esc(meta['title'])}</h1>
    <div class="post__tags">{tags}</div>
    <div class="post__content reveal is-visible">
{body_html}
    </div>
    <div class="hero__actions post__footer-actions">
      <a class="btn btn--stamp" href="/blog/">&larr; All field notes</a>
      {switch}
    </div>
  </article>
</main>
"""
    page += FOOTER
    out = BLOG_DIR / slug / ("index.html" if lang == "en" else "id/index.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")


def build_rss(posts):
    items = []
    for e in posts[:20]:
        meta = e["en"]["meta"]
        body_html = markdown.markdown(e["en"]["body"], extensions=["fenced_code", "tables"])
        pub = datetime.strptime(meta["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        items.append(f"""    <item>
      <title>{esc(meta['title'])}</title>
      <link>{BLOG_URL}{esc(e['slug'])}/</link>
      <guid isPermaLink="true">{BLOG_URL}{esc(e['slug'])}/</guid>
      <pubDate>{pub.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
      <description>{esc(meta.get('excerpt', ''))}</description>
      <enclosure url="" length="0" type="text/html"/>
    </item>""")
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Aditya Firmansyah — Field Notes</title>
    <link>{BLOG_URL}</link>
    <description>Practitioner notes on software engineering, AI agents, and self-hosting.</description>
    <language>en</language>
    <atom:link href="{BLOG_URL}rss.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (BLOG_DIR / "rss.xml").write_text(rss, encoding="utf-8")


def main():
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    posts = load_posts()
    build_listing(posts)
    for e in posts:
        build_post(e, "en")
        if "id" in e:
            build_post(e, "id")
    build_rss(posts)
    print(f"built: listing + {len(posts)} post(s) "
          f"({sum(1 for e in posts if 'id' in e)} bilingual), rss.xml")


if __name__ == "__main__":
    main()
