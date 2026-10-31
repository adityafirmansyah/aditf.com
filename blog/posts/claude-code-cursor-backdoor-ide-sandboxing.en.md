---
title: Backdooring Claude Code on Cursor: Why IDE Extensions Must Be Sandboxed
slug: claude-code-cursor-backdoor-ide-sandboxing
date: 2026-10-31
excerpt: An 11-hour breach of Cursor's marketplace proxy injected a reverse SSH backdoor into Claude Code. Developer tools cannot safely share an unsandboxed runtime with workstation credentials.
tags: security, ai-agents, developer-tooling, supply-chain
---

When you install an Integrated Development Environment (IDE) extension, you are not granting scoped permissions to a sandbox. You are launching an unconfined Node.js process under your user account.

That distinction matters.

On October 29, 2026, developers installing or updating Anthropic's Claude Code extension inside Cursor received a malicious payload. For eleven hours, Cursor's proxy distributed compromised extension packages.

The implant dropped an attacker key into authorized keys. Then it opened an outbound reverse Secure Shell (SSH) tunnel straight to an attacker server.

Most teams treat extension registries like mobile app stores. We assume automated scanners keep our workstations safe.

They do not.

When an extension runtime shares full privileges with your local user, a proxy compromise becomes a total workstation breach.

## The Eleven-Hour Injection Window

Between 2:27 AM PT and 1:35 PM PT on October 29, Cursor served backdoored builds of `Anthropic.claude-code`. The affected releases were versions 2.1.312 and 2.1.313.

The upstream source was clean. Anthropic security engineers David Dworken and Felix Rieseberg confirmed that Anthropic infrastructure was untouched. The official Microsoft Visual Studio Marketplace and Open VSX registries remained clean.

The breach hit Cursor's caching proxy (`marketplace.cursorapi.com`). This proxy caches Open VSX packages and serves editor-specific extensions.

An attacker compromised that proxy pipeline. They swapped the extension bundle before Cursor's automated supply-chain scanners could catch the change.

Endpoint security firm Phorion published the technical breakdown. The discussion quickly reached 857 points on Hacker News and 149 points on Lobste.rs.

Cursor took the marketplace offline to rotate signing keys. They worked with the upstream hosting provider to terminate the attacker server. Anthropic quickly shipped clean version 2.1.314.

## Anatomy of the Payload: From IIFE to Reverse SSH

The attack succeeded because it did not wait for user input. The attacker prepended an Immediately Invoked Function Expression (IIFE) to the minified `extension.js` bundle.

```javascript
// Malicious IIFE prepended to extension.js
(function() {
  const fs = require('fs');
  const { exec } = require('child_process');
  // Runs immediately when Node loads the module
})();
```

Node executed the payload the instant the editor loaded the file. It ran before the extension reached its legitimate `activate()` lifecycle hook.

No prompts appeared. No clicks were required.

Once running, the implant carried out several targeted actions:

- It created `~/.ssh` if the folder did not exist.
- It wrote an Ed25519 public key with comment `svc-telemetry` to `~/.ssh/authorized_keys` with 0600 permissions.
- It started an outbound reverse SSH tunnel (`-R *:0:localhost:22`) to `134.209.82.225:22` using an embedded private key.
- It harvested up to 40 environment variables matching tokens like `AWS`, `GCP`, `KEY`, or `SECRET`.
- It beaconed host metadata to `134.209.82.225:8099/beacon` and `127.0.0.1:8099/beacon`.

The attacker also established persistence across reboot:

- On macOS: a LaunchAgent plist at `~/Library/LaunchAgents/com.apple.sysmond.plist`.
- On Linux: a crontab entry running `@reboot ~/.config/.smt`.
- On Windows: a scheduled task named `SysMon` and a script in the Startup folder.

A logic bug limited damage on non-root macOS setups. The script ran `systemsetup -getremotelogin` to check SSH status. That utility requires root privileges. Because the command returned an administrative error instead of string `Off`, the script skipped enabling remote login.

Even with that blunder, the attacker still stole cloud credentials and developer identity data.

## The Architectural Flaw: Zero-Isolation Runtimes

The problem is bigger than Cursor's proxy. The core issue lies in the execution model of modern IDEs.

Web browsers spent twenty years isolating tabs behind capability models. Mobile operating systems run each app inside strict sandboxes.

VS Code and its forks did not follow that design. An extension executes as plain Node.js with the developer's full User Identifier (UID) privileges:

```
+---------------------------------------------------------------+
| Developer Workstation (UID 1000)                              |
|                                                               |
|   +-------------------+       +---------------------------+   |
|   | Unsandboxed IDE   | ----> | Reads ~/.ssh/id_ed25519   |   |
|   | Extension Process | ----> | Reads ~/.aws/credentials  |   |
|   | (Node.js runtime) | ----> | Harvests active shell env |   |
|   +-------------------+       +---------------------------+   |
+---------------------------------------------------------------+
```

Your extensions can read private SSH keys without prompting. They can inspect your shell history, clone private git repositories, and exfiltrate cloud credentials.

Cursor relied on automated scanners to spot malicious code on the proxy. That strategy will always lag behind determined attackers.

You cannot secure an unconfined runtime with static scanners alone. If bad code lands on the machine, the game is already over.

## How We Harden AI Agent Workflows in Production

In my own setup at GOSG Consulting and across Dagango.com, we run autonomous agent fleets every day. Our setups run coding agents and Command Line Interface (CLI) workflows through tools like Claude Code and Hermes.

My baseline rule is simple: AI coding tools are untrusted third-party code. We do not run autonomous coding agents directly on primary workstations with production keys.

We enforce four isolation practices across our fleet:

- **Isolated execution namespaces.** Agents run inside unprivileged Linux containers or ephemeral Virtual Machines (VMs) without access to the host filesystem.
- **Ephemeral scoped credentials.** We issue short-lived access tokens rather than static cloud keys.
- **Socket containment.** We never mount or forward the host `SSH_AUTH_SOCK` into an agent runtime.
- **Strict egress filtering.** Outbound network rules block unexpected ports, including outbound SSH traffic on port 22.

Here is a baseline egress filter using `iptables` to block rogue tunnels from worker containers:

```bash
# Drop outbound SSH connections originating from container workers
iptables -A OUTPUT -p tcp --dport 22 -m owner --uid-owner agent-worker -j DROP
```

If an extension tries to spawn a reverse tunnel, the network stack drops the packets immediately. The beacon dies before reaching the Command and Control (C2) server.

## Sandboxing Is the Only Durable Boundary

The Cursor team handled the incident quickly. They took down the proxy, rotated keys, and patched the pipeline. Anthropic responded with clean builds within hours.

Yet treating this incident as an isolated proxy breach misses the lesson.

Tomorrow, an attacker might compromise an npm dependency or hijack a developer account. When they do, IDE extensions will still run with unrestricted user permissions.

We need capability-based security in our development environments. Editors must require explicit permissions before an extension touches local storage, network sockets, or sub-processes.

Until editor vendors build real sandboxes, developers must draw the boundary themselves. Run your AI tooling in containers, isolate your keys, and assume any extension can execute arbitrary code.
