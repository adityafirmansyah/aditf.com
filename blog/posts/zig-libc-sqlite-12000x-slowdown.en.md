---
title: Zig's libc Rewrite Made SQLite 12,000x Slower. Your Tests Wouldn't Catch It
slug: zig-libc-sqlite-12000x-slowdown
date: 2026-11-05
excerpt: A cross-compiled Rust service lost 12,000x on SQLite inserts because Zig's libc rewrite walked the whole string inside every strchr call. Local tests passed on macOS.
tags: rust, zig, sqlite, performance, compilers
---

Inserting 40,000 JSON records into SQLite should take milliseconds. For Dennis Forbes it pinned a full CPU core for minutes, and his write-up landed on a number that reads like a typo: 12,000x slower.

Lock contention was not the problem. Neither was fsync, disk I/O, or a missing index. The binary had been cross-compiled for Linux through `zig cc`, and the C standard library (libc) sitting underneath it had quietly turned SQLite's parser quadratic.

That is the part worth your attention. Not the Zig bug itself, which upstream is fixing. The fact that an entire class of regression is invisible to the test suite most of us actually run.

## The libc your tests never touched

Forbes benchmarked a 1.2 MB JSON payload fed to SQLite as a batch of 40,000 records. On macOS, where his integration tests ran, the same workload finished in sub-millisecond time.

The difference was not the hardware. It was the linker.

`cargo-zigbuild` hands linking to `zig cc`, which ships its own C library implementations. That is the whole reason the tool exists: emit Linux binaries from a Mac or a CI runner without booting a Docker build container. The convenience is real. So is the cost.

A native build on your laptop links Apple's libc. Your production artifact links Zig's `libzigc`. That is Zig's own version of `strchr`, `strspn`, `strstr` and the rest of that family.

Your tests exercised Apple's copies. You shipped Zig's.

## Shlemiel the Painter, again

C strings are not strings. They are a pointer and a promise that a zero byte exists somewhere ahead of it. A Zig slice is a pointer and a length. Every bridge between those two representations needs the length, and the only way to get it from a bare `char*` is to walk forward until you hit the terminator.

Go read Joel Spolsky's 2001 essay "Back to Basics" if you have not. His Shlemiel paints one meter per stroke, then walks back to the can for every stroke, so painting a longer fence takes quadratic time. The essay is twenty-five years old and it still predicts production incidents.

Here is the shape of what `libzigc` did, roughly:

```zig
// illustrative sketch, not the literal patch
const n = std.mem.len(ptr);           // scan to the NUL byte first: O(remaining)
const s = ptr[0..n];                  // now we have a slice
const idx = std.mem.indexOfScalar(u8, s, ':');  // then search: another O(remaining)
```

A call that should stop at the first colon now reads to the end of the buffer first. Do that once and nobody notices. Do it in a loop over a 1.2 MB document and the loop becomes quadratic.

The tell is that `strchrnul` exists at all. That function returns a pointer to the terminator instead of the length, precisely because C callers often do not need to know how long the rest of the string is. A rewrite that computes the length up front has discarded the reason the API was shaped that way.

PR #37417 corrects `strchr`, `strchrnul` and the neighbouring functions. The fix is unglamorous, which is what you want in a libc: search with a bounded scan, skip the length when the caller never asked for it.

## Tokenizers live on the worst-case path

The mechanism matters more than the specific functions. SQLite's lexer tokenizes JSON and SQL by advancing a pointer through the buffer, calling `strchr` and `strspn` to skip whitespace and find the next delimiter.

That loop was always linear. Each call advanced the cursor by a few bytes, and the total work stayed proportional to the input. Now every call walks to the end of the buffer regardless of where it finds its match, so N tokenization steps each cost O(N).

Total: O(N²). At 1.2 MB that is roughly a trillion byte comparisons where the old build did about a million. The 12,000x figure stops looking mysterious.

## The reproduction is a straight line

Zig issue #37402 carries a synthetic `strchr` loop, compiled with `zig cc -target x86_64-linux-musl`:

- 1 MB: 2.8 seconds
- 2 MB: 11 seconds
- 4 MB: 46 seconds

Double the input, quadruple the time. That ratio is the fingerprint of quadratic growth, and it is far more useful than any absolute number.

The same loop built with `musl-gcc` finished under 5 milliseconds at every one of those sizes. Not a little faster. Four orders of magnitude faster, on the same machine, doing the same thing.

## What I changed in my own build

I cross-compile Rust backend services and Dagango.com worker pipelines for Linux VPS and bare metal with `cargo-zigbuild`, for exactly the container-free reason above. Four changes came out of reading this:

1. **Benchmark on the target libc, not the host.** The perf test runs inside the same toolchain that produces the artifact, against the musl binary, not a native debug build.
2. **Assert growth, not latency.** Parse 1 MB and 4 MB in CI and check that the time ratio stays near 4x. Absolute timings flake on shared runners; a 16x ratio does not lie.
3. **Treat a Zig version bump as a dependency change.** Pin it, then require a bench run before the bump merges. `zig cc` is now a production dependency of the build, and it deserves the same scrutiny as a crate.
4. **Keep one `musl-gcc` build around as a control.** When a number moves, you need a second implementation to tell you whether the code changed or the toolchain did.

None of that is exotic. It is the ordinary discipline you already apply to database drivers and allocators, applied to something we all quietly assumed was a boring linker flag.

## An ABI is a performance contract too

Zig is rewriting libc, and Rust is rewriting coreutils, and both efforts are worth doing. But functional equivalence and a passing test suite are the easy half of the job.

The hard half is that a C library is forty years of undocumented asymptotics. Callers wrote loops that depend on `strchr` stopping at the first hit. Nobody wrote that requirement down, because everybody already knew it, so it never made it into a test.

If you are replacing a thirty-year-old primitive, "does it return the right value?" is the easy question. The one that matters is whether it still costs what callers assumed it costs. That second question has no compiler warning and no unit test. It only has a benchmark, and only if you remember to run it against the binary you actually ship.
