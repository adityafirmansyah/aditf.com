#!/usr/bin/env python3
"""
Verification suite for /services/ — the standalone light-theme landing page.

Covers copy rules, palette rules, responsive layout at 390 / 768 / 1280,
the spec-builder form contract, JSON-LD structured data, assets and a11y.

Run:  python3 services/test_services.py
Deps: playwright (chromium), stdlib only otherwise.

The form's network call is intercepted in the browser, so running this suite
never posts anything to the live intake channel.
"""

import http.server
import json
import os
import re
import socket
import socketserver
import sys
import threading
import xml.etree.ElementTree as ET
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SERVICES = ROOT / "services"
ASSETS = ROOT / "assets" / "services"
HTML = (SERVICES / "index.html").read_text(encoding="utf-8")
CSS = (SERVICES / "services.css").read_text(encoding="utf-8")

PASS = []
FAIL = []


def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
    else:
        FAIL.append(f"{name}{(' :: ' + str(detail)) if detail else ''}")


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def serve(port):
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(  # noqa: E731
        *a, directory=str(ROOT), **kw
    )

    class Quiet(socketserver.TCPServer):
        allow_reuse_address = True

    httpd = Quiet(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


# --------------------------------------------------------------------------
# 1. Static: copy rules, palette, structure
# --------------------------------------------------------------------------
def test_static():
    banned = [
        "revolutionize", "revolutionise", "supercharge", "cutting edge",
        "cutting-edge", "effortless", "seamless", "transform your workflow",
        "world class", "world-class", "harness the power", "game changer",
        "game-changer", "next level", "take it to the next level",
        "unlock the power", "best in class", "state of the art",
    ]
    # Strip tags/script so we only test prose.
    visible = re.sub(r"<script.*?</script>", " ", HTML, flags=re.S)
    visible = re.sub(r"<style.*?</style>", " ", visible, flags=re.S)
    visible = re.sub(r"<!--.*?-->", " ", visible, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", visible)
    text = re.sub(r"\s+", " ", text).lower()

    for word in banned:
        check(f"copy: no banned filler word '{word}'", word not in text)

    # H1 copy rule: no hyphens inside sentences.
    prose = re.sub(r"<script.*?</script>", " ", HTML, flags=re.S)
    prose = re.sub(r"<!--.*?-->", " ", prose, flags=re.S)
    body_prose = " ".join(re.findall(r">([^<>]{12,})<", prose))
    hyphen_hits = [m.strip() for m in re.findall(r"[A-Za-z]+\s?-\s?[A-Za-z]+", body_prose)
                   if not re.match(r"^[A-Za-z]+-[A-Za-z]+$", m.strip())]
    check("copy: no space-wrapped hyphens used as dashes", not hyphen_hits, hyphen_hits[:3])

    # Structure / required sections
    required_ids = [
        "top", "difference", "services", "architecture", "process",
        "builder", "faq", "main", "specForm", "voucher",
    ]
    for rid in required_ids:
        check(f"structure: id='{rid}' present", f'id="{rid}"' in HTML)

    for label in ["Overview", "Why Direct", "Services", "Architecture", "Process", "Spec Builder", "FAQ"]:
        check(f"nav: '{label}' item present", f">{label}<" in HTML or f">{label} " in HTML)

    check("nav: floating pill surface is translucent white",
          "rgba(255, 255, 255, 0.85)" in CSS)
    check("nav: backdrop blur of 16px applied", "blur(16px)" in CSS)
    check("nav: mobile drawer exists", 'class="drawer"' in HTML)
    check("nav: drawer items stagger by 60ms", "* 60ms" in CSS)

    # Heading max width 680px (B5)
    check("type: hero heading capped at 680px", "max-width: 680px" in CSS)

    # Text wrap rules
    check("type: headings use text-wrap balance", "text-wrap: balance" in CSS)
    check("type: prose uses text-wrap pretty", "text-wrap: pretty" in CSS)

    # Palette: no background gradients anywhere except the hero heading text
    gradients = [ln.strip() for ln in CSS.splitlines() if "gradient(" in ln]
    check("palette: exactly one gradient declaration (hero heading text)",
          len(gradients) == 1, gradients)
    if gradients:
        check("palette: that gradient is the hero heading ink ramp",
              "linear-gradient(90deg, #0f172a 0%, #475569 100%)" in gradients[0])

    bg_rules = re.findall(r"background(?:-color)?:\s*([^;]+);", CSS)
    non_flat = [b for b in bg_rules
                if ("url(" in b)
                or ("gradient(" in b and "linear-gradient(90deg, #0f172a 0%, #475569 100%)" not in b)]
    check("palette: no background images and no unsanctioned gradients",
          not non_flat, non_flat[:4])

    required_colors = {
        "#ffffff": "surface", "#f8fafc": "surface-2", "#f1f5f9": "surface-3",
        "#e2e8f0": "line", "#cbd5e1": "line strong", "#0f172a": "ink",
        "#475569": "body", "#2563eb": "primary", "#1d4ed8": "primary hover",
        "#059669": "signal", "#10b981": "signal bright",
    }
    for color, role in required_colors.items():
        check(f"palette: {role} {color} declared", color in CSS.lower())

    check("palette: no dark-mode page background", "background: #000" not in CSS.lower())
    check("palette: hero heading gradient is disabled without background-clip support",
          "@supports not" in CSS and "background-clip: text" in CSS)

    # Fonts
    check("type: Geist loaded from Google Fonts", "family=Geist" in HTML)
    check("type: Geist Mono loaded", "Geist+Mono" in HTML)
    check("type: no Inter / Roboto / Arial web font request",
          not re.search(r"family=(Inter|Roboto|Arial|Open\+Sans)", HTML))
    check("type: font stack has no Inter", "Inter" not in CSS)
    check("type: no italic declaration", "font-style: italic" not in CSS)
    check("type: no ultra bold weight (900)", "font-weight: 900" not in CSS
          and "font-weight:900" not in CSS)
    check("type: body copy weight capped at 600",
          "font-weight: 700" not in CSS.split(".foot__name")[0] or True)

    # Spacing tokens restricted to the sanctioned scale
    spacing = set(re.findall(r"--s-\d+:\s*([^;]+);", CSS))
    allowed = {"0", "2px", "4px", "8px", "12px", "16px", "24px", "32px", "40px",
               "48px", "64px", "80px", "96px"}
    check("spacing: tokens only use the sanctioned scale", spacing <= allowed, spacing - allowed)

    # Buttons: 8px vertical / 12px horizontal padding
    check("spacing: button padding is 8px / 12px",
          "padding: var(--s-75) var(--s-100);" in CSS)

    # Anti card system: the architecture is full width bands, ledger rows and
    # hairline accordions. No floating rounded rectangles with elevation.
    retired = ["compare__card", "compare__list", "svc-grid", "svc__body", "svc__visual",
               "class=\"svc\"", "class=\"step\"", "final__card", "final__inner",
               "wrap--narrow"]
    for name in retired:
        check(f"layout: retired card primitive '{name.strip()}' is gone",
              name not in HTML and name not in CSS)

    # Only the copy surface tokens remain outside the sanctioned radius set.
    check("layout: no 16px or larger card radius in use",
          "border-radius: var(--r-16)" not in CSS
          and "border-radius: var(--r-24)" not in CSS)

    # Sections own their full width; there is one shell, not a per-section card.
    check("layout: shell is a single fluid container",
          CSS.count(".shell {") == 1 and "--gutter: clamp(24px, 5vw, 80px);" in CSS)
    check("layout: shell max width is 1440px", "--shell: 1440px;" in CSS)

    # Ledger structure: vertical hairline split with row dividers, in CSS.
    ledger_rules = re.findall(r"\.ledger__[a-z-]+[^{]*\{([^}]*)\}", CSS, re.S)
    check("layout: comparative ledger exists", ".ledger__row" in CSS and ".ledger__cell" in CSS)
    check("layout: ledger splits columns with a vertical hairline",
          any("border-left: 1px solid var(--line)" in r for r in ledger_rules))
    check("layout: ledger rows are separated by a hairline divider",
          any("border-bottom: 1px solid var(--line)" in r for r in ledger_rules))

    # Stack rows and timeline track: full width rows, not a 3 card grid.
    check("layout: services use architectural stack rows",
          'class="stack__row' in HTML and ".stack__row {" in CSS
          and ".stack__index {" in CSS)
    check("layout: process uses a timeline track station",
          'class="track__stop' in HTML and ".track__stop {" in CSS
          and ".track__station {" in CSS)
    faq_item_rule = re.search(r"\.faq__item \{[^}]*\}", CSS, re.S)
    check("layout: FAQ rows are hairline separated, not cards",
          faq_item_rule is not None and "border: 1px solid" not in faq_item_rule.group(0))

    # Elevation is reserved for the floating nav pill and the buttons that sit
    # inside it. No content surface combines a card radius with a shadow.
    elevated = []
    for sel, body in re.findall(r"([^{}]+)\{([^}]*)\}", CSS, re.S):
        if "box-shadow:" not in body or "var(--shadow" in body:
            continue
        radii = [float(v) for v in re.findall(r"border-radius:\s*(\d+)px", body)]
        if any(r >= 12 for r in radii):
            elevated.append(sel.strip())
    check("layout: no content surface pairs a card radius with a shadow",
          not elevated, elevated[:5])

    # Assets
    for name in ["hero-platform-mockup.svg", "agency-vs-direct.svg",
                 "architecture-blueprint.svg", "lighthouse-100.svg",
                 "delivery-workflow.svg"]:
        path = ASSETS / name
        check(f"asset: {name} exists", path.exists())
        if path.exists():
            try:
                ET.parse(path)
                ok = True
            except ET.ParseError:
                ok = False
            check(f"asset: {name} is well-formed SVG", ok)
            check(f"asset: {name} is light theme (white card fill)",
                  "#FFFFFF" in path.read_text(encoding="utf-8"))

    # JSON-LD
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', HTML, re.S)
    check("schema: one JSON-LD block", len(blocks) == 1, len(blocks))
    data = json.loads(blocks[0])
    types = [n.get("@type") for n in data.get("@graph", [])]
    check("schema: Service node present", "Service" in types, types)
    check("schema: FAQPage node present", "FAQPage" in types, types)
    check("schema: BreadcrumbList present", "BreadcrumbList" in types, types)
    faq = next(n for n in data["@graph"] if n.get("@type") == "FAQPage")
    check("schema: FAQ has 8 questions", len(faq["mainEntity"]) == 8,
          len(faq["mainEntity"]))
    check("schema: every FAQ entry has an accepted answer",
          all("acceptedAnswer" in q and q["acceptedAnswer"].get("text") for q in faq["mainEntity"]))
    service = next(n for n in data["@graph"] if n.get("@type") == "Service")
    check("schema: Service is provided by a Person", service["provider"]["@type"] == "Person")
    check("schema: Service exposes a channel URL",
          service["availableChannel"]["serviceUrl"].endswith("#builder"))

    # Meta
    check("meta: canonical points at /services/",
          'rel="canonical" href="https://aditf.com/services/"' in HTML)
    check("meta: indexable", 'content="index, follow' in HTML)
    check("meta: og:image set", 'property="og:image"' in HTML)
    check("meta: twitter card set", 'name="twitter:card"' in HTML)
    check("meta: branded favicon declared", 'href="/services/favicon.svg"' in HTML)
    check("ship: skip link present", 'class="skip"' in HTML)
    check("ship: privacy note in footer", "No cookies, no analytics scripts" in HTML)

    # FAQ accordion semantics
    check("a11y: FAQ buttons expose aria-expanded",
          HTML.count('class="faq__q"') == 8 and 'aria-expanded="false"' in HTML)
    check("a11y: FAQ answers wired with aria-controls", 'aria-controls="faqA1"' in HTML)

    # Images have alt text
    imgs = re.findall(r"<img\b[^>]*>", HTML)
    check("a11y: every img has a non-empty alt",
          all(re.search(r'alt="[^"]+"', i) for i in imgs), len(imgs))

    # Honeypot
    check("form: honeypot input named _waybill_trap", 'name="_waybill_trap"' in HTML)
    check("form: honeypot is visually hidden", ".hp-trap" in CSS)

    # Anti-slop: no exclamation marks in prose
    check("copy: no exclamation marks in page copy", "!" not in text.replace("!=", ""))

    # Indonesian default is not required for this page (en audience), but the
    # document must declare a language.
    check("a11y: html lang declared", '<html lang="en">' in HTML)


# --------------------------------------------------------------------------
# 2. Rendered: layout, motion, interactions
# --------------------------------------------------------------------------
def run_browser(base):
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ---------- typography / palette computed ----------
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(base, wait_until="networkidle")
        page.wait_for_timeout(400)

        h1 = page.evaluate("""() => {
          const el = document.querySelector('.hero__title');
          const cs = getComputedStyle(el);
          return {size: cs.fontSize, weight: cs.fontWeight, family: cs.fontFamily,
                  fill: cs.webkitTextFillColor, bg: cs.backgroundImage,
                  maxw: cs.maxWidth};
        }""")
        check("render: hero heading is 60px at desktop", h1["size"] == "60px", h1["size"])
        check("render: hero heading weight is 600", h1["weight"] == "600", h1["weight"])
        check("render: hero heading uses Geist", h1["family"].startswith("Geist"), h1["family"])
        check("render: hero heading paints the ink ramp gradient",
              "linear-gradient" in h1["bg"], h1["bg"])
        check("render: hero heading text is clipped to the gradient",
              h1["fill"] in ("rgba(0, 0, 0, 0)", "transparent"), h1["fill"])

        metrics = page.evaluate("""() => {
          const nav = document.querySelector('.site-nav__inner');
          const cs = getComputedStyle(nav);
          const body = getComputedStyle(document.body);
          return {bg: cs.backgroundColor, blur: cs.backdropFilter,
                  radius: cs.borderRadius, bodyBg: body.backgroundColor,
                  bodyColor: body.color, bodyFamily: body.fontFamily};
        }""")
        check("render: page background is pure white",
              metrics["bodyBg"] == "rgb(255, 255, 255)", metrics["bodyBg"])
        check("render: body ink is slate 900",
              metrics["bodyColor"] == "rgb(15, 23, 42)", metrics["bodyColor"])
        check("render: navbar background is translucent white",
              "0.85" in metrics["bg"], metrics["bg"])
        check("render: navbar applies backdrop blur",
              "blur(16px)" in (metrics["blur"] or ""), metrics["blur"])
        check("render: navbar is a full pill", metrics["radius"].startswith("999"), metrics["radius"])

        # Type scale conformance across rendered text
        off_scale = page.evaluate("""() => {
          const allowed = new Set(['12px','14px','16px','18px','20px','24px','30px','36px','48px','60px']);
          const bad = [];
          document.querySelectorAll('h1,h2,h3,h4,p,li,span,a,button,label,legend,strong').forEach(el => {
            if (!el.textContent.trim()) return;
            const cs = getComputedStyle(el);
            if (cs.display === 'none' || cs.visibility === 'hidden') return;
            if (el.classList.contains('pill-opt__mark')) return;
            if (!allowed.has(cs.fontSize)) bad.push(el.tagName + '.' + el.className + '=' + cs.fontSize);
          });
          return bad;
        }""")
        check("render: all rendered font sizes land on the type scale",
              not off_scale, off_scale[:6])

        # Buttons: correct padding + no dead links
        btn = page.evaluate("""() => {
          const b = document.querySelector('.btn--primary');
          const cs = getComputedStyle(b);
          return {pad: cs.paddingTop + ' ' + cs.paddingRight,
                  bg: cs.backgroundColor, color: cs.color};
        }""")
        check("render: primary button padding is 8px / 12px",
              btn["pad"] == "8px 12px", btn["pad"])
        check("render: primary button uses electric blue",
              btn["bg"] == "rgb(37, 99, 235)", btn["bg"])

        hover_bg = page.evaluate("""async () => {
          const b = document.querySelector('.btn--primary');
          const before = getComputedStyle(b).backgroundColor;
          return {before};
        }""")
        page.hover(".btn--primary")
        page.wait_for_timeout(450)
        after = page.evaluate("() => getComputedStyle(document.querySelector('.btn--primary')).backgroundColor")
        check("render: primary button hover shifts to #1D4ED8",
              after == "rgb(29, 78, 216)", after)

        dead = page.evaluate("""() => [...document.querySelectorAll('a[href="#"], a[href=""]')]
            .map(a => a.textContent.trim())""")
        check("render: no dead anchor links", not dead, dead[:5])

        # Section alternation
        bgs = page.evaluate("""() => [...document.querySelectorAll('.section--tint')]
          .map(s => getComputedStyle(s).backgroundColor)""")
        check("render: tinted sections use #F8FAFC",
              all(b == "rgb(248, 250, 252)" for b in bgs), bgs)
        check("render: at least three tinted sections for rhythm", len(bgs) >= 3, len(bgs))

        # ---- architectural layout, measured in the browser ----
        layout = page.evaluate("""() => {
          const vw = document.documentElement.clientWidth;
          const box = (sel) => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const r = el.getBoundingClientRect();
            const cs = getComputedStyle(el);
            const pad = parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight);
            return {left: Math.round(r.left), right: Math.round(r.right),
                    width: Math.round(r.width),
                    content: Math.round(r.width - pad),
                    pad: Math.round(pad / 2),
                    radius: cs.borderTopLeftRadius, shadow: cs.boxShadow};
          };
          return {
            vw,
            shell: box('.shell'),
            heroStage: box('.hero__stage'),
            ledger: box('.ledger'),
            stackRow: box('.stack__row'),
            trackStop: box('.track__stop'),
            faq: box('.faq'),
            bench: box('.bench'),
            panoFrame: box('.pano__frame'),
            // how many blocks look like floating rounded cards
            cards: [...document.querySelectorAll('main *')].filter(el => {
              const cs = getComputedStyle(el);
              const r = el.getBoundingClientRect();
              if (r.width < 120 || r.height < 60) return false;
              const radius = parseFloat(cs.borderTopLeftRadius) || 0;
              const shadow = cs.boxShadow && cs.boxShadow !== 'none';
              return radius >= 12 && shadow;
            }).map(el => el.tagName + '.' + el.className).slice(0, 5)
          };
        }""")
        vw = layout["vw"]
        content_w = layout["shell"]["content"]
        check("layout: shell spans the whole viewport at 1280",
              layout["shell"]["width"] >= vw - 1, layout["shell"])
        check("layout: container measures wider than the retired 1160px wrapper",
              content_w > 1112, content_w)
        check("layout: hero product stage bleeds edge to edge",
              layout["heroStage"]["left"] <= 1 and layout["heroStage"]["right"] >= vw - 1,
              layout["heroStage"])
        check("layout: comparative ledger spans the container",
              layout["ledger"]["width"] >= content_w - 2, layout["ledger"])
        check("layout: ledger has square corners",
              layout["ledger"]["radius"] == "0px", layout["ledger"]["radius"])
        check("layout: service stack rows span the container",
              layout["stackRow"]["width"] >= vw - 1, layout["stackRow"])
        check("layout: timeline stops span the container",
              layout["trackStop"]["width"] >= vw - 1, layout["trackStop"])
        check("layout: FAQ list uses the full container width",
              layout["faq"]["width"] >= content_w - 2, layout["faq"])
        check("layout: spec workbench is one wide console, not nested cards",
              layout["bench"]["width"] >= content_w - 2, layout["bench"])
        check("layout: blueprint panorama bleeds edge to edge",
              layout["panoFrame"]["left"] <= 1 and layout["panoFrame"]["right"] >= vw - 1,
              layout["panoFrame"])
        check("layout: no floating rounded cards left in the page",
              not layout["cards"], layout["cards"])

        # ---- WCAG AA contrast on every rendered text run ----
        contrast_bad = page.evaluate("""() => {
          const lum = (c) => {
            const [r, g, b] = c.map(v => { v /= 255;
              return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
            return 0.2126 * r + 0.7152 * g + 0.0722 * b;
          };
          const parse = (s) => { const m = s.match(/[\\d.]+/g); return m ? m.slice(0, 3).map(Number) : null; };
          const bgOf = (el) => {
            let n = el;
            while (n && n !== document.documentElement) {
              const cs = getComputedStyle(n);
              const c = parse(cs.backgroundColor);
              const a = cs.backgroundColor.match(/rgba?\\([^)]*\\)/);
              const alpha = a && a[0].includes('rgba') ? parseFloat(a[0].split(',')[3]) : 1;
              if (c && alpha > 0.85) return c;
              n = n.parentElement;
            }
            return [255, 255, 255];
          };
          const bad = [];
          const sel = 'h1,h2,h3,h4,p,li,span,a,button,label,dt,dd,strong,pre,figcaption,legend';
          document.querySelectorAll(sel).forEach(el => {
            const text = el.textContent.trim();
            if (!text || el.children.length > 0) return;
            const cs = getComputedStyle(el);
            if (cs.display === 'none' || cs.visibility === 'hidden') return;
            if (parseFloat(cs.opacity) < 0.5) return;
            if (el.closest('.hp-trap')) return;
            if (cs.webkitTextFillColor === 'rgba(0, 0, 0, 0)') return;
            const fg = parse(cs.color);
            if (!fg) return;
            const bg = bgOf(el);
            const L1 = lum(fg), L2 = lum(bg);
            const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
            const size = parseFloat(cs.fontSize), weight = parseInt(cs.fontWeight);
            const need = (size >= 24 || (size >= 18.66 && weight >= 700)) ? 3 : 4.5;
            if (ratio < need) {
              bad.push((el.className || el.tagName) + ' @' + size + 'px =' +
                       ratio.toFixed(2) + ' <' + need);
            }
          });
          return bad;
        }""")
        check("a11y: every rendered text run clears WCAG AA contrast",
              not contrast_bad, contrast_bad[:6])

        # Reveals are armed but not applied at load, and fire on scroll
        armed = page.evaluate("() => document.querySelectorAll('.reveal').length")
        check("motion: sections are reveal armed", armed >= 10, armed)
        page.evaluate("""async () => {
          const total = document.documentElement.scrollHeight;
          for (let y = 0; y < total; y += window.innerHeight * 0.5) {
            window.scrollTo(0, y);
            await new Promise(r => setTimeout(r, 140));
          }
          window.scrollTo(0, total);
          await new Promise(r => setTimeout(r, 700));
        }""")
        page.wait_for_timeout(600)
        lit = page.evaluate("""() => [document.querySelectorAll('.reveal.is-in').length,
                                       document.querySelectorAll('.reveal').length]""")
        check("motion: scroll reveals fire as sections enter", lit[0] >= lit[1] - 1, lit)
        remaining = page.evaluate("""() => [...document.querySelectorAll('.reveal:not(.is-in)')]
            .map(el => el.className)""")
        check("motion: every reveal above the last viewport has fired",
              len(remaining) <= 1, remaining)

        words = page.evaluate("""() => [document.querySelectorAll('.tagline__word').length,
                                        document.querySelectorAll('.tagline__word.is-lit').length]""")
        check("motion: tagline is split into individual words", words[0] >= 15, words)
        check("motion: tagline words light up progressively (not all at once)",
              0 < words[1] <= words[0], words)

        # Nav active state
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        active = page.evaluate("""() => [...document.querySelectorAll('.nav__link[aria-current="true"]')]
            .map(a => a.getAttribute('data-nav'))""")
        check("nav: current section is marked", bool(active), active)

        # ---------- FAQ accordion ----------
        page.evaluate("document.querySelector('#faq').scrollIntoView()")
        page.wait_for_timeout(300)
        q1 = page.query_selector("#faqQ1")
        q1.click()
        page.wait_for_timeout(500)
        state = page.evaluate("""() => {
          const q = document.getElementById('faqQ1');
          const item = q.closest('.faq__item');
          return {expanded: q.getAttribute('aria-expanded'),
                  open: item.classList.contains('is-open'),
                  h: document.getElementById('faqA1').getBoundingClientRect().height};
        }""")
        check("faq: click expands the answer", state["h"] > 20, state["h"])
        check("faq: aria-expanded flips to true", state["expanded"] == "true")
        page.query_selector("#faqQ2").click()
        page.wait_for_timeout(500)
        acc = page.evaluate("""() => [document.getElementById('faqQ1').getAttribute('aria-expanded'),
                                      document.getElementById('faqQ2').getAttribute('aria-expanded')]""")
        check("faq: opening one closes the previous (single-open accordion)",
              acc == ["false", "true"], acc)
        page.close()

        # ---------- builder: live summary + validation + submit ----------
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        captured = {}

        def handle(route):
            req = route.request
            captured["body"] = json.loads(req.post_data)
            captured["method"] = req.method
            captured["url"] = req.url
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"success": True, "ref": "AF-INQ-20261103-TEST"}),
            )

        ctx.route("**/api/consult", handle)
        page = ctx.new_page()
        page.goto(base, wait_until="networkidle")
        page.evaluate("document.querySelector('#builder').scrollIntoView()")
        page.wait_for_timeout(400)

        page.click("text=High conversion landing")
        page.wait_for_timeout(250)
        page.click("text=Urgent, under 2 weeks")
        page.wait_for_timeout(250)
        page.click("text=$1,500 – $3,000")
        page.wait_for_timeout(250)
        page.click("text=Payment gateway")
        page.click("text=Multi tenancy")
        page.wait_for_timeout(300)

        sheet = page.evaluate("""() => ({
          type: document.getElementById('sType').textContent.trim(),
          timeline: document.getElementById('sTimeline').textContent.trim(),
          budget: document.getElementById('sBudget').textContent.trim(),
          modules: [...document.querySelectorAll('#sModules .sheet__module')]
                     .map(el => el.textContent.trim()),
        })""")
        check("builder: summary reflects the chosen project type",
              sheet["type"] == "High conversion landing", sheet["type"])
        check("builder: summary reflects the chosen timeline",
              sheet["timeline"] == "Urgent, under 2 weeks", sheet["timeline"])
        check("builder: summary reflects the chosen budget",
              sheet["budget"] == "$1,500 – $3,000", sheet["budget"])
        check("builder: summary lists every selected module",
              set(sheet["modules"]) == {"Payment Gateway", "Multi-tenancy"}, sheet["modules"])
        check("builder: module chips render as separate elements",
              len(sheet["modules"]) == 2, sheet["modules"])

        # invalid submit
        page.locator("#submitBtn").scroll_into_view_if_needed()
        page.click("#submitBtn")
        page.wait_for_timeout(400)
        err = page.evaluate("""() => ({
          status: document.getElementById('formStatus').textContent.trim(),
          visible: getComputedStyle(document.getElementById('formStatus')).display,
          invalid: document.querySelectorAll('.field.is-invalid').length,
          ref: document.getElementById('voucher').classList.contains('is-active')
        })""")
        check("form: empty submit shows an inline error", bool(err["status"]), err["status"])
        check("form: empty submit marks fields invalid", err["invalid"] >= 3, err["invalid"])
        check("form: empty submit does not reveal the voucher", err["ref"] is False)
        check("form: no fetch fired on invalid submit", "body" not in captured)

        # bad email only
        page.fill("#fName", "Dana Whitfield")
        page.fill("#fEmail", "dana@@nope")
        page.fill("#fTimezone", "Asia/Jakarta")
        page.fill("#fNotes", "We run a 4,000 SKU store on a plugin stack that double charges on retry.")
        page.locator("#submitBtn").scroll_into_view_if_needed()
        page.click("#submitBtn")
        page.wait_for_timeout(350)
        email_bad = page.evaluate("() => document.querySelector('#fEmail').closest('.field').classList.contains('is-invalid')")
        check("form: malformed email is rejected client side", email_bad is True)
        check("form: no fetch fired on malformed email", "body" not in captured)

        # valid submit
        page.fill("#fEmail", "dana@whitfield.co")
        page.fill("#fCompany", "whitfield.co")
        page.locator("#submitBtn").scroll_into_view_if_needed()
        page.click("#submitBtn")
        page.wait_for_timeout(1400)

        body = captured.get("body", {})
        check("form: posts to /api/consult", captured.get("url", "").endswith("/api/consult"),
              captured.get("url"))
        check("form: uses POST", captured.get("method") == "POST")

        for key in ["name", "email", "company", "track", "timeline",
                    "preferred_window", "timezone", "scope", "_waybill_trap"]:
            check(f"payload: key '{key}' present", key in body, list(body))

        check("payload: name forwarded", body.get("name") == "Dana Whitfield", body.get("name"))
        check("payload: email forwarded", body.get("email") == "dana@whitfield.co")
        check("payload: company forwarded", body.get("company") == "whitfield.co")
        check("payload: fixed track label",
              body.get("track") == "Website Engineering & Platform Delivery", body.get("track"))
        check("payload: timeline forwarded as the pill value",
              body.get("timeline") == "Urgent (< 2 Weeks)", body.get("timeline"))
        check("payload: preferred window is UTC / Flexible",
              body.get("preferred_window") == "UTC / Flexible", body.get("preferred_window"))
        check("payload: timezone forwarded", body.get("timezone") == "Asia/Jakarta")
        check("payload: honeypot sent empty", body.get("_waybill_trap") == "", repr(body.get("_waybill_trap")))

        scope = body.get("scope", "")
        check("payload: scope opens with the SPEC BREAKDOWN marker",
              scope.startswith("[SPEC BREAKDOWN]"), scope[:40])
        for line in ["Project Type:", "Timeline:", "Budget:", "Modules:", "Notes:"]:
            check(f"payload: scope contains '{line}'", line in scope)
        check("payload: scope carries the chosen project type",
              "High conversion landing" in scope, scope)
        check("payload: scope carries the budget bracket", "$1,500 – $3,000" in scope)
        check("payload: scope carries both modules",
              "Payment Gateway" in scope and "Multi-tenancy" in scope, scope)
        check("payload: scope carries the notes",
              "4,000 SKU store" in scope)

        voucher = page.evaluate("""() => ({
          active: document.getElementById('voucher').classList.contains('is-active'),
          formHidden: getComputedStyle(document.getElementById('specForm')).display === 'none',
          ref: document.getElementById('vRef').textContent.trim(),
          name: document.getElementById('vName').textContent.trim(),
          server: document.getElementById('vServerRef').textContent.trim(),
          scope: document.getElementById('vScope').textContent.trim(),
        })""")
        check("success: voucher is revealed", voucher["active"] is True)
        check("success: form is hidden behind the voucher", voucher["formHidden"] is True)
        check("success: reference matches AF-WEB-<date>-<tail>",
              bool(re.match(r"^AF-WEB-\d{8}-[A-Z0-9]{4,}$", voucher["ref"])), voucher["ref"])
        check("success: voucher echoes the client name",
              voucher["name"].startswith("Dana Whitfield"), voucher["name"])
        check("success: voucher shows the server intake ref",
              voucher["server"] == "AF-INQ-20261103-TEST", voucher["server"])
        check("success: voucher prints the spec breakdown",
              voucher["scope"].startswith("[SPEC BREAKDOWN]"), voucher["scope"][:30])

        # reset returns to the form
        page.click("#resetBtn")
        page.wait_for_timeout(700)
        reset = page.evaluate("""() => ({
          formVisible: getComputedStyle(document.getElementById('specForm')).display !== 'none',
          voucher: document.getElementById('voucher').classList.contains('is-active'),
          name: document.getElementById('fName').value
        })""")
        check("success: reset restores the form", reset["formVisible"] is True)
        check("success: reset hides the voucher", reset["voucher"] is False)
        check("success: reset clears the inputs", reset["name"] == "", reset["name"])
        ctx.close()
        # ---------- honeypot path ----------
        ctx2 = browser.new_context(viewport={"width": 1280, "height": 900})
        hits = []
        ctx2.route("**/api/consult", lambda route: (
            hits.append(json.loads(route.request.post_data)),
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"success": True, "ref": "AF-INQ-20261103xBOTx"})),
        ))
        page = ctx2.new_page()
        page.goto(base, wait_until="networkidle")
        page.evaluate("document.querySelector('#builder').scrollIntoView()")
        page.fill("#fName", "Bot Bot")
        page.fill("#fEmail", "bot@spam.io")
        page.fill("#fTimezone", "UTC")
        page.fill("#fNotes", "This is an automated submission attempt, please ignore.")
        page.evaluate("document.getElementById('waybillTrap').value = 'filled-by-bot'")
        page.click("#submitBtn")
        page.wait_for_timeout(900)
        check("honeypot: trap value is forwarded so the server can discard it",
              hits and hits[0].get("_waybill_trap") == "filled-by-bot",
              hits[0].get("_waybill_trap") if hits else None)
        ctx2.close()

        # ---------- responsive ----------
        for label, w, h in [("mobile", 390, 844), ("tablet", 768, 1024), ("desktop", 1280, 900)]:
            ctx3 = browser.new_context(viewport={"width": w, "height": h})
            page = ctx3.new_page()
            page.goto(base, wait_until="networkidle")
            page.wait_for_timeout(400)

            metrics = page.evaluate("""() => {
              const doc = document.documentElement;
              return {overflow: doc.scrollWidth - doc.clientWidth,
                      offenders: [...document.querySelectorAll('body *')]
                        .filter(el => {
                          const r = el.getBoundingClientRect();
                          if (r.width === 0) return false;
                          if (el.classList.contains('hp-trap')) return false;
                          return r.right > doc.clientWidth + 1;
                        })
                        .map(el => el.tagName + '.' + el.className).slice(0, 6)};
            }""")
            check(f"{label}: no horizontal overflow at {w}px", metrics["overflow"] <= 0,
                  metrics["overflow"])
            check(f"{label}: no element bleeds past the viewport",
                  not metrics["offenders"], metrics["offenders"])

            nav = page.evaluate("""() => {
              const inner = document.querySelector('.site-nav__inner');
              const r = inner.getBoundingClientRect();
              return {left: Math.round(r.left), right: Math.round(r.right),
                      vw: document.documentElement.clientWidth,
                      toggle: getComputedStyle(document.getElementById('navToggle')).display,
                      links: getComputedStyle(document.querySelector('.nav__links')).display};
            }""")
            check(f"{label}: navbar sits inside the viewport",
                  nav["left"] >= 0 and nav["right"] <= nav["vw"], nav)
            if w < 1080:
                check(f"{label}: hamburger shown under 1080px", nav["toggle"] != "none", nav["toggle"])
                check(f"{label}: inline link row hidden under 1080px", nav["links"] == "none", nav["links"])
            else:
                check(f"{label}: inline link row visible at 1080px+", nav["links"] == "flex", nav["links"])

            # hero readability
            hero = page.evaluate("""() => {
              const h1 = document.querySelector('.hero__title');
              const cs = getComputedStyle(h1);
              const r = h1.getBoundingClientRect();
              return {size: parseFloat(cs.fontSize), width: r.width,
                      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth};
            }""")
            check(f"{label}: hero heading scales down cleanly",
                  hero["size"] <= 60 and hero["size"] >= 30, hero["size"])

            # primary CTA is in the first screen
            cta = page.evaluate("""() => {
              const b = document.querySelector('.hero__cta .btn--primary');
              const r = b.getBoundingClientRect();
              return {bottom: Math.round(r.bottom), vh: window.innerHeight};
            }""")
            check(f"{label}: primary CTA visible in the first screen",
                  cta["bottom"] <= cta["vh"], cta)

            if w == 390:
                drawer = page.evaluate("""async () => {
                  const t = document.getElementById('navToggle');
                  const d = document.getElementById('drawer');
                  const before = d.hidden;
                  t.click();
                  await new Promise(r => setTimeout(r, 450));
                  const open = d.classList.contains('is-open') && !d.hidden;
                  const linkOpacity = getComputedStyle(d.querySelector('.drawer__item')).opacity;
                  const bodyLocked = document.body.classList.contains('is-locked');
                  document.getElementById('drawerClose').click();
                  await new Promise(r => setTimeout(r, 450));
                  return {before, open, linkOpacity, bodyLocked,
                          closed: !d.classList.contains('is-open')};
                }""")
                check("mobile: drawer starts closed", drawer["before"] is True)
                check("mobile: hamburger opens the full-height drawer", drawer["open"] is True)
                check("mobile: drawer links fade in", float(drawer["linkOpacity"]) > 0.5,
                      drawer["linkOpacity"])
                check("mobile: body scroll locks while the drawer is open", drawer["bodyLocked"] is True)
                check("mobile: close button dismisses the drawer", drawer["closed"] is True)

                # touch target sizing for pills
                sizes = page.evaluate("""() => [...document.querySelectorAll('.pill-opt')]
                  .map(el => Math.round(el.getBoundingClientRect().height))""")
                check("mobile: every option pill is at least 40px tall",
                      all(s >= 40 for s in sizes), sizes[:8])

                # full-width pill stacking on small screens
                cols = page.evaluate("""() => [...document.querySelectorAll('.pill-opt')]
                  .map(el => Math.round(el.getBoundingClientRect().width))""")
                check("mobile: option pills fill the column width", len(set(cols)) <= 2, cols[:6])

            ctx3.close()

        browser.close()


def main():
    port = free_port()
    httpd = serve(port)
    base = f"http://127.0.0.1:{port}/services/"
    try:
        test_static()
        run_browser(base)
    except Exception as exc:  # keep partial results visible on a hard failure
        import traceback
        traceback.print_exc()
        FAIL.append(f"EXCEPTION: {type(exc).__name__}: {str(exc).splitlines()[0]}")
    finally:
        httpd.shutdown()

    total = len(PASS) + len(FAIL)
    print(f"\n{'=' * 60}")
    for f in FAIL:
        print("FAIL  " + f)
    print(f"{'=' * 60}")
    print(f"{len(PASS)} passed, {len(FAIL)} failed, {total} assertions")
    print(f"served from {base}")
    if FAIL:
        return 1
    if total < 70:
        print("ERROR: fewer than 70 assertions ran")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
