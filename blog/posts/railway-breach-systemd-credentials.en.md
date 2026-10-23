---
title: Railway's Breach Was a Database. Your Env Vars Are Still the Wrong Vault.
slug: railway-breach-systemd-credentials
date: 2026-10-23
excerpt: Railway's October 2026 breach exposed decrypted environment variables from a secrets database. The storage plane was the target, but the habit of storing credentials in env vars made the blast radius huge.
tags: devops, security, linux, self-hosting, cloud
---

On October 21, 2026, Railway told customers that an unauthorized third party had reached the systems storing their environment variables. For some of them, the disclosure reads, attackers "obtained the decrypted contents." Builds stopped worldwide that morning. The next day, teams were rotating AWS keys they had no way to redeploy.

The breach is the news. The design decision behind it is the lesson. Railway's storage plane got hit, which means the size of the damage was set years earlier by every team that treated a vendor dashboard as the place production credentials live.

## What Railway actually disclosed

The disclosure is unusually direct about the mechanism. Upstream AI inference providers were notified to revoke keys proactively. All deployments were paused while the investigation ran.

On October 22, Railway published two remediation guides under Mykal Machon's byline, one for AWS access keys and one for Google Cloud service account keys. The AWS guide is the more useful of the two:

- Deactivate the exposed key instead of deleting it, so you can revive it if something you forgot about breaks.
- Search CloudTrail event history by access key ID, which keeps management API calls for 90 days.
- **Look for calls your app never makes:**

  ```
  RunInstances
  CreateUser
  CreateAccessKey
  AttachUserPolicy
  CreateRole
  PutBucketPolicy
  ```
- Repeat the search in every Region, including the ones you don't use.

The GCP guide adds a detail people miss under pressure. Disabling a service account key blocks new logins, but tokens already issued from it stay valid for up to an hour. If you need the access cut now, disable the whole service account and revoke any unexpected `Service Account Token Creator` grants.

There is also a trap that only exists on a PaaS. Railway's own guide says updating a key is a variable edit plus a redeploy. Deploys were frozen. So the correct advice, rotate immediately, arrived with a second sentence nobody parsed in time: rotating is useless until the control plane that just failed comes back.

That ordering matters more than it looks. A rotation procedure that depends on the compromised plane is not a procedure.

## The thread blamed the wrong layer

Hacker News thread 50188228 (590 points, 334 comments) split fast, and both halves were partly right.

One camp wanted a pointer instead of a stored value: "Use environment variables to point to where secrets are located, not to store their values." That is numbsafari's line. Then tptacek pushed back on the premise itself: "there's no reason to believe 'environment variables' were the reason this data was breached."

I think tptacek is right about this incident. The attacker hit a database of secrets, not a process environment. Had every Railway customer injected credentials as files, that database would have been just as juicy, and the freeze would have looked identical.

Numbsafari is right about the next incident. An environment variable is a weak container for a credential regardless of who stores it. Two separate claims got merged in that thread, and merging them is how fifteen years of bad practice survives a very public breach.

## Where a variable leaks, concretely

I ran the comparison on this box instead of arguing it. systemd 259, a user unit, one variable:

```bash
systemd-run --user --unit=probe-longrun --collect \
  --property=Environment=PROBE_HMAC=super-secret-value \
  /bin/sleep 12
```

Then, from an ordinary shell as the same user:

```bash
PID=$(systemctl --user show -p MainPID --value probe-longrun)
tr '\0' '\n' < /proc/$PID/environ | grep PROBE_HMAC
ps eww -p "$PID" | tr ' ' '\n' | grep PROBE_HMAC
```

Both printed `PROBE_HMAC=super-secret-value`. No root, no debugger, no container escape, no `/proc` hardening to defeat. The same trick works on any process that inherited the variable, which includes every child and every `sh -c` in a deploy script.

Twelve-Factor said to keep config in the environment because config must not live in code. That reasoning was sound for database hostnames. It was never sound for a live API key. A process's environment is readable by whoever can read that process, and that set is larger than most teams assume.

## What the Linux alternative actually does

systemd credentials are not a secrets manager. They are a way for the service manager to hand a unit a file it cannot modify, read from outside, or find in `process.env`.

```ini
[Service]
User=dagango-api
LoadCredentialEncrypted=dbpass:/etc/credstore.encrypted/dbpass.enc
ExecStart=/usr/local/bin/api
```

The unit reads `$CREDENTIALS_DIRECTORY/dbpass`. Same probe, with the variable replaced by a credential:

```
cred_dir=/run/user/1000/credentials/run-p2707281-i11091151.service
-r-------- 1 aditf aditf 18 dbpass
environ_has_credname=0
touch $CREDENTIALS_DIRECTORY/newfile  ->  Permission denied
NAME   SECURE SIZE PATH
dbpass weak    18B  .../run-p2707281-i11091151.service/dbpass
```

Four properties held up:

- The directory is read-only to the unit and sits outside the environment entirely.
- Credential files are mode 0400, owned by the unit's UID.
- Nothing usable appears in `/proc/$PID/environ` or `ps eww`.
- The ciphertext is bound to a credential name. Copying `dbpass.enc` to `renamed.enc` made decryption refuse it: `Name in credential doesn't match expectations`.

That last one is the property a multi-tenant platform cannot give you, because the platform holds the key by design.

## What this does not solve

TPM2 is not free money. `systemd-analyze has-tpm2` on this machine reports `partial` and exits 16, so the encrypt path falls back to `/var/lib/systemd/credential.secret`, readable only by root. That file plus the host is enough to decrypt, which is the whole point of TPM2 binding: it removes the file from the equation. Not every box has the chip.

Note the `weak` label in the listing above. A user-scope credential backed by ordinary memory is honest about being weaker than a ramfs-backed one.

The other honest cost is migration. Every service gets touched, every secret re-issued, every unit file gets a `LoadCredential=` line. On a small fleet that is a weekend. On hundreds of services it is two quarters and a long argument about who owns the rollback plan.

None of that argues for leaving production credentials in a vendor's database. It argues for doing the boring version first:

- rotate everything that ever lived in Railway,
- read CloudTrail and Cloud Audit Logs for that window,
- then decide which secrets deserve a host-bound file instead of a text box.

The dashboard field was always the weak link. The freeze just made it visible to people who had not thought about it since 2011.
