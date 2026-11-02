---
title: PostgreSQL 19 Is Late Because Finding Bugs Got Cheap
slug: postgres-19-verification-bottleneck
date: 2026-11-02
excerpt: PostgreSQL 19 slid to November 19 and lost three features late in beta. The cause is not worse code. Naming a defect got cheap while verifying one stayed human work.
tags: postgresql, ai-engineering, software-reliability, open-source, database-internals
---

PostgreSQL 19 reaches general availability on November 19, 2026. For a project that has landed every major release between mid-September and mid-October for the past decade, that breaks the one piece of scheduling everyone had learned to trust.

Robert Haas, a PostgreSQL major contributor and committer, wrote up why on October 30. His answer is not that the developers started writing worse code. It is that a lot of people got much better at finding the mistakes those developers were already making.

## The window broke, and three features went with it

The pattern Haas describes is not folklore: no earlier than mid-September, no later than mid-October. PostgreSQL 19 RC 1 landed on October 15. RC 2 is due November 12, the same day as the quarterly update release, so that batch of fixes reaches the new major before it ships. General availability follows a week later.

Feature freeze happened on April 8, the way it does every year. Between August 27 and September 15 the project reverted three merged capabilities:

- UPDATE/DELETE ... FOR PORTION OF, the temporal-table syntax for editing a slice of history.
- SQL Property Graph Queries (SQL/PGQ), the new graph-query layer.
- ALTER TABLE ... MERGE PARTITION and SPLIT PARTITION.

Late reverts do happen in a beta cycle. Pulling three finished features a month before the first release candidate is a different kind of event.

## The commit counts, and the number hiding inside them

Haas compared commits across the same calendar window in both years, from feature freeze through September 25:

- 2025: 1,037 commits to master, 724 back-patched to REL_18_STABLE.
- 2026: 1,443 commits to master, 1,169 back-patched to REL_19_STABLE.
- The branch one release older: 248 commits to REL_17_STABLE in 2025, 433 to REL_18_STABLE in 2026.

Back-patching is what a project does when a defect turns out to affect versions already in production, not only the one under development. The stable-branch fix count rose 61.5%. The count for the older branch rose 74.6%.

Subtract the back-patches from the master totals and the interesting number appears: 313 commits of other work in 2025, 274 in 2026. Less new work landed, and a much larger share of what did land was repair.

Haas allows for the possibility that committers simply made more mistakes this year, then dismisses it. The people reviewing PostgreSQL patches were about as conservative in 2026 as in 2025. What changed is how quickly their mistakes got found.

## The reports are not spam

The comfortable explanation is AI noise: too many low-quality reports, maintainers buried under plausible nonsense. That reading does not survive contact with the reports themselves, at least not the ones posted in public.

HN user tibbar spent a summer on AI-assisted bug hunting in PostgreSQL. Most of what turned up never got reported:

> The list got so long that I had to triage what I even had time to report, and settled for a dozen or two out of hundreds of candidates.

What sat in the pile:

- serialization anomalies under SERIALIZABLE, including write skew where both transactions commit.
- foreign key integrity violations, one traced to a lock lost during toasting.
- planner bugs, such as partition pruning that drops a RANGE default partition.
- several candidates in CVE territory.

The write-skew report is the one I would hand to anyone who thinks this is noise. A Tid Range Scan, an access path added in PostgreSQL 14, lets two serializable transactions read the same range and both commit. The schedule is short:

```sql
-- both sessions: BEGIN ISOLATION LEVEL SERIALIZABLE;
SET enable_seqscan = off;
SELECT sum(v) FROM trs WHERE ctid >= '(0,0)' AND ctid <= '(0,100)';  -- 0
-- each session updates a different row, both COMMIT, final sum = 2
-- no serial order gives 2; both serial orders give 3
```

The control experiment on that reproducer is the interesting part. Set `enable_tidscan = off` in both sessions, which forces the same reads through a sequential scan, and the second commit fails with "could not serialize access due to read/write dependencies among transactions". Merely leaving `enable_seqscan` on is not enough, because the planner still prefers the Tid Range Scan for that qualifier. The reporter's own note is blunt: a control written that way is not a control.

That is the shape of the whole problem. The bug is real and the reproducer is real. Confirming it still took someone who understood the planner well enough to build a valid control.

Not everyone buys the framing. HN user ltbarcly3 reports finding a late-beta bug that crashed an entire cluster, back when LLMs did not exist. His read is that the project may be over-reacting to defects that could simply be patched.

That is a fair objection. Patch-versus-revert is a real engineering judgment.

## Naming a defect is cheap, verifying one is not

Haas puts the asymmetry dryly: those fixes still need review and commit by humans, and "those humans have not gotten any smarter between 2025 and 2026."

An LLM can read forty years of C and propose thousands of candidate defects in the time a committer reviews one. Discovery moved by orders of magnitude. Verification moved by roughly nothing.

The reason is what review actually checks. A PostgreSQL patch is not accepted because the tests pass. It is accepted because someone traced the lock ordering, walked the interaction with MVCC snapshots, and decided the fix is safe to apply to a stable branch that shipped years earlier.

An LLM-drafted patch that ignores coding standards is a nuisance at review time. One that quietly changes lock acquisition order is an outage six months later.

## The bill arrives as reverted features

Haas names the second-order effect. Review hours that would have gone into auditing the release went into back-branch fixes instead, so the project found its feature problems later and had less room to repair them. The revert is the symptom. The cause is a queue nobody staffed for.

For a project with a fixed set of committers that trade is arithmetic. Every hour spent deciding whether a reported bug is real is an hour not spent on the release. When incoming volume rises faster than review capacity, something has to give. The thing that gives first is the newest code, because it has the fewest years of people staring at it.

## What I would change

I run PostgreSQL for Dagango.com on bare-metal Linux, and I also run a fleet of agents that open changes and file QA findings against my own code. The lesson transferred in about a week. The expensive part was never generating the change. It was deciding whether to believe it.

Four things I would put in place before pointing an agent fleet at a codebase where bugs matter:

- **Budget the review, not the generation.** Track human hours per accepted fix as a headline metric. If that number climbs while agent pull requests climb faster, throughput did not improve.
- **Make "is this real?" cheap.** A harness that spins the exact version in a container turns a reported defect into a verdict in minutes.
- **Tier by blast radius.** Data loss and serialization violations jump the queue. Style findings wait for a batch.
- **Keep the confirmed regressions.** Every verified bug becomes a test, and that corpus is the only asset that makes the next thousand reports cheaper to triage.

## The narrowest stage sets the throughput

PostgreSQL will most likely answer this with process and tooling: more triage help, automated runs of every submitted reproducer, and probably a hard conversation about what a maintainer is expected to absorb per week. Whatever they land on will be verification infrastructure.

The general form is worth carrying into any team running agents. An AI fleet multiplies the number of changes and findings that reach a human. It does not multiply the number of humans. Throughput is still set by the narrowest stage, and in most organisations that stage has a name and a calendar.

Haas closes his post saying he and others are working hard on the answer. Anyone running an agent fleet should be working on the same question, because a found bug is now nearly free and a trusted fix is not.
