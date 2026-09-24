---
title: Your Agent's Config Silently Failed: The Canary Test That Catches It
slug: agent-config-canary-test
date: 2026-09-24
excerpt: Claude Code shipped AGENTS.md support gated behind a remote flag, so telemetry-off users got silent failures. Here's the five-second test that catches this class of bug in any agent setup.
tags: ai-agents, claude-code, developer-tooling, debugging, llm-workflows
---

A markdown file sits in your repo. Your coding agent walks right past it. No error, no warning, just quietly dumber output than it should be giving you.

That's what happened to Claude Code users who disabled telemetry. The bug hit Hacker News on September 23rd and reached 466 points and 267 comments within a day. The root cause was almost insulting in its simplicity: a purely local file read, gated behind a remote feature flag that telemetry-off users could never reach.

## What actually broke

Claude Code 2.1.277 shipped AGENTS.md support as a built-in plugin. The plugin registers with `isOnByDefault = false`, and its availability check queries a remote flag called `tengu_agents_md_mod`, falling back to `false` if the flag can't be fetched.

Reading a markdown file from your working directory needs zero network calls. But the permission to read it lived behind one anyway. If telemetry was off, the flag request never went out, the fallback kicked in, and AGENTS.md was never loaded, silently, every single session.

The counterintuitive part is how you'd try to fix it and fail:

- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` blocks the flag fetch.
- `DISABLE_TELEMETRY=1` blocks it too.
- Setting either variable to `0` does **not** help, because Claude Code's env-var handling treats any value as "set," true or false as a string be damned.
- A `.claude/settings.json` env block clearing both variables has no effect at all. There's no per-repo opt-in.

Only a session-level override, `claude --settings '{"env":{...}}'`, actually works, and only starting from the second session, because the first session is what fetches the flag in the first place. Third-party gateways, Bedrock, and Vertex all inherit the same failure, because the remote flag can't resolve true through any of them either.

## The apology was the fast part

Traction here moved quicker than the fix itself. The underlying GitHub issue was filed only three days before the HN post, with the author's own measurements attached. An Anthropic engineer, `mpoteat`, showed up in the thread and owned it directly: "this was a fully human error on my part."

The mechanism causing the bug was a rollout kill-switch, meant for remote disable in an emergency, that telemetry-off users structurally could never receive.

A fix shipped in v2.1.281 the same day. Same-day, named, in-public correction is the part of this story worth remembering as much as the bug.

## The canary test you can run today

The single most useful artifact from this whole incident isn't the bug. It's the verification method the author used to prove it. Drop a canary word into your instruction file, then ask the agent to report it back while explicitly forbidding it from reading files to find the answer.

```
echo 'The canary word is PERIWINKLE.' > AGENTS.md
```

Then ask your agent, fresh session, no file reads allowed: "What's the canary word? Say NONE if you don't have one." Run it twice. The first session in a config change is often the one that fetches a flag or reloads a cache, so the real test is whether the second session still gets the word right.

Generalize this pattern past AGENTS.md. Every instruction surface in a multi-agent setup deserves the same five-second check:

- Hermes skills that might get pruned from context.
- CLAUDE.md or AGENTS.md files that might silently fail to load.
- System prompts that might get truncated or swapped.
- MCP configs that might reference a server that never actually connected.

"The file exists" is not evidence that "the agent received it." Those are two different claims, and the gap between them is exactly where this bug lived for however many sessions it went unnoticed.

## Workarounds if you're stitching multiple tools together

If you use both Claude Code and Codex on the same repo, `@path` imports aren't gated by the same flag, which gives you a one-line escape hatch:

```
echo '@AGENTS.md' > CLAUDE.md
```

That costs you the exact convenience AGENTS.md support was supposed to deliver: one shared file instead of a per-tool copy. But it works reliably where the native plugin doesn't.

Shared skills have a similar problem. Codex reads `.agents/skills` natively, but Claude Code 2.1.280 only recognizes those paths through `/import`, which copies the files rather than referencing them. A copy drifts from its source the moment either side changes.

The author's workaround is a symlink: `.claude/skills` pointing at `../.agents/skills`, so both tools read the same files on disk instead of maintaining two versions that quietly diverge. An HN commenter, `vorticalbox`, reported the identical duplication pain across Cursor and Claude, so this isn't a one-tool problem.

## What this means if you're running a fleet, not a CLI

Two HN comments frame the design lesson better than I could. `mgaldys4` put it plainly: "Reading a local file should never depend on a remote feature flag, and silently skipping it with no warning is worse."

`nfRfqX5n` added the sharper observation: "can't tell if this was intended or a bug." That uncertainty is itself the whole problem, since a well-behaved system doesn't leave that question open.

If you're building or operating any kind of agent harness, the rule set is short:

1. Gate remote things remotely. Gate local things locally. Don't cross the streams.
2. If you must skip loading something, print a warning. Silent skips are how this bug survived multiple releases undetected.
3. Version-pin your harness. A silent behavior change on upgrade is worse than a loud failure on install.

I run a multi-agent Hermes fleet across coding, QA, and PR review through a custom provider. This incident is a direct prompt to go verify my own instruction delivery in CI, rather than assume a config file getting committed means it's getting read.

"The agent behaved oddly" is a config-delivery question before it's ever a model question. Run the canary test on your own setup this week. It takes less time than reading this post did.
