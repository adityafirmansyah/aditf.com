---
title: "Why next/font/google Broke Our CI: Self-Hosting 13 Font Subsets for Zero-Network Builds"
slug: nextjs-self-host-font-subsets-zero-network-builds
date: 2026-10-07
excerpt: Our master CI died twice in twelve hours inside next/font/google, on commits that carried identical font code. Here is how Dagango.com vendors 13 font subsets on disk and makes next build fetch nothing.
tags: nextjs, frontend, performance, webdev, architecture
---

## `next build` is not an offline command

I assumed `next/font/google` handled fonts. In the browser it does: no layout shift, no request from your visitor to Google, files served from your own origin.

None of that says anything about the machine running `next build`. That loader still opens an HTTPS connection to fonts.googleapis.com, every single time.

So your deploy now hangs off someone else's CDN, and you find out at the worst moment.

## Two red builds in twelve hours

Master CI died inside that fetch twice in about twelve hours, with no font code in either diff.

The red runs were `36935742623` (merge `42875bb`) and `36851269872` (`f6b3627`). Both surfaced as `An error occurred in next/font`, then this:

```
TypeError: Cannot read properties of null (reading '1')
    at @next/font/dist/google/loader.js
```

The commits immediately before and after each red run carried identical font code, and built green. Every occurrence was a false red that cost a triage. A pipeline that cries wolf is also a pipeline that can hide a real break.

## Where the fetch lives

The build-time request comes from `@next/font/dist/google/fetch-resource.js`.

If Google's CDN flakes or throttles that call, the loader tries to destructure a response that never arrived and throws on `null`. The dependency is real, it is external, and it sits directly between you and a green build.

## Latin-only was never an option

The quick fix is to vendor the Latin woff2 files and stop there. On a Latin-only marketing site, that is genuinely enough.

Dagango.com is multi-tenant. Merchants write storefront copy in Vietnamese, Cyrillic, Greek and Devanagari alongside Latin. Drop the non-Latin files and those characters fall back to a system font with mismatched metrics and missing glyphs.

Google serves this set for the three platform families:

- Baloo 2 (display): `latin`, `latin-ext`, `vietnamese`, `devanagari`.
- Public Sans (body): `latin`, `latin-ext`, `vietnamese`.
- JetBrains Mono: `latin`, `latin-ext`, `vietnamese`, `cyrillic`, `cyrillic-ext`, `greek`.

That is 13 files and 225 KB, and it is the complete set for these families rather than a selection from it.

## next/font/local drops a `unicodeRange` on a `src` entry

`next/font/local` has no `subsets` option, and it cannot express a subset through a range on a source entry either. The bundled loader destructures each entry as `{ path, style, weight, ext, format }`, so a range you attach there is silently discarded.

`declarations` is the escape hatch. The loader copies every declaration into the `@font-face` it generates, so one call per (family, subset) can carry that subset's exact range.

```ts
export const baloo2LatinExt = localFont({
  src: [{ path: "./Baloo2-latin-ext-700.woff2", weight: "700", style: "normal" }],
  variable: "--font-baloo-2-latin-ext",
  display: "swap",
  preload: false,
  adjustFontFallback: false,
  declarations: [
    { prop: "font-family", value: "Baloo 2" },
    { prop: "unicode-range", value: "u+0100-02ba,...,u+a720-a7ff" },
  ],
});
```

Note the `font-family` declaration. A saved tenant theme resolves a platform default family by name (`lib/theme/derive.ts`), and the storefront shell deliberately requests no stylesheet for it. Scoped to Next's generated name, that tenant would silently render through the fallback face.

## Keep the fallback faces from multiplying

`next/font` emits one metric-matched `... Fallback` face per call, so leaving the defaults alone would mint one for every subset. We set two knobs instead:

- `preload: true` only on the three Latin calls, which are the files the build preloads.
- `adjustFontFallback: false` on the other ten, so no subset mints a second `... Fallback` family.

All 13 calls get composed into a single `fontVariables` string applied on `<html>`. Keep that composition intact. A `localFont()` call whose class is never applied is tree-shaken away, and its `@font-face` and file go with it.

## Proving the build fetches nothing

A config that looks air-gapped is not evidence. We ran the build under `strace`:

```
strace -f -e trace=connect -o /tmp/build-conn.log ./node_modules/.bin/next build
```

Then counted the connect traffic:

```
BUILD_EXIT=0
CONNECT_LINES=0
HTS443=0
DNS_LINES=0
```

No outbound sockets, no DNS lookup, no port 443 connection for the whole build.

## One honest delta

Everything above is byte-for-byte what the Google loader was already emitting. The nuance is the three `... Fallback` faces that remain: their `size-adjust` numbers change after the swap.

The reason is that the Google loader reads Next's precomputed capsize table, while the local loader measures the font file itself with fontkit. That touches only text drawn from a fallback face, meaning the pre-swap window and the two arrow glyphs no subset carries. Everything drawn with the webfonts is unchanged.

## What I would copy

If your `next build` still talks to the network, you do not have an offline build. Vendor the woff2 files your loader is already emitting, give each subset its own call, then prove the silence with `strace`.

Finish with a test that fails when a font call goes unreferenced. That is the failure mode which survives every green build: a `localFont()` call with no class on `<html>` ships three faces instead of 13.
