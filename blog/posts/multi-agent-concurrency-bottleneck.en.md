---
title: The Multi-Agent Concurrency Bottleneck: Why Your Coding Fleet Locks Up
slug: multi-agent-concurrency-bottleneck
date: 2026-10-14
excerpt: Three coding agents on one repository stop failing on model quality. The failures become file locks, bound ports, and database races. Here is the isolation that fixes it.
tags: ai-agents, devops, software-engineering, architecture, git
---

## Your fleet does not stall on reasoning

One coding agent fails in ways that look like reasoning failures. So you rewrite the prompt. You add context. You try a bigger model.

Run four agents at once and the failure mode changes. Our review dispatch died at 05:35 with one line in the log: `duplicate session: main`. The model was fine. A session write guard saw an active turn in the session that dispatch wanted and refused to open it.

That is the shift nobody warns you about. Past one agent, your bottleneck stops being the model and becomes the operating system under it.

We run a fleet against Dagango.com, a Next.js frontend plus a FastAPI backend. Here are the four places it seized up, and the isolation layers that fixed each one.

## Bottleneck one: one session, one writer

Agent platforms like to route work into a single canonical chat session. That is fine for a chat. It is fatal for a fleet.

Every concurrent caller then contends for the same write guard. The guard has names you will learn quickly:

- `SessionActiveWriteGuardError`
- HTTP 409 on the turn
- `session_active_turn`
- `duplicate session: main`

The lock itself is correct behaviour. One session should have one writer. The mistake is putting many agents behind one session in the first place.

You do not fix this with retries. A retry loop against a held guard is a queue with extra steps.

The fix is one disposable session per dispatch, named so it cannot collide:

```bash
SESSION_ID="${PROFILE}-pr${PR_NUM}-$(date +%s)"
hermes -p "$PROFILE" chat -Q --oneshot \
  --session "$SESSION_ID" \
  --query-file "$BRIEF_FILE"
```

We learned the cost the loud way. A dead review dispatch looked like a slow one. It left a 1,114-byte findings file that stopped at its first section, and the pull request it was meant to gate ended up with zero reviews.

## Bottleneck two: ports are a shared namespace

Files can be isolated per agent. Sockets cannot.

Our QA runs bound hardcoded ports. One round used backend 8012 with frontend 3312. Another used 8003 and 3303. Both worked, because we ran them one at a time.

Start two at once and you get one of two outcomes. The second server dies with `EADDRINUSE`. Or worse, it binds nothing at all. It finds a server already listening and quietly tests the previous agent's build.

That second outcome is the dangerous one. It reports a green run against code nobody asked about.

Derive the port from the work item, so two agents cannot want the same number:

```bash
BACKEND_PORT=$((8100 + PR_NUM))
FRONTEND_PORT=$((3400 + PR_NUM))
```

The same trick appears in Playwright configs as `reuseExistingServer`. In a worktree fleet, that flag means "reuse whatever server happens to be up". Gate it on the per-worktree port, or turn it off.

## Bottleneck three: two runners, one database

Here is the failure that wastes the most debugging time, because it looks like a product bug.

Two QA runners start together. Both run migrations. Then both seed fixtures into one shared PostgreSQL instance.

The ordering is now nondeterministic. A test that passes at 10:00 fails at 10:05 with no code change, because the other runner truncated a table it was still using.

You can chase that for a day. It is not your code.

Give each run its own database, created before the agent starts and dropped after:

```bash
TEST_DB_NAME="<project>_test_${PR_NUM}"
createdb "$TEST_DB_NAME"
```

One caveat from our own setup: copying the environment file into a worktree gets you halfway. Point the connection string at the per-run database too, or the worktree quietly reconnects to the shared one.

## Bottleneck four: one repository, one index

This is the one that loses work, and it loses it silently.

Give two agents one working directory and they collide on every stateful git operation. The index file is a single resource. `git checkout` in one agent overwrites uncommitted edits in the other, and `reflog` is your only recovery.

The failure list is longer than the index lock:

- `git checkout` overwrites another agent's uncommitted edits.
- `git stash` piles up across agents, and someone pops the wrong entry.
- `npm ci` interleaves writes into `node_modules` and corrupts the tree.
- a parallel build mixes two agents' sources into one bundle.

`git worktree` is the structural answer. One repository keeps one object store. Each agent gets its own working directory, its own index and its own branch:

```bash
git worktree add --detach /home/aditf/e2e-verify/wt-pr105 fix/gate-checkout
```

Git enforces one useful rule for free. A branch can only be checked out in one worktree, so the filesystem itself stops two agents writing the same branch.

Two gotchas bite immediately:

- Untracked files like `.env` do not follow a new worktree, so copy them in during creation.
- Worktrees accumulate. Ours number 21 in `git worktree list`, holding 1.3 GB on disk, so prune on the way in.

## The isolation layer everybody forgets: the browser

Visual QA is the fifth layer, and it is the one that silently produces false evidence.

Two agents driving Chrome over CDP share the same cookie jar and local storage by default. They also share the active tab list. Agent B navigates, and agent A's assertions now run against agent B's page.

Give every run its own browser session:

```
browser_exec(session="pr-<PR_NUM>")
```

That is a one-line change with a real consequence. Without it, a passing accessibility check can be a check of your teammate's page.

## What the isolation adds up to

The architecture is not clever. It is five lines in one dispatch script:

- a disposable session ID per run,
- a port derived from the PR number,
- a database named after the PR number,
- a dedicated worktree per agent,
- an isolated browser session per run.

Each layer answers a different shared resource, and none of them overlap. Fix three and the fourth still fails, which is why partial isolation feels worse than none.

## What I would tell you before you scale

Start the isolation work before you add the fourth agent, not after. The first collision looks like a flaky test. You will spend a week blaming your own code.

Then accept the real tradeoff. Isolation costs you coordination. Someone still has to decide the merge order, and `WorktreeRemove` fires once per session rather than once per agent, so worktrees pile up until you sweep them.

We pay both costs. They are still cheaper than debugging a race that only appears when two agents are awake.
