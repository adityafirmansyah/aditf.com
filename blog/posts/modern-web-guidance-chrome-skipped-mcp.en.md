---
title: "Modern Web Guidance 1.0: Why Chrome Skipped MCP to Stop Agents Writing 2019 JavaScript"
slug: modern-web-guidance-chrome-skipped-mcp
date: 2026-11-11
excerpt: "Modern Web Guidance 1.0 ships 200+ browser-primitive guides as a 7MB offline CLI skill, and its rejection of MCP tells you more about AI coding agents than the guides do."
tags: ai-agents, web-development, javascript, devtools
keywords: modern web guidance, ai coding agents, browser primitives vs javascript, agent skills vs mcp, legacy-scan web modernization
---

Ask a coding agent for a modal dialog and you get the shape its training corpus rewards:

- a nested `<div>` stack with a hardcoded z-index ladder,
- a manual focus trap wired to `keydown`,
- and a scroll-lock hack that breaks on iOS.

The browser has shipped `<dialog>` and `showModal()` for years. The agent knows the name. It almost never reaches for it.

I see that modal in plenty of agent PRs landing in the Dagango.com repo. The diff is tidy and the tests pass. Wrong primitive.

Modern Web Guidance 1.0, published on November 10, 2026 by Philip Walton on the Chrome for Developers blog, is the Chrome team's answer to exactly that failure. Firefox, Edge, and MDN steward it alongside Chrome. The guides are good. The packaging decision underneath them is better.

## Why do coding agents still write 2019 JavaScript?

Because the corpus they trained on is mostly pre-2022 Stack Overflow. The modal answer that won the thread back then was a div overlay and a focus trap. Nothing in the model's objective rewards reaching for the platform first.

So the code passes review. That's the trap. A bot sees a working modal and moves on. Nobody measures that the working modal is 50 lines of JavaScript the browser handles with a single element.

Here is what the guides push instead:

- `<dialog>` plus `showModal()` in place of an overlay div and manual inert handling,
- `field-sizing: content` in place of a textarea resize listener,
- CSS anchor positioning in place of a `getBoundingClientRect()` loop on scroll,
- and scroll-snap in a navigation drawer instead of pointer-event drag maths.

That last substitution is the one I'd underline. The `navigation-drawer` guide moves the swipe gesture into a scrolling container with two snap stops. Momentum, interruption, and velocity come from the browser.

Read the list again as a whole. Each line answers the browser primitives vs JavaScript question the same way, and none needs a dependency.

## Modern Web Guidance ships as a 7MB skill, not an MCP server

On the Hacker News thread, Paul Irish described the decision in one sentence. He spent nine months on "how to ship this as an agent skill + (Agentic RAG) CLI without blowing up your context window".

The alternative on the table was a Model Context Protocol (MCP) server. An MCP server is always on. Its tool schemas sit in context on every turn, whether or not you touch a layout that day.

What shipped instead:

- a 500MB native retrieval stack compressed into a roughly **7MB pure-JS package**,
- offline BM25 (a lexical ranking function) plus a local embedding model, answering in about **10ms on CPU** with no network calls and no API keys,
- and a skill description of roughly **205 tokens** that has to earn activation on a frontend task.

The skill activates first. Then the agent runs `search "<use case>"`, and `retrieve <guide-id>` pulls exactly one guide into context. Nothing else rides along.

This is the agent skills vs MCP argument in its cleanest form. Progressive disclosure wins because the scarce resource is attention, not bandwidth.

Simon Willison suggested a grep-able markdown index on GitHub Pages as an alternative to installing anything. Irish agreed for occasional use and flagged that the index's own token cost is too high for daily work. Fine trade, honestly measured.

## The receipts behind the 55% to 92% jump

Chrome ran Codex, Claude, and Antigravity against 200 tasks. Scoring used roughly 1,700 Playwright and abstract syntax tree (AST) assertions. Unguided agents passed 55%. With the skill installed, 92%.

Partner numbers point the same way. note inc. ran a 180-pass evaluation on its production Next.js codebase, moving from 61% to 94% on modern web checks. Across 431 merged pull requests, correct Largest Contentful Paint (LCP) image prioritization rose 28%.

MetaMask runs the guidance as a review bot on every pull request to its extension repo, configured with a three-line prompt. In five weeks the bot reviewed about 480 PRs and commented on 64. Engineers fixed 43 findings at a median of 15 minutes from comment to fix.

Those findings clustered in accessibility, HTML semantics, and forms. That tracks with every linter I've wired into continuous integration (CI). The tool catches what has a rule, and the boring middle stays invisible.

## legacy-scan is deterministic on purpose

The CLI ships a `legacy-scan` workflow trained on 30,000 GitHub repositories. Irish reports 92% average precision on held-out repos.

The announcement is honest about scope. The scan is static analysis over HTML, CSS, JavaScript and `package.json`, checking a deliberately limited set of patterns. Narrow first, with agentic audits planned later.

```shell
# install into a project
npx modern-web-guidance@latest install

# scan an existing codebase for upgrade candidates
npx modern-web-guidance@latest legacy-scan .
```

Determinism is the whole point of legacy-scan web modernization. An agent told to modernize a file rewrites the whole file. A scanner reports the file, the line and the matched pattern. That bounds the diff before the agent touches anything.

## The Chrome-dominance objection is fair, and partly answered

HN user `advisedwang` raised the sharpest objection in that thread, warning the road ends at a dominant-browser web. Replies came fast. `super256` pointed at the contributor list. Philip Walton confirmed Firefox and Edge as contributors, then conceded Mozilla joined only in the last few weeks and hasn't had much influence yet.

What actually limits the risk is Baseline, the cross-browser compatibility standard the guides build on. A non-Baseline feature has to come with documented fallback. Guides covering origin trial APIs stay hidden behind explicit opt-in through a `.mwgrc` file.

That is a constraint on the recommendation engine. A promise would be cheaper to make and worth less.

## What I'd do with this first

Install it with telemetry off, then run the scan read-only on a branch before any agent touches the output:

```shell
DISABLE_TELEMETRY=1 npx modern-web-guidance@latest install
```

Two rules for the first pass:

- treat `legacy-scan` hits as review candidates rather than tickets,
- and read the fallback section of any guide recommending something your Baseline targets don't cover.

Then keep a human on the accessibility findings, which no linter was catching before.

I run a daily fleet of AI coding agents on a Celeron host, and the thing I want from them is mostly restraint. A skill that activates on a layout task and stays quiet otherwise is worth more to me than a server that is always present and usually irrelevant.

## FAQ

### Does the skill work without an agent?

Yes. The CLI searches and retrieves on its own, and the announcement notes developers already use the guides as a learning resource. Run `npx modern-web-guidance@latest search "..."` yourself and read what comes back.

### Will legacy-scan fix my code by itself?

No. It identifies candidates through static analysis and hands them to the agent. Since the rewrite is still an agent action, read the diff before you merge it.

### What happens with a feature that isn't Baseline yet?

Guides for origin trial and volatile single-engine features stay searchable but are gated on retrieve until you opt in via `.mwgrc`. That gate exists so an agent doesn't adopt an unstable API on your behalf.
