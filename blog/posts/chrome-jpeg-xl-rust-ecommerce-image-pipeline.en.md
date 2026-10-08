---
title: "Chrome 155 Ships JPEG XL in Rust: What It Actually Changes for an E-Commerce Image Pipeline"
slug: chrome-jpeg-xl-rust-ecommerce-image-pipeline
date: 2026-10-08
excerpt: Chrome 155 reverses its 2022 decision and ships JPEG XL decoding, built on a pure-Rust decoder. For a platform that got burned by AVIF's encoding cost, this is the format worth re-evaluating.
tags: web-performance, rust, ecommerce, browsers, architecture
---

## Google un-deleted a format it killed in 2022

Chrome dropped JPEG XL in 2022, officially for "lack of ecosystem interest." On October 6, 2026, Chrome 155 ships it back.

The HN thread covering the reversal cleared 500+ points and 350+ comments. One of the sharper top-level comments on that thread put the subtext bluntly: Google's own executives didn't need convincing by an argument, they just gave up once every other browser had shipped it.

Safari has supported JPEG XL since September 2023. Firefox is in progress. Chrome was the last tier-1 holdout, and that holdout is what mattered: a format with Safari-only support is a curiosity, not a catalog format.

## Why Chrome needed Rust to say yes

The blocker was never compression quality. It was `libjxl`, the ~100,000-line C++ reference decoder.

Chromium runs untrusted, network-delivered bytes through its decoders inside the renderer process. That is exactly the shape of risk the project's own "Rule of Two" security doctrine exists to flag: pick at most two of the following.

- Untrustworthy input.
- Unsafe implementation language.
- High privilege.

A C++ image decoder parsing bytes from the open internet at renderer privilege is three for three.

Google's answer was `jxl-rs`, a full Rust reimplementation of the decoder. Chrome's own announcement is specific about the tradeoff they were not willing to accept:

> "Memory safety is crucial, but a memory-safe decoder that is approximately as fast as the best non-memory-safe alternative is a much more obvious choice than a choice with a significant performance compromise."

Getting there needed `target_feature_11`, a Rust feature that had to be stabilized first, so SIMD acceleration could run without `unsafe` blocks. That is the actual engineering story here: a specific compiler feature landing specifically so a security team could ship a performance-critical decoder without an escape hatch into unsafe code.

## The format AVIF should have been for a catalog

Here is the part the frontend compression benchmarks skip. AVIF's 30-50% size win over JPEG is a browser-side number. Getting there server-side is a different problem.

AVIF encoding is CPU-heavy, especially at the quality settings worth shipping. We felt this directly: merchants on Dagango.com bulk-upload hundreds of product photos in one import, and that turns into a burst of encode jobs landing on the same worker pool at once.

A JPEG encode of the same batch finishes in a fraction of the time AVIF needs at a comparable quality target. Multiply that gap by a few hundred images arriving in the same five minutes, and the AVIF jobs back up the queue, not the decode path browsers compete on.

That is a server-side cost that compression benchmarks never show, because benchmarks compare output bytes, not CPU-seconds spent producing them.

JPEG XL doesn't eliminate that cost. It makes a different cost unnecessary.

## Lossless JPEG transcoding is the actual migration path

JPEG XL can repack an existing JPEG's own DCT coefficients, bit for bit, into a `.jxl` container.

- No re-encode.
- No generational quality loss, the kind that compounds every time a lossy image gets decoded and re-saved.
- A real-world size cut of roughly 20%, from a transform, not a recompress.

For a multi-tenant platform holding years of merchant-uploaded JPEGs, that is the whole migration story. We are not asking a background worker to re-encode a catalog from pixels. We are repacking a bitstream.

Compare that to the AVIF path. Every image in the catalog needs a full decode-then-encode pass to get a smaller file, at AVIF's CPU cost, and a lossy image gets slightly worse every time it goes through that pass. JPEG XL's lossless transcode skips both problems for every JPEG already sitting in storage.

## Progressive decode without a thumbnail pipeline

JPEG XL's bitstream is progressive by construction. A browser can render a usable low-resolution preview from the first chunk of bytes and keep sharpening as more arrives, without the server generating a separate thumbnail asset.

For buyers on throttled mobile connections across Southeast Asia, that is the difference between a blank product card and a recognizable one while the rest of the image streams in. It also removes a whole class of infrastructure: no thumbnail-size matrix to generate, store, and keep in sync with the original.

One HN commenter closed the thread's most pointed exchange with the plainest version of the win. Art and catalog sites get the biggest gain from JPEG XL, because they can losslessly repackage every JPEG they already have for close to zero cost.

## What I'd actually ship

Don't rip out AVIF. Keep serving it where the encode cost is already amortized, like editorial or hero images that get encoded once and served millions of times.

Point JPEG XL specifically at the problem AVIF made worse: the merchant catalog upload path, where thousands of JPEGs arrive in bursts and need to go somewhere cheap, fast, and without quality loss.

Browser support finally clearing tier-1 is the headline. The real decision in front of a platform like ours is narrower: use lossless JPEG XL transcoding to stop paying AVIF's encode tax on content you didn't need to re-encode in the first place.
