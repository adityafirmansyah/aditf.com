---
title: Why Your Postgres LIKE Query Silently Seq Scans (And the One-Line Fix)
slug: postgres-like-queries-seq-scan-fix
date: 2026-09-25
excerpt: On a default en_US.UTF-8 Postgres, a UNIQUE (tenant_id, slug) index cannot serve LIKE 'prefix%' queries. Here are the benchmark numbers at 20,000 rows and the varchar_pattern_ops index that fixes it.
tags: postgresql, database, backend, performance, optimization, sql
---

You created a `UNIQUE (tenant_id, slug)` index and assumed `WHERE slug LIKE 'kaos%'` would use it. On a stock Ubuntu Postgres, you assumed wrong.

Here is the trap. Your query is fast in dev. Your SQLite-backed unit tests pass in microseconds. Then the production catalog crosses ten thousand rows, and every slug lookup quietly becomes a full table scan.

I hit this when building readable product slugs for a multi-tenant e-commerce platform. The collision check ran a prefix query, and it looked instant locally. On a real Postgres 18.6 database with 20,000 products for one tenant, it did this instead:

```
Seq Scan on products
  Filter: tenant_id = 1 AND slug ~~ 'kaos%'
  Rows Removed by Filter: 22000
  Buffers: shared hit=256
  Execution Time: 4.52 ms
```

Every row, every request. The index existed. Postgres simply refused to use it.

## The Index Was Never Eligible

The reason is collation, and it is not a Postgres bug.

A standard B-tree index on a `text` or `varchar` column is built using the database's collation. On most Linux distributions the default is `en_US.UTF-8`, a linguistic collation. It sorts by language rules, not by raw bytes.

`LIKE`, meanwhile, is strictly byte-based matching. Postgres cannot use an index whose ordering is linguistic to answer a question about byte ranges, so it falls back to a full scan.

- In linguistic collation, case and accented characters interleave by cultural convention, so byte order and index order diverge.
- `LIKE 'prefix%'` needs a contiguous byte range to work as an index scan.
- Once the index order is not byte order, no range guarantee exists, and the planner gives up on the index.

The fix is to give Postgres a byte-ordered index for that column specifically. You are telling it: for this column, sort by raw bytes, so prefix ranges line up.

## The Fix Is One Line

Postgres ships an operator class built for exactly this: `varchar_pattern_ops`.

```sql
CREATE INDEX idx_products_tenant_slug_prefix
  ON products (tenant_id, slug varchar_pattern_ops);
```

This is not a replacement for your unique constraint. It is an additional index, and the plan changes immediately:

```
Index Only Scan using idx_products_tenant_slug_prefix on products
  Index Cond: (tenant_id = 1 AND slug ~>=~ 'kaos' AND slug ~<~ 'kaot')
  Heap Fetches: 0
  Buffers: shared hit=3
  Execution Time: 0.39 ms
```

Watch what the planner did to your `LIKE`. It rewrote it as a range comparison, `slug ~>=~ 'kaos' AND slug ~<~ 'kaot'`, where `~>=~` and `~<~` are the byte-ordering operators `pattern_ops` owns. The scan touches three buffers, not 256.

Against the Seq Scan above, that is an **11.6x speedup**, and it is flat. The old query got more expensive as the table grew. This one stays O(log N), no matter how many products a tenant adds.

## Why Your Tests Never Caught This

Two reasons, and both hide the bug until production.

The first is scale. A Seq Scan over 50 rows finishes in roughly 0.05 ms. That is not slow. It only gets slow once the table is large, so a small dev database will never show you the problem.

The second is SQLite. If your FastAPI or SQLAlchemy suite runs against in-memory SQLite, you are not testing Postgres index behaviour at all. SQLite has no locale-dependent B-tree operator classes, so the same query that Seq Scans on Postgres runs fine there.

Your test suite was green. Your staging database was empty. The bug shipped, and nobody saw it until the catalog was big enough to hurt.

The lesson is not that Postgres is slow. It is that an index on the column you query is not the same as an index that can answer your query. Collation decides whether those two things match.

## Two Edge Cases That Bite Later

**You still need both indexes.** A `varchar_pattern_ops` index cannot enforce uniqueness under linguistic collation, and a standard B-tree cannot do prefix matching. The jobs are different:

- `UNIQUE (tenant_id, slug)` protects data integrity.
- `varchar_pattern_ops` makes prefix lookups fast.

Keep both if you need both guarantees. Under a non-C collation, no single index does both jobs.

**Capped slugs break naive prefixes.** If you cap slugs at 70 characters, you might back off to the last hyphen so you do not cut a word. That means a `-2` candidate is not always a strict prefix of the base. Query against a stable stem instead:

```sql
SELECT slug FROM products
WHERE tenant_id = :t AND slug LIKE :stem || '%'
```

Use `base[:62]` as the stem, not the full capped base. Otherwise your collision check misses candidates it should catch, and you ship a duplicate.

## What To Do This Week

Check whether any `LIKE 'prefix%'` query on a text column has a matching `pattern_ops` index. On a default `en_US.UTF-8` database, it probably does not.

You can list the indexes on your slug column and confirm the operator class in use:

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'products';
```

If your unique composite index shows up without `varchar_pattern_ops`, your prefix query is not using it. Add the operator-class index alongside it, then run `EXPLAIN (ANALYZE, BUFFERS)` before and after. The plan should move from a `Seq Scan` with a filter count that grows with your table, to an `Index Only Scan` with single-digit buffer reads.

One line, one index, and the scan disappears. The index you already had was never eligible in the first place.
