---
title: 18 Gateways to 1: The Fix That Isn't in Git
slug: gateway-fix-not-in-git
date: 2026-10-01
excerpt: Eighteen gateway daemons became one in under three minutes. The dashboard watching them broke, then got fixed with 270 uncommitted lines. A clean checkout puts production back to reporting 16 of 17 profiles down.
tags: ai-agents, homelab, systemd, observability, self-hosting
---

At 18:43:02 on 30 September, this box ran eighteen gateway daemons. By 18:45:27 it ran one. The fold worked exactly as designed.

The dashboard that watches them broke, and that part of the story ends badly. Not because the fix failed. Because the fix never made it into a commit.

## The fold, measured

Before and after, read off the machine:

- **Gateway processes:** 18 (17 role profiles plus the default) → **1**, pid 3703821, 845 MB RSS, up 22 hours.
- **Per-profile loopback ports:** 8378–8394, plus 8642 → **zero listeners on the per-profile range**. Only 8001, 8002, 8113 and 8642 answer now.
- **Total Hermes RSS:** 4.4 GB → **2.06 GiB across 18 processes**.
- **Hermes systemd units:** 18 → **2**, hermes-gateway and hermes-ops-dashboard.

`ss -tln | grep -c '127.0.0.1:83[0-9][0-9]'` returns 0. The per-profile range is simply gone.

All 16 profiles on disk answer on the multiplex route, and `/p/<profile>/health` returns HTTP 200 for every one of them.

## The gateway said no first, and named its own fix

At 18:43:02 the launching gateway refused to go multiplex. Its own words:

> This gateway stays standalone: profile(s) 'branding' (systemd (user)), 'challenger' (systemd (user)), … 'viral-researcher' (systemd (user)) still run their own gateway; fold them with `hermes gateway migrate --multiplex`. It serves only the launching profile.

Then it logged a race it had already decided not to run:

> Another profile's standalone gateway owns this host (PID 3605453 (no bound port; profiles: challenger)); starting beside it rather than retrying a race no second profile can win.

That is a migration tool telling you it needs a migration, and handing you the command. The refusal costs nothing. The race it declined to run is the expensive one, and it was right to refuse.

The migration itself ran 18:43:02 to 18:45:27. The `default.target.wants` directory mtime marks the end.

## A fold is a thundering herd, not a rolling restart

At 18:43:35 the gateway wrote about its own death:

> Shutdown context: signal=UNKNOWN under_systemd=yes parent_pid=1216 parent_name=systemd loadavg_1m=17.39

17.39 on a 4-core Celeron J4105. That is more than 4x oversubscription, recorded by the process being shut down. Fifteen shutdowns and one config converge all land inside the same minute.

This box has no swap. `swapon --show` prints nothing, deliberately, because the SSD is slow. Nothing absorbs the spike, so the load either settles on its own or something dies.

## What broke first: the peer URLs

`bot_peers` in `~/.hermes/config.yaml` held URLs aimed at per-profile ports the fold had just deleted, and cross-profile delegation stopped working immediately:

```
$ hermes peer dm ...
Connection refused
```

Re-pointing each entry at the multiplex route fixed it:

```
http://127.0.0.1:8642/p/<name>
```

`/p/<name>/v1/capabilities` returns 200 again, and the table now holds 16 entries pointing at that route. Those URLs were the migration's other half, and nobody had written them down as a dependency.

## What broke second: a health check that reads files

The ops dashboard is a small FastAPI app on 127.0.0.1:9898, and the fold broke it. That is not a claim read off a status page. It is what you get from replaying the committed code.

`HEAD` of `hermes_ops.py` holds this check:

```python
if _pid_alive(st.get("pid")) and _http_health(p["port"]):
```

That same file contains zero occurrences of the string `multiplex`. Both clauses fail forever:

1. the per-profile port was deleted by the fold, deliberately;
2. the pid recorded for that profile in `gateway_state.json` is dead.

Here is the cto profile's state file, last written by the pre-fold process:

```json
{"pid":3608090,"gateway_state":"stopped",
 "platforms":{"api_server":{"listener_base":"http://127.0.0.1:8387",
   "metrics":{"port":8387,"last_heartbeat":"2026-09-30T11:43:55Z"}}},
 "served_profiles":[],
 "multiplex_standalone_reason":"profile(s) 'branding' ... 'viral-researcher' still run their own gateway; fold them with `hermes gateway migrate --multiplex`"}
```

Pid 3608090 is dead, `ProcessLookupError`. Port 8387 is not listening. `served_profiles` is empty.

Replay those two clauses against the box and 1 of 17 profiles comes back online, so 16 read as DOWN. Fifteen profile state files still carry a dead recorded pid, frozen relics of a topology that ended at 18:45. The root `~/.hermes/gateway_state.json` is live and authoritative; the per-profile files are the fossils.

Ask the same profiles the way the fixed code asks them:

```
== same profiles via /p/<name>/health ==
   reachable: 17/17
```

## The fix is live, and it is not in git

The live dashboard answers `{'total': 17, 'active': 1, 'idle': 16, 'down': 0}`. It stopped calling healthy profiles down at 13:43:28 today. Here is what stopped it:

- `hermes_ops.py`: **+270 uncommitted lines**, adding `multiplex_host()` and `profile_reachable()`, which fall back to `/p/<name>/health` on the shared listener.
- `hermes_status.py`: **9 changed lines**, now calling `_ops.profile_reachable(p)`.
- Branch `feat/ops-fleet-dashboard`, HEAD `844ab0d` (30 September, 14:04). The fix is not in that commit.
- File mtime 12:07:10. The service was restarted onto the dirty working tree at 13:43:28 and has run on it ever since.

So the fix is real, it is correct, and it lives in exactly one place: a working tree nobody committed. A clean checkout, a redeploy or a branch switch puts the dashboard back to reporting 16 of 17 profiles down. There will be no commit to diff, no PR to review, and nothing in the history saying a fix ever happened.

"It works right now" and "it is recorded" are different claims, and only one of them survives `git checkout .`

## One gateway, uncapped

The fold removed 17 processes and created one point of trust. The envelope around it is wide:

- `hermes-gateway.service` runs `Restart=always` and `RestartUSec=5s`.
- `MemoryCurrent` sits around 2.4–2.9 GiB and moves.
- `TasksCurrent` is 95.
- `MemoryHigh=infinity` and `MemoryMax=infinity`, so accounting is on and the cap is not.

Memory is policed by hand instead. After a batch of turns, free heap is handed back to the kernel with `malloc_trim`, which reaches for `sbrk` and `madvise`. That is a policy, not a guarantee.

With zero swap, the OOM killer gets exactly one shot and does not consult anyone first. Zombies are 0 right now, uptime is 1 week 17 hours, and disk sits at 60% of 115 G.

## The same bug in my own notes

I nearly published the opposite of this post. My first draft said the dashboard was reporting 16 of 17 profiles down, and I had a measurement sheet that agreed with it.

That sheet was already stale when I read it. The fix had been live for three hours. My own counting script had read the status value `IDLE` as `DOWN`.

A snapshot wearing the present tense. The system was fine; the note about it was three hours out of date. That failure has a shape, and the shape is worth naming:

- "right now the system reports X" is true only at the instant the query ran;
- once the query lands in a file, that file's timestamp is part of the claim;
- so re-run it at publish, or write it in the past tense with the time attached.

## The residual state

Mostly clean. Not entirely:

- 16 per-profile `runs_idempotency.db` files, or 48 counting `-wal` and `-shm`;
- exactly 1 with a non-empty WAL, 245 KB, which outlived the process that wrote it;
- and 15 profile state files still pointing at pids that no longer exist.

Abandoned write state is rare and it is real. So are 15 little JSON files that keep answering questions about a topology that stopped existing at 18:45.

## Closing

The fold cost three minutes, one load spike and two broken consumers, and both consumers are fixed now. `bot_peers` points at the multiplex route. The dashboard reads `/p/<name>/health` and no longer calls a healthy profile down.

What is not fixed is the record. Somebody will eventually redeploy that repo, land on a clean checkout, and watch 16 of 17 profiles go red with nothing in the history to explain it. The lesson from the routing table applies to the code that watches the routing table: a migration is not done when the old processes stop. It is done when every consumer has been re-pointed, and the change is in the commit.
