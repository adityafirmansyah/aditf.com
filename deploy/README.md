# Deploy infra for aditf.com

This directory is **infrastructure-as-code**. It is denylisted from the public
payload, so nothing here is ever served from the webroot.

## post-receive

The real deploy mechanism. `git push vps main` triggers it on the VPS:

    archive the commit tree -> /var/www/aditf.com -> nginx -t -> systemctl reload nginx

GitHub (`origin`) is a **mirror only** — pushing there deploys nothing.

### Install / update

The hook on the VPS is a plain file; it is not deployed by itself. After
changing `deploy/post-receive`, install it:

```bash
ssh aditf@103.193.178.152 '
  cp /opt/aditf.git/hooks/post-receive \
     /opt/aditf.git/hooks/post-receive.bak-$(date +%Y%m%d-%H%M%S) 2>/dev/null || true
  cat > /opt/aditf.git/hooks/post-receive && chmod +x /opt/aditf.git/hooks/post-receive
' < deploy/post-receive
```

Then verify with a no-op deploy (re-pushes current `main`, changing nothing):

```bash
git push vps main        # expect "[deploy] Done. Live at https://aditf.com"
```

### Why paths are tree-derived

The hook used to keep an explicit allowlist of extra top-level paths. Anything
not listed was silently never deployed — which is exactly how `sitemap.xml`
froze after it was first added, and it would have dropped `favicon.ico` and
`favicon.svg` too. Deriving the list from the pushed commit's own tree means a
new top-level file ships the moment it is committed, and `git archive` can
never fail on a path that isn't in the tree.

The denylist (`.gitignore`, `deploy`) keeps repo metadata and this directory out
of the webroot. A tree containing only denylisted paths aborts loudly rather
than deploying nothing silently.

### Sequencing rule

**Install the hook before merging a PR that adds a new top-level file.** The
running hook is what archives the pushed commit, so an old allowlist hook will
drop new files even after the code is merged.

### Deletions

`tar -x` only adds and overwrites; it never prunes. A file removed from the
repo lingers in the webroot. That is deliberate — an `rsync --delete` here
could remove certbot- or nginx-managed paths. Delete leftovers by hand:

```bash
ssh aditf@103.193.178.152 'rm /var/www/aditf.com/<path>'
```

## Testing locally

`post-receive` can be tested without a VPS by cloning a bare repo, rewriting
`DEPLOY_DIR`/`GIT_DIR` with `sed`, and stubbing `sudo` on `PATH`. Verify:
payload deploys, denylist holds, **historical** pre-blog commits still deploy,
a deny-only tree aborts without touching nginx, and `nginx -t` runs before
reload. Truncate the stub's call log immediately before each invocation or a
previous test's entries produce a false failure.
