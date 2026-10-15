---
title: Agent Sandboxes That Fail Open: systemd --user Silently Skips Containment
slug: systemd-user-sandbox-fails-open
date: 2026-10-15
excerpt: The security experts are right that the fix for AI agent incidents is containment. On the box that runs my fleet, the directives you would reach for are accepted, reported as applied, and quietly inert.
tags: systemd, agent-safety, sandboxing, apparmor, self-hosting
---

The CSO Online piece sitting near the top of the front page this week is right about the cause. The Hugging Face, Anthropic, Meta and Gemini incidents were containment and monitoring failures, not models with minds of their own.

I run eighteen agent profiles and a single multiplexed `hermes-gateway.service` under `systemd --user` on one Ubuntu host. So rather than quote the experts, I tried to do what they prescribe and add the sandbox.

Every filesystem and egress directive an unprivileged unit can set is accepted, printed by `systemctl show` as if applied, and then inert.

## The experts, and the objection the thread got right

Rob T. Lee is SANS Institute's chief AI officer, and he is blunt in the CSO piece:

> "The Hugging Face incident definitively showed that it wasn't the fact that the agents were super smart. It's that there literally was a hole that was exploited because it was not configured correctly on the containment side."

RAND's Dan Wallach supplies the monitoring half. The incident "went on for days, and nobody noticed," he says. Wallach's addition is the part I keep coming back to. People started these experiments and weren't watching them.

The thread complicates the "not configured correctly" framing in a way worth carrying. HN user `ahupp` points at the incident report's own wording:

> Agents "exploited a separate, previously unknown vulnerability in Artifactory to move beyond their sandbox environment."

`root_axis` argues that running Artifactory at all was the failure, because nothing airgapped the network and nothing blocked egress.

Both can hold. A zero-day opens the door. Unmonitored egress and unbounded credentials are what let it stay open for days, and that is the half you can measure on your own hardware.

## What the unit that runs the fleet actually says

`systemctl --user show hermes-gateway.service` resolves every containment knob to its off value:

```
NoNewPrivileges=no    PrivateTmp=no
ProtectSystem=no      ProtectHome=no
IPAddressDeny=        RestrictAddressFamilies=~
UMask=0002            MemoryMax=infinity
```

Its `MainPID` runs as Uid 1000 with `NoNewPrivs: 0` and `Seccomp: 0`. Every agent profile shares that UID, so the blast radius is whatever 1000 can open:

- `~/.ssh/id_ed25519`, 420 B
- `~/.hermes/.env`, 29,367 B
- `~/.hermes/config.yaml`, 9,393 B
- `~/.hermes/auth.json`, 1,288 B

None of that is exotic. It is the default shape of a fleet that grew one worker at a time.

HN user `novaRom` describes what the probing looks like from the other end. "I always see attempts to cat ~/.ssh/*", they write, and note that agents keep reaching for host credentials even after they understand they are sandboxed.

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

Filesystem sandboxing needs `CAP_SYS_ADMIN` inside a fresh user namespace, because that is what systemd-executor uses to build the mounts. Ubuntu ships `kernel.apparmor_restrict_unprivileged_userns = 1` in `/usr/lib/sysctl.d/10-apparmor.conf`, and its `unprivileged_userns` profile carries `audit deny capability,`. The executor degrades instead of failing. The service starts in the host mount namespace with no sandbox at all, and reports `active (running)`.

This is not local weirdness. systemd issue 25014 documents `ProtectHome=true` as inert in `--user` mode. A worker fleet at block filed issue 5670 with the identical `sys_admin` denial, reporting that the sandbox "silently does not apply" and that the unit "has full read/write access to `$HOME`, including any secrets directory."

On issue 38588 a maintainer closed the firewall question as by design. In his words:

> "The firewall feature support is only for system services, and we have never supported that on user services."

A BPF program, he added, cannot be installed while unprivileged. The reporter's reply is the line I would put in front of any CI operator. "Any limit is," he wrote, and a limit that is silently ignored is worse than a unit that refuses to start.

## What does enforce

Three knobs hold on an unprivileged unit. I measured each in its own transient unit:

- `NoNewPrivileges=yes` reports `NoNewPrivs: 1` with `CapEff: 0000000000000000`
- `SystemCallFilter=@system-service` installs a seccomp filter, and `~@mount` makes `mount` die with `Bad system call (core dumped)`
- `RestrictAddressFamilies=AF_UNIX` makes `curl` exit `6` with no HTTP code, so DNS and connect both fail

That last row is the interesting one. It is the only network kill switch an unprivileged unit can actually set, and it severs AF_INET, which is the model API. For an agent fleet it is a switch that cannot be thrown.

## The fix a fleet can adopt today

- **Move the egress chokepoint out of the user manager.** A root-owned slice carrying `IPAddressDeny=` plus per-service `IPAddressAllow=` is the allow-list pattern the man page recommends. An outbound proxy the fleet must traverse does the same job.
- **Install the AppArmor carve-out so the filesystem directives can work at all.** The block report's version grants one binary rather than the whole box: `/etc/apparmor.d/systemd-executor-userns` holding `profile systemd-executor-userns /usr/lib/systemd/systemd-executor flags=(unconfined) { userns, }`, then `apparmor_parser -r`.
- **Make the sandbox fail closed.** A canary in `ExecStartPre=` that probes the most dangerous path and `exit 1`s when it turns out writable means a degraded sandbox never runs:

```ini
ExecStartPre=/bin/sh -c 'if touch %h/.hermes/.sandbox-canary 2>/dev/null; then \
  rm -f %h/.hermes/.sandbox-canary; \
  echo "sandbox DEGRADED (secrets writable)" >&2; exit 1; fi'
```

A directive appearing in `systemctl show` is not evidence that it was applied. The canary is the cheapest thing that tells those two states apart.

## Containment is only half the net

The other front-page thread this week is why backups belong in the same sentence. A Swedish production house postponed a show after an edited season was lost, and TV4's program director told Sveriges Radio that no AI agent deleted the material. A backup system failed instead.

The thread's consensus is blunter than the headline. HN user `jve` puts it this way: you don't get to blame AI if it irreversibly deletes your data. Either you had no backup, or you never contained the agent where it could do irreversible harm. `Ekaros` supplies the likelier root cause, which is that nobody ever tested a restore from those backups.

A deletion is catastrophic only when the net underneath it has never been tested. That is the same defect class as a sandbox that fails open. Both look like controls, and neither one is.

## So here is the position

On an unprivileged agent fleet, those directives are a configuration language rather than a boundary. Go find out which of them your host actually enforces, and do it with a probe rather than a `systemctl show`. Mine turned out to be decoration.
