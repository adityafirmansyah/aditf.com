---
title: Agent Sandboxes That Fail Open: systemd --user Silently Skips Containment
slug: systemd-user-sandbox-fails-open
date: 2026-10-15
excerpt: Configure ProtectHome=yes, ProtectSystem=strict and IPAddressDeny=any on a systemd --user unit and systemctl show reports them all as active. On modern Ubuntu they fail open and enforce nothing.
tags: systemd, agent-safety, sandboxing, apparmor, self-hosting
---

## The sandbox you were told to configure

If you run autonomous coding agents, or any unprivileged daemon, as a `systemd --user` unit, the standard hardening advice is containment.

Set `ProtectHome=yes` and `ProtectSystem=strict` so the process cannot read your keys. Add `IPAddressDeny=any` so it cannot phone home with them. Then `systemctl --user show` reports every one of those directives as active.

On a modern Ubuntu host, they do nothing at all.

I found this the honest way. I run eighteen agent profiles behind a single multiplexed `hermes-gateway.service`. I tried to add the sandbox, and then I measured what actually enforced. Every filesystem and egress directive an unprivileged unit can set was accepted, printed by `systemctl show` as applied, and inert.

## What the unit that runs the fleet actually says

`systemctl --user show hermes-gateway.service` resolves every containment knob to its off value:

```
NoNewPrivileges=no    PrivateTmp=no
ProtectSystem=no      ProtectHome=no
IPAddressDeny=        RestrictAddressFamilies=~
UMask=0002            MemoryMax=infinity
```

Its `MainPID` runs as Uid 1000 with `NoNewPrivs: 0` and `Seccomp: 0`. Every agent profile shares that UID, so the blast radius is whatever UID 1000 can open:

- `~/.ssh/id_ed25519`, 420 B
- `~/.hermes/.env`, 29,367 B
- `~/.hermes/config.yaml`, 9,393 B
- `~/.hermes/auth.json`, 1,288 B

None of that is exotic. It is the default shape of a fleet that grew one worker at a time. Assume any agent that goes off-script already has all four of those files within reach.

## Reproducing the silent no-op

One transient unit per property. Each probe writes a canary into `$HOME/.hermes` and prints its own mount namespace:

```bash
systemd-run --user --wait -p ProtectHome=yes \
  /bin/sh -c 'touch $HOME/.hermes/canary; readlink /proc/self/ns/mnt'

systemd-run --user --wait -p IPAddressDeny=any \
  /bin/sh -c 'curl -s -o /dev/null -w "%{http_code}\n" https://example.com'
```

Measured here on Ubuntu 26.04.1, kernel 7.0.0-38-generic, systemd 259.5:

- `ProtectHome=yes` writes the canary and reports `mnt:[4026531832]`, identical to the parent
- `ReadOnlyPaths=/home/aditf/.hermes` does exactly the same
- `PrivateUsers=yes` stacked with `ProtectHome=yes` still does the same
- `IPAddressDeny=any` returns `200` from `example.com`, and `301` from a raw `http://1.1.1.1`

`systemctl show` reports `IPAddressDeny=::/0 0.0.0.0/0` throughout, because the property is parsed and displayed whether or not anything enforces it.

The only signal is one journal line, printed once per boot:

```
systemd[1277]: run-p1951633-i14538200.service: unit configures an IP firewall, but not running as root.
systemd[1277]: (This warning is only shown for the first unit using IP firewalling.)
```

Two faults live here and they deserve separate names. The IP firewall is unsupported by design on user units. The mount-based directives are supported, advertised, and inert.

## Why it degrades instead of failing

`journalctl -k` names the cause. An AppArmor profile transition, immediately followed by a denial:

```
apparmor="AUDIT" operation="userns_create" ... target="unprivileged_userns"
  execpath="/usr/lib/systemd/systemd-executor"
apparmor="DENIED" operation="capable" ... capability=21 capname="sys_admin"
```

Filesystem sandboxing needs `CAP_SYS_ADMIN` inside a fresh user namespace, because that is what systemd-executor builds the mounts with. Ubuntu ships `kernel.apparmor_restrict_unprivileged_userns = 1` in `/usr/lib/sysctl.d/10-apparmor.conf`, and its `unprivileged_userns` profile carries `audit deny capability,`.

So the executor degrades instead of failing. The service starts in the host mount namespace with no sandbox at all, and still reports `active (running)`.

This is not local weirdness. systemd issue 25014 documents `ProtectHome=true` as inert in `--user` mode. A worker fleet at block filed issue 5670 with the identical `sys_admin` denial, reporting that the sandbox "silently does not apply" and that the unit "has full read/write access to `$HOME`, including any secrets directory."

On issue 38588 a maintainer closed the firewall question as by design:

> "The firewall feature support is only for system services, and we have never supported that on user services."

A BPF program, he added, cannot be installed while unprivileged. For a fleet operator, the asymmetry is the whole problem. A unit that refuses to start is a bug report you fix on a Tuesday. A limit that is silently ignored is a belief you keep until something proves it wrong.

## What does enforce

Three knobs hold on an unprivileged unit. I measured each in its own transient unit:

- `NoNewPrivileges=yes` reports `NoNewPrivs: 1` with `CapEff: 0000000000000000`
- `SystemCallFilter=@system-service` installs a seccomp filter, and `~@mount` makes `mount` die with `Bad system call (core dumped)`
- `RestrictAddressFamilies=AF_UNIX` makes `curl` exit `6` with no HTTP code, so DNS and connect both fail

That last row is the interesting one. It is the only network kill switch an unprivileged unit can actually set, and it severs AF_INET, which is the model API. For an agent fleet it is a switch that cannot be thrown.

## The fix a fleet can adopt today

Three changes, in the order of what buys you the most:

- **Move the egress chokepoint out of the user manager.** A root-owned slice carrying `IPAddressDeny=` plus per-service `IPAddressAllow=` is the allow-list pattern the man page recommends. An outbound proxy the fleet must traverse does the same job.
- **Install the AppArmor carve-out so the filesystem directives can work at all.** Ubuntu already ships this pattern for Chrome and bwrap. The carve-out grants one binary rather than the whole box: `/etc/apparmor.d/systemd-executor-userns` holding `profile systemd-executor-userns /usr/lib/systemd/systemd-executor flags=(unconfined) { userns, }`, then `apparmor_parser -r`.
- **Make the sandbox fail closed.** A canary in `ExecStartPre=` that probes the most dangerous path and `exit 1`s when it turns out writable means a degraded sandbox never runs:

```ini
ExecStartPre=/bin/sh -c 'if touch %h/.hermes/.sandbox-canary 2>/dev/null; then \
  rm -f %h/.hermes/.sandbox-canary; \
  echo "sandbox DEGRADED (secrets writable)" >&2; exit 1; fi'
```

A directive appearing in `systemctl show` is not evidence that it was applied. The canary is the cheapest thing that tells those two states apart.

## Probe it before you trust it

On an unprivileged agent fleet, those containment directives are a configuration language rather than a boundary. That is fine as long as you know which is which.

So test it. Spawn a transient unit with the properties you believe are protecting you, and try to do the thing they are supposed to prevent. Mine turned out to be decoration, and I would rather learn that from a canary than from an incident report.
