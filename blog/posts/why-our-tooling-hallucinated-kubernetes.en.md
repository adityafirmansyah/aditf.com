---
title: Why Our Multi-Agent Tooling Hallucinated Kubernetes (And How We Fix Context Poisoning)
slug: why-our-tooling-hallucinated-kubernetes
date: 2026-10-19
excerpt: Our internal developer tooling for docs and runbooks cleanly approved a specification claiming Dagango.com runs on Kubernetes. Here is how context poisoning broke verification.
tags: ai-agents, software-architecture, devops, prompt-engineering, software-engineering
---

## The architecture we never built

At Dagango.com, we run an autonomous multi-agent fleet for internal documentation, code reviews, and system specifications. On October 17, 2026, that pipeline cleanly approved an architectural runbook claiming our platform runs on Kubernetes.

We have never deployed Kubernetes in production.

Dagango.com runs on simple Linux servers and bare-metal nodes. Our actual production stack relies on:

- plain systemd service units for process supervision,
- nginx reverse proxies handling TLS termination,
- and single-binary background workers running under local user accounts.

Our repositories contain zero pods, Helm charts, or cluster ingress controllers.

Our developer tooling went far beyond mentioning Kubernetes in passing. It confidently described cluster scaling policies and pod restart behavior across multiple detailed technical paragraphs.

## How the research agent poisoned upstream context

The failure began upstream from the generator agent and the verification reviewer. The hallucination was planted early inside the initial research summary.

When LLMs summarize system state from fragmented notes, they do more than extract raw facts. They compress information and bridge narrative gaps:

- the researcher ingested author profile notes mentioning past microservices consulting work,
- it parsed a separate note about Dagango.com running a Next.js and FastAPI monorepo,
- and it fused both items into a single plausible technical stack.

The resulting brief declared that Dagango.com operated a containerized microservices fleet on Kubernetes.

Once that claim landed inside `brief.md`, our pipeline's trust boundaries completely inverted. In our tooling design, the research summary represents sourced ground truth. Downstream generator agents face strict prohibitions against altering the brief or accusing it of fabrication without external contradiction.

The research agent suffered from aggressive semantic synthesis rather than a random hallucination. That synthesis poisoned the shared context for every subsequent stage.

## The illusion of layered synthetic review

To prevent technical inaccuracies and drift, we placed an adversarial verification agent at the end of the pipeline.

The reviewer runs on Claude Opus with strict verification rules. It flags technical specifications containing invented metrics or fake engineering anecdotes.

Yet the verifier scored the Kubernetes runbook with zero critical defects:

- the verifier checked whether the generated draft stayed faithful to the research brief,
- it found that the brief explicitly specified Kubernetes as the deployment platform,
- and it concluded that the generator followed instructions accurately.

This is the central illusion of layered LLM review. A verifier instructed to check factual alignment against upstream context cannot detect when the upstream context itself is fabricated.

The reviewer functioned as a compliance checker instead of a fact checker. Because the lie was present in the source prompt, the verifier treated it as verified ground truth.

## Statistical plausibility vs semantic invariants

Our automated verification is actually very good at catching certain classes of hallucinations.

In previous runs, it caught invented performance numbers and exaggerated metrics. When a generator tried to claim a 91% cache hit ratio without empirical evidence, the verifier flagged it immediately.

Numbers can be verified against server logs and external benchmarks:

- numeric values usually possess explicit primary source citations,
- percentages must align with telemetry data recorded in repository artifacts,
- and benchmark metrics fail verification when absent from referenced URLs.

Architectural claims behave completely differently. To an LLM, Kubernetes sounds entirely plausible for a multi-tenant Next.js and FastAPI e-commerce application. The claim exhibits high statistical plausibility while being factually untrue for our specific infrastructure.

LLMs evaluate semantic plausibility instead of empirical ground truth. Without an explicit invariant assertion, a plausible falsehood passes automated review every time.

## Cascading consensus in agent echo chambers

Stacking multiple AI agents fails to create genuine independent verification. In practice, it builds an echo chamber.

Once a false premise crosses the prompt boundary into shared state, subsequent models amplify the claim. The generator agent never questioned whether Dagango.com needed Kubernetes. Instead, it generated detailed technical prose describing how our background workers handled container lifecycles.

The pipeline produced synthetic consensus through four distinct stages:

- the researcher invented the architecture through loose profile synthesis,
- the generator elaborated the premise with realistic operational jargon,
- the verifier validated that the prose faithfully matched the brief,
- and our workflow automation prepared the document for internal handoff.

Every model agreed with the premise. Each turn added plausible corroborating detail to a foundational lie.

When engineers assume that three separate agent turns equal three independent reviews, they mistake layered computation for independent verification.

## Concrete defenses against context poisoning

Fixing this vulnerability required structural changes rather than minor prompt tweaks.

In our production developer tooling, the immediate fix was straightforward:

- **Explicit architectural invariants in SOUL contracts.** We added deterministic negative constraints to agent system prompts. Both the researcher's and auditor's contracts now explicitly state that Dagango.com runs on Linux VPS instances with systemd and nginx, and never on Kubernetes.
- **Decoupled invariant validation.** Rather than allowing the verifier to treat the brief as unquestioned ground truth, critical infrastructure facts must be verified against hardcoded system invariants.
- **Human architectural gatekeeping.** While automated agents handle documentation drafting and syntax checks, human engineers must retain the authority to catch semantic drifts that pass synthetic consensus.

Negative constraints in prompt profiles stop known hallucinations immediately. But long-term reliability requires treating upstream LLM outputs as untrusted input rather than ground truth.

## Pragmatic takeaways for agentic engineering

Autonomous multi-agent architectures are rapidly moving from research demos into production developer tooling.

Yet as teams delegate complex tasks to agent fleets, context poisoning remains a silent failure mode. If your review agents rely on shared prompts generated by upstream models, your verification pipeline is compromised from the start.

Engineering reliable agent workflows demands clear boundaries:

- treat upstream LLM outputs as untrusted user input rather than ground truth,
- encode critical domain invariants as deterministic code assertions instead of soft prompt guidance,
- and maintain human verification at critical deployment boundaries.

AI agents can draft, format, and organize technical documentation with remarkable speed. But keeping their claims tethered to real-world infrastructure remains our responsibility as systems engineers.
