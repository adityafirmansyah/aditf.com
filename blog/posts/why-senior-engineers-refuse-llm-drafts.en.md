---
title: Martin Fowler on LLM Voice: Why Senior Engineers Refuse AI Drafts
slug: why-senior-engineers-refuse-llm-drafts
date: 2026-10-30
excerpt: Martin Fowler warned that LLM drafts trap writers in an uncanny valley you cannot edit out. Here is why the fix is architectural separation, not abandoning AI tools.
tags: ai tooling, software engineering, technical writing, llms, developer experience
---

Martin Fowler published an essay on October 29, 2026, titled "LLM Voice". His thesis was simple: never use a Large Language Model (LLM) to write your first draft. When an automated tool generates the initial text, the resulting prose lands in an uncanny valley.

Fowler pointed out that AI prose induces visceral reader fatigue. The rhythm feels deceptively smooth. Yet the substance atrophies to the point of revulsion. Even aggressive manual rewriting struggles to wash out that polite, predictable cadence.

I recognize that feeling immediately. It kills trust. After 13 years of shipping production code and writing engineering architecture specs, technical credibility is the hardest asset to earn. It is also the easiest to burn.

When readers sense a machine faking conviction, they close the tab. Fowler's remedy, however, stops short. He suggests abandoning AI drafting altogether.

I disagree. The real fix is architectural. You do not throw away the engine. You simply change where you place the boundaries.

## The Linguistics of Alignment Slop

On Hacker News (HN) thread 50290177, developers debated why AI text feels so exhausting. The discussion cited empirical linguistics research from arXiv:2410.16107 on grammatical and rhetorical styles.

The research paper demonstrates that stylistic uniformity is not an accident of raw web pretraining. Instead, the collapse happens during post-training. Supervised Fine-Tuning (SFT) and preference alignment algorithms systematically flatten rhetorical variation across models.

Techniques like Reinforcement Learning from Human Feedback (RLHF) and Direct Preference Optimization (DPO) penalize sharp edges. To maximize safety scores and avoid offending users, the model adopts defensive habits:

- It balances every declarative assertion with unprompted disclaimers.
- It pads transitions with sycophantic, polite phrases.
- It forces paragraphs into symmetrical structures.
- It replaces concrete engineering trade-offs with generic platitudes.

The model writes like an anxious corporate spokesperson. It plays defense. When you ask it for a technical draft, it strips out the friction that makes engineering writing trustworthy.

## The Ptacek Rule for Adversarial Review

Security practitioner Thomas Ptacek proposed a clean operational rule for using language models in technical work. His rule is strict: use the model as an adversarial critic, never as a copywriter.

Models excel at spotting logical gaps. You can paste an architectural spec into the prompt and issue explicit diagnostic directives:

- Point out any failure modes this design overlooked.
- List the operational prerequisites the document failed to explain.
- Identify where the technical argument jumps to an unearned conclusion.
- Flag edge cases that break this database migration.

Notice the restraint in those directives. You never ask the model how to rephrase the sentence. You explicitly instruct it not to offer text suggestions.

The moment you let an LLM rewrite your paragraphs, its symmetrical cadence infects your voice. The critique belongs to the machine. The prose must remain yours.

## Decoupling Research from Drafting in Production

In our autonomous multi-agent pipeline at Field Notes, we run daily publishing workflows with a fleet of Hermes agents. We also maintain production multi-tenant systems at Dagango.com.

We faced Fowler's exact dilemma early on. When you give a model a loose prompt and ask it to write an article, it produces unreadable fluff.

Our solution was total decoupling between research and drafting. We split the responsibilities across three isolated agent roles:

- **Research Agent**: Collects raw data and verifies Hypertext Transfer Protocol (HTTP) 200 response codes on all primary sources. It cannot write prose.
- **Drafting Agent**: Takes the structured brief and authors the text under strict negative styling constraints and hard length caps.
- **Auditor Agent**: Runs deterministic code to check sentence lengths and count commas.

Here is what that pipeline looks like in practice:

```text
[Primary Sources] ──> (Researcher) ──> [Structured Brief (Facts Only)]
                                              │
                                              ▼
                                     (Typewriter Agent)
                                              │
                                              ▼
[Audit Passes]   <── (Auditor Linter) <── [Raw Draft]
       │                      │
       ▼                      ▼
  [Publish PR]         [Numbered Rejection]
```

The research stage produces only verifiable facts like benchmark numbers or repository commits. Because the researcher generates no narrative text, the drafting stage has no pre-existing AI cadence to inherit.

## Negative Constraints and Register as Firewalls

Drafting tools need strict negative constraints. Positive instructions like "write engagingly" only trigger more sycophantic behavior. You protect voice by defining what the generator cannot do.

We enforce mechanical limits that break the default assistant rhythm:

- Hard cap of 35 words per sentence.
- Maximum of three commas per sentence to eliminate clause stuffing.
- Automatic conversion of any two-item enumeration into a bulleted list.
- Explicit bans on bloated vocabulary and corporate transition markers.

This defense becomes even more critical in bilingual technical environments. When prompted in Indonesian, generic models default to stiff bureaucratic phrasing. They lean heavily on formal copulas like `adalah` and `merupakan`.

To defeat that drift, we enforce a native casual Indonesian register using *gue* and *lo*. We keep natural engineering loanwords like *deploy*, *runner*, and *pipeline*.

We never translate English drafts sentence by sentence. We author the Indonesian version fresh from the core technical point. That preserves the practitioner voice across both languages.

## The Senior Engineer's Takeaway

Martin Fowler is right about the threat. If you lean on language models to draft your thoughts, you will sound like every other automated blog on the internet.

You do not have to unplug the tools. You just have to treat them like untrusted external dependencies. Here is the operational checklist for your next technical document:

1. **Gather facts first**: Use automated tools to verify external links and extract metrics before writing narrative text.
2. **Enforce adversarial review**: Ask the model to poke holes in your logic or flag missing edge cases, with a strict ban on suggested phrasing.
3. **Draft with hard structural gates**: Write your own prose, or bind generation to strict negative constraints that forbid corporate filler and comma-heavy sentences.

Your readers do not want polished corporate neutrality. They read your work for the scar tissue and real production numbers. They want your unfiltered architectural opinions. Keep those human.
