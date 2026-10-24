---
title: Inside NVIDIA OpenShell: SMT Provers and Credential Proxies for Agent Fleets
slug: nvidia-openshell-agent-fleet-sandboxing
date: 2026-10-24
excerpt: OpenShell hides credentials behind a mediated proxy and gates policy changes with a Z3 solver. The sandbox is the easy half to copy. The per-sandbox model is the half that bites.
tags: ai-agents, sandboxing, rust, security, devops
---

OpenShell hit Hacker News on 22 October 2026 with 490 points and 211 comments. It is NVIDIA's Apache-2.0 runtime for autonomous agent fleets, and it currently sits at 0.1.5, five patch releases past the 0.1.0 tag in late September. Most of the thread fought about telemetry. The architecture underneath is the part I keep re-reading.

My own default for a coding agent, until recently, was a container plus `-e OPENAI_API_KEY`. That is not isolation. It is a convenience wrapper for handing my cloud bill to a process that takes orders from whatever text it happens to read.

Container isolation answers "can these two processes see each other's memory". It does not answer "can this process see a secret".

Once the key lives in the environment, every mechanism that gives an agent useful access becomes an exfiltration path. A malicious dependency in a lockfile. A poisoned build script. A `curl` the model invented at 2am.

DNS tunneling alone is enough, and nobody notices a few hundred lookups.

## Put the secret behind a proxy, not in the box

OpenShell's bet is structural. The agent holds zero resident credentials. Requests bound for an approved endpoint get credentials injected on the way out, by a supervisor that runs outside the sandbox.

The sandbox side is the cheap part to reproduce:

- `Landlock` confines which files the workload can open.
- `seccomp` user notification stages network operations before they execute.
- The workload runs under one non-root identity, with no Linux capabilities.

What makes it work is the seam. Supervisor and sandbox talk over a single mutually authenticated HTTP/2 connection carrying many independent streams. The compute driver picks the transport:

- a Unix socket for Docker and Podman,
- TCP for Kubernetes,
- vsock for MicroVM.

Each TCP connection gets its own stream with its own backpressure. A slow package download cannot stall DNS resolution or an exec. Anyone who has run an agent behind a single-threaded proxy has felt the alternative.

## Four questions the solver answers

Policy expansion is where agent sandboxing usually rots. An agent hits a wall, proposes a rule, gets it approved, and a year later the policy file is a museum of one-off exceptions nobody dares revoke.

NVIDIA's answer is `openshell-prover`. It is a Rust crate, and it encodes three inputs as a Z3 SMT model: the policy, the credential set attached to the sandbox, and a registry of what each binary can do.

Then it runs reachability queries over four categories:

- `link_local_reach`: does the policy reach a host in `169.254.0.0/16` or `fe80::/10`? That covers cloud metadata endpoints.
- `l7_bypass_credentialed`: can a binary on a non-HTTP wire protocol reach a host where a credential is in scope?
- `credential_reach_expansion`: does a binary reach a new host and port tuple with a credential in scope?
- `capability_expansion`: on an endpoint the binary already reaches, does the change add an HTTP method?

The first two are unconditional risks. The last two are delta properties: the gateway proves the baseline and the merged policy, then surfaces only the new paths.

Any finding blocks auto-approval. An empty delta lets the proposal through, but only once a reviewer opts in through `proposal_approval_mode` at gateway or sandbox scope.

One distinction trips people up. Boundary checks and proposal-risk checks answer different questions, so passing one tells you nothing about the other. The CLI runs boundary checks, written for agents that need to confirm a subagent's policy stays inside the parent's. The advisor runs proposal-risk checks on every rule an agent proposes.

## The prover is per-sandbox, and your fleet is not

Here is the line I would staple to any internal design doc: the model is per-sandbox. The crate's own README states that it does not reason about cross-sandbox or cross-binary intent, and that two sandboxes sharing a credential through external policy get analysed independently.

That is the confused deputy problem, and it needs no exotic attacker. A network-restricted agent that can post a task to an unconstrained deployment agent over your message bus has an egress path no per-sandbox policy describes. The sandbox holds. The fleet leaks.

Formal verification does not make this worse. It makes it legible, because the model's scope is written down instead of implied by marketing.

If you are wiring delegation between agents, the graph is what to verify. Who may dispatch to whom, and which credential ends up attached to a request at the far end of the chain. Proving each node alone is table stakes, not the whole contract.

## Default-on telemetry, and three exits

Telemetry ships as a default-on Cargo feature. The documentation draws the line narrowly: sandbox lifecycle outcomes, provider profile buckets, policy decision counts, aggregate network denial categories. No sandbox names. No hostnames, file paths, prompts, or credentials.

HN user `overflowy` pasted that policy into a thread comment along with the opt-out flags, and much of the argument ran from there. `lcampbell` objected to the wording on the grounds that collected categories are introduced with "such as" rather than an exhaustive list, while calling the documented disable good enough. `Lammy` argued that no network connection is anonymous, since the connection alone leaks your IP and the hours you work.

`dangoodmanUT` put the tradeoff most plainly: default telemetry is a bad default, and the control surface is "almost too pedantic". I think both halves are correct, and the second half is why the first is forgivable.

Three exits exist, and they are not equivalent:

- `OPENSHELL_TELEMETRY_ENABLED=false` on the gateway deployment.
- `server.telemetryEnabled=false` for Helm installs.
- A build with `--no-default-features --features defaults-without-telemetry`, which leaves no endpoint and no emission code in the binary.

The first two are configuration. The third is the only one I would trust on a box holding production credentials, because a flag can be unset by the next person to touch the values file.

## What I actually took from it

The runtime is not the lesson. The lesson is the split between what an agent can do and what an agent knows. OpenShell's mediated channel answers the second question properly, and most homegrown harnesses never think to ask it.

The second lesson is that a verifier with a documented scope beats a heuristic with a landing page. Per-sandbox modelling is a genuine limitation. It is also printed in the README, which means I can design around it instead of meeting it during an incident.

If I were starting a fleet tomorrow, the order would be boring: credentials behind a proxy first, filesystem and syscall limits second, and the SMT prover only once those two exist. A solver reviewing a policy that already hands out raw API keys is doing careful arithmetic on the wrong problem.
