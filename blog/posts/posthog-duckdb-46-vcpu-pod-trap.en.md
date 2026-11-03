---
title: The 46-vCPU Pod Trap: What PostHog Learned by Leaving DuckDB
slug: posthog-duckdb-46-vcpu-pod-trap
date: 2026-11-03
excerpt: PostHog ran DuckDB as a multi-tenant warehouse for five months, then scrapped it. The lesson is about where a single-node engine stops being a bargain.
tags: duckdb, architecture, databases, posthog, devops
---

On November 2, 2026, PostHog published "Why we're moving our warehouse off DuckDB". Five months earlier, on June 29, 2026, they published the post explaining why they had moved onto it. Same team, same petabytes, opposite conclusion.

I read both posts and the Hacker News thread that followed. My read is that this was never a DuckDB failure. It's a boundary failure.

PostHog took an embedded, in-process analytical engine designed to own one machine and sold it as a hosted multi-tenant warehouse at 2 PB. The engine did exactly what it promises. The wiring around it did not.

## DuckDB is not the villain here

Their own post says it plainly: DuckDB is probably the best single-node tool for analysing a heap of data, and that node can be your laptop. I agree, and I run it that way over Parquet files sitting on local NVMe. The properties that make it excellent locally are the same ones that break inside a cloud product:

- No network hop between the query engine and the bytes it scans.
- One process owning one memory budget, so spilling to disk stays a local decision.
- A single tenant whose query pattern you can actually reason about.

All three are properties of the machine holding the data, not of the database engine. You cannot buy them separately from the hardware.

## You pay for the query before you can see it

The numbers that matter came from the author in the comments, not from the blog post. Most customer pods ran 46 vCPUs and 360 GB of RAM on Elastic Kubernetes Service (EKS), and customers still asked for more.

That is one tenant on one very large node. A distributed engine sizes itself after the query arrives: Trino and Snowflake parse it, split it into stages, then hand each stage as many workers as it needs. The expensive machine exists only while the query runs. A single-node engine has to be sized before the query, so you provision for the worst query you might receive and hope the next one is smaller.

The author's illustration ends the argument. One query running for 12 hours, then another 10 hours of work from the same customer arriving behind it. Two long queries and your 46-vCPU pod is an expensive queue nobody else can use.

## The catalog that re-read itself on every commit

DuckLake is a more interesting failure than DuckDB, because it's a design tradeoff rather than a bug. Its catalog schema has to stay portable across many SQL databases, which caps any engine-specific optimization. At PostHog's scale, a single-table write could take more than three minutes, because every commit re-read statistics for the entire catalog.

Over 99% of those statistics rows belonged to tables that no longer existed. Pruning them made writes 30 to 50 times faster. The rows kept growing back anyway.

The dogfood dataset at the point they gave up: about 2 PB, roughly 1 trillion rows, and 15.3 million snapshots. Their fixes lived in a fork of DuckLake, which is where the compatibility argument quietly eats itself. A format built for portability forced patches nobody else could receive.

## Port 5432 is a promise, not a protocol

The best part of the June pitch was that your tools already speak Postgres. Point dbt, Metabase or psql at port 5432 and it works. Everything pleasant about that offer is also what makes it expensive to operate.

- Connections are stateful, so an L4 network load balancer (NLB) forwards raw TCP to one specific pod.
- An L7 load balancer (ALB) can instead route on HTTP headers and check health per request.
- Idle connections and TTLs turn into per-tenant accounting as the fleet grows.
- Every Postgres client expects slightly different behaviour, and that long tail never closes.

PostHog ended up on NLBs because stateful pgwire leaves little choice. That single decision removes header routing, per-request health checks and connection draining. Those are the mechanics that make ephemeral pods behind a load balancer feel boring.

## Then they rebuilt the format. That's the part I'd question

PostHog's replacement is their own flavour of Trino plus a new open table format called HogLake. That's three architectures in six months for the same product surface, and the HN thread was merciless about it.

Worth stating clearly, since the thread kept missing it and the author had to correct people: PostHog did not leave ClickHouse. ClickHouse still runs the product analytics. Only the customer warehouse moved, first to DuckDB and now to Trino.

In the comments they note they tried Apache Iceberg and found writes too slow. I believe the measurement. I don't think it settles the diagnosis, because a slow write path is precisely the symptom that gets a format replaced instead of profiled.

## The rule I actually apply

An embedded engine belongs in production when the execution boundary and the hardware boundary are the same thing. SQLite for transactional workloads, DuckDB for analytical ones: both are superb when the process, the data and the disk are one machine and one tenant owns all three.

Dagango.com runs a multi-tenant monorepo on Linux VPS and bare metal. Every request arrives at an L7 boundary over HTTP, stateless, with the tenant resolved from the request. The tenant is a row and a policy, not a container pretending to be a machine. Where we do need hard isolation, we isolate at the process boundary with a known memory ceiling.

Before putting an embedded engine behind a hosted API, these are the questions I'd answer in writing:

1. Does the tenant send the query, or does my own code generate it?
2. Can I resize between queries, or only before them?
3. What does one customer's worst query cost every other tenant?
4. If I hand out a wire protocol, will it survive an L7 proxy?
5. Where is the memory ceiling enforced, and does it fail closed?

## What actually broke

PostHog's retrospective is one of the more honest pieces of engineering writing published this year. They named the pods, the write latency and the client tail instead of blaming a benchmark.

The lesson is narrower than "DuckDB can't scale" and more useful. Per-tenant instances sound like multi-tenancy and are not. The bill for that confusion arrives later, as a pod spec that says 46 vCPUs and 360 GB, for one customer, running one query.
