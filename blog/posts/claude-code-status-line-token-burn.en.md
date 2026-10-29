---
title: Why Claude Code Burned 20% of API Requests on Status Lines
slug: claude-code-status-line-token-burn
date: 2026-10-29
excerpt: An OpenTelemetry audit revealed Claude Code spent nearly 20% of its API requests generating three-word terminal status lines. Polling frontier models for UI progress is an architectural leak every agent harness must fix.
tags: ai agents, claude code, prompt engineering, developer tools, software architecture
---

When an OpenTelemetry audit revealed that one in every five Application Programming Interface (API) calls in Claude Code was spent generating three-word status lines, it exposed an expensive flaw in agent telemetry.

Flamerix AI analyzed request metrics from `claude_code.api_request` events grouped by `query_source`. The data was startling. A background polling routine named `agent_summary` accounted for 16.4% of total token spend and 19.7% of all requests.

That background routine actually outspent the main interactive conversation, which consumed 15.7% of tokens. The telemetry audit highlighted several stark figures:

- 96% of all status queries were dispatched to Claude 3 Opus.
- The input-to-output token ratio reached approximately 9,000 : 1.
- Every thirty seconds, the client fed 50,000 to 100,000 tokens into the model to produce three words of terminal feedback.
- Telemetry events confirmed that UI spinners were competing directly with actual engineering work for model throughput.

## The OR Expression You Couldn't Turn Off

In Claude Code versions 2.1.257 through 2.1.312, background subagents ran with an aggressive polling loop. A hardcoded `setInterval` timer fired every thirty seconds. On every tick, the client packaged the entire conversation transcript of every active background agent and shipped it back to the frontier model.

The goal was simple. The client wanted to update terminal status text like "analyzing repo" or "editing test suite".

The trouble was that users could not disable it. While documentation referenced an `agentProgressSummaries` flag, the implementation wrapped it in a hardcoded OR expression. That flag remained glued to `true` in the bundled binary.

If you launched three parallel background agents to refactor tests, your client sent three massive prompts every thirty seconds. The loop ran relentlessly regardless of whether the agent had produced new output:

- Transcripts were re-sent even when an agent was idle waiting on a shell command.
- Background subagents accumulated conversation history rapidly, making subsequent queries heavier.
- Network bandwidth on local developer machines was consumed uploading duplicate prompts continuously.

Anthropic engineer Edwin Arbus confirmed the polling mechanism on Hacker News (thread #50284255). He noted that status queries accounted for roughly 6% of total terminal spend across users submitting telemetry. Arbus pointed to an upcoming prompt cache alignment fix in version 2.1.311+ and an in-progress short-notes mode for smaller models.

## The Prompt Cache Mirage

The standard defense for frequent polling is prompt caching. If the conversation transcript is already cached, each read costs only 10% of the normal input token price. That discount sounds reassuring until you run the basic arithmetic of background fleets.

Even with a 98% prompt cache hit rate, polling creates continuous financial drag:

- A 100,000-token transcript read at 10% cost still bills 10,000 token-equivalents every thirty seconds.
- Three active subagents generate 360 status queries per hour.
- At 10,000 discounted tokens per call, that background churn burns 3.6 million input tokens an hour just to refresh three terminal lines.
- Across a full workday, status polling alone can burn tens of millions of billable tokens.

Then consider cache misses. When an agent writes code or receives a tool result, the prompt prefix shifts. Cache Time To Live (TTL) expirations also cause recurring cache evictions.

Prompt cache entries expire after five minutes of inactivity. When a background subagent pauses to wait on slow builds or external network calls, that TTL window closes silently. The very next status query pays full price for 100,000 input tokens.

Flamerix AI found that the remaining 2% cold cache misses accounted for more than a third of the feature's entire token cost. A single cold miss on Opus wipes out hours of cached savings in an instant.

## Disarming Bun Bytecode at Runtime

Claude Code does not ship as plain JavaScript inside `node_modules`. It is distributed as precompiled Bun bytecode. Developers could not simply patch source files on disk to kill the timer.

Flamerix AI engineered an ingenious workaround using Bun's preload hook (`BUN_OPTIONS=--preload`). Their `no-agent-summary.js` script intercepts timer registration at startup:

```javascript
// Hook setInterval to neutralize the agent_summary loop
const originalSetInterval = globalThis.setInterval;

globalThis.setInterval = function (callback, delay, ...args) {
  const fnStr = Function.prototype.toString.call(callback);
  if (fnStr.includes("agentProgressSummaries") || fnStr.includes("agent_summary")) {
    // Delay timer to 2^31 - 1 milliseconds (~24.8 days)
    return originalSetInterval.call(this, callback, 2147483647, ...args);
  }
  return originalSetInterval.call(this, callback, delay, ...args);
};
```

By checking `Function.prototype.toString`, the preload hook traps the specific summary callback. It pushes the timer interval out to 2147483647 milliseconds—effectively disarming the loop without crashing the process.

Anthropic subsequently shipped version 2.1.311+, adjusting cache breakpoints to reduce recurring miss penalties.

## Telemetry Must Be Push-Based and Local

In my own setup, I manage an autonomous multi-agent Hermes fleet across Linux VPS nodes and an Intel Celeron J4105 homelab box. Our agents handle automated coding tasks, Quality Assurance (QA) runs, and Pull Request (PR) reviews. If our harness polled a frontier model like Opus every thirty seconds just to draw a CLI spinner, our API bills would spiral immediately.

Agent User Experience (UX) should never depend on recurring frontier model inference. Instead, practical agent telemetry follows three design rules.

- Push on deterministic transitions. Emit status messages during tool execution, file edits, or step completions rather than on a wall-clock timer.
- Use local models for summaries. When an agent needs conversational compression, delegate to Small Language Models (SLMs) or fast deterministic heuristics.
- Never couple terminal rendering to billable tokens. The terminal interface should reflect known state machines, not speculative model generation.

When model providers build developer harnesses, they face a subtle incentive trap. A loose timer loop silently inflates billed token consumption while giving users pretty terminal animations. As developers, we need transparent event-driven telemetry.

Stop polling Opus for UI eye-candy.
