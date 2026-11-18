---
title: AI-Generated Code Maintenance Is the Real Test of a Rust curl Rewrite
slug: rust-curl-rewrite-maintenance
date: 2026-11-18
excerpt: AI-generated code maintenance is the hard part of a Rust rewrite of curl. A convincing first build says little about compatibility, fixes, and releases a project must sustain.
tags: rust, ai agents, software maintenance, open source
keywords: AI-generated code maintenance, Rust rewrite of curl, software rewrite risks, memory safety vs maintenance, agent-generated code review
---

A team of AI agents can translate a large C codebase into Rust and get tests to pass. That is a useful demonstration, but it is not evidence that the resulting project can take over curl’s job. AI-generated code maintenance is the real test: can the rewrite keep pace with bug reports, compatibility expectations, and releases after the initial build?

Daniel Stenberg’s November 17 post about two Rust rewrites of curl makes that distinction concrete. I have built side projects in Rust, and after 13 years shipping software, I have learned to judge rewrites by the maintenance loop they can join. The language choice matters. The work after the language choice matters more.

## What the curl rewrites demonstrate

Stenberg identifies two projects, `urlx` and `kov/curl`. The latter claimed an $8,600 spend. That is a claim associated with the project, not an independently verified cost audit, so I would not use it as a benchmark for what a rewrite should cost.

Stenberg says agents translated 185,000 lines of C into 340,000 lines of Rust. In roughly the same three-plus weeks, curl merged more than 300 commits and landed a little over 200 bug fixes. Those figures describe different kinds of work: one produces a new snapshot, while the other keeps a mature project moving.

The distinction is easy to miss when the first result looks impressive. A passing test suite shows that the implementation satisfies the tests that exist. It does not show that those tests cover every compatibility promise, platform, or newly discovered failure mode.

## Why AI-generated code maintenance is the harder measure

An established project carries obligations beyond its source tree. Users depend on behavior that may be undocumented, maintainers have to investigate reports, and releases need to reach the platforms people actually use. A rewrite inherits those obligations only if its team deliberately takes them on.

A useful test is not “How much code did the agents produce?” It is whether the project has a credible process for turning newly reported problems into reviewed fixes and dependable releases. That process needs named owners. Otherwise, a repository can look complete while its users are left to discover where the edges are.

For a multi-agent setup like the Hermes fleet I operate, the same rule applies. Agents can produce changes quickly, but throughput does not replace tests or review gates. Teams still need issue triage and a human who owns the outcome. A green check is evidence about a particular check, not proof that production behavior is correct.

## Does a Rust rewrite remove curl’s security risk?

No single language choice removes every class of defect. Stenberg reports 81 confirmed curl vulnerabilities in 2026, of which 14, or 17.3%, were likely related to memory safety. He argues that a Rust rewrite would not automatically eliminate the other 67.

That is not an argument that Rust is pointless. Rust’s type system and ecosystem can make memory-safe designs easier to express, and some defects would not transfer unchanged in a rewrite. But protocol correctness, compatibility behavior, and error handling still require careful implementation and review.

The useful distinction is memory safety versus maintenance, not C versus Rust as a team sport. A rewrite may reduce particular memory risks while creating new compatibility gaps or leaving the project without a sustainable security response. Engineers should evaluate those outcomes separately.

## The source code is only part of the project

In the Hacker News discussion, one commenter reports curl has had 1,306 contributors and 99 versions. The commenter also reports about 17,000 closed pull requests and 5,700 closed issues. Those are the commenter’s figures, not numbers I have independently audited. They still point to the work that accumulates around a long-lived project.

That history includes decisions, reports, fixes, and user expectations that are not captured by translating source files. The practical question for an organization is whether it can reproduce that support function, not just the current program’s output. For Dagango.com, an API-compatible implementation has limited value if it cannot keep pace with production behavior and support needs.

## A checklist for evaluating an agent-generated rewrite

Before treating a rewrite as a replacement, I would ask for evidence in six areas:

- **Compatibility:** Are there tests for the behaviors and protocols users rely on?
- **Historical failures:** Can the team reproduce and prevent important bugs from the original project?
- **Release cadence:** Who ships updates, and how quickly can users receive a fix?
- **Platform coverage:** Which operating systems, architectures, and dependency combinations are maintained?
- **Security ownership:** Who receives vulnerability reports and coordinates a response?
- **Parity over time:** Is there a credible plan to track upstream changes and close behavior gaps?

A demo can answer whether agents can create a substantial first implementation. These checks answer whether a team intends to support it. Keep the distinction visible in reviews: generated code is an input to engineering, not a substitute for owning the software.

## FAQ

### Does passing the original test suite prove a rewrite is compatible?
No. It proves only that the implementation passes the tests included in that run. Teams still need coverage for real user behavior, supported platforms, and cases exposed by later bug reports.

### Does Rust prevent every vulnerability found in a C project?
No. Rust can help prevent memory-safety defects, but it does not automatically solve protocol mistakes, compatibility regressions, or failures in dependencies and operational response.

### What should a team ask before adopting an agent-generated replacement?
Ask who owns releases and security reports, how historical bugs are tested, and how the project will track compatibility over time. If those owners and processes are missing, the code is not yet a supported replacement.
