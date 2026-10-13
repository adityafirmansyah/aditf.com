---
title: Codex's Auto-Started Daemon: What systemd Would Have Done Differently
slug: codex-daemon-vs-systemd-supervision
date: 2026-10-13
excerpt: Since 0.157.0, Codex CLI starts a persistent, self-updating background daemon on qualifying interactive sessions. Here is what that breaks, and what a supervised service would have done instead.
tags: agents, systemd, self-hosting, coding-agents, linux
---

## A daemon you did not start

On 2026-09-25 the 0.157.0 release notes gained one sentence:

> Enabled automatic background-server startup for eligible interactive sessions, with recovery choices when server settings are incompatible.

That is the entire disclosure. It names neither the persistent process, nor the 374 MB package copy, nor the updater that ships with it.

Issue #48195 was filed the same day. It reached the Hacker News front page just over two weeks later, with north of 500 points and 250-plus comments. The thread kept circling one question: who owns this process, and which copy of it is running?

Issue #48195 answers the first half. Since 0.157.0, opening a qualifying interactive session spawns `codex app-server --managed-daemon`.

It runs in its own session with no TTY. It gets reparented to PID 1. Close every Codex window and it keeps running, until you stop it explicitly or reboot.

My position, up front: a coding agent CLI should be a service I supervise, not a daemon that installs itself. That is not nostalgia for init scripts. It is the difference between one process I can name and one I have to hunt for.

## It copies itself out of your package manager's reach

The daemon does not run the binary your package manager just installed. It makes a copy first.

From the daemon's own README: `bootstrap` "copies the invoking package into `CODEX_HOME/packages/app-server-daemon` and prints an installation message without asking for confirmation". That copy is roughly 374 MB. It holds the `codex` binary, `codex-code-mode-host`, and bundled `bwrap`, `zsh` and `rg`. It lands under `~/.codex/packages/app-server-daemon/releases/<version>/`, byte-identical to the package npm installed seconds earlier.

Then the provenance break arrives. The binary you audited is no longer necessarily the binary running your turn. The version you pinned is no longer the version executing.

The sibling issues spell out the fallout:

- **#48050:** the Arch package stops launching at all without `--no-daemon`.
- **#46468:** an npm update leaves the app-server running the old version.
- **#41188:** there is no supported way to point the daemon at an externally managed executable.
- **#42457:** hooks in `--remote` mode receive the daemon's working directory, not the session's.

Four separate reports, one root cause. The daemon owns its own copy, so the package manager no longer owns anything.

## The updater and its 60-second patience

A detached process called `codex app-server daemon pid-update-loop` checks for updates five minutes after start, then hourly. You did not schedule it. The first session you opened did.

Issue #40969 documents what that costs on a long-lived daemon. The app-server implements a correct graceful drain, and it waits for running turns to finish. The daemon grants that drain 60 seconds before sending `SIGKILL`.

The reporter was running 13 long-lived threads where a Go build and test turn takes 3 to 30 minutes. Every auto-update destroyed in-flight work.

The README now exposes two `settings.json` keys:

```json
{
  "shutdownGraceSeconds": 60,
  "updater": { "autoUpdateEnabled": false }
}
```

So the 60 seconds is a documented constant now, not an accident. It is still 60 seconds against a 30-minute build. At the time of that report, there was no supported way to disable auto-update at all.

## Stopping it does not stop it

The clearest sign that this is a supervision bug rather than a taste question is what happens when you turn it off. The issue author found a second bug while escaping.

`codex app-server daemon stop` stops the app-server, and leaves the updater running. The `pid-update-loop` was still alive 70 seconds later and needed a manual `pkill`. This is his shutdown chain:

```sh
codex features disable daemon_auto_start
codex app-server daemon stop
pkill -f 'app-server daemon pid-update-loop'
rm -rf ~/.codex/packages/app-server-daemon
```

Four commands. One of them is a `pkill` against a process the tool never admitted it started. A service manager that leaks half of itself on stop is broken at the one job service managers exist to do.

## The environment of whoever started first

Yesterday's thread kept asking which copy of the daemon was running. Today a new report answered a worse question: whose credentials are inside it?

Issue #53547 was filed at 2026-10-13T04:00:03Z against codex-cli 0.162.1 on macOS, under ten hours after the Hacker News thread went up. The reproduction is three commands. Export a marker variable in one directory, start Codex with the daemon enabled, then ask an unrelated session in another directory what it can see. It sees the marker.

The README already concedes the mechanism: "Shared clients use the environment inherited when the daemon started. Opening a new terminal or clearing variables there does not clear the running daemon's environment; per-client environment isolation is not provided."

Read that as an agent operator and the failure class is obvious. `HTTPS_PROXY`, `AWS_PROFILE`, `NODE_EXTRA_CA_CERTS` and every project-scoped token in your shell belong to whichever session started the daemon first. The #48195 reporter launched Codex through a wrapper that set a per-invocation proxy. The daemon kept the first session's proxy and routed every later session's traffic through it.

That is credential and proxy bleed across workstreams you believed were separate. The #53547 reporter calls it "somewhere between a bug and a security issue". I would drop the hedge.

## What systemd --user already provides

Everything the daemon improvises has been a solved problem in user services for years. I run 17 agent profiles plus a default on one box, and there the question was settled long ago by a single multiplexed service. The load-bearing lines:

```
[Service]
Type=simple
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=70
```

Map those across and the daemon reads as a reimplementation with the missing cases left in:

- `Restart=always` with `RestartSec=5` replaces a self-installing updater.
- `KillMode=mixed` gives the SIGTERM-then-SIGKILL ladder deliberately, main process first.
- `TimeoutStopSec=70` makes the drain budget an explicit, reviewable line in a file I own.
- cgroup memory accounting replaces a hopeful `ps`.
- `journalctl` replaces a daemon-private log directory.

Concretely, on the box I am writing this on, `systemctl --user show hermes-gateway.service` answers in one command what the Codex daemon makes you dig for:

- `MemoryCurrent` around 5.9 GiB and `MemoryPeak` at 8.6 GiB, on a 15 GiB four-core Celeron J4105.
- `TasksCurrent` hovering near 100.
- `NRestarts=2`, with `MainPID=802421` up since 2026-10-12 09:19:59.
- `MemoryAccounting=yes`.

One owner. One lifecycle. One place to read memory, restart counts and logs.

## The bill, priced before adoption

A 374 MB copy per install is cheap in isolation. It stops being cheap when you multiply it.

- 17 profiles times 374 MB works out to 6.21 GiB.
- Free space on this volume: 17 GiB of 115 GiB, at 86% used.

That is not a hypothetical for me. It is a third of the disk I have left, spent on copies of a binary I already own.

Packaging has already voted. nixpkgs ships a patch that flips the feature registry entry from `default_enabled: true` to `default_enabled: false`, and the package wiring cites issue #48195 in a comment right above it.

The documentation is the last to know. The official config reference documents the CLI's own `check_for_update_on_startup` and carries zero rows for `daemon_auto_start`. Meanwhile the daemon module's README still opens by calling itself "experimental", while shipping enabled by default.

## What I would pick

The defensible setup is boring, and it is the same shape as everything else I care about on that box:

- Pass the documented foreground or `--no-daemon` flag, or disable the feature and run your own unit.
- Own the `ExecStart` line, so the binary is the one you installed.
- Let the supervisor own restarts, the drain budget and the SIGKILL ladder.
- Read memory and logs from the cgroup and the journal.

If a tool will not let itself be supervised and pinned, that is now a shipping criterion for me. An hourly timer is not a provenance record, and whichever session happened to open first is not an owner.
