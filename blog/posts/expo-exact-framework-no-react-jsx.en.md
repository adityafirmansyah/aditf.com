---
title: Expo Exact Framework: Native Apps With No React, No JSX
slug: expo-exact-framework-no-react-jsx
date: 2026-11-10
excerpt: The Expo Exact framework drops React, JSX, and the JavaScript bridge, betting that a virtual clock and a ten-verb driver make native apps buildable by AI agents.
tags: react, ai-agents, rust, frontend-engineering, architecture
keywords: expo exact framework, agent native ui architecture, expo ditching react, contract dsl rust, ai coding agent frontend testing, deterministic ui testing agents
---

On November 9, the Expo team pushed `expo/exact` public. It is a cross-platform UI runtime targeting web, macOS, iOS, and Linux. No React anywhere in the view. No JSX either.

Your first frame arrives before a single line of application JavaScript runs.

Two claims about the Expo Exact framework are true at once. It is the most honest piece of frontend infrastructure I have read this year, and it is a bet against the thing that currently makes models good at frontend.

Both halves matter if you ship software with agents.

## What the Expo Exact framework removes from the stack

Exact is not React Native, and it is not a React renderer. The repo states it plainly: "No JSX or React tier." Then, with unusual honesty for a launch, it adds: "The door stays open, but no one is building it."

What is left is an agent-native UI architecture. The runtime is built so a program can inspect and drive it directly.

What replaces the component tree:

- **Contract**, a small domain-specific language (DSL) for views. Closed record types, keyed lists, typed values, no escape hatch into arbitrary code.
- **A baked plan.** Contract compiles in four passes: syntax, types, analysis, lowering. Constant data is evaluated into the plan at build time, so first paint needs nothing else.
- **A Rust kernel.** `exact-kernel` lays out a columnar node arena using CSS rules through a patched Taffy. Text measurement is CoreText on Apple hosts and cosmic-text on Linux.
- **Host painters.** AppKit on macOS, UIKit on iOS, DRM/KMS (Direct Rendering Manager with Kernel Mode Setting) plus evdev input on Linux, and a ~20 KB runtime driving the real Document Object Model (DOM) on web.

Data logic sits behind one seam. TypeScript compiles to Hermes bytecode at build time and loads after the first pixel, or you write a Rust crate instead. Every answer from a data source gets checked against the shape Contract declared.

No webview. No JavaScript bridge. Hydration is not a bug you fix on this architecture. It is a design you never ship.

## Why is a virtual clock better than `await sleep(500)`?

Most agent-written UI tests die inside a wait. The agent taps a button, sleeps 500 ms, and screenshots. The animation is at 40% instead of finished. The next run it is at 60%.

That test is not flaky because the app is broken. It is flaky because wall-clock time is not an observable.

Exact hands the clock to the agent. Between two driver operations, nothing moves. Instead of sleeping, the agent sends `clock +60000` or `clock settle` and then reads the result.

That is what deterministic UI testing looks like when the runtime cooperates. Same input, same frame, every run, on every host.

```sh
bun scripts/agent.mjs web tree "tap change-station" "type station-search Palo" \
  "clock +60000" state "screenshot out.png"
```

Ten operations in total, and the count is a design decision: `tree · screenshot · tap · type · state · layout · logs · clock · prefer · perf`. The README explains why there are not more. An agent API grows one reasonable addition at a time "until no one can hold it in mind".

Tests work the same way. An `app.test.contract` file is a script of those operations. The same file runs unchanged on web, macOS, the iOS Simulator, and Linux headless. Caltrain's three tests take about two seconds on the web host.

## Where the real cost lands: training distribution

This is where I stop applauding.

Contract is small on purpose, so a whole app fits inside a context window. That is a real correctness win. Every write is declared, every list is keyed, every value is typed. Mistakes come back as refusals that say what to do.

The compiler reports up to twenty independent errors in one run.

But zero-shot fluency on TSX (TypeScript XML) and Tailwind CSS is not a property of TSX. It is a property of trillions of tokens of prior knowledge. Contract has almost none of that yet.

The Hacker News thread made the same point from a few directions. `doodlesdev` predicted the framework would work well with a frontier model and much worse with a cheaper one. `btown` argued that a DSL carrying arbitrary expressions needs a formal language spec, a generated lexer and parser, and a stdlib that behaves identically on every target.

The architectural comparisons landed too. `ogoffart`, who works on Slint, noted that the design is close to his framework. Both are Rust with a declarative DSL and their own compiler, both keep logic in a host language, and both expose tooling an agent can drive.

His sharpest difference: Slint has held a stable API since 2023, while Exact is pre-1.0 and changes daily. `zoom6628` reached further back, to QML and Qt.

Then there is `mrbombastic`, who wrote that prioritizing agents over humans in developer tooling makes him "sympathize with the Butlerian jihad". I laughed at that line more than I should have. The discomfort underneath it deserves a real answer, and nobody in the thread gave one.

## Six checks, sixty-five seconds, fifteen documents

The part I will actually copy lives in a single markdown file. `rules/RULES.md` treats every budget as a trade rather than a limit:

- **Six blocking checks, 65 seconds total.** A seventh requires deleting one in the same pull request.
- **1,500 lines per source file.** Generated files are exempt, since they are built and never committed.
- **15 documents in the working set.** A sixteenth requires archiving one.
- **700 words for the rules file itself.** If it grows, something becomes a check or stops being a rule.

The line doing the real work is short: "A limit gets exceptions. A trade doesn't."

This matches what I see running an agent fleet all day. Agents perform well inside a system with a small, low-latency, strictly bounded surface. Put the same agent in a repo where build scaffolding outweighs the feature, and the failure rate stops being funny.

## What I would actually steal this week

I would not migrate a product to Exact today. I would take three ideas from it this week.

- **Steal the clock.** Replace one `sleep` in your harness with an explicit settle step and measure. A single test tells you whether your app has an observable settled state at all.
- **Count your verbs.** Write down the operations your agent really uses. Above ten, and a few of them are one operation wearing two names.
- **Copy the trade wording.** "A seventh check requires deleting one" is governance a reviewer cannot argue with.

The README's "What works today, and what doesn't yet" section is the honest one. Windows control parity, Android delivery, camera access and signed TypeScript updates all sit on the unfinished list. Read it before you bet a sprint on this.

## FAQ

### Does Exact replace React Native for Expo apps?

No. Exact has no React tier at all, and React Native remains what Expo supports. Treat this as an experiment in machine-first UI architecture, with no migration path for a live product.

### Can an agent build and verify a whole app unaided?

The README documents one run: a fresh agent on a clean clone, given the quick-start prompt, finished a todo app in about 57 minutes. Its tests passed on web, macOS, and the iOS Simulator. About 25 of those minutes were the first macOS and iOS builds, roughly 13 each.

### Why delete JavaScript from the boot path instead of optimizing it?

Because startup is emergent and cannot be retrofitted later. `RULES.md` says the boot graph is budgeted from commit one and counted, not timed, so a regression fails a check instead of showing up as a slow benchmark.
