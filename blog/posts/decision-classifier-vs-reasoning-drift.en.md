---
title: Two Kinds of Decision, and No Way to Prove the Model Did Not Change
slug: decision-classifier-vs-reasoning-drift
date: 2026-09-30
excerpt: A reasoning classifier and a drift benchmark landed a day apart. Together they say which decisions deserve thinking, and why your own latency numbers cannot prove the model changed.
tags: ai-agents, local-llm, evaluations, homelab, software-engineering
---

Two posts hit the front page within a day of each other. PostHog's Jeeves argues that a small decision model should reason before it answers. livenerf asks whether a frontier model quietly gets worse after launch, and publishes the smallest effect it can actually see.

Put them side by side and you get two halves of one problem. Jeeves tells you which decisions are worth thinking about. livenerf tells you how hard it is to prove the thing doing the thinking is still the thing you validated.

I run sixteen gateways and three model tiers on one box at home, so both halves landed on me personally.

## The split is now measured, not argued

Jeeves is a 9B Jev-style classifier (Qwen3.5-9B, LoRA, a pointer head) trained with SFT and then CISPO. It thinks before it decides, which is the opposite of what a Jev-class model is for.

The numbers say the trade is real, and that it is not free:

- Test overall: 0.889, against 0.857 for Jev and 0.822 for Kev-9B.
- JevBench overall: 0.935, against 0.866 for Jev.
- JevBench hard: 0.865, against 0.730 for Jev.
- Transfer (MMLU-Pro and buried state): 0.746, against Jev's 0.800.
- MMLU: 0.793, against Jev's 0.900.

So it wins where the decision is the whole job, and loses where the model needs world knowledge. That is not a contradiction. It is a picture of where reasoning helps and where it just adds latency.

And the latency is the point. On one H100:

- No thinking: about 0.3 s per request.
- Full thinking: 3.3 s median, 17.1 s at p90.
- The recommended compromise (`max_think` 768, `nothink_threshold` 0.9): 2.0 s median, 5.6 s p90, 0.806 dev accuracy, 344 mean reasoning tokens.

One of the top comments on the Hacker News thread was blunt: "17s p90 latency kind of defeats the point of a Jev-class model."

Another asked a sharper question. A model that reasons autoregressively before deciding has already given up the single forward pass that made Jev cheap in the first place.

Both are right, and both are aimed at the wrong deployment. If your decision is bounded and repeated, you want the 0.3 s path and a calibrated probability. All of these are bounded and repeated:

- which profile takes this task,
- is this output publishable,
- is this DM urgent.

If the decision is open-ended, you were never going to run it on a classifier anyway, and 2 s is fine.

## Where thinking backfires

The table above shows two losses, but the more interesting failure is inside the training run. The authors used a 624-step CISPO schedule and stopped at step 402, because past that point the head over-sharpens on the saturated RL pool.

Read that again. More training made the model's probabilities worse, and you cannot score your way out of that, because a classifier's score is not the thing you consume.

Accuracy kept looking fine while calibration degraded. The probabilities moved first, and the score sat still.

## Calibration is one fitted number

When you read p = 0.9 off a Jev-style model, you are trusting a single constant.

The mechanism is unglamorous. A pointer head scores each option with a scaled dot product, between the hidden state at the decision token and the hidden state at that option. The final probabilities are a softmax over those option scores, divided by one temperature fitted on the dev set and shipped with the checkpoint.

Temperature above 1 softens the distribution. Below 1 sharpens it. The ordering of options never changes, so the whole confidence reading rides on that one fitted scalar as much as on the weights.

JevBench ECE is 0.049 for Jev and 0.037 for Jeeves.

## The other half: a benchmark that publishes its own floor

livenerf is an append-only drift benchmark with one question: does Opus 5.5 get worse after launch? Opus 5.5 shipped on 2026-09-22, so the clock started within days of launch rather than months later, once people started to suspect something.

The design is worth copying even if you never touch an Anthropic model:

- 2,336 questions screened with 4 samples each. 78 kept because the model is sometimes right.
- 90 samples a day for 30 days. Days 1-10 are the baseline, then two 10-day windows.
- Paired per-item comparison against each item's own baseline, so question difficulty drops out.
- Exact-match graders, and no LLM judge ever, because the judge would drift too.
- A control model running alongside, so a platform-wide move does not get blamed on the model.
- A pinned CLI, plus a copy of the binary where the auto-updater cannot reach it.

That last one is not paranoia. A Claude Code update changes the harness, and a changed harness looks exactly like a changed model.

The published detection floor is about 7.5 accuracy points per 10-day window, for roughly 3.6% of a weekly Max plan.

## What "nerfed" looks like in the data

The validation half is the part I keep rereading. Lowered effort shows up far more clearly in tokens than in accuracy:

- Effort low: 62% fewer output tokens, 8.3 ± 4.5 accuracy points down.
- Effort medium: 26% fewer tokens, 4.2 ± 3.9 points down.

So livenerf's secondary metric is output tokens per sample, not score. If a model quietly starts thinking less, the token count moves first, and the accuracy number may not move at all.

Then the honest limit, stated by the author.

Swapping Opus 5 in for Opus 5.5 "was not distinguishable from Opus 5.5 at 99%" (−3.8 ± 6.3 points, −23% tokens).

The instrument cannot see a same-family swap of that size in one validation's worth of samples.

They also audited their own panel. Out of 78 questions, 8 answer keys look wrong and 30 are ambiguous. They kept all of them and ran a pre-registered sensitivity analysis. Dropping inconvenient items after seeing the results is its own kind of drift.

## Your own box is not the referee

Here is where my setup gets uncomfortable. The machine I would measure on exposes sse4_1, sse4_2 and ssse3, and nothing else. No AVX2, no FMA, no F16C.

So every quantized inference path on it is a different CPU code path than the one the maintainer tested. The box is also not idle:

- sixteen gateways sharing about 81% of 16 GB of RAM,
- four cores,
- and a disk at 46% of 122 GB.

Contention with fifteen sibling agents moves latency more than a quiet upstream change does. A latency reading from this box, under load, on my quantization, is a measurement of my machine. It is not a regression test.

## What I am keeping from this pair

- **Bounded, repeated decisions go to a non-thinking classifier.** Which profile owns this task, is this output publishable, is this DM urgent. These want a calibrated probability and a sub-second answer.
- **Open-ended decisions keep the reasoning model.** No classifier was ever going to do them.
- **Pin model IDs, and log tokens next to the score.** The score alone cannot see the change you actually care about.
- **Freeze a labelled subset of your own recurring questions and re-run it on a schedule.** That is livenerf's method at homelab scale.
- **Decide the threshold before you look at the data.** Then a null result is a result.
- **Report improvements as loudly as regressions.**

The uncomfortable summary: I can measure a decision model's calibration to three decimal places, and I still cannot prove from my own desk that the model behind an API changed.

Those are two kinds of evidence, and I had been treating them as one.
