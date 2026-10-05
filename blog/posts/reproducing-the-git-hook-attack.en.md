---
title: "Reproducing the .git Hook Attack: git status Runs an Attacker's Command"
slug: reproducing-the-git-hook-attack
date: 2026-10-05
excerpt: Frank Wiles got a fake project inquiry, a Dropbox folder of specs, and a hidden .git with a post-checkout hook. I reproduced both vectors on git 2.53.0, and the popular fix is overridable.
tags: git, security, ai-agents, supply-chain, devtools
---

## The ask was a payload

Frank Wiles got an inquiry that read like every other one. An Ed Tech web app, an NDA before the call, specs in a Dropbox folder. He opened the folder.

Then the "client" said the NDA was in the NDA branch, and he just needed to switch to it. That switch is `git checkout`. That is the entire attack.

The write-up is now the top item on lobste.rs, with 129 points and 39 comments.

This is not a story about one careless contractor. It is a story about a command every developer reads as harmless. We treat `git checkout` as a read. It runs code.

## What ran when he switched branches

Wiles missed the `.git` directory sitting in the Dropbox folder. Inside it was a `post-checkout` hook wired to a Vercel app for command and control. In his words, it would "download an OS specific binary," run it, and delete itself.

He alerted Dropbox and Vercel's security teams. He suspects the goal was his GitHub account and client access.

Nothing here is a git bug. The docs say it plainly. `post-checkout` "is invoked when a git-checkout or git-switch is run after having updated the worktree." A file in `.git/hooks/` is executable code git will run for you.

## Repro 1: a checkout runs the hook

I wanted to know how much of this holds on a current git, so I built it. One repo, one branch, one hook that logs its arguments:

```sh
# .git/hooks/post-checkout
#!/bin/sh
echo "ran: args=$# prev=$1 new=$2 flag=$3" >> hook.log
```

Then the exact step the attacker asked for:

```
$ git checkout nda
Switched to branch 'nda'
$ cat hook.log
ran: args=3 prev=3dfc32704f4b... new=3dfc32704f4b... flag=1
```

It ran on git 2.53.0. Three arguments, matching the docs: previous HEAD, new HEAD, and the branch-checkout flag.

The part that matters is what you cannot see. `git status` stayed clean. `git ls-files` listed only `README.md`. The hook lives inside `.git`, so it never shows up in a diff, a review, or a directory listing.

## Repro 2: git status runs your config

A hook needs you to check out a branch. The top comment in the lobste.rs thread needs nothing from you. User agwa described shipping a `.git/config` with `core.fsmonitor` set to a command. That command then runs on "very basic ones like `git status`."

I tested it. A script path in `.git/config`, then a plain status:

```
$ git config core.fsmonitor /path/to/fsmon.sh
$ git status
$ cat fs.log
FSMONITOR EXECUTED args=2 1791180551388075699
```

That is the worse vector. `git status` is what your editor, your build, and your agent run without thinking. agwa's list is blunt: IDEs, `go build`, and shell prompt integrations all run it implicitly.

The docs confirm why a pathname is dangerous. `core.fsmonitor` "was extended to allow boolean values in addition to hook pathnames." A path is a command, and older clients can misread even `true` as one.

## Why clones are safe and a Dropbox folder is not

Here is the distinction that decides whether you are exposed, and it is narrower than people assume. git will not put a `.git/` path in a tree. I tried the plumbing route:

```
$ git update-index --add --cacheinfo 100755,<blob>,.git/hooks/post-checkout
error: Invalid path '.git/hooks/post-checkout'
fatal: git update-index: --cacheinfo cannot add .git/hooks/post-checkout
```

A plain `git add` of that same path does nothing at all, silently. So a hook cannot ride in a commit. A fresh clone of my booby-trapped repo carried only `*.sample` files. A checkout there ran nothing.

agwa draws the line where the git project draws it. Cloning "is in fact the only safe way to get a repo from an untrusted source." A malicious clone counts as a vulnerability. A malicious tarball is your problem.

That gives three cases:

- **Clone from a URL.** git checks it out for you, safely.
- **Extract a zip or tarball.** The `.git` is already inside. This is the hostile path.
- **Open a folder someone shared.** The Wiles case. No clone, no checks.

z3bra in the thread hit the same wall from the other side. A clone of a repo that tried to ship `.git/hooks/post-checkout` died with `fatal: unable to checkout working tree`. vifon adds one exception worth knowing. A real `git bundle` is safe, because cloning from it will not check those files out.

## The mitigation everyone posted is overridable

The most-upvoted fix was arialdo's. Disable hooks globally with `git config --global core.hooksPath /dev/null`.

Good instinct, and it does not hold. oger predicted the hole, and I reproduced it. With that global setting in place, the hook stayed silent. Then one repo-local line:

```
[core]
    hooksPath = .git/hooks
```

The hook ran again. Repo config beats global config, so a hostile repo re-arms itself.

What holds is the per-command form. Command-line config is applied last:

```
$ git -c core.hooksPath=/dev/null checkout nda
$ git -c core.fsmonitor=false status
```

Both suppressed execution against the hostile repo. The git-config docs endorse the form directly, writing the parameter as `git -c core.hooksPath=/dev/null`.

## Why agents are the softer target

I run a 17-profile agent fleet. Coding, QA, and PR-review agents clone repositories and run `git status` and `git checkout` unattended, with their git credentials in the environment. That is exactly what the attacker wanted: access to an account and its clients.

The attack fits an agent better than a human. An agent is often handed a repo as a folder or a tarball, not a clone. It runs `git status` constantly. Nothing in its context is looking for a `.git` directory.

The hardening that follows is short:

- **Clone, never copy.** If you must move a repo, clone it and delete the source.
- **Inject the two flags.** Put `-c core.hooksPath=/dev/null -c core.fsmonitor=false` in the agent's git wrapper.
- **Sandbox the credentials.** Run agent git in a container with scoped, short-lived tokens.
- **Inspect before the first command.** Check `.git/hooks` and `.git/config` on any repo a third party supplied.

loldot's line in the thread is the right default: "I just consider everything project someone sends me as a malicious." benoliver999 notes the same shape shows up in take-home interview bundles that ship a `.git`.

## The takeaway

`git checkout` is not a read. It is a program loader with a familiar interface, and `git status` can be one too. The fix is not a clever global flag, because a repository can fight you for control of its own config.

Clone what you do not trust. Copy nothing. And when someone tells you the NDA is on a branch, ask why they need you to run a checkout.