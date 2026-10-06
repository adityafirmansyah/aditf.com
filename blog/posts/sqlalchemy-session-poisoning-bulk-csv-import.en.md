---
title: The SQLAlchemy Session Poisoning Trap in Bulk CSV Import
slug: sqlalchemy-session-poisoning-bulk-csv-import
date: 2026-10-06
excerpt: One failed row in a bulk import can poison a shared SQLAlchemy session and kill the next 497. Here is the real session-lifecycle fix, with numbers from PostgreSQL 18.6.
tags: python, sqlalchemy, postgresql, backend, architecture
---

## A failed row should not fail its siblings

Row 3 of a 500-row CSV import trips a unique constraint. The insert raises, you log it, and you move on to row 4. Row 4 comes back with a session error, and so does row 5.

So does every row after it. Your "partial success" importer is now a total failure, and the database holds two products instead of 497.

That is the trap, and it does not require Celery, Redis, or a background worker queue to escape. It is a transaction-lifecycle bug, and the fix is smaller than the incident it causes.

We hit it while building the bulk CSV product import for Dagango.com, a Next.js/FastAPI e-commerce platform. Rather than reach for an async queue, we ran a spike against real PostgreSQL 18.6 to test whether synchronous batching with proper session recovery holds up. It does.

## Postgres aborts the transaction, not the statement

Inside a transaction block, an error on one statement does more than fail that statement. PostgreSQL marks the whole transaction aborted. Every later command gets this:

```
25P02: current transaction is aborted, commands ignored until end of transaction block
```

Class 25 is `invalid_transaction_state`, and `25P02` is `in_failed_sql_transaction`. This is documented Postgres behavior, not a flag you can turn off. The error is at the transaction level, not the statement level, which is exactly why a per-statement `try` block cannot save you.

The exception you see next depends on how you talk to the database, and this detail matters:

- **Raw `Session.execute()` loop:** the next statement raises `sqlalchemy.exc.InternalError` with sqlstate `25P02`, wrapping `psycopg.errors.InFailedSqlTransaction`.
- **ORM `add` + `commit` loop:** the next `commit()` raises `sqlalchemy.exc.PendingRollbackError`.

Both are the same underlying problem: you have not rolled back yet. Neither is an `IntegrityError`, so an `except IntegrityError: continue` never catches them, and the import dies on row 4.

## rollback() is the whole recovery

The fix is one line. It is only one line:

```python
db.rollback()
```

That is the load-bearing call, and it does both jobs. It un-aborts the Postgres transaction, and it discards the pending object graph. In SQLAlchemy 2.0, `Session.rollback()` runs `SessionTransaction._restore_snapshot`, which expunges the session's new states and marks them transient:

```python
to_expunge = set(self._new).union(self.session._new)
self.session._expunge_states(to_expunge, to_transient=True)
```

So the failed product, its images, and its variants leave the session with the rollback. There is no half-pending ghost left to re-attach on the next insert.

This is where a lot of advice, including a comment sitting in our own code, gets it wrong. The common move is to follow `rollback()` with `db.expunge_all()`, on the theory that rollback alone leaves stale objects behind. On SQLAlchemy 2.0 that theory is false.

We confirmed the recovery matrix on the real stack. This is the next row's fate under each recovery:

- `rollback()` only → **OK**.
- `expunge_all()` only → FAILS (`PendingRollbackError`).
- `rollback()` + `expunge_all()` → OK.
- Neither → FAILS (`PendingRollbackError`).

Two things fall out of that:

- `expunge_all()` alone does not even un-abort the transaction, so it fails by itself.
- Once you have rolled back, adding `expunge_all()` changes nothing.

It is explicit, defensive surplus. Keep it if you like the belt-and-braces, but it is not the fix, and skipping it will not poison your next row.

After the rollback the session is verifiably clean, and those are the numbers the spike checks:

- `is_active=True`
- `in_transaction=False`
- `new`, `dirty`, `deleted` all zero
- `identity_map` zero

That is the precondition for row 4 to succeed.

## What 500 rows actually cost on Postgres 18.6

We ran the real importer loop against real PostgreSQL 18.6 in a scratch schema, with realistic multi-relational rows: products, variant combinations, image URLs. Then we dropped the schema. The recovery used was a bare `rollback()`. Six of six scenarios passed.

The failure cases used a genuine unique-constraint violation from Postgres, not a simulated one:

- 1 failing row out of 10 → exactly 9 products created
- 2 failing rows in one run → exactly 8 products created
- zero orphan images or variants in either case

Each surviving product carried its own row's images and variant combo. A deliberate steelman, a partial flush where the parent product INSERT succeeds and a child fails on a check constraint, also left `identity_map` at zero. The horror story you may have heard, where row 8 quietly inherits row 3's children, did not reproduce in any configuration we tested.

Then the throughput number that settles the architecture question:

- 500 rows committed synchronously in roughly 5 seconds
- min ≈ 8 ms/row, p50 ≈ 10 ms, p95 in the low tens of ms
- 500/500 committed, 0 errors

Five seconds of synchronous work sits comfortably inside a normal HTTP request timeout. The import cap is a deliberate 500 data rows and a 2 MiB body, refused before any row is written. That is a few seconds of work, not a timeout risk.

## The slug collision that does not fail

We assumed duplicate titles in a CSV would blow up on the unique slug constraint. The spike corrected us.

`slugify.unique_slug` re-reads the tenant's taken slugs on every attempt and appends `-2`, `-3`, `-4`, with no bound. A duplicate title is a second product with a numbered slug, not an error.

`SlugAllocationFailed` is a concurrency outcome. To exhaust the three allocation attempts, the tenant's slug set has to change between the read and the INSERT, the concurrent-create race. So the report shows the operator the slug actually allocated, including a `-2` suffix, instead of failing a row that was fine.

## The upstream leak worth naming

One limitation we did not paper over: the creator's retry wraps an unqualified `except IntegrityError`. It is not filtered by constraint. Any integrity failure on that INSERT, a foreign key, a NOT NULL, a different unique constraint, gets retried three times and then surfaces as `SlugAllocationFailed`.

The importer reports that code verbatim and claims no more than the creator knows. Narrowing it belongs to `create_product`, not to the import unit, so we named it instead of hiding it.

## The takeaway

Here is the part worth taking to your own importer. The recovery is not exotic, and it is not two lines. It is `db.rollback()`, once per failed row, and SQLAlchemy 2.0 does the graph cleanup for you inside that call. Measure your row cost before you reach for a background queue, because a five-second synchronous import with a hard row ceiling is a smaller thing to own than a worker fleet.

The session's own state is the only thing you have to get right.
