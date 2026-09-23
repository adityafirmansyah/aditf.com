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
    sitemap.xml                  every HTML URL (repo root, auto-regenerated)
    robots.txt                   crawler rules + sitemap pointer (repo root)
    blog/<slug>/og.png           social share card (when Pillow is available)

SEO: every page carries canonical, Open Graph, twitter:card and JSON-LD.
sitemap.xml/robots.txt are GENERATED, not hand-written — a hand-maintained
sitemap goes stale the moment a post is added, so they are rebuilt on every run.
"""
import html as h
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import markdown

# Pillow is optional: without it the build still succeeds, it just skips the
# social share cards. Never let an image dependency break publishing.
try:
    from PIL import Image, ImageDraw, ImageFont
    HAVE_PIL = True
except ImportError:  # bind the names so linters see them as always-defined
    Image = ImageDraw = ImageFont = None
    HAVE_PIL = False

BLOG_DIR = Path(__file__).resolve().parent          # .../blog
REPO_DIR = BLOG_DIR.parent                          # repo root
POSTS_DIR = BLOG_DIR / "posts"
SITE_URL = "https://aditf.com"
BLOG_URL = SITE_URL + "/blog/"
WORDS_PER_MIN = 200

# --- site identity (used by Open Graph + JSON-LD) ---------------------------
SITE_NAME = "Aditya Firmansyah"
BLOG_NAME = "Field Notes"
AUTHOR = "Aditya Firmansyah"
AUTHOR_JOB = "Senior Software Engineer — Full-Stack Developer"
AUTHOR_URL = SITE_URL + "/"
SAME_AS = [
    "https://github.com/adityafirmansyah",
    "https://linkedin.com/in/aditya-firmansyah-21940845",
]
SITE_DESCRIPTION = ("Aditya Firmansyah — Senior Software Engineer & Full-Stack Developer. "
                    "13+ years building logistics platforms, microservices, and cloud-native "
                    "applications.")
BLOG_DESCRIPTION = ("Practitioner notes on software engineering, AI agents, e-commerce, and "
                    "self-hosting by Aditya Firmansyah.")

# Waybill design tokens (mirrors styles.css :root)
INK = "#14181B"
INK_SOFT = "#1B2023"
PAPER = "#EDE6D6"
PAPER_DIM = "#9CA3A0"
AMBER = "#E8871E"
OG_W, OG_H = 1200, 630

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


def iso_date(iso):
    """YYYY-MM-DD -> full ISO-8601 with UTC offset (required by JSON-LD/sitemap)."""
    try:
        return datetime.strptime(iso, "%Y-%m-%d").replace(tzinfo=timezone.utc).isoformat()
    except (ValueError, TypeError):
        return datetime.now(timezone.utc).isoformat()


def og_block(title, description, url, image=None, locale="en_US",
             og_type="website", site_name=None, published=None, author=None,
             tags=None, jsonld=None):
    """Open Graph + twitter:card + JSON-LD for one page."""
    out = []
    sn = site_name or f"{BLOG_NAME} — {SITE_NAME}"
    out.append(f'<meta property="og:site_name" content="{esc(sn)}">')
    out.append(f'<meta property="og:type" content="{esc(og_type)}">')
    out.append(f'<meta property="og:title" content="{esc(title)}">')
    out.append(f'<meta property="og:description" content="{esc(description)}">')
    out.append(f'<meta property="og:url" content="{esc(url)}">')
    out.append(f'<meta property="og:locale" content="{esc(locale)}">')
    if image:
        out.append(f'<meta property="og:image" content="{esc(image)}">')
        out.append(f'<meta property="og:image:width" content="{OG_W}">')
        out.append(f'<meta property="og:image:height" content="{OG_H}">')
        out.append(f'<meta property="og:image:alt" content="{esc(title)}">')
    # twitter — summary_large_image needs the card type set explicitly
    out.append('<meta name="twitter:card" content="summary_large_image">')
    out.append(f'<meta name="twitter:title" content="{esc(title)}">')
    out.append(f'<meta name="twitter:description" content="{esc(description)}">')
    if image:
        out.append(f'<meta name="twitter:image" content="{esc(image)}">')
    out.append(f'<meta name="author" content="{esc(author or AUTHOR)}">')
    out.append('<meta name="theme-color" content="#14181B">')
    if published:
        out.append(f'<meta property="article:published_time" content="{esc(published)}">')
    for t in (tags or []):
        out.append(f'<meta property="article:tag" content="{esc(t)}">')
    if jsonld:
        out.append('<script type="application/ld+json">'
                   + json.dumps(jsonld, ensure_ascii=False) + '</script>')
    return "\n".join(out)


def person_jsonld():
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": AUTHOR,
        "jobTitle": AUTHOR_JOB,
        "url": AUTHOR_URL,
        "sameAs": SAME_AS,
        "address": {"@type": "PostalAddress", "addressLocality": "Surakarta",
                    "addressRegion": "Central Java", "addressCountry": "ID"},
    }


def head(title, description, extra="", url=None, image=None, locale="en_US",
         og_type="website", published=None, tags=None, jsonld=None,
         site_name=None):
    """Build <head>. SEO tags are emitted only when `url` is supplied, so legacy
    callers that omit it still produce valid pages."""
    seo = ""
    if url:
        seo = og_block(title, description, url, image=image, locale=locale,
                       og_type=og_type, site_name=site_name, published=published,
                       tags=tags, jsonld=jsonld)
        seo = "\n<link rel=\"canonical\" href=\"" + esc(url) + "\">\n" + seo
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
{seo}
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

def build_listing(posts, og_url=None):
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
    page = head(f"{BLOG_NAME} — {SITE_NAME}", BLOG_DESCRIPTION,
                url=BLOG_URL, image=og_url,
                locale="en_US", og_type="website", jsonld={
                    "@context": "https://schema.org",
                    "@type": "Blog",
                    "name": f"{BLOG_NAME} — {SITE_NAME}",
                    "description": BLOG_DESCRIPTION,
                    "url": BLOG_URL,
                    "inLanguage": ["en-US", "id-ID"],
                    "publisher": {"@type": "Person", "name": AUTHOR, "url": AUTHOR_URL},
                    "blogPost": [{
                        "@type": "BlogPosting",
                        "headline": e["en"]["meta"]["title"],
                        "url": f"{BLOG_URL}{e['slug']}/",
                        "datePublished": iso_date(e["en"]["meta"]["date"]),
                    } for e in posts],
                })
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
    has_other = other in e
    # ABSOLUTE urls only: Google ignores hreflang/canonical with relative hrefs
    # (the previous version emitted a relative EN alternate, so the pairing was
    # silently broken).
    url = BLOG_URL + (f"{slug}/" if lang == "en" else f"{slug}/id/")
    alt_url = BLOG_URL + (f"{slug}/id/" if lang == "en" else f"{slug}/")

    extra = []
    if has_other:
        extra.append(f'<link rel="alternate" hreflang="{other}" href="{esc(alt_url)}">')
    extra.append(f'<link rel="alternate" hreflang="{lang}" href="{esc(url)}">')
    # x-default helps Google pick a version for unmatched locales
    extra.append(f'<link rel="alternate" hreflang="x-default" href="{esc(BLOG_URL + slug + "/")}">')

    title = f"{meta['title']} — {BLOG_NAME}"
    description = meta.get("excerpt", title)
    og_image = build_og_image(slug, meta["title"], fmt_date(meta["date"]), lang)
    published = iso_date(meta["date"])

    jsonld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": meta["title"],
        "description": description,
        "datePublished": published,
        "dateModified": published,
        "inLanguage": "id-ID" if lang == "id" else "en-US",
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "keywords": ", ".join(meta["tags"]),
        "author": {"@type": "Person", "name": AUTHOR, "url": AUTHOR_URL,
                   "jobTitle": AUTHOR_JOB},
        "publisher": {"@type": "Person", "name": AUTHOR, "url": AUTHOR_URL},
        "articleSection": "Software Engineering",
        "wordCount": len(re.findall(r"\S+", body)),
    }
    if og_image:
        jsonld["image"] = [og_image]
    if has_other:
        # schema.org hasTranslation makes the bilingual pairing machine-readable
        jsonld["hasTranslation"] = {
            "@type": "BlogPosting", "url": alt_url,
            "inLanguage": "id-ID" if lang == "en" else "en-US"}

    page = head(title, description, "\n".join(extra), url=url, image=og_image,
                locale="id_ID" if lang == "id" else "en_US", og_type="article",
                published=published, tags=meta["tags"], jsonld=jsonld,
                site_name=f"{BLOG_NAME} — {SITE_NAME}")
    # set the lang attribute correctly on the real <html> element (the previous
    # implementation appended a stray '<html lang="id"' fragment into <body>)
    page = page.replace('<html lang="en">', f'<html lang="{lang}">', 1)
    page += NAV
    tags = "".join(f"<span>{esc(t)}</span>" for t in meta["tags"])
    switch = ""
    if has_other:
        label = "Baca dalam Bahasa Indonesia" if lang == "en" else "Read in English"
        switch = f'<a class="btn btn--ghost post-lang-switch" href="{alt_url}">{label}</a>'
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



def build_sitemap(posts):
    """Generate sitemap.xml at repo root covering every HTML URL.

    Regenerated on every build so it can never go stale when the daily pipeline
    adds a post. Uses lastmod from the post date (or now for the index pages).
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = [(SITE_URL + "/", now, "weekly", "1.0"),
            (BLOG_URL, now, "daily", "0.9")]
    for e in posts:
        d = e["en"]["meta"]["date"]
        urls.append((f"{BLOG_URL}{e['slug']}/", d, "monthly", "0.8"))
        if "id" in e:
            urls.append((f"{BLOG_URL}{e['slug']}/id/", d, "monthly", "0.7"))

    body = "\n".join(
        f"""  <url>
    <loc>{esc(u)}</loc>
    <lastmod>{esc(lm)}</lastmod>
    <changefreq>{cf}</changefreq>
    <priority>{pr}</priority>
  </url>""" for u, lm, cf, pr in urls)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
{body}
</urlset>
"""
    (REPO_DIR / "sitemap.xml").write_text(xml, encoding="utf-8")
    return len(urls)


def build_robots():
    """robots.txt at repo root: allow everything, point at the sitemap."""
    txt = f"""User-agent: *
Allow: /

# Crawl-delay kept low: static site, no backend load.
Crawl-delay: 1

Sitemap: {SITE_URL}/sitemap.xml
"""
    (REPO_DIR / "robots.txt").write_text(txt, encoding="utf-8")


FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _font(size):
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    """Greedy word wrap to a pixel width."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def build_og_image(slug, title, date_str, lang):
    """Render a 1200x630 waybill-style share card. Returns the public URL or None.

    Text-only (no photo) — matches the site's design language. Skipped silently
    when Pillow is unavailable so publishing never depends on it.
    """
    if not HAVE_PIL:
        return None
    out_dir = BLOG_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"og.{lang}.png"

    img = Image.new("RGB", (OG_W, OG_H), INK)
    d = ImageDraw.Draw(img)

    # left amber rule + waybill band
    d.rectangle([0, 0, 10, OG_H], fill=AMBER)
    d.rectangle([60, 58, OG_W - 60, 112], outline="#2B3236", width=2)
    d.rectangle([60, 58, 64, 112], fill=AMBER)

    eyebrow = f"FIELD NOTES  ·  {date_str}  ·  {'EN' if lang == 'en' else 'ID'}"
    d.text((84, 74), eyebrow, font=_font(24), fill=PAPER_DIM)

    # title, wrapped
    tf = _font(64)
    lines = _wrap(d, title, tf, OG_W - 150)[:4]
    y = 170
    for ln in lines:
        d.text((64, y), ln, font=tf, fill=PAPER)
        y += 78

    # author block pinned near the bottom
    d.text((64, OG_H - 130), AUTHOR, font=_font(34), fill=AMBER)
    d.text((64, OG_H - 84), AUTHOR_JOB, font=_font(24), fill=PAPER_DIM)
    d.text((64, OG_H - 50), SITE_URL, font=_font(22), fill="#5A6469")

    img.save(out, "PNG", optimize=True)
    return f"{SITE_URL}/blog/{slug}/og.{lang}.png"


def build_blog_og_image():
    """Share card for the /blog/ listing itself. Returns public URL or None."""
    if not HAVE_PIL:
        return None
    out = BLOG_DIR / "og.png"
    img = Image.new("RGB", (OG_W, OG_H), INK)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 10, OG_H], fill=AMBER)
    d.rectangle([60, 58, OG_W - 60, 112], outline="#2B3236", width=2)
    d.rectangle([60, 58, 64, 112], fill=AMBER)
    d.text((84, 74), "CARGO LOG  ·  ADITF.COM", font=_font(24), fill=PAPER_DIM)
    d.text((64, 180), "Field Notes", font=_font(96), fill=PAPER)
    for i, ln in enumerate(_wrap(d, BLOG_DESCRIPTION, _font(34), OG_W - 160)[:3]):
        d.text((64, 300 + i * 46), ln, font=_font(34), fill=PAPER_DIM)
    d.text((64, OG_H - 130), AUTHOR, font=_font(34), fill=AMBER)
    d.text((64, OG_H - 84), AUTHOR_JOB, font=_font(24), fill=PAPER_DIM)
    d.text((64, OG_H - 50), SITE_URL, font=_font(22), fill="#5A6469")
    img.save(out, "PNG", optimize=True)
    return f"{SITE_URL}/blog/og.png"


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
    blog_og = build_blog_og_image()
    build_listing(posts, og_url=blog_og)
    for e in posts:
        build_post(e, "en")
        if "id" in e:
            build_post(e, "id")
    build_rss(posts)
    n_urls = build_sitemap(posts)
    build_robots()
    print(f"built: listing + {len(posts)} post(s) "
          f"({sum(1 for e in posts if 'id' in e)} bilingual), rss.xml, "
          f"sitemap.xml ({n_urls} URLs), robots.txt, "
          f"og images={'yes' if (HAVE_PIL and blog_og) else 'skipped (no Pillow)'}")
    if not HAVE_PIL:
        print("  note: Pillow unavailable — social share cards skipped; "
              "pages still carry all other SEO tags.", file=sys.stderr)


if __name__ == "__main__":
    main()
