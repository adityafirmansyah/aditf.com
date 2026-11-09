---
title: Agent Memory Doesn't Need a Schema, It Needs a Byte Budget
slug: agent-memory-byte-budget
date: 2026-11-09
excerpt: The push to standardize agent memory fixes the wrong layer. What actually degrades models is a store that never evicts, and a byte ceiling plus on-demand skills fixes it.
tags: ai-agents, llm-tooling, system-architecture, devops
---

On November 7, 2026, Mads Thines published the case for giving agent memory its OpenTelemetry moment. Nine memory formats, none of them readable by the others, and a 2019 precedent that fixed exactly this kind of fragmentation. The diagnosis lands.

The prescription aims one layer too high. What developers complain about is mostly eviction, not serialization.

An agent writes a transient debugging decision into a store that never forgets, then reads it back in every later session as a standing rule. You can stop that tonight with a byte ceiling. A shared schema only standardizes the shape of the mess.

## What OpenTelemetry actually agreed on

The comparison table is the most useful part of the post. It sorts nine families of memory, from a Markdown file at a known path to a graph with two timelines. Read the Forget column:

```
format                        unit of memory                forgetting
AGENTS.md / CLAUDE.md         whole Markdown file           never, a person edits it
Anthropic memory tool         file under /memories          only if the model deletes it
Copilot Memory                fact plus code citations      28 days unused
Letta core memory             labelled block, char limit    never
Mem0                          extracted fact                optional expiry date
LangGraph BaseStore           JSON value at namespace+key   optional TTL
MCP reference memory server   entities and relations        never
Graphiti / Zep                fact on a graph edge          invalidated, not deleted
LoreKit                       record with scope and key     only if a TTL is set
```

Four of the nine carry a built-in or optional expiry, and a fifth, Graphiti, invalidates facts instead of deleting them. The remaining four never forget unless a person or the model goes back and removes an entry one at a time.

OpenTelemetry's shared layers were a data model, semantic conventions, a wire protocol, and reference SDKs. Vendors kept competing on storage and query.

The data model was the part that worked, and the reason is unglamorous. A span gets consumed by a machine that indexes it. A memory note gets consumed by attention, so every token of envelope competes with reasoning.

## The complainers are describing eviction

The Hacker News thread ran 105 comments, and the objections were operational rather than aesthetic. The comment from `slopinthebag` states the charge plainly: "at this point i'm pretty convinced agent memory is strictly harmful. it remembers the wrong things, and then turns them into an inane focus for each task."

`SwellJoe` said the same thing: "Everybody builds one, and then eventually realizes it makes the model stupid and confused."

`Kwpolska` named the mechanism. Claude Code writes one-off decisions and transient problems into memory, and later sessions then act on context that never held in general. `nonethewiser` called the effect confirmation bias, and estimated that an unvetted note is at most 90% correct.

Not one of those comments asks for a wire format. Each one describes an entry that should have been deleted and survived.

## Anthropic put a number on it

Anthropic's research writeup on agent memory components is blunt about injection: "Injected memories use up valuable tokens, and an incorrect note can be carried into every session."

The same section adds that loading a note does not guarantee the model acts on it, because longer instruction files reduce adherence.

Claude Code's mitigation lives inside the product. It loads only the first 200 lines or 25 KB of MEMORY.md. `troupo` quoted that cap in the thread to argue that these files are often ignored rather than obeyed.

Two failure modes, one fix: keep the injected layer small.

## Three tiers on one box

My fleet runs nineteen agent profiles on this machine, with 1,392 SKILL.md files between them, 58 to 166 per profile. Thirteen of the nineteen also carry a `memories/MEMORY.md`. Those files run from 594 bytes on viral-researcher to 8,985 bytes on cto. The root profile's store sits at 9,040 bytes.

Context splits into three tiers:

```
SOUL.md              identity and hard rules, loaded every session
skills/**/SKILL.md   procedural runbooks, loaded on a trigger match
memories/MEMORY.md   facts, capped and consolidated on write
```

The cap is the load-bearing part. Writes fail when the store is full, so the agent has to consolidate or delete before it can add anything. Three profiles here set an explicit ceiling of 6,000 or 9,000 characters. The rest run at the 2,200-character default.

At 2,200 characters, a session's vocabulary runs out fast. That is the feature. It forces a decision about what deserves to survive, made while the current task is still in front of the model.

## A byte ceiling beats an envelope

LoreKit's record adds exactly the fields a shared format needs: address, key, lifecycle, and written_by. The last one is the sharpest idea in the proposal. It lets a reader weight a note by who wrote it, and a fact extracted by a service is weaker evidence than a directive a human typed.

Metadata cannot evict anything, though. A record that declares its own expiry still needs something to enforce that expiry. No format can decide that last month's debugging shortcut stopped being true. A budget forces the judgement at write time, which is the only moment the context is loaded.

A ceiling does not replace curation either. Someone still has to open the file now and then and read it top to bottom. Consolidation of a wrong premise only produces a tidier wrong premise, and that failure is invisible to every metric except a human read.

## What I would copy before there is a standard

Three parts of the proposal are worth building now, standard or not:

- Conventions for address levels and attribute namespaces, so two tools can describe the same repo without a translation layer.
- Conformance tests in place of a reference implementation, because a test suite survives a rewrite of the storage layer.
- Live addressing between concurrent tools, the harder half of the problem and the half the current proposals mostly skip.

On that third point, the existing work is honest about its own scope. MacPaw's `.mem` bundle, the Open Memory Protocol draft, and Cognee's COGX all concentrate on export: moving one person's memory between vendors. A CI job, an editor agent, and a review bot reading the same record at the same time is still unsolved.

Standardize the vocabulary, not the storage. Put a byte ceiling on anything that gets injected into every session, and move procedure into files that load when a trigger fires. A memory format with no forgetting path is a format that ships context rot by default.
