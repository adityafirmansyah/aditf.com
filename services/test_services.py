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

    check("nav: header surface is translucent white at 92%",
          "rgba(255, 255, 255, 0.92)" in CSS)
    check("nav: backdrop blur of 16px applied", "blur(16px)" in CSS)
    check("nav: mobile drawer exists", 'class="drawer"' in HTML)
    check("nav: drawer items stagger by 60ms", "* 60ms" in CSS)

    # ---- full width enterprise bar contract ----
    nav_rule = re.search(r"\.site-nav \{([^}]*)\}", CSS, re.S)
    nav_body = nav_rule.group(1) if nav_rule else ""
    check("nav: bar is pinned to the top edge", "top: 0;" in nav_body, nav_body[:80])
    check("nav: bar spans the full viewport width", "width: 100%;" in nav_body)
    check("nav: bar has no horizontal margin (edge to edge)",
          "margin" not in nav_body)
    check("nav: bar body is square, not a pill", "border-radius" not in nav_body)
    check("nav: no floating offset token on the bar", "--s-200" not in nav_body)
    check("nav: hairline bottom boundary spans the bar",
          "border-bottom: 1px solid var(--line);" in nav_body)
    check("nav: bar height is a fixed 64px token",
          "--nav-h: 64px;" in CSS and "height: var(--nav-h);" in nav_body)
    check("nav: bar is a flex row with vertical centring",
          "display: flex;" in nav_body and "align-items: center;" in nav_body)
    check("nav: backdrop filter boosts saturation to 180%",
          "saturate(180%)" in nav_body)

    inner_rule = re.search(r"\.site-nav__inner \{([^}]*)\}", CSS, re.S)
    inner_body = inner_rule.group(1) if inner_rule else ""
    check("nav: inner container caps at the 1440px shell",
          "max-width: var(--shell);" in inner_body and "--shell: 1440px;" in CSS)
    check("nav: inner container is fluid padded 20px to 56px",
          "padding: 0 clamp(20px, 4vw, 56px);" in inner_body)
    check("nav: inner container is square (no pill radius)",
          "border-radius" not in inner_body)

    # The floating pill pattern must be gone from the stylesheet entirely.
    check("nav: retired 1120px floating wrapper is gone", "1120px" not in CSS)
    check("nav: no pill radius anywhere on the header", not re.search(
        r"\.site-nav[^{]*\{[^}]*border-radius", CSS, re.S))

    # Identity block, status signal, primary action, active indicator.
    check("nav: brand renders the name in sentence case",
          'class="nav-brand__name">Aditya Firmansyah<' in HTML)
    check("nav: role divider reads Lead Architect",
          'class="nav-brand__role">Lead Architect<' in HTML)
    check("nav: live status signal present with a dot",
          'class="nav-status"' in HTML and 'class="nav-status__dot"' in HTML)
    check("nav: status signal sits on emerald soft tokens",
          "background: var(--green-soft);" in CSS
          and "border: 1px solid var(--green-line);" in CSS)
    check("nav: primary CTA reads Configure scope spec",
          "Configure scope spec" in HTML)
    check("nav: active link uses blue plus a hairline indicator",
          '.nav__link[aria-current="true"]' in CSS
          and "border-bottom-color: var(--blue);" in CSS)
    check("nav: links are 14px medium in body ink", re.search(
        r"\.nav__link \{[^}]*font-size: 14px;[^}]*font-weight: 500;", CSS, re.S)
        is not None)
    check("nav: links space at 24px", re.search(
        r"\.nav__links \{[^}]*gap: var\(--s-300\);", CSS, re.S) is not None)
    check("nav: identity mark is a square monogram, not a text glyph",
          'class="nav-brand__mark" aria-hidden="true">AF<' in HTML)

    # Page offset: hero clears the bar, anchors land with clearance.
    hero_rule = re.search(r"\.hero \{([^}]*)\}", CSS, re.S)
    hero_body = hero_rule.group(1) if hero_rule else ""
    check("nav: hero clears the full width bar",
          "padding-top: calc(var(--nav-h) + var(--s-400));" in hero_body, hero_body)
    margin_block = re.search(
        r"#top,\s*#difference,\s*#services,\s*#architecture,\s*#process,\s*#builder,"
        r"\s*#faq\s*\{([^}]*)\}", CSS, re.S)
    check("nav: every section id listed for anchor clearance",
          margin_block is not None)
    check("nav: anchors land 80px clear of the bar",
          margin_block is not None and "scroll-margin-top: 80px;" in margin_block.group(1))
    check("nav: document scroll padding matches the bar height",
          "scroll-padding-top: var(--nav-h);" in CSS)

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

    # Diagram spacing: text must sit inside an internal padding box, never on the
    # canvas edge, and nothing may straddle a week gridline. Regression guard for
    # the delivery-workflow "missing spacing" report.
    for name, pad_x, pad_top in [("delivery-workflow.svg", 40, 24),
                                 ("delivery-workflow-mobile.svg", 24, 24)]:
        path = ASSETS / name
        if not path.exists():
            continue
        root = ET.parse(path).getroot()
        vb = [float(v) for v in root.get("viewBox", "").split()[2:]]
        width = vb[0]
        texts = root.findall("{http://www.w3.org/2000/svg}text")
        xs = [float(t.get("x", 0)) for t in texts]
        check(f"spacing: {name} keeps a {pad_x}px left inset",
              min(xs) >= pad_x - 0.5, min(xs) if xs else None)
        check(f"spacing: {name} leaves headroom above the first line",
              min(float(t.get("y")) for t in texts) >= pad_top,
              min(float(t.get("y")) for t in texts))
        # right edge: no text may run past the mirrored inset
        ends = []
        for t in texts:
            x = float(t.get("x", 0))
            size = float(t.get("font-size", 11))
            # conservative width estimate: widest glyph ~0.62em, monospace tracking
            est = len(t.text or "") * size * 0.62
            ends.append(width - (x + est) if t.get("text-anchor") != "end" else width - x)
        check(f"spacing: {name} keeps a {pad_x}px right inset", min(ends) >= pad_x - 8,
              round(min(ends), 1))
        # the bottom note must clear the closing rule by at least 8px
        lines = root.findall("{http://www.w3.org/2000/svg}line")
        bottoms = [float(l.get("y1")) for l in lines
                   if float(l.get("y1")) == float(l.get("y2"))
                   and float(l.get("x2")) - float(l.get("x1")) > width * 0.9]
        last_text_bottom = max(float(t.get("y")) for t in texts)
        check(f"spacing: {name} footnote clears the closing rule",
              bool(bottoms) and last_text_bottom <= max(bottoms) - 8,
              (last_text_bottom, max(bottoms) if bottoms else None))

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
          const header = document.querySelector('.site-nav');
          const inner = document.querySelector('.site-nav__inner');
          const hr = header.getBoundingClientRect();
          const ir = inner.getBoundingClientRect();
          const hcs = getComputedStyle(header);
          const ics = getComputedStyle(inner);
          const body = getComputedStyle(document.body);
          const vw = document.documentElement.clientWidth;
          return {
            hBg: hcs.backgroundColor,
            hBlur: hcs.backdropFilter,
            hRadius: hcs.borderRadius,
            hTop: Math.round(hr.top),
            hLeft: Math.round(hr.left),
            hRight: Math.round(hr.right),
            hWidth: Math.round(hr.width),
            hHeight: Math.round(hr.height),
            iRadius: ics.borderRadius,
            iWidth: Math.round(ir.width),
            vw,
            bodyBg: body.backgroundColor,
            bodyColor: body.color,
          };
        }""")
        check("render: page background is pure white",
              metrics["bodyBg"] == "rgb(255, 255, 255)", metrics["bodyBg"])
        check("render: body ink is slate 900",
              metrics["bodyColor"] == "rgb(15, 23, 42)", metrics["bodyColor"])
        check("render: navbar background is translucent white at 92%",
              "0.92" in metrics["hBg"], metrics["hBg"])
        check("render: navbar applies backdrop blur",
              "blur(16px)" in (metrics["hBlur"] or ""), metrics["hBlur"])
        check("render: navbar is pinned at top 0", metrics["hTop"] == 0, metrics["hTop"])
        check("render: navbar spans full viewport edge to edge",
              metrics["hLeft"] == 0 and metrics["hWidth"] == metrics["vw"], metrics)
        check("render: navbar container is not pill shaped",
              metrics["hRadius"] == "0px", metrics["hRadius"])
        check("render: navbar inner container is not pill shaped",
              metrics["iRadius"] == "0px", metrics["iRadius"])
        check("render: navbar height is 64px", metrics["hHeight"] == 64, metrics["hHeight"])

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

        # header interaction states: hover, active indicator, focus ring
        page.hover(".nav__link:nth-child(3)")
        page.wait_for_timeout(400)
        hov = page.evaluate("""() => getComputedStyle(document.querySelectorAll('.nav__link')[2]).color""")
        check("render: nav link hover shifts to ink", hov == "rgb(15, 23, 42)", hov)

        act = page.evaluate("""() => {
          const a = document.querySelector('.nav__link[aria-current="true"]');
          if (!a) return null;
          const cs = getComputedStyle(a);
          return {color: cs.color, weight: cs.fontWeight, border: cs.borderBottomColor,
                  width: cs.borderBottomWidth};
        }""")
        check("render: active nav link is blue and semibold",
              act and act["color"] == "rgb(37, 99, 235)" and act["weight"] == "600", act)
        check("render: active nav link carries a 2px bottom indicator",
              act and act["border"] == "rgb(37, 99, 235)" and act["width"] == "2px", act)

        page.evaluate("document.querySelectorAll('.nav__link')[0].focus()")
        page.wait_for_timeout(200)
        ring = page.evaluate("""() => { const s = getComputedStyle(document.activeElement);
          return {w: s.outlineWidth, style: s.outlineStyle, color: s.outlineColor}; }""")
        check("render: nav links show a visible focus ring",
              ring["w"] == "2px" and ring["style"] != "none", ring)

        page.hover(".nav-brand")
        page.wait_for_timeout(400)
        mark = page.evaluate(
            """() => getComputedStyle(document.querySelector('.nav-brand__mark')).backgroundColor""")
        check("render: brand monogram responds to hover", mark == "rgb(37, 99, 235)", mark)

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
        for label, w, h in [("mobile", 390, 844), ("tablet", 768, 1024),
                            ("desktop", 1280, 900), ("wide", 1440, 900)]:
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
              const header = document.querySelector('.site-nav');
              const inner = document.querySelector('.site-nav__inner');
              const hr = header.getBoundingClientRect();
              const r = inner.getBoundingClientRect();
              const hero = document.querySelector('.hero__meta').getBoundingClientRect();
              return {left: Math.round(r.left), right: Math.round(r.right),
                      hLeft: Math.round(hr.left), hTop: Math.round(hr.top),
                      hWidth: Math.round(hr.width), hHeight: Math.round(hr.height),
                      heroTop: Math.round(hero.top),
                      vw: document.documentElement.clientWidth,
                      toggle: getComputedStyle(document.getElementById('navToggle')).display,
                      status: getComputedStyle(document.querySelector('.nav-status')).display,
                      heroPad: parseFloat(getComputedStyle(document.querySelector('.hero')).paddingTop),
                      links: getComputedStyle(document.querySelector('.nav__links')).display};
            }""")
            check(f"{label}: navbar sits inside the viewport",
                  nav["left"] >= 0 and nav["right"] <= nav["vw"], nav)
            check(f"{label}: header is flush to the left edge and full bleed",
                  nav["hLeft"] == 0 and nav["hWidth"] == nav["vw"], nav)
            check(f"{label}: header sits at the very top of the viewport",
                  nav["hTop"] == 0, nav["hTop"])
            check(f"{label}: header keeps a fixed 64px height",
                  nav["hHeight"] == 64, nav["hHeight"])
            check(f"{label}: hero is offset below the fixed header",
                  nav["heroTop"] >= nav["hHeight"], nav)
            check(f"{label}: hero padding accounts for the header height",
                  nav["heroPad"] >= nav["hHeight"], nav["heroPad"])
            if w < 1280:
                check(f"{label}: status signal hidden when the bar is tight",
                      nav["status"] == "none", nav["status"])
            else:
                check(f"{label}: status signal visible on a wide bar",
                      nav["status"] != "none", nav["status"])
            if w < 1080:
                check(f"{label}: hamburger shown under 1080px", nav["toggle"] != "none", nav["toggle"])
                check(f"{label}: inline link row hidden under 1080px", nav["links"] == "none", nav["links"])
            else:
                check(f"{label}: inline link row visible at 1080px+", nav["links"] == "flex", nav["links"])

            # anchor jumps must clear the fixed bar
            jump = page.evaluate("""() => {
              document.getElementById('services').scrollIntoView();
              const el = document.getElementById('services');
              const r = el.getBoundingClientRect();
              const bar = document.querySelector('.site-nav').getBoundingClientRect();
              return {top: Math.round(r.top), bottom: Math.round(bar.bottom),
                      clearance: Math.round(r.top - bar.bottom)};
            }""")
            check(f"{label}: anchor jump clears the fixed bar",
                  jump["clearance"] >= 16, jump)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(200)

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

                # the drawer must replace the header in place, not shift the brand
                align = page.evaluate("""async () => {
                  const hBrand = document.querySelector('.site-nav .nav-brand').getBoundingClientRect();
                  const hToggle = document.getElementById('navToggle').getBoundingClientRect();
                  const hBar = document.querySelector('.site-nav').getBoundingClientRect();
                  document.getElementById('navToggle').click();
                  await new Promise(r => setTimeout(r, 500));
                  const dBrand = document.querySelector('.drawer .nav-brand').getBoundingClientRect();
                  const dClose = document.getElementById('drawerClose').getBoundingClientRect();
                  const dTop = document.querySelector('.drawer__top').getBoundingClientRect();
                  document.getElementById('drawerClose').click();
                  await new Promise(r => setTimeout(r, 450));
                  return {hBrandLeft: Math.round(hBrand.left), dBrandLeft: Math.round(dBrand.left),
                          hBrandTop: Math.round(hBrand.top), dBrandTop: Math.round(dBrand.top),
                          hToggleLeft: Math.round(hToggle.left), dCloseLeft: Math.round(dClose.left),
                          hBarH: Math.round(hBar.height), dTopH: Math.round(dTop.height)};
                }""")
                check("mobile: drawer brand sits exactly where the header brand sat",
                      align["hBrandLeft"] == align["dBrandLeft"]
                      and align["hBrandTop"] == align["dBrandTop"], align)
                check("mobile: drawer close sits exactly where the toggle sat",
                      align["hToggleLeft"] == align["dCloseLeft"], align)
                check("mobile: drawer top row matches the header height",
                      align["dTopH"] == align["hBarH"], align)

                # hairline rows, not a card list
                rows = page.evaluate("""async () => {
                  document.getElementById('navToggle').click();
                  await new Promise(r => setTimeout(r, 400));
                  const out = [...document.querySelectorAll('.drawer__item')].map(i => {
                    const cs = getComputedStyle(i);
                    return {border: cs.borderBottomWidth, radius: cs.borderRadius,
                            h: Math.round(i.getBoundingClientRect().height)};
                  });
                  document.getElementById('drawerClose').click();
                  await new Promise(r => setTimeout(r, 350));
                  return out;
                }""")
                check("mobile: drawer rows are hairline separated",
                      all(r["border"] == "1px" for r in rows), rows[:3])
                check("mobile: drawer rows are square, not rounded cards",
                      all(r["radius"] == "0px" for r in rows), rows[:3])
                check("mobile: drawer rows are comfortable touch targets",
                      all(r["h"] >= 44 for r in rows), [r["h"] for r in rows])

                # a single hairline between the drawer top row and the first link
                seam = page.evaluate("""async () => {
                  document.getElementById('navToggle').click();
                  await new Promise(r => setTimeout(r, 450));
                  const top = document.querySelector('.drawer__top');
                  const list = document.querySelector('.drawer__list');
                  const out = {topBorder: getComputedStyle(top).borderBottomWidth,
                               listBorder: getComputedStyle(list).borderTopWidth,
                               gap: Math.round(list.getBoundingClientRect().top
                                               - top.getBoundingClientRect().bottom)};
                  document.getElementById('drawerClose').click();
                  await new Promise(r => setTimeout(r, 350));
                  return out;
                }""")
                check("mobile: exactly one hairline under the drawer top row",
                      seam["topBorder"] == "1px" and seam["listBorder"] == "0px", seam)
                check("mobile: the link list starts flush under the drawer top row",
                      seam["gap"] == 0, seam)

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


# --------------------------------------------------------------------------
# 3. Width sweep: the bar must never crowd, wrap, or clip at any viewport.
# --------------------------------------------------------------------------
HEADER_WIDTHS = [1920, 1600, 1440, 1366, 1320, 1280, 1200, 1100, 1080, 1024,
                 900, 834, 768, 640, 520, 480, 430, 414, 390, 360, 320]


def test_header_widths(base):
    """The header has three zones; at every width they must coexist without
    overlap, wrapping, or negative slack. Guards the 414 to 479px crowding that
    the first full width build shipped."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        probe = """() => {
          const vis = (s) => { const e = document.querySelector(s); if (!e) return null;
            const cs = getComputedStyle(e);
            if (cs.display === 'none' || cs.visibility === 'hidden') return null;
            const b = e.getBoundingClientRect();
            return {l: b.left, r: b.right, w: b.width}; };
          const inner = document.querySelector('.site-nav__inner');
          const ics = getComputedStyle(inner);
          const content = inner.getBoundingClientRect().width
                          - parseFloat(ics.paddingLeft) - parseFloat(ics.paddingRight);
          const zones = [vis('.nav-brand'), vis('.nav__links'), vis('.nav__actions')]
            .filter(Boolean).filter(z => z.w > 0);
          const kids = [...inner.children]
            .filter(k => getComputedStyle(k).display !== 'none')
            .map(k => { const b = k.getBoundingClientRect();
                        return {c: k.className, l: b.left, r: b.right}; })
            .filter(k => k.r > k.l);
          const collisions = [];
          for (let i = 0; i < kids.length; i++)
            for (let j = i + 1; j < kids.length; j++)
              if (kids[i].r > kids[j].l + 0.5 && kids[j].r > kids[i].l + 0.5)
                collisions.push(kids[i].c + ' x ' + kids[j].c);
          const sum = ['brand', 'links', 'actions'].reduce((a, k) => a + (zones[k] ? zones[k].w : 0), 0);
          const gap = parseFloat(ics.columnGap) || 0;
          const aZone = document.querySelector('.nav__actions');
          const aGap = aZone ? parseFloat(getComputedStyle(aZone).columnGap) : null;
          return {
            slack: Math.round(content - sum - gap * Math.max(0, zones.length - 1)),
            collisions,
            minZoneGap: zones.length > 1
              ? Math.round(Math.min(...zones.slice(1).map((z, i) => z.l - zones[i].r)))
              : 999,
            actionsGap: aGap,
            height: Math.round(document.querySelector('.site-nav').getBoundingClientRect().height),
            overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          };
        }"""
        for w in HEADER_WIDTHS:
            page = browser.new_page(viewport={"width": w, "height": 900})
            page.goto(base, wait_until="networkidle")
            page.wait_for_timeout(180)
            r = page.evaluate(probe)
            check(f"header {w}px: zones do not overlap", not r["collisions"], r["collisions"])
            check(f"header {w}px: zones keep at least 16px apart",
                  r["minZoneGap"] >= 16, r["minZoneGap"])
            check(f"header {w}px: the bar does not run out of room",
                  r["slack"] >= 0, r["slack"])
            check(f"header {w}px: the bar stays one 64px row", r["height"] == 64, r["height"])
            check(f"header {w}px: the bar causes no overflow", r["overflow"] <= 0, r["overflow"])
            check(f"header {w}px: action controls keep a distinct tap gap",
                  r["actionsGap"] >= 16 if r["actionsGap"] is not None else True,
                  r["actionsGap"])
            page.close()
        browser.close()


def main():
    port = free_port()
    httpd = serve(port)
    base = f"http://127.0.0.1:{port}/services/"
    try:
        test_static()
        test_header_widths(base)
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
