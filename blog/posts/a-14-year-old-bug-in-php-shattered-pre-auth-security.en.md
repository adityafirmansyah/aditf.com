---
title: A 14-Year-Old Bug in PHP Just Shattered Pre-Auth Security for 70% of the Web
slug: a-14-year-old-bug-in-php-shattered-pre-auth-security
date: 2026-10-27
excerpt: A flaw in PHP's own request parser, present since 2012, hands unauthenticated attackers code execution on default configs. PHP runs roughly 70% of the web.
tags: security, php, devops, vulnerability, software-engineering
---

On October 21, 2026, PHP shipped fixes for two critical vulnerabilities, CVE-2026-109618 and CVE-2026-109619. Both score 9.2 in version 4.0 of the Common Vulnerability Scoring System (CVSS). The pair is called PHP2Shell, and CISA added both to its Known Exploited Vulnerabilities catalog on October 26.

W3Techs puts PHP at 69.2% of all sites whose server-side language it can identify. That is the measurement behind the "roughly 70% of the web" headlines.

The exploit needs no bad plugin or sloppy filter. It executes inside the engine's own request parser, while the multipart body is still being turned into `$_POST` and `$_FILES`. Your router does not exist yet.

That ordering makes PHP2Shell a patch-right-now problem, not a hardening exercise. Every input check I own sits downstream of corrupted code.

## The parser runs before modules are activated

PHP builds `$_POST` and `$_FILES` before any script can read them, so the parse happens during request startup. The ordering in `main/main.c`, quoted from Calif's disclosure:

```c
PG(modules_activated) = 0;
/* ... */
php_hash_environment();   /* Parses request variables and multipart input. */
zend_activate_modules();  /* Calls normal module RINIT functions. */
PG(modules_activated) = 1;
```

Two consequences follow:

- a multipart request is parsed whether or not the endpoint accepts an upload,
- a fatal error during that parse is not an application error, and your handler never runs.

The path is reachable under defaults. `session.upload_progress.enabled` ships `On`, letting the session extension open and update a session while the body is read.

## Count first, allocate second

Calif's team traced it to a hash table insertion routine, `_zend_hash_str_add_or_update_i`. Element counts are bumped before the bucket is initialized:

```c
idx = ht->nNumUsed++;
ht->nNumOfElements++;
p = ht->arData + idx;
p->key = zend_string_init(str, len, persistent); /* may zend_bailout() */
```

When the key allocation hits `memory_limit`, PHP does not unwind cleanly. It jumps out through C-level `longjmp()` with the count already incremented. Teardown later walks `ht->arData` up to `nNumUsed` and treats the half-written bucket as live data.

Reaching that limit is cheap. A multipart part built to the RFC1867 upload format can carry an empty filename, escaping `max_file_uploads`, yet PHP still creates six `$_FILES` entries for it. A nested field name like `files[a][b][c]` builds that hierarchy six times over.

Hundreds of such records fit inside the default 8 MiB `post_max_size` while occupying more than the default 128 MiB heap. Chunked HTTP/1.1 or lengthless HTTP/2 bodies clear the same cap, because PHP compares the declared `Content-Length` rather than consumed bytes.

## mod_php and PHP-FPM are not the same fight

Both server application programming interfaces (SAPIs) parse the body identically. What differs is the worker's fate after a startup fatal.

On Apache with `mod_php`, a startup failure still reaches `php_request_shutdown()`. The heap is freed and the Apache child survives to serve the next request. Session globals left pointing into that freed heap get consumed by the next multipart request, yielding remote code execution against arbitrary PHP scripts with no application involvement.

PHP-FPM takes the other branch. A startup failure calls `php_module_shutdown()` and returns `FPM_EXIT_SOFTWARE`, so the worker exits and the stale pointers die with it. On FPM the fatal must land after a successful startup, once the application has started decoding something.

That second chain needs an application-level trigger:

- the app decodes serialized data under attacker memory pressure,
- the decode runs through `session_start()`, `session_decode()`, `unserialize()` or a wrapper such as WordPress's `maybe_unserialize()`,
- the fatal skips `php_var_unserialize_destroy()`, so the Basic extension's `BG(unserialize).data` pointer and its nesting level survive,
- the request heap is freed while the FPM worker stays alive,
- the next multipart request reaches session upload progress before Basic's init, reuses the abandoned decoder bookkeeping, and writes a controlled `zval` into reclaimed memory via destructor-list arithmetic.

Calif demonstrated that chain against nginx. The prerequisite is not exotic. A session ID chosen by the attacker plus one `session_start()` call is surface many PHP applications expose.

## The patch fixes a failure mode

The fix runs deeper than a bounds check. Out-of-memory no longer aborts an operation mid-flight. It becomes a soft error at the next VM safe point, so cleanup runs and the pointer clears before the memory is released. Past a higher threshold it becomes a hard `_exit()`.

Shutdown also resets long-lived state that used to survive:

- session globals,
- error backtraces,
- OPcache shared memory.

Objects decoded by the upload-progress handler stay `__PHP_IncompleteClass`, so neither an autoload nor a `__destruct()` runs during that early decode.

Read that list as an admission. Containment that depends on a non-local jump landing where cleanup can still reach is not containment. It is a coin flip, and this one took a long time to come up tails.

## If you cannot patch this hour

Zero-day or not, upgrades wait for change windows. Every measure below is partial, none substitutes for the patched release.

```ini
; emergency only, revert after upgrading
session.upload_progress.enabled = 0
fatal_error_backtraces = 0        ; PHP 8.5.x
memory_limit = -1
```

Five details decide whether they actually help:

- restart every worker after editing `php.ini`, because running Apache children and FPM workers hold old values,
- set `pm.max_requests = 1` while exposed, breaking the requirement that one worker handle both requests,
- switch off `session.upload_progress` knowing it covers neither the OPcache arm nor the backtrace arm,
- don't substitute `RLIMIT_AS` or `RLIMIT_DATA` for `memory_limit`, because OS limits bypass PHP's cleanup path,
- accept that `memory_limit = -1` trades code execution for a trivial memory-exhaustion denial of service.

I would weigh that last trade hardest on a shared machine. An attacker who cannot write a bucket can still send the nested empty-upload payload and eat the box's RAM.

## Inventory is the harder half

Only four releases carry fixes: PHP 8.5.12, 8.4.27, 8.3.36 and 8.2.35. Nothing below 8.2 gets one; the earliest affected path dates to PHP 5.4.0, March 2012. CISA's advice for 8.1 or older: take it offline.

Listing that estate is heavier work than the upgrade. PHP hides where nobody labels it:

- `php-cgi` and LiteSpeed invocations,
- FrankenPHP build images,
- container images baked months ago,
- vendor appliances whose admin console never mentions the runtime.

What I would change in my own stack:

- reject `multipart/form-data` at ingress for routes that never accept uploads, so it never reaches PHP,
- rebuild images against a patched version, not edit `php.ini` on a live host,
- sandbox the worker so a popped process cannot exec a shell or fetch a tool, the activity CISA asks defenders to watch for,
- treat `session_start()` on an attacker-supplied ID as input surface, since on FPM it is one.

Most hardening advice for a web stack assumes the application is where input becomes dangerous. PHP2Shell breaks that assumption at the engine boundary. A request lives twice, once inside the parser and once inside your code, and only the second life has your firewall in front of it.
