---
title: 'AWS Emulator: 438 API Models, Zero Human-Written Code'
slug: aws-emulator-agent-fleet-harness
date: 2026-11-12
excerpt: AWS Emulator covers 438 AWS API models, and the commit log is all IssueFinderAgent and IssueFixerAgent. The harness did the work, not the model.
tags: ai agents, aws, rust, cloud, software engineering
keywords: aws emulator, autonomous ai agents, rust cargo workspace, localstack alternative, multi-agent coding fleet, smithy api modeling
---

AWS shipped AWS Emulator to GitHub on November 11, 2026, under a Creative Commons CC0 public dedication. The repository covers 438 AWS API models. Matthew Goldberg, a Sr. Principal Engineer at AWS, says in the announcement post that his team has not written or reviewed any of the code.

That claim is the easy part to repeat and the hard part to believe. So I read the repository instead of the press release, starting with `AGENTS.md`. That file is the working guide every agent loads before it touches the tree, and it is where the actual design lives.

## AWS Emulator runs between a spec and a live-cloud oracle

Goldberg's starting point was an Anthropic result from earlier in 2026: give agents a well-defined spec plus a reference implementation, and they can build something that faithfully implements it. AWS had both halves already. The AWS API Models are the spec. The real cloud is the reference implementation.

The first team of autonomous AI agents turns those two into tests. Each test is a real AWS scenario, and the agents verify it against live AWS before submitting it. After that the test can be replayed as many times as you like without calling AWS again.

The fidelity suite now holds tens of thousands of scenarios. That is the part most teams skip when they wire up a coding fleet, and it is the part that decides whether the fleet converges or drifts.

Goldberg's weekend experiment is the cleanest demo of that loop in action. He gave Kiro, AWS's spec-driven agentic coding tool, a short instruction:

- write tests from the AWS Command Line Interface (CLI),
- iterate on those tests until they pass against real AWS,
- build an in-memory implementation that those same tests pass against.

Fifteen minutes later he had a passable Amazon Simple Queue Service (SQS).

## Three agent teams, one closed loop

The fleet is split by function because, in Goldberg's words, the agents have more success on bounded tasks. The split is not a management nicety. It is what keeps each role's output checkable by the next one.

- **Test builders** turn the API models into cloud-verified scenarios. Their output is a pass/fail the rest of the system can trust without an opinion.
- **Issue finders** replay that suite locally, watch for divergence, and file structured issues. They are told to group failures that probably share a root cause.
- **Issue fixers** take exactly one issue, check out the code, and edit until the failing test goes green.

One issue per fixer is the detail I would steal first. It caps the blast radius of any single agent edit, and it makes a bad fix cheap to revert.

## What the AWS Emulator workspace actually looks like

The Rust Cargo workspace gives every service its own crate. Changing one service recompiles one crate, not the whole emulator, which is the difference between a fleet that works in parallel and a fleet that queues.

```
aws-emulator/
├── Cargo.toml                 # workspace root: NOT editable by agents
├── services/service-<name>/   # one crate per service
│   ├── build.rs               # generates from the Smithy model
│   ├── smithy-model/          # <name>.json, drives the wire protocol
│   └── src/ops/               # one file per operation
├── core/router/               # re-rendered on every service add
├── vendor/engine/             # agent-immutable, single shared engine
└── issues/                    # fixed and open, as directories
```

The `services/` directory currently holds 436 `service-*` crates next to a shared `common` crate. The 438 figure comes from the API-model count in the announcement, so the two numbers are tallying different units.

Two more boundaries matter. `vendor/engine` is vendored and off-limits, so there is exactly one in-memory engine and nobody forks it. The root `Cargo.toml` is read-only for agents, and the router gets re-rendered rather than hand-edited.

Build cost is the honest downside. A full debug build needs at least 100 GB of free disk, which is what a workspace of this shape costs.

## Why did an earlier fleet build its own Python interpreter?

In an earlier version of this system, the agents decided to build their own Python interpreter to support AWS Lambda functions.

Nobody asked for that. It is the most useful failure story in the whole announcement, because it looks like creativity from the outside and like drift from the inside. Goldberg's framing is that agents need a coloring book: a well-defined area to fill in, with the assurance that the larger picture will come together.

The current `AGENTS.md` reads like a list of everything that went wrong before. Three rules are worth copying straight into any agent fleet you run.

- Credentials are created through the emulator's credential store. Agents never construct an access key or secret themselves, and never log one.
- URLs that callers fetch later go through the emulator's own signer. An agent that hand-rolls `X-Amz-Signature` produces a URL that points at the real service or fails verification.
- Resource endpoints come from the emulator's context object. Nothing is assembled from `<service>.<region>.amazonaws.com`, because the agent would be reaching for production.

That third rule is the one that matters most in practice. An agent that can reach a real cloud endpoint can spend real money, and no prompt politely asking it not to counts as a control.

## The merge gate is the actual product

Every fixer change passes a gate before it lands. The gate blocks code that does not compile. Agents also review the change against coding standards, check it for security problems, and confirm fidelity did not regress. A failed check sends the change back for rework.

AWS reports thousands of issues fixed per day, with hundreds of agents working the same repo concurrently. Commits stack on AWS CodeCommit, get built and retested, and only reach GitHub at the end of a release.

Read the commit log and the harness is visible in the author field. Recent entries alternate between `IssueFinderAgent` filing issues and `IssueFixerAgent` closing them. No human name appears.

## Where the human hours went instead

Generating code with a large language model (LLM) is cheap now. What is not cheap is the work that makes generated code trustworthy, and that work did not shrink. It moved.

For AWS it moved into a short list:

- the Smithy API modeling layer, where every service's operations are defined before code exists (Smithy is AWS's interface definition language),
- a live-cloud oracle the whole fleet is graded against,
- crate boundaries that stop agents from colliding,
- a merge gate that nobody can talk their way past.

I run a multi-agent coding fleet against our own monorepo, and this matches what I see. The failures are never about whether the model can write Rust. They are about two agents editing the same root manifest at once, or one agent quietly inventing a dependency it did not need because nobody told it what already existed.

The Python interpreter is that same failure with a bigger bill.

All that engineering investment in boundaries and live oracles makes the resulting artifact trustworthy to run locally.

That credibility is also why the LocalStack news matters here. LocalStack ended its Community edition on March 23, 2026, and its remaining free tier excludes commercial use. Teams that lost an unauthenticated local emulator now want a free one. A CC0 release with published fidelity scores is a credible LocalStack alternative for continuous integration (CI) work, even with gaps in the long tail of services.

## FAQ

### Do I need an AWS account to run AWS Emulator?

No. Start the binary and point your software development kit (SDK) at `https://127.0.0.1:9297`, which serves a self-signed certificate. Your requests never leave the machine. AWS charges no separate emulator fee, and the README is explicit that it is not for production workloads or for security testing.

### Why do I see 436 service crates when AWS says 438?

The 438 is an API-model count from the announcement. The `services/` directory currently carries 436 `service-*` crate directories plus a shared `common` crate. The workspace and the announcement are tallying different units.

### Can I use it as a drop-in LocalStack replacement?

Check the fidelity scores published with each release before you commit a CI pipeline to it. The repository tracks gaps honestly: open items live in `issues/things-that-do-not-work/`, and repaired ones move to `issues/things-that-now-work/`. For embedded Rust tests it goes one step further. The emulator compiles into your test binary, so there is no endpoint or certificate to configure.

## What I would take from this

You do not need 438 API models to benefit from the shape. Start with an oracle your fleet can be graded against, then cut the workspace into small units, then put one gate in front of the shared branch. Skip the oracle and you get a fleet that is fast, confident, and wrong.
