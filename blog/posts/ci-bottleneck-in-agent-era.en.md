---
title: AI Agents Flooded Our PR Queue: Fixing CI Before It Breaks
slug: ci-bottleneck-in-agent-era
date: 2026-09-22
excerpt: Coding agents made writing PRs nearly free, which means your pipeline is now the bottleneck. Here's what Linear's CI rework maps to on a small-team budget.
tags: ci-cd, ai-agents, developer-productivity, testing, github-actions
---

Fourteen PRs sitting in the queue on a Tuesday morning, all from agents, none from a human who typed a single line. That's the Hermes fleet I run against dagango.com and a couple of client repos on a normal week. Coding and QA agents don't sleep, don't get tired of writing tests, and don't feel bad opening PR #15 while #12 is still running CI. The thing that broke first wasn't the codebase. It was the pipeline validating it.

Linear posted about this exact problem on September 21st ("AI coding has made CI a bottleneck, so we reworked ours to keep up"), and it climbed past 230 points and 250-plus comments on Hacker News within a day. Every team running agents at scale seems to have hit the same wall around the same time. Linear's own product data tells the wider story: teams that connected a coding agent roughly tripled weekly PRs over two years, from 21 to 65, while AI moved from under one issue in a thousand to just under half of everything created in Linear. In their CI post specifically, they said internal test suites had nearly quadrupled since January. None of this is Linear-specific. It's what happens to any pipeline built for humans once your "junior developers" are agents running in parallel around the clock.

## The bottleneck moved from writing code to verifying it

For years, the constraint in software delivery was authoring: writing the code, writing the tests, writing the PR description nobody reads. Agents collapsed that cost close to zero. CI capacity didn't collapse with it, because CI was sized for how fast humans produce PRs, and agents produce them at an entirely different pace. Linear held PR wait time around 5-6 minutes despite the test suite explosion, but only because they actively cut runner time per test roughly in half. Verification capacity is now something you have to engineer for, the same way you'd engineer for database load or API rate limits.

I felt this directly the week I turned three coding agents loose on the dagango.com repo. GitHub Actions minutes on our plan burned through a month's worth in nine days. The code quality wasn't the problem. The pipeline choking on job count was.

## Cheapest win: fix the infrastructure before touching the pipeline logic

Linear's first lever cost them zero pipeline changes: swapping GitHub Actions for faster third-party runners made jobs 34% faster on average, with `tsc` type-checking dropping 52%. No workflow rewrite, no new tooling to learn, just a different runner underneath the same YAML.

For a small team or UMKM-budget setup, premium hosted runners get expensive fast once job count is exploding instead of shrinking, because per-minute billing punishes exactly the volume agents create. Self-hosted runners on commodity hardware change that math. Mine live on a homelab box I'd be embarrassed to mention in a hardware forum, and they still win on wall-clock time to first result: no queue to wait in, no meter running, nothing to do with the hardware itself being fast.

## Count runner starts, not seconds

Linear's second lesson: fix your critical path before you micro-optimize anything inside it. Capping git fetch depth took their slowest gate job from 94 seconds down to 20. Batching seven tiny checks into two jobs saved roughly 87,000 runner-minutes a month, 11.8% of their total CI spend. Neither change touched test logic. Both wins came from counting how many jobs ran, regardless of how long each one took.

```yaml
# Before: 7 jobs = 7x cold-start tax
jobs:
  lint: {...}
  typecheck: {...}
  unit-fast: {...}
  unit-slow: {...}
  format-check: {...}
  license-check: {...}
  deps-audit: {...}

# After: 2 jobs, same checks, far fewer runner starts
jobs:
  static-checks: # lint + typecheck + format + license + deps-audit
    run: pnpm lint && pnpm typecheck && pnpm format:check && pnpm license:check && pnpm audit
  tests:
    run: pnpm test:unit
```

Every job start carries fixed overhead (checkout, dependency restore, environment setup) before it runs a single assertion. Multiply that by agent-generated PR volume and it stops being a rounding error. On our own pipeline the shape was different, five jobs instead of Linear's seven, but the fix was identical: folding them into two cut our average PR gate time by almost a third, no test logic touched.

## Test isolation is now a cost center, and agents make it riskier

Vitest's default per-file isolation rebuilds the module graph for every test file. Safe, and expensive at scale. Linear's `isolate: false` opt-in was their single biggest saving, around 17% of monthly CI cost, dropping their API shard runtime from 32.8 to 22 minutes. It's also the riskiest change on the list: turning off isolation means tests can leak state into each other if they're not written carefully.

Your agents write most of your tests now, and they don't reliably know when a test needs isolation. A human who's been burned by shared mutable state writes defensive tests out of scar tissue. An agent optimizing for "make CI green" will happily write a test that passes in isolation and corrupts the next test's fixtures when isolation is off. Linear gated this with explicit opt-in comments and per-file teardown requirements: mark tests as isolation-safe one at a time, and review those markings like a security-sensitive diff. On our Next.js projects, that means pure-function unit tests only, zero shared module state, nothing that touches a database fixture or a mocked API client.

## Don't cache what's cheaper to rebuild

Linear's `node_modules` cache took about 28 seconds to restore. A filtered `pnpm install` took 7.5. They deleted the cache. Caching feels like a free win because it's the default advice everywhere, but it carries a restore cost that almost nobody benchmarks against the alternative. The lesson generalizes past node_modules: a cache is a bet that restore time beats rebuild time, and that bet doesn't always pay off.

## What should agent-era CI actually gate on?

The HN thread under Linear's post split into two camps worth knowing about. One commenter, yieldcrv, argued that unit tests in general have become cosmetics that inflate coverage numbers, and made a point worth sitting with: he doesn't see agents using tests any differently than a junior or mid-level developer does, because humans weren't exactly rigorous about it either. Another, sz4kerto, made the sharper practitioner point: review has quietly shifted from reviewing the code to reviewing the tests, because that's where an agent's actual claims about correctness now live. Solomon Hykes, Docker's founder, argued build and test need to be scheduled as one system rather than bolted together, treating verification as infrastructure rather than an afterthought.

Running this fleet daily, my read is simple: gate hard on the money path, the handful of flows that actually break your business if they break, and let everything else be cheap and fast. An agent-generated test that's green doesn't mean the thing it tests is real. The agents will keep opening PRs at whatever pace they run at, pipeline ready or not. Ours wasn't, for about nine days straight, until we started treating runner starts and isolation policy as engineering decisions instead of an afterthought bolted onto a green checkmark.
