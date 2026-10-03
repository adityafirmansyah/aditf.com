---
title: You Said No MCP: The Tool-Loadout Tradeoff Nobody Tests
slug: mcp-in-core-tool-loadout-tradeoff
date: 2026-10-03
excerpt: Pi spent a year saying it would never speak MCP, then shipped it in the core. The reason was not that MCP got better. The sandbox underneath it did.
tags: ai-agents, mcp, tooling, architecture, self-hosting
---

Earendil published "You Said No MCP!" on 29 September, and the thread that followed is the rare HN fight that stays technical for 351 comments.

The setup is a public reversal. For a year, Pi's site and its podcasts said the same thing: Pi does not support MCP. The current release ships MCP in the core.

The reflex reading is that the protocol won. Read the actual post and the reason is different. Nothing about MCP convinced them. The thing they had to build to run it, a JavaScript sandbox called Codemode, was worth building on its own.

## The reversal is a refactor decision, not a conversion

Their argument is careful, and it is worth separating from the headline.

- "The first thing to remember is that the world is not static."
- The MCP they dismissed a year ago is not the MCP they are shipping now.
- The code changes MCP required were "generally useful" on their own.

That last point is the load-bearing one. Bringing MCP into core needed the same thing Pi needed anyway, in their words: "a sandbox to play with in the form of an interpreter."

So they built the sandbox first. MCP got a place in the core because it was already sitting on a floor they wanted.

## Composition is the part that is still unsolved

They do not pretend the problem is gone. Read the admission in full, because it relocates the blame:

> "The biggest issue with MCP continues to be that it's hard to compose. Even with codemode, which is just a neat little sandbox to allow composing of tool calls, MCP doesn't fully deliver on this."

Then the sentence the thread skipped. That difficulty, they write, is "less the problem of MCP but the MCP servers out there."

This is the practitioner takeaway. The protocol is a spec. The servers are other people's engineering, and most of them are not built for the job.

## The tool contract is the real defect

Their description of the average MCP server will be familiar to anyone who has watched a context window fill up:

- servers "just dump tools into the context,"
- and return prose "to optimize on their side for token efficiency by returning text."

Their stated target is a different contract entirely. They want MCP to sit "much closer to OpenAPI with intelligent tool discovery," where two rules hold:

1. tools return structured data, not text;
2. tools are discoverable through their documentation and description.

That is the axis to judge any tool surface on, protocol name aside. A tool that dumps a paragraph into my context to say what a single JSON field would say is a tax I pay on every turn.

## Codemode is the actual engineering lesson

Strip away the MCP framing and Codemode is a design pattern you can copy today, whether or not you ever run the protocol.

- It runs harness-side, "where the harness runs," because the harness loop is trusted and the tools it calls usually are not.
- It composes calls with JavaScript instead of one ordered tool call per turn.
- Its state lives "as part of the session transcript instead of the file system."
- Its safety story is modest and stated as such: small JavaScript engines can ship "as WASM binaries and allow reasonable levels of protection."

None of that works on an old model. They name the prerequisites outright, having spent recent months on them so Pi could "make sense with new models that allow deferred tool loading, mid-conversation system messages and reasoning level changes."

That is the part worth internalizing. Adopting a wider tool surface is safe only after your harness can defer tool loading, return structured results, and compose inside a sandbox whose lifetime is the session.

The worked example is a loop over a Linear issue tracker. Four parallel workers classify comment tone and rank the most frustrated reporters. The transcript closes with a recount of "331 earlier calls" — one summary line standing in for 331 tool invocations the model never had to hold.

## What my own loadout actually costs

I run sixteen agent profiles from one box, and the advice to "just add the protocol" collides with a real budget. I counted it, per platform, across all of them.

- The CLI platform declares 27 builtin toolsets and enables 19 of them.
- The Discord surface declares the same 27 and enables 17.
- MCP servers configured anywhere in that fleet: zero.

Zero is not an accident. Every toolset I enable spends context on every turn, and the deferred-loading trick that makes Codemode safe is exactly what lets Pi ship a wide surface without paying for all of it at once. Without that, adding 27 toolsets is how you make a model worse at the 19 it already had.

## The counter-arguments worth engaging

The thread's best objections are not about GitHub culture. They deserve to be listed:

- `otabdeveloper4` calls MCP "the NIH non-standard version of OpenAPI."
- `_fw` answers with ubiquity: MCP is suboptimal, "but so is USB-C. So is NVME, so is HDMI."
- `ramses0` points at xkcd #927 and the standards-soup it satirises.
- `mikeocool` walks through the OpenAPI-plus-OAuth2 setup that should have shipped instead.

The strongest is `wren6991`: "if LLMs want to compose multiple operations, they have the perfect tool for this: bash." If that is true, Codemode is a wheel with extra steps.

`hobofan` gives the reply that matters. "In many scenarios, e.g. running the harness server-side, as is the case for chat interfaces, you don't really want to expose OS shell access as that opens up a huge security attack surface."

Which is the whole post in one exchange. Composition needs isolation, and isolation is what you were building anyway.

## Cheap isolation is what sets the ceiling

Netlify's migration from V8 isolates to Firecracker MicroVMs is the same lesson from the infrastructure side. The numbers are concrete:

- roughly 5x faster at the median;
- warm invocations at ~5-6 ms p50, down from 25-40 ms;
- p99 invocations 47.4% faster;
- 99.998% availability;
- cold invocations on about 1.2% of requests, at roughly 9 ms each.

The security reading in that thread is the part to sit with. As `phickey` puts it, "the V8 team does not consider them to be a security boundary."

Both posts are answering one question. How much can you safely hand a model? The answer is set by how cheap your isolation is, and how strong your isolation actually is. A session-scoped sandbox and a MicroVM are the same bet at two different sizes.

## What I am taking from this pair

- **Judge a tool surface by its contract.** Structured results and real discoverability beat protocol branding.
- **Build the sandbox before you widen the loadout.** Composition without isolation is a bigger attack surface with better marketing.
- **Defer tool loading.** A wide surface is only cheap when the model does not have to see all of it.
- **Watch what a tool puts in the transcript.** The 331-call collapse is a design target, not a novelty.

Pi did not cave to MCP. It built an interpreter, and MCP fit inside it. That is a better reason to ship a protocol than liking the protocol.
