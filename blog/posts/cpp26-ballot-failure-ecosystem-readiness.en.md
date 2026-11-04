---
title: What a Failed C++26 Ballot Says About Shipping to an Ecosystem
slug: cpp26-ballot-failure-ecosystem-readiness
date: 2026-11-04
excerpt: C++26's draft standard was reported disapproved in its ISO ballot over contracts. The useful question is what separates a feature that passes every internal gate from one an ecosystem can safely depend on.
tags: cpp, software-engineering, standards, systems-design, release-engineering
---

The C++26 draft standard was reported disapproved in its ISO ballot in late October 2026, after a twelve-week vote. By the account of one committee member, that outcome is close to unprecedented.

I do not sit in WG21, the ISO working group that develops the C++ standard. Whether contract assertions belong in the language is not my argument.

What interests me is the shape of the failure. A feature cleared every gate its own community controls, then failed at the one gate where outsiders hold votes.

That is a shipping problem before it is a language problem, and it is one platform teams meet constantly without the luxury of a twelve-week comment period.

## What the record actually says

The arithmetic matters here, so take it slowly. Approval needed two thirds of the participating-member (P-member) votes in favour and at most a quarter against. The draft got neither:

- 12 of 20 P-member votes in favour, against the 14 that two thirds requires.
- 9 of 22 votes negative, against the 5 that a quarter allows.

Either shortfall fails the draft on its own. The denominators differ because the 22 counts observer-member votes too. Mateusz Pusz counts eight of those nine negatives as coming from P-members. The rest includes Iran, an observer member.

No official ISO record is public. The tally comes from a LinkedIn post by Robert Seacord and a 25 October article by Pusz, and the wro.cpp writeup collecting both marks every number as reported rather than confirmed. The disapproval itself is solid. The arithmetic behind it is second-hand.

That gap deserves a second look. A process that decides the fate of a language ended up with its own vote count circulating as hearsay, and the national bodies' comments stay unpublished.

The argument traveled anyway. By 4 November the story sat on the Hacker News front page at 174 points and 74 comments.

The thread could not agree on what the objection really was. Some read it as technical. Others called it procedural or political.

Andreas Fertig, who represents Germany's vote on the committee, says he searched the ISO system and found one other disapproved DIS, or Draft International Standard: the C++/CLI language specification from 2006. That project was halted.

## The gate nobody in the room can vote at

The committee voted the draft forward in March 2026 with contracts included, by more than the majority it needed. Months later the national bodies voted no on the same text.

Same artifact, different electorate. The people who spent years on the design had no vote at the gate that decided it.

Fertig's reading is that a number of national bodies believe the feature is not ready for release. He also argues the objecting papers restate old arguments rather than adding information.

That distinction carries real weight. If you have already heard an objection and rejected it, hearing it again should not reset the decision. If you have not heard it, it should.

The technical file is harder to wave away. WG21 papers are numbered proposals, and P4334R0 carries Stroustrup among its signatories. It indicts the contracts design on three counts:

- unimplemented,
- incomplete,
- untried at scale.

Pusz adds that contract assertions on GCC 16 rest on an experimental implementation of the disputed part.

Read those two together and you get the exact state the ballot rejected. Shipped far enough to try. Not settled enough to depend on.

## Every recovery path costs a cycle

The ISO directives quoted in P4388R0 leave four routes:

- another eight-week ballot on a revised draft,
- a revised committee draft for comments,
- a draft Technical Specification,
- cancellation of the project.

All four need a recommendation from WG21 and a decision by the SC22 chair. SC22 is the ISO subcommittee that covers programming languages. So there is no fast compromise on demand. WG21 next meets in Búzios from 16 to 21 November.

Then there is the clock. The project was registered on 2 January 2025, and an ISO project that has not reached approval after 36 months is cancelled automatically. P4388R0 reads the single permitted extension as leaving until the end of 2027.

None of the four routes is a rollback. Each one spends time the project does not get back.

## The same wall inside a commerce platform

On Dagango.com the dangerous change is rarely the hard one to write. It is the easy one that lands on a shared surface tenant integrations already consume.

A pricing invariant is a decent example of the shape. The code is a few lines. The meaning is a contract with every tenant whose invoices read from it.

Three questions decide whether that change is ready:

- Who is allowed to rule on what happens when the invariant breaks for a tenant we have never met?
- Which consumers read this output, including the ones outside our repositories?
- What is the fallback path, and does rolling back require a data migration?

If any of those has no written answer, the change is available. It is not committed.

For that kind of change I want a flag file that is deliberately boring:

```yaml
pricing.invariants.enforce:
  default: off              # available to tenants, not committed to them
  enabled_for: [internal-smoke]
  on_violation: reject      # decided once, not left to each caller
  fallback: legacy_pricing_v2
```

Every line answers one of the three questions. The enforcement behaviour is written down instead of inherited from whoever wrote the caller.

If you already ship C++26 features, Pusz's practical note is worth repeating. Nothing needs undoing yet, and the ballot does not change what compilers already ship.

## What maturity actually looks like

An approval rule that needs two thirds and caps opposition at a quarter is deliberate. It exists so a minority with a real objection can stop a release that everyone would otherwise have to live with.

That is an expensive rule, and the C++ community just paid for it. Fertig's own conclusion is that trust is what got shaken, and consensus runs on trust. I would broaden it. A gate that only holds while everyone already agrees was never doing work, in a language committee or in a commerce platform.
