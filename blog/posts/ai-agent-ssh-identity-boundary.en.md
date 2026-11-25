---
title: AI Coding Agent SSH Security Needs an Identity Boundary
slug: ai-agent-ssh-identity-boundary
date: 2026-11-25
excerpt: AI coding agent SSH security depends on more than hiding private keys. Separate the agent’s identity and permissions from yours, then add key-use controls that fit the risk.
tags: ai-agents, ssh, security, linux, developer-tools
keywords: AI coding agent SSH security, SSH agent key constraints, least privilege for coding agents, separate Linux user for AI agents, short-lived SSH certificates
---

I can remove every Secure Shell (SSH) private-key file from disk and still let an artificial intelligence (AI) coding agent act with my identity. That is why AI coding agent SSH security starts with a harder question: which identity and permissions does the running process actually have?

Key storage matters. But moving a key behind an agent socket addresses one part of the problem, not the authority available to the process using it. If your agent can read your repositories, use your credentials, and reach your SSH agent, it may act through those access paths even without copying a private-key file.

## AI coding agent SSH security starts with identity

Johanna Larsson’s November 23 post, “You Can’t Afford SSH Keys on Disk,” describes moving SSH clients to Bitwarden’s SSH agent and removing local key copies. It also describes setting the approval interval to match a four-hour vault-lock interval. That is a reasonable credential-handling choice. It is not, by itself, a process-containment policy.

The distinction matters because the agent and the key have different security boundaries. An SSH agent holds keys and offers signing or authentication operations to clients. A process that can access the agent may be able to request those operations, depending on its setup and any required confirmation. Preventing key-file scraping does not automatically prevent a process from using an available authentication interface.

The OpenSSH agent protocol makes this boundary explicit. Request for Comments (RFC) 9987 says the design aims to prevent an unprivileged attacker from obtaining a copy of loaded keys. It also warns that this may not prevent theft of their use when keys are loaded without confirmation. Those are different outcomes: copying secret material versus requesting authentication through an agent that remains available.

That difference is central for coding agents. If you start one as your normal user, assume it can exercise the permissions granted to that user unless you have tested a control that blocks a particular path. A prompt asking the model to be careful is not an operating-system boundary.

## What SSH agent key constraints can and cannot do

OpenSSH provides useful controls for limiting how a loaded key is used. The `ssh-add` manual documents options for lifetime limits, confirmation, and destination constraints. Each can reduce exposure, but none should be mistaken for a general sandbox around an agent process.

- A lifetime limit removes a key from the agent after a chosen interval.
- Confirmation requires approval for authentication requests.
- Destination constraints restrict the destinations for which a key may be used.

These controls add friction to credential use. They do not by themselves decide which directories a process can read, whether it can access a developer’s Git credentials, or whether it can modify files outside a project. Treat them as layers around authentication, not substitutes for access control.

The Hacker News discussion on Larsson’s post had 163 points and 107 nested comments when checked on November 25. One recurring concern was straightforward: an agent running as the developer may inherit the developer’s access. Several commenters pointed toward a separate user with minimal permissions, which also makes actions easier to attribute.

## Build least privilege for coding agents in layers

For a Linux-based agent workflow, I start by asking what the agent needs to do, then grant only that access. A separate Linux user for AI agents is a useful starting boundary because it separates process ownership and home-directory credentials from the human account.

I operate a Linux-based Hermes agent fleet, so I treat process identity and repository scope as separate decisions. A concrete review starts by checking which OS account launches an agent and testing which repositories that account can write. The brief here is a design recommendation, not a claim about a measured permission layout across my fleet.

A practical checklist:

- **Separate service identity.** Run the agent under its own OS account instead of your interactive account.
- **Narrow repository scope.** Give it access only to the working tree or repositories it needs.
- **Limit credentials.** Use narrowly scoped tokens and avoid passing credentials the task does not require.
- **Disable unnecessary forwarding.** Do not expose an SSH agent to remote hosts or processes that do not need it.
- **Keep attribution.** Make logs distinguish agent activity from actions taken directly by a human.

This is a design checklist, not a claim that one specific fleet configuration has been benchmarked. The boundary is useful only if you can test it: confirm which files the service account can read, which repositories it can write, and whether the agent can reach your personal SSH socket.

Credential choice can then scale with the threat model. A passphrase-protected key with a timed `ssh-agent` may be enough for a developer using a local agent for low-risk tasks. Add confirmation or destination constraints when an approval step or narrower destination access is worth the friction. Hardware-backed keys or short-lived SSH certificates can make sense when infrastructure supports them and the operational cost is acceptable.

Short-lived credentials are not magic either. They reduce the window in which a credential remains useful, but they do not stop an authorized agent from acting during that window. Scope and identity still matter.

## Make the boundary testable before making it clever

Isolation adds setup and workflow friction. Separate accounts need deliberate repository permissions, credential provisioning, and a clean way to review changes. A strict boundary that nobody can maintain will eventually be bypassed for convenience.

I would begin with one testable change: run the agent as a dedicated user and verify its filesystem and credential access before expanding the workflow. Then add key constraints or shorter-lived credentials where the threat model warrants them. Keep the human account out of the agent’s environment unless a task requires a specific capability.

That gives the team an auditable starting point. It also makes later exceptions visible instead of turning “the agent needs access” into an unexamined grant of the developer’s entire identity.

## FAQ

### Does removing SSH keys from disk stop an agent from authenticating as me?
No. It reduces exposure to direct key-file theft, but a process with access to an SSH agent may still request authentication operations. Confirmation and destination constraints can narrow that path.

### Do SSH agent constraints sandbox a coding agent?
No. They govern key use, such as lifetime, approval, or destination. Use operating-system permissions and repository scope to control broader process access.

### When are short-lived SSH certificates useful?
They are useful when your infrastructure can issue and validate them and when reducing credential lifetime helps your threat model. They still need appropriate identity separation and permissions.