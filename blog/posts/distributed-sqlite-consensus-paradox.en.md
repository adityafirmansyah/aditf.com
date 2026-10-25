---
title: The Distributed SQLite Paradox: You Pay for Consensus, Then Queue Behind One Writer
slug: distributed-sqlite-consensus-paradox
date: 2026-10-25
excerpt: Raft-replicated SQLite buys you failover and charges you milliseconds per write. Most production apps need WAL streaming to S3, not a cluster.
tags: sqlite, distributed-systems, databases, devops, architecture
---

Philip O'Toole published a twelve-year retrospective on rqlite on October 23. It is the cleanest map of distributed SQLite anyone has written, and I think it quietly argues against the way most teams buy the category.

My position, up front: for the majority of production applications, a consensus-replicated SQLite cluster is the wrong purchase.

Here is the arithmetic.

Every write goes through a leader, crosses the network, and waits for a quorum of nodes to acknowledge it on disk. When that finishes, you still write through SQLite's single-writer lock. You traded microseconds for milliseconds and bought failover, which a backup file in object storage also gives you.

## Three corners, one question each

His chronology is tidy.

Consensus came first: rqlite in September 2014, Canonical's dqlite in 2017. Streaming came second, when Ben Johnson released Litestream in early 2021. Merge came third, with cr-sqlite adding CRDTs to the engine in 2022.

Each corner exists to answer one question.

- **Consensus (rqlite, dqlite):** what if the machine dies and I cannot wait to restore?
- **Streaming (Litestream, LiteFS):** what if the machine dies?
- **Merge (cr-sqlite):** what if two machines both accept writes while offline?

That list is the whole argument. Most of the Hacker News thread is people defending different answers to different questions, which is why nobody there converts anybody.

O'Toole's own framing is the sentence to memorize: "The first question is more common, the second is the one people have when they come to rqlite."

Read it twice. The common question does not need a cluster. The rare question does, and it is a question about restore time rather than scale.

## What consensus costs

A single-node SQLite database in WAL mode runs inside your process. No socket between your query and the page cache, no serialization layer, no membership protocol. HN commenter rapind benchmarked that in Rust: 193,000 writes per second, each write holding the lock for roughly 5 µs.

A Raft write cannot look like that. The leader appends the entry, ships it to a majority, waits for their disk acknowledgements, then applies it.

Every transaction pays a network round trip and at least one extra fsync over the single-node case. Microseconds become milliseconds.

Then the paradox lands.

After paying for replication, you are still writing through one writer. Consensus replicates a log; it does not make writers concurrent. SQLite serializes writes in every configuration, so contention appears in a cluster exactly as it appears on one box:

```
SQLITE_BUSY: database is locked
```

What changes is the retry cost. On one node, a busy timeout and a shorter transaction usually absorb the retry. Behind consensus, each retry also pays a round trip.

There is one more limit worth knowing before you move. gregsadetsky flagged it in the thread: rqlite does not officially support BEGIN/COMMIT, so interactive multi-statement transactions are off the table.

## The field reports

Clustered SQLite does not read like a success story in that thread.

- Commenter esafak runs dqlite in a small cluster and wants out, citing "Loads of '500 database locked' errors".
- Canonical issue #908, opened on 2026-09-28 and still open, is an assertion abort in the dqlite VFS after hours of locked-database retries.
- In that report the cluster lost its only voting member, and the abort took the node's control plane down with it.
- Commenter piterrro calls Cloudflare D1 unreliable next to raw Durable Objects, and unconscionable agrees.
- Commenter ruther4d adds that D1 databases cannot be created dynamically, which makes per-tenant isolation harder.

There is counter-evidence, and it is more instructive than the complaints. qaq runs rqlite in production and is happy with it.

What rqlite holds is a tenant and operator registry that app nodes pull down, so the load stays very light. When the control layer dies, the platform degrades to "no new tenants" instead of going dark.

That is the shape worth copying: the writes are small and failover has to be instant.

## The stack I would run on a VPS

For a multi-tenant commerce platform on a Linux VPS, my default is one SQLite database per tenant on local NVMe, with Litestream shipping the WAL to object storage. Queries and writes never leave the machine. Durability leaves on a timer.

A replica stanza looks like this:

```yaml
dbs:
  - path: /srv/app/tenants/acme/store.db
    replicas:
      - type: s3
        bucket: acme-wal
        path: tenants/acme
        retention: 720h
        sync-interval: 1s
```

Restore is one command:

```bash
litestream restore -o /srv/app/tenants/acme/store.db s3://acme-wal/tenants/acme
```

The database side needs three pragmas at open time.

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
```

What you give up is precise, so state it plainly. Your recovery point objective is the sync interval, which means one second of committed writes can vanish in a hard failure. Your recovery time objective is however long an object download and a process restart take.

If that arithmetic clears your requirements, you do not need consensus. The decision collapses into three cases.

1. A restore measured in tens of seconds is acceptable, so run single-node SQLite with Litestream.
2. Failover must be automatic and the write path touches money, so run rqlite and budget for millisecond writes.
3. Writes must land in several regions at once, so stop wrapping a file and move to Postgres or CockroachDB.

## Twelve years later

O'Toole closes with a line the category rarely repeats: the idea was open source for eight years before anyone sold it. Turso raised venture money on a fork of the engine and was acquired by Supabase in 2026. Cloudflare sells D1 as a managed product from a company that sees no obligation to explain the internals.

The lesson I take is narrower than "distributed wins". Ask what a dead node actually costs you: an hour of manual restore, or an outage you have to explain to a customer.

Most teams answer "an hour" and then buy the cluster anyway. The next year goes into lock timeouts sitting behind a consensus round trip, in a system whose only real requirement was a backup that works.
