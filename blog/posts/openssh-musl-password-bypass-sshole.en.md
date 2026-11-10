---
title: Four Decades of Defensive Workarounds, One OpenSSH musl Password Bypass
slug: openssh-musl-password-bypass-sshole
date: 2026-11-06
excerpt: How layered workarounds created the OpenSSH musl password bypass (*sshole) on Alpine Linux hosts, allowing long passwords to unlock accounts marked with an asterisk.
tags: openssh, security, musl, alpine, ai-agents
keywords: openssh musl password bypass, sshhole vulnerability, openssh 10.6p2 release, alpine linux ssh vulnerability, ai agents security embargo
---

On the Alpine hosts I run, a 300-character password is an authentication bypass. Not a buffer overflow. Not a race condition. Just a long string of `a` presented to an account whose `/etc/shadow` field is `*`.

Özgün Kültekin named the bug *sshole and published the timeline at sshhole.com as a history lesson. That framing is right. Nobody here made a single mistake. Six defensive decisions each did exactly what they were designed to do.

Every layer worked. The stack did not.

## Six decisions, one hole

The chain, welded in this order:

- In **1980**, Bill Joy writes `*` into `/etc/passwd` next to `daemon`, so no password can ever match that account. The convention survives into `/etc/shadow`.
- In **1997**, the Single Unix Specification requires `crypt()` to return NULL when it cannot hash. Many callers never checked, and got a segfault instead of a failed login.
- In **August 2012**, musl commit `b3c4cc12` stops returning NULL. Failure now yields `"*"`, so careless callers fail closed without crashing.
- Then **twenty days later**, commit `88bf5a8a` ships SHA-512 crypt with a hard 256-byte cap (`KEY_MAX`). Long passwords make the key derivation function expensive, so musl refuses them.
- In **2016**, `pick_salt()` lands for CVE-2016-6210. OpenSSH was leaking account existence through `crypt()` timing, and the fix hashes against a borrowed salt when an account has no real hash.
- In **2022**, Alpine 3.16 commit `fbe926af` moves root's locked field from `!` back to `*`, because without pluggable authentication modules (PAM) the `!` also killed public-key logins.

Plot those six on one timeline and the collision is obvious. musl's failure value is `"*"`. The shadow convention for a locked account is `*`. And the 2016 timing fix exists specifically to run `crypt()` for accounts that have no hash.

## Why did OpenSSH invoke crypt() on locked accounts?

A normal password check has three steps:

- sshd takes the salt out of the stored field,
- hashes what you typed with that salt,
- then compares the output to the field.

An account locked with `*` has no salt of its own, so `pick_salt()` borrows one from a user who has a real password. That neighbour is half the exploit.

```c
/* the shape of the check, not literal source */
hash  = crypt(password, borrowed_salt);   /* musl: "*" if input > 256 bytes */
match = strcmp(hash, shadow_field) == 0;  /* "*" vs "*" -> 0, accepted */
```

Two conditions must line up. The password has to exceed musl's 256-byte cap, and the shadow field has to be exactly `*`. His browser demo puts the usable range at 257 to 1024 characters.

## Alpine supplied the other half

Alpine did not invent the `*` field, and it had a good reason to adopt it. In 2019, CVE-2019-5021 exposed Docker images shipping with no root password at all. Alpine locked root with `!`, which is correct on a system running PAM.

Without PAM, `!` also refuses public-key logins. Cloud images log in with keys, so the fix broke its own users. Alpine 3.16 switched the field to `*` and keys worked again.

On Alpine's official AWS and Azure images, the default `alpine` user gets `*` and passwordless `doas`. So the bypass does not stop at a user shell. It stops at root.

## Ten years of near misses

Why did this sit from 2016 to 2026? Mostly, who tests what.

OpenSSH's login tests run on OpenBSD and glibc. Most distributions push password auth through PAM, which rejects `*` before `crypt()` is ever called. musl does not test sshd, and sshd does not test musl.

Three people got close:

- A 2013 Debian bug (#714219) asked glibc to copy musl's `"*"`. Six years later Debian moved to libxcrypt, which returns `"*0"`, and the report closed. One character away.
- A December 2024 thread on the musl list reported BusyBox `passwd` breaking on a 257-character password. Same sentinel, same 256-byte limit, and nobody typed the word sshd.
- On October 30, 2026, a security review of OpenSSH touched `pick_salt()`. The bug sat four lines below the change, four days before Kültekin found it.

## The embargo died with it

Damien Miller announced 10.6p2 on November 5, 2026, the day after the report reached him. His stated reason is the part that outlives the CVE:

> We have recently observed multiple cases of rapid bug rediscovery by AI agents, sometimes within hours, and so now consider long embargo periods to be a dangerous practice that primarily benefits attackers.

The release notes carry the same message in project voice. When an AI-found bug is independently rediscovered by a second researcher, an adversary who never reports it can probably find it too.

The discovery is worth noting too. Kültekin built sshd across a matrix of libc, PAM and shadow layouts, then fired 17,600 login attempts at the builds. Malformed hashes, broken accounts, absurd password lengths. His site says agent swarms did the grinding.

I run a similar fleet myself for runbooks and code review at Dagango.com, so that part reads as familiar rather than alarming.

## What I changed on my hosts

The affected set is narrower than the headline suggests. glibc distributions are fine, and so is anything with PAM in the path. Patch the musl hosts anyway:

```bash
# Alpine and other musl hosts: upgrade, then confirm the build
apk upgrade openssh
apk list -I openssh   # expect openssh-10.6p2-*

# Cannot patch right now? Turn password auth off outright.
printf 'PasswordAuthentication no\n' > /etc/ssh/sshd_config.d/00-no-passwords.conf
rc-service sshd restart
```

A host already running `PasswordAuthentication no` never had a door to open. That line did more work than we credited it for.

For triage, the project ships a log check at github.com/oz9un/sshole. It looks for the signature of a password accepted for an account that has none.

## What actually changes

I am not filing this under "Alpine problem". The interesting failure is the interface. A locking convention in a text file and an error sentinel in libc are both useful conventions. Neither is an authentication boundary, and nothing in the stack was built to notice that they had become the same value.

The operational lesson is duller and more useful. If upstream ships emergency releases within a day because agents rediscover bugs in hours, my patch cadence has to survive that rhythm. A monthly maintenance window bets that the gap between disclosure and exploitation is still measured in months.

On the hosts I run, that bet stopped being cheap this week. Write your affected-host inventory down before you need it. Mine was a shell history, which is not an inventory.

## FAQ

### Does this bypass work if PAM is enabled on Alpine Linux?
No. Hosts that route authentication through Linux-PAM are unaffected because PAM verifies account lock flags before delegating to `crypt()`.

### Can attackers exploit this on hosts with PasswordAuthentication disabled?
No. If your `sshd_config` enforces `PasswordAuthentication no`, the password verification flow is never invoked.

### Does upgrading OpenSSH or musl completely remediate the issue?
Yes. Upgrading to OpenSSH 10.6p2 adds explicit checks that reject passwords longer than 256 bytes and refuses authentication if `crypt()` returns an error sentinel like `"*"`. musl has also patched its failure sentinel handling.
