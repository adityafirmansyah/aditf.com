---
title: "Reproducing the .git Hook Attack: git status Runs an Attacker's Command"
slug: reproducing-the-git-hook-attack
date: 2026-10-05
excerpt: Frank Wiles got a fake project inquiry, a Dropbox folder of specs, and a hidden .git with a post-checkout hook. I reproduced both vectors on git 2.53.0, and the popular fix is overridable.
tags: git, security, ai-agents, supply-chain, devtools
---

## The ask was a payload

Frank Wiles got an inquiry that looked like every other one he receives. An Ed Tech company wanted a web app built, asked him to sign an NDA before the call, and shared the specs in a Dropbox folder. So he opened the folder.

Inside, the "client" had left a note: the NDA was in the NDA branch, and he just needed to switch to it. That instruction is the entire attack. Switching branches means running `git checkout`, and `git checkout` runs code.

The write-up he published afterwards is now the top item on lobste.rs, with 129 points and 39 comments.

This is not a story about one careless contractor. Most developers read `git checkout` as a harmless lookup, and it can execute code on their machine instead.

## What ran when he switched branches

Wiles missed the `.git` directory sitting in the Dropbox folder, and that directory is where the attack lived. Inside it was a `post-checkout` hook wired to a Vercel app for command and control. In his words, it would "download an OS specific binary," run it, and delete itself.

He alerted Dropbox and Vercel's security teams afterwards. He suspects the goal was his GitHub account and the client access that came with it.

Nothing here is a git bug, and the docs say so outright. `post-checkout` "is invoked when a git-checkout or git-switch is run after having updated the worktree." A file in `.git/hooks/` is executable code that git will run for you.

## Repro 1: a checkout runs the hook

I wanted to know how much of this still holds on a current git, so I rebuilt it from scratch. One repository, one branch, one hook that logs its arguments:

```sh
# .git/hooks/post-checkout
#!/bin/sh
echo "ran: args=$# prev=$1 new=$2 flag=$3" >> hook.log
```

Then I ran the exact step the attacker asked for:

```
$ git checkout nda
Switched to branch 'nda'
$ cat hook.log
ran: args=3 prev=3dfc32704f4b... new=3dfc32704f4b... flag=1
```

It ran on git 2.53.0, and it passed three arguments exactly as the docs describe: the previous HEAD, the new HEAD, and the branch-checkout flag.

The important part is what you cannot see. `git status` stayed clean, and `git ls-files` listed only `README.md`. The hook lives inside `.git`, so it never appears in a diff, a review, or a directory listing.

## Repro 2: git status runs your config

A hook needs you to check out a branch first. The top comment in the lobste.rs thread describes a vector that needs nothing from you at all. User agwa wrote about shipping a `.git/config` with `core.fsmonitor` set to a command, which then runs on "very basic ones like `git status`."

I tested that too. I pointed a script path in `.git/config` and ran a plain status:

```
$ git config core.fsmonitor /path/to/fsmon.sh
$ git status
$ cat fs.log
FSMONITOR EXECUTED args=2 1791180551388075699
```

This is the worse vector, because `git status` is a command your editor, your build, and your agent run without thinking. agwa's list is blunt: IDEs, `go build`, and shell prompt integrations all run it implicitly.

The docs explain why a pathname is dangerous here. `core.fsmonitor` "was extended to allow boolean values in addition to hook pathnames," so a path is treated as a command. Older clients can even misread `true` as one.

## Why clones are safe and a Dropbox folder is not

One distinction decides whether you are exposed, and it is narrower than most people assume. git refuses to put a `.git/` path into a tree at all. I tried the plumbing route to confirm that:

```
$ git update-index --add --cacheinfo 100755,<blob>,.git/hooks/post-checkout
error: Invalid path '.git/hooks/post-checkout'
fatal: git update-index: --cacheinfo cannot add .git/hooks/post-checkout
```

A plain `git add` of the same path does nothing at all, and it does not even warn you. So a hook cannot ride along in a commit. When I cloned my booby-trapped repo fresh, it carried only the `*.sample` files, and a checkout there ran nothing.

agwa puts the line where the git project puts it: cloning "is in fact the only safe way to get a repo from an untrusted source." A malicious clone counts as a vulnerability in git. A malicious tarball is your own problem.

That leaves three cases:

- **Clone from a URL.** git checks it out for you, safely.
- **Extract a zip or tarball.** The `.git` is already inside. This is the hostile path.
- **Open a folder someone shared.** The Wiles case. No clone, no checks.

z3bra ran into the same wall from the other direction. A clone of a repo that tried to ship `.git/hooks/post-checkout` died with `fatal: unable to checkout working tree`. vifon adds one exception worth knowing: a real `git bundle` is safe, because cloning from it will not check those files out.

## The mitigation everyone posted is overridable

The most-upvoted fix was arialdo's, which disables hooks globally with `git config --global core.hooksPath /dev/null`.

That is a good instinct, but it does not hold. oger predicted the hole, and I reproduced it. With that global setting in place, the hook stayed silent. Then I added one repo-local line:

```
[core]
    hooksPath = .git/hooks
```

The hook ran again, because repo config beats global config, and a hostile repo can re-arm itself.

What does hold is the per-command form, since command-line config is applied last:

```
$ git -c core.hooksPath=/dev/null checkout nda
$ git -c core.fsmonitor=false status
```

Both forms suppressed execution against the hostile repo. The git-config docs endorse them directly, writing the parameter as `git -c core.hooksPath=/dev/null`.

## Why agents are the softer target

I run a 17-profile agent fleet. The coding, QA, and PR-review agents clone repositories and run `git status` and `git checkout` unattended, with their git credentials sitting in the environment. That is exactly what the attacker was after: access to an account and the clients attached to it.

The attack fits an agent better than a human, because an agent is often handed a repo as a folder or a tarball rather than a clone. It runs `git status` constantly, and nothing in its context is looking for a `.git` directory.

The hardening that follows is short:

- **Clone, never copy.** If you must move a repo, clone it and delete the source.
- **Inject the two flags.** Put `-c core.hooksPath=/dev/null -c core.fsmonitor=false` in the agent's git wrapper.
- **Sandbox the credentials.** Run agent git in a container with scoped, short-lived tokens.
- **Inspect before the first command.** Check `.git/hooks` and `.git/config` on any repo a third party supplied.

loldot's line in the thread is the right default: "I just consider everything project someone sends me as a malicious." benoliver999 notes the same shape shows up in take-home interview bundles that ship a `.git`.

## The takeaway

`git checkout` is not a read. It can run a program, and it wears an interface that makes it look like it only reads. `git status` can do the same.

The fix is not a clever global flag, because a repository can fight you for control of its own config. Clone what you do not trust and copy nothing, and when someone tells you the NDA is on a branch, ask why they need you to run the checkout yourself.
