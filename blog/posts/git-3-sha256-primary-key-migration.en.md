---
title: Git 3.0's SHA-256 Default Is a Primary-Key Migration
slug: git-3-sha256-primary-key-migration
date: 2026-10-02
excerpt: I created a SHA-256 repository with the git I already have. Two of three daily operations failed outright, and the third is documented to die on older clients. The hash is not the migration; the key is.
tags: git, developer-tooling, migrations, version-control, storage
---

## The fight is about the hash. The bill is about the key.

Scott Chacon's "Git 3.0's upcoming SHA-256 default will be a costly mistake" is on the Hacker News front page right now. It sits at 364 points and about 350 comments, and most of that thread is arguing about hash functions. That is not where the money is.

I agree with the article on cost and disagree with the drama. SHA-256 is the right hash, and it should be the default eventually. But the expensive part is not cryptographic.

A commit hash stopped being an internal identifier years ago. It is a primary key, with foreign keys scattered across forge APIs, CI configs, release scripts, permalinks and Slack threads. When the key is also the public interface, changing it is not an index migration. It is an ecosystem migration.

I did not want to argue that from a reading of the post, so I spent a minute in a shell instead. The git here is 2.53.0, and it is enough.

## One minute of shell, most of the argument

Create a SHA-256 repository and name a commit:

```bash
git init --object-format=sha256 s256
cd s256 && echo hi > a.txt && git add a.txt && git commit -m first

git rev-parse HEAD
# 5a14a64b8b6e5d545d946d1284b5f422502e8af6fcfde892185d7e6cb1f30e4b
git rev-parse --short HEAD
# 5a14a64
```

That full name is 64 hex characters. A SHA-1 repository on this same box names its commit with 40. The short form is seven characters either way, so `--short` output survives the change and the full name does not.

Then do the three things I do with a repository every day.

- **Push it.** To a bare repo created with `git init --bare --object-format=sha256`, the push succeeds. To a plain `git init --bare`, it dies with exit 128 and `fatal: the receiving end does not support this repository's hash algorithm`.
- **Push it across formats.** A SHA-256 repository pushing to a SHA-1 bare repo fails the same way, exit 128, with `fatal: the remote end hung up unexpectedly` on top.
- **Submodule it.** Adding the SHA-256 repository as a submodule of a SHA-1 superproject fails with `error: cannot add a submodule of a different hash algorithm`.

Two of the three fail outright, in one sitting. Note what the first one means: the receiving repo has to know the hash format at `init` time. You cannot push a SHA-256 repository into a repository that already exists in SHA-1, because the format is not a property of the objects. It is a property of the repository.

## The one-way door is the format version

A SHA-256 repository writes two lines into `.git/config`:

```
[core]
	repositoryformatversion = 1
[extensions]
	objectformat = sha256
```

The transition document is explicit about why those lines exist. Setting them makes every Git later than v0.99.9l "die instead of trying to operate on the SHA-256 repository," in the doc's own words.

Between v0.99.9l and v2.7.0 the error is `fatal: Expected git repo version <= 0, found 1`. After v2.7.0 it becomes `fatal: unknown repository extensions found: objectformat compatobjectformat`. Either way it stops.

That is not a feature flag a team flips on its own schedule. An older client cannot read the repository at all, which puts every consumer on one side of a line or the other.

## The document already answered half the thread

Chacon's "you can't push it anywhere" reads as a bug report in the thread. The transition doc frames it as the interim state, and it describes the bridge in some detail.

The workaround is a bidirectional mapping table between SHA-256 and SHA-1 object names, generated locally and verified with `git fsck`, plus the `extensions.compatObjectFormat` setting. Objects can be named by either their 40-character or 64-character name. Fetches from a SHA-1 server convert into SHA-256 form and record the mapping. Pushes to a SHA-1 server convert on the way out, so the server never learns which hash the client uses.

What the same document lists as out of scope is the part the thread skips:

- intermixing objects that use multiple hash functions in a single repository;
- shallow clones and fetches into a SHA-256 repository;
- skipping the fetch of some submodules;
- borrowing objects from a SHA-1 repository through `objects/info/alternates`;
- migrating `git notes` trees to SHA-256 names;
- SHA-256 support in the Git protocol itself.

So the disagreement is not whether an interim state exists. It is what the interim state costs, and the doc ends that section bluntly: "Until Git protocol gains SHA-256 support, using SHA-256 based storage on public-facing Git servers is strongly discouraged."

## What actually breaks, and it is not the hash function

Chacon's cost list is the concrete one. Read it as an inventory of interface sites, not as a scare story.

- Every forge repository lands in one bucket or the other, and the two cannot be mixed.
- Submodules require both sides to match, as the third command above demonstrated.
- Converting an existing project rehashes every object and invalidates every existing signature.
- Permalinks carrying full hashes in Slack, emails and docs stop resolving.
- Any tooling that expects 40 characters for a hash has to guess or detect the format.

That last one is his sentence, and my own box is a small sample of it. Ten repositories, all SHA-1, none carrying an `objectformat` key in `.git/config`. On Git 3.0 day each of them becomes a decision, and every script, hook and integration that parses a hash becomes part of that decision.

## The counter-arguments, by name

`ltbarcly3` calls it "Y2K fud" and makes the strongest case for the other side. Leave SHA-1 as the default until it is critical, and everyone switches on the same afternoon. Forges that were never forced to implement SHA-256 end up in that scramble.

`plorkyeran` points out the forge problem is a choice about implementation, not a property of hashes. `GrantMoyer` links the transition doc and notes several of the author's reservations are already addressed. `gorgoiler` notices the same thing from the other direction: the bidirectional mapping is exactly the interoperability the post says is missing.

On the trust side, `Strilanc` rejects the framing outright. `mort96` walks through the mirror and tooling case: "I deal with things which reference commits by hash in repos all the damn time. There are thousands of them in every Yocto project!"

## The proposal the thread walked past

The constructive half of the post is an independently signed tree hash. Rehash the tree contents with a second algorithm and sign both, so SHA-1 keeps serving content retrieval while the second hash carries verification.

Colin Walters' git-evtag has done this since 2015, adding a `Git-EVTag-v0-SHA512` checksum over the commit, tree and every blob to the tag before signing it.

`SmasherEpilepti` said it best in the thread: "It's probably the most interesting part of the article, but it's getting the least attention."

Linus made the same argument in 2005: the real security is in distribution, not in the hash.

## Same shape, a different store

The other front-page story from the same day is turbopuffer's "RIP, vector database." It is the same lesson written from the index side. Their v1 and v2 stored every document under its ANN address, so when SPFresh rebalanced the vectors, the whole document moved with them. Updating one vector could move hundreds of attributes and their indexes.

v3's fix is stated flatly: don't key on the ANN address. The ANN index becomes just another secondary index. Their full-text postings went from a median of about 1.5 entries per block to fixed blocks of roughly 256, and the index got ten times smaller while queries got up to twenty times faster.

The scale makes the point about cost: 1T+ documents, 10M+ writes per second, 25k+ queries per second, single indexes of 100B+ vectors serving 200 ms p99 reads at 1k+ QPS. That is the receipt for what an unchosen key costs when it has quietly become the interface.

## What I would do before Git 3.0 day

The takeaway is not "avoid SHA-256," and it is not "wait for someone else to decide." It is that your hash-format assumptions are now inventory, so write them down.

- Run the reproduction above, in a throwaway directory, on the git you actually use.
- Grep the pipeline for 40-character hash assumptions and for code that shortens or compares hashes.
- Check `git config --get extensions.objectformat` across your repositories and record which format each one is.
- Ask which of your consumers cannot be updated on your schedule, because those are the ones the `repositoryformatversion = 1` line locks out.

A hash function is a one-line change in a config. The key built on it is the interface a decade of tooling grew around. Migrating the second one is the bill, and the smart move is to know the size of it before the default flips underneath you.
