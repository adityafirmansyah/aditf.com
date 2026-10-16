---
title: Why I Built mycv.ai.id: How AI Resume Tools Silently Strip Technical Depth and Hallucinate Dates
slug: why-i-built-mycv-ai-id
date: 2026-10-16
excerpt: Standard AI resume builders quietly strip concrete tech stacks into corporate fluff and hallucinate that 2026 dates are from the future. Here is how I engineered mycv.ai.id to stop them.
tags: ai-engineering, resume-optimization, ats-parser, python, fastapi, anti-slop, self-hosting
---

## What happens when an engineer uses generic AI resume tools

Every software engineer is told to run their resume through an LLM before applying. Recruiter blogs and career influencers promise that ChatGPT will polish your experience into an ATS-friendly masterpiece.

When an engineer with thirteen years of shipping software actually does this, something destructive happens quietly in the output.

Specific architectural stacks get flattened into corporate filler. A bullet about architecting a Next.js App Router and FastAPI monorepo with PostgreSQL tenant isolation gets replaced with "spearheaded application architecture to support enterprise growth."

Worse, the model flags recent experience as a temporal impossibility. Because popular LLMs carry training cutoffs from 2024 or early 2025, an entry like "Aug 2024 – Jul 2026" gets docked as an invalid future date.

I built mycv.ai.id this week to fix these exact failure modes. It is a self-hosted resume engine on an Ubuntu VPS, built with FastAPI and React 19, designed around one principle: an LLM needs deterministic fences, or it will ruin your technical signal.

## The keyword-stripping and AI-slop trap

When you ask an unconstrained LLM to optimize a resume for an Applicant Tracking System, its RLHF training defaults to corporate HR language. The model assumes high-impact writing means using executive verbs.

That bias strips the exact keywords technical recruiters and engineering directors search for:

- Concrete frameworks like Next.js, FastAPI, Medusa, and React 19 disappear into "modern web technologies."
- Architectural patterns like monorepos, Kubernetes deployments, gRPC services, and tenant isolation become "scalable systems."
- Testing practices like TDD and CI quality gates get diluted into "ensured high code quality."

In commit `4490e8b`, I codified a zero-AI-slop policy inside `backend/app/services/optimizer.py`. We put an absolute ban on corporate fluff verbs and generic buzzwords:

```python
# From backend/app/services/optimizer.py (commit 4490e8b)
SYSTEM_CV_EXPERT = """
STRICT ZERO-AI-SLOP RULES (Non-Negotiable):

1. ABSOLUTE BAN ON AI RESUME SLOP & EMPTY CORPORATE CLICHÉS:
   - FORBIDDEN ACTION VERBS: NEVER use "Spearhead", "Spearheaded", "Spearheading",
     "Pioneered", "Orchestrated", "Fostered", "Leveraged", "Championed", "Catalyzed".
   - FORBIDDEN BUZZWORDS: NEVER use "robust", "seamless", "cutting-edge", "game-changer",
     "revolutionary", "holistic", "synergistic", "dynamic environment".
"""
```

The system prompt enforces direct practitioner verbs instead. Every action must open with words like Built, Architected, Engineered, or Deployed.

Every bullet point must satisfy a three-part engineering formula:

- What concrete system was built or refactored.
- Which specific technologies and tools were used.
- What measurable technical outcome resulted.

If the candidate input mentions Kubernetes and gRPC, those terms are non-negotiable. The model is forbidden from abstracting them away.

## The 2026 calendar cutoff defect

The second failure mode is subtle and infuriating.

When testing resumes with recent tenures, the ATS audit engine kept docking candidates from a score of 96 down to 88. The reason was temporal hallucination.

The model saw "Aug 2024 – Jul 2026" and treated July 2026 as a date from the future. Because its weights were frozen before mid-2025, the model concluded the candidate had fabricated their employment history.

In commit `4b90aba`, I added dynamic server-side temporal injection:

```python
# From backend/app/services/optimizer.py (commit 4b90aba)
from datetime import datetime

def get_current_date_context() -> str:
    now = datetime.now()
    return f"{now.strftime('%B %Y')} (Year {now.year})"

# Injected directly into the system prompt and audit evaluator:
"""
REAL-WORLD DATE CONTEXT:
- The current calendar date is October 2026 (Year 2026).
- All employment dates through October 2026 are valid, normal historical dates.
- NEVER flag dates occurring in or before October 2026 as 'the future'.
"""
```

Once the model receives runtime calendar grounding, the hallucination vanishes. It evaluates completed 2026 tenures as authentic history instead of penalizing candidates for living in the present.

## True vector PDFs vs visual canvas printing

Most modern resume builders sell visual templates designed in Figma or HTML canvas. They look sleek on a screen, but they fail digital ATS parsers like Workday, Greenhouse, and Taleo:

- Two-column layouts split text streams, causing parsers to read across columns and scramble job titles with skills.
- Browser `window.print()` outputs inconsistent micro-margins and unmapped character glyphs.
- Graphic elements and skill progress bars turn into unparseable binary noise.

I chose Python's ReportLab to generate single-column, print-ready vector PDFs directly. Every font is registered via `pdfmetrics` using true TrueType files: Inter for modern sans, Merriweather for executive serif, and IBM Plex Mono for technical roles.

In commit `7678422`, we solved two subtle rendering bugs:

```python
# From backend/app/services/pdf_generator.py (commit 7678422)
# Frame content box is [margin+6 .. PAGE_WIDTH-margin-6], i.e. doc.width - 12.
usable_width = doc.width - 12

# Dynamic glyph advance calculation for hanging indents:
bullet_glyph = "\u2022"
bullet_gap = "\u00a0\u00a0"
bullet_indent = (
    pdfmetrics.stringWidth(bullet_glyph, cfg["font_body"], cfg["body_size"])
    + pdfmetrics.stringWidth(bullet_gap, cfg["font_body"], cfg["body_size"])
)
```

ReportLab's `SimpleDocTemplate` adds six points of padding inside its internal Frame. Using the raw page width caused job-title tables to bleed six points into the left margin.

Calculating `usable_width = doc.width - 12` anchors every table flush with the text margin. Calculating hanging indents from exact glyph advance ensures wrapped bullet points align beneath the text rather than under the bullet dot.

## Localizing payment for emerging markets

Western career platforms lock export buttons behind recurring credit card subscriptions. For Indonesian engineers and local tech talent, credit card auto-billing creates immediate friction.

I integrated native dynamic QRIS using Bank Indonesia's EMVCo specification in commit `90c4584`:

- The backend parses static QRIS Tag-Length-Value (TLV) payloads.
- It flips Tag 01 from static (`11`) to dynamic (`12`).
- It injects Tag 54 carrying the exact transaction amount plus a three-digit unique verification code.
- It recalculates the CRC-16/CCITT-FALSE checksum on Tag 63.

Candidates scan the QR code with GoPay, OVO, BCA, or any banking app. The payment reconciles automatically on our self-hosted Linux VPS, without sending user data or payment credentials to third-party subscription traps.

## What building this taught me about AI engineering

The actual intelligence in an AI application does not come from the model. It comes from the deterministic boundary you build around it.

An unconstrained LLM defaults to mediocrity:

- It replaces concrete engineering accomplishments with hollow management jargon.
- It invents timeline anomalies because it has no awareness of the wall clock.
- It encourages pretty visual formats that fail machine parsing.

Deterministic boundaries change how the model behaves. Once you enforce strict prompt fences, temporal grounding, and vector rendering, it stops acting like an over-eager intern. It becomes a reliable compiler for your career.
