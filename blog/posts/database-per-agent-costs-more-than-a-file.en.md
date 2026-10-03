---
title: A Database Per Agent Costs More Than a File
slug: database-per-agent-costs-more-than-a-file
date: 2026-10-03
excerpt: Supabase says agents should be able to create a database as cheaply as a file. I already run one database per agent on a mini-PC, so I counted. The create is free; everything after it is the bill.
tags: sqlite, databases, ai-agents, infrastructure, self-hosting
---

## The pitch, in the vendor's own words

Supabase is acquiring Turso, and it framed the whole deal around agents. Supabase says it is already launching over one million databases per week. Agents, in its words, are "spinning up millions of databases to power the prototypes, explorations, dashboards, and apps they're building."

The promise is that agents "should be able to create a database as easily as creating a file, with just as little concern about cost."

I already live in that future. Sixteen agent profiles run on this box, each with its own `state.db`. The box is a 10-watt Celeron mini-PC, not a pitch deck. So I counted.

The create really is as cheap as a file. Nothing after it is.

## What Supabase is actually buying

The mechanics behind the pitch are Turso's. They rebuilt SQLite in Rust, and the cloud platform "can manage millions of databases, loading them when needed and suspending them when they're not."

That last sentence is the deal. Turso's own rewrite post is blunt about why it exists. After two years of libSQL, it says, "Independent usage of libSQL as a SQLite replacement remained low". Most users, it adds, came for SQLite-over-the-wire rather than core database improvements.

So Supabase is not buying a faster storage engine. It is buying the control plane: the machinery that suspends, resumes, checkpoints and backs up a million small databases. The file format was never the hard part.

## The bill, itemized

Scope: my home directory, with `node_modules` and VCS internals skipped. Measured 2026-10-03.

- **16 agent profiles**, each with a `state.db`. Counting the root database, that is 17 `state.db` files at 633 MB.
- **259 other `.db` files**, 61 MB.
- **16 `runs_idempotency.db` files**, 0.6 MB.
- **71 `.db-wal` files**, 108 MB.
- **71 `.db-shm` files**, 2 MB.
- **11 `state.db.bak` snapshots** from 24–27 September, 292 MB.

That is 449 files and about 1.1 GB. The largest single database is `eng-frontend/state.db` at 158 MB.

## A database is not a file. It is three.

SQLite is honest about this in its own docs. "There is an additional quasi-persistent '-wal' file and '-shm' shared memory file associated with each database," it says, which "can make SQLite less appealing for use as an application file-format". That caveat is about general-purpose container formats rather than the embedded use case.

Every database here runs in WAL mode, so every one of them is three files on disk. The write-ahead log holds transactions that are committed but not yet folded back into the main file.

On this box, the 17 `state.db-wal` files hold 60 MB. The biggest three (cto, pr-reviewer and branding) sit at exactly 6 MB each. SQLite only checkpoints automatically at 1,000 pages, so a busy agent can park a lot of committed data in a sidecar.

## Two costs that never make the slide

The first is read access. A WAL database cannot be opened by a process with only read permission, because the opener needs write access to the `-shm` shared-memory file. So the obvious escape hatch fails: copy the `.db` somewhere and read it.

The second is backups. Eleven dated copies from four days in September add up to 292 MB. That is a quarter of the whole footprint, from 16 agents, with no retention policy and nobody asking for it.

Scale either cost to a million databases a week and it stops being a rounding error.

## The counter-arguments are worth carrying

The rewrite drew real objections, not just applause. The thread ran to 202 points and 105 comments, with both Turso's CEO and cofounder replying.

arnath asked why anyone would rewrite software that is, in his words, "widely considered one of the best written and tested pieces of software in the world".

smt88 argued the real win from a Rust rewrite is fewer "serious security vulnerabilities and memory bugs", not more speed or stability.

The performance receipts were worse. Alexey Milovidov opened ClickBench issue #336, titled "Add Turso (it is unbelievably slow) (it also does not work)". A later pull request reads: "Turso - it is ridiculously slow, can't believe that".

Commenter f311a noted repeated benchmark attempts where, as he put it, "each time new bugs were found". Another, menaerus, reported a loader stuck at "4 kilobytes per second".

Turso cofounder penberg answered in-thread. "It's all in the ingestion before the benchmark," he wrote. "We do intend to improve it but not the highest priority right now".

CEO glommer handled the acquisition question himself. "We were doing fine," he said. "This is a strategic acquisition". He also said Turso "grew revenue > 5x this year", and is fully MIT.

That is the honest version. The engine has rough edges, and the control plane is the asset.

## What I would actually do

At 16 agents, I can clean this up by hand:

1. Checkpoint the write-ahead logs, so the 60 MB folds back into the main files.
2. Set a retention policy and delete the September backups.
3. Keep idle profiles' databases off the hot path.

At a million databases a week, none of that is manual. The checkpointing, backup and retention machinery is the product, and it is exactly what Supabase is buying.

The model is right. A database per agent is a good shape.

Just do not price it by the create.