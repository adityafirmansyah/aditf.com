---
title: Agent Skills Are Environment Notes, Not Prompt Tricks
slug: agent-skills-environment-notes
date: 2026-10-26
excerpt: The "skills are worthless" argument is aimed at prompt folklore. What runs on a 19-profile agent fleet is closer to operational code, and it carries a real context bill.
tags: ai-agents, skills, context-engineering, supply-chain, agent-fleet
---

Three agent-skill repositories trended on GitHub today. The counts are from the API, measured this morning:

- cloudflare/security-audit-skill at 47,315 stars
- Nutlope/hallmark at 34,379
- pbakaus/impeccable at 88,034

On the same day, a post titled "AI Skills" are worthless in 2026 reached the lobste.rs front page.

Both things are true, and most of the argument between them is people discussing different objects. What a marketplace calls a skill is usually prompt trivia aimed at a model. What runs on my 19-profile agent fleet is closer to notes about the environment the model executes inside, and those notes survive model upgrades.

That distinction decides what belongs in a skill file. It also decides what the file quietly charges you.

## The context bill, measured

The skeptics are right about the economics, and the numbers on my own machine are worse than the complaint. HN user prodigycorp, in the thread under the Cloudflare skill: "There are way too many skills for the platform. ... The way it is right now pollutes our context window."

Here is what that looks like on this box:

```bash
find ~/.hermes/profiles -name SKILL.md -not -path '*/.deleted/*' | wc -l
# 1285
```

Nineteen agent profiles, 1,285 skill files, 13.7 MB of markdown. Loaded raw, that is roughly 3.4 million tokens.

Nobody loads all of it. Progressive disclosure means the harness sees a name and a one-line description first, and opens the body only when a task matches. So the honest figure is the description layer, which sits in front of every task before any work starts:

- 77 KB of descriptions
- about 19,000 tokens
- a 177x gap between advertising a skill and using one

That gap is the design constraint. Shelf space is cheap; the shelf label is the budget.

## What a model cannot re-derive

The test I apply now is simple: could a better model figure this out alone, given the same repo and the same question? Three rules from my own pipeline fail that test:

- Reddit's JSON endpoints answer with an HTML block page on this host. Exact comment counts come from the HN Algolia API or not at all.
- Every source URL gets an HTTP check before it is cited. A dead link at research time is a correction; a dead link at publication is a retraction.
- The brand name is Dagango.com, spelled out every time. A model that has never seen the internal codename will invent something plausible.

None of those are tricks for getting a model to behave. They are facts about a host, a provider and a naming decision. Training weights do not carry them, and a better model does not start carrying them.

## The backlash is a category error, twice over

Charles Miller's post is better than its title. Its opening example is the C folklore that `i++` is slower than `++i`, a habit compilers made irrelevant decades ago. He extends that to prompt engineering, then delivers the verdict everyone quoted. A skill that can be picked up in a few weeks and is obsolete a few months later "has no value outside the moment."

On lobste.rs, roryokane pointed out what a lot of readers had missed. In Miller's post, "AI skills" means the skills of humans who use AI. So the argument that travelled is about a person's ability to prompt, wearing the name of a file format.

The model-facing half of the thesis is still correct. Anything that only concerns phrasing a request gets absorbed into the product. That is why I stopped writing skills that describe how to talk to a model.

The useful line in that thread came from markerz: "Skills should generally be pretty light weight." That is a context-budget argument, which is the one worth having.

## Six phases, not an incantation

The Cloudflare skill is the counter-example, and it is worth reading past the star count. Its README says plainly that it "is the skill that seeded Cloudflare's vulnerability discovery harness."

The workflow is six phases:

- **Reconnaissance:** map architecture, trust boundaries and input surfaces into a coverage ledger.
- **Coverage-led hunting:** assign isolated hunters per ledger unit.
- **Candidate validation:** hand each finding to a fresh verifier that tries to disprove it.
- **Structured output:** write confirmed, needs-validation and rejected records against a JSON schema.
- **Independent verification:** separate agents check the final source claims.
- **Reporting:** derive the documents from verified records only.

That is a review process written as markdown, and the design principle that sells it is one sentence: the agent that checks a finding is never the agent that found it. It is the same separation I use between coding agents and the QA pass.

Their README also reports that a single run found roughly half of the vulnerabilities that repeated runs found in total. That is an argument for orchestration. It is not an argument for a better prompt.

## Distribution is not trust

The part nobody trends about: a skill is markdown that the harness treats as instructions carrying your privileges.

Unit 42 documented the June 2026 version of that failure on ClawHub. A skill named tradingview-ai-indicator-assistant shipped a prerequisite block pointing at a paste site. The user was told to pipe a base64 blob into a shell, which downloaded the cluw infostealer.

The report's own summary is the sentence worth keeping. It describes the isolation gap directly: "a single malicious skill can grant an attacker full control over the agent's permissions and access to the underlying system."

Synthesia's writeup makes the same point from the engineering side. Their team got generic results at first. A bare request to review a diff produced, in their words, "an OWASP top-ten checklist applied to your code," so they built an audit skill tuned to their stack and their common pitfalls.

They also landed the context argument better than the HN thread did. A precise scope is the difference between an agent staying inside its lane and "wandering through unrelated files polluting its context window."

## What I check before an install

Reading the file is a lower bar than it sounds, and it filters most of what is on a marketplace.

- Read the whole SKILL.md and skip past the description. The malicious ones hide the payload in a setup step.
- Grep for `curl`, `npx` and anything that writes outside the skill directory.
- Ask whether the skill needs a sandbox to be safe. Cloudflare's README requires one that disables external networking before it will execute target code.
- Pin the version and commit it. Every skill I keep has a diff history.
- Delete anything you installed for one task. The long tail is where the description budget goes.

The same tests apply to writing. One lesson per file, and the lesson has to be something the model got wrong on this machine at least once.

## What survives a model upgrade

My largest skill is 100 KB, around 25,000 tokens of accumulated pitfalls from a research pipeline that has been running for months. Grotesque by the standards of a prompt pack, and it earns its size because every paragraph was paid for by a failure I do not want to repeat.

Most skill files on that fleet will be dead within a year, and they should be. The ones that outlive their model are the boring ones: what this host blocks, what this provider charges, what the product is called. That knowledge has a shorter half-life than a compiler's and a longer one than any prompt trick.
