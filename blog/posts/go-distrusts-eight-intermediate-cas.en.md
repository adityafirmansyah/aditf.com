---
title: When the Compiler Becomes a CA: Go's Emergency Distrust of Eight SPKIs
slug: go-distrusts-eight-intermediate-cas
date: 2026-10-20
excerpt: Eight eMudhra intermediates were revoked for key compromise on October 18. A day later Go shipped the only enforcement most backend services will ever receive.
tags: golang, security, pki, tls, devops
---

On October 18, 2026, the CCADB revocation log gained eight eMudhra intermediates marked `cACompromise`. Six chain up to emSign Root TLS CA - G3. The other two chain to emSign Root CS CA - G3. Between them they cover DV, OV and EV issuance.

The mitigation most backend engineers will actually receive came as a literal in the standard library. Go released go1.27.3 and go1.26.10 under CVE-2026-111943. Inside `crypto/x509` sits a map of eight SHA-256 SPKI hashes, plus a filter that drops any chain containing one of them.

Roland Shoemaker wrote the commit, tracked as issue 82345 and reviewed as CL 851047. It was backported through CL 851145 for Go 1.26 and CL 851165 for Go 1.27. The diff is 42 lines added against zero removed, spread over three files.

I wanted to know whether that list actually matches the CCADB record. So I pulled the eight values out of `verify.go` and recomputed the SPKI SHA-256 of every revoked certificate. Eight matches out of eight.

That is not a heuristic blocklist of suspicious issuers. Those eight certificates are pinned by public key.

## What the patch actually does

```go
// src/crypto/x509/verify.go
var distrustedSPKIHashes = map[string]struct{}{
	"ebed6475c2c2d80fcb199f3fe8dd6e6b3ce60b77eb15d4e42c3dec0c6f5b5105": {},
	"49dd353dc2b919a3770645117d0e60c16115e7d1bc259eefe734b00ea434fe5f": {},
	// ... six more entries, elided here
}

func containsDistrustedSPKIHash(chain []*Certificate) bool {
	for _, c := range chain {
		h := sha256.Sum256(c.RawSubjectPublicKeyInfo)
		if _, ok := distrustedSPKIHashes[hex.EncodeToString(h[:])]; ok {
			return true
		}
	}
	return false
}
```

Two details carry the weight. Rejection is keyed on the SPKI hash, so a reissued certificate with a fresh serial number is still caught as long as it reuses the compromised key pair. And the loop walks every certificate in the chain instead of only the leaf.

The call sites matter more than the map. `root_darwin.go` tests `containsDistrustedSPKIHash(chain[0])`. `root_windows.go` runs `slices.DeleteFunc(chains, containsDistrustedSPKIHash)`. Both run on a chain the OS already built, via `SecTrustCopyCertificateChain` and `CertGetCertificateChain`.

The platform hands back a chain it considers valid, and Go throws it away anyway.

## Revocation has been decorative for years

Every team operating an API runs the same availability math on OCSP, and the math always lands in the same place.

- **Hard-fail OCSP** turns a slow responder into an outage, so almost nobody ships it in front of production traffic.
- **Soft-fail OCSP** answers "good" whenever the check errors out. An attacker who controls the network path simply drops traffic to the responder's IP.
- **CRLs** arrive on the CA's publishing schedule, weigh more than most polling loops can justify, and are rarely fetched per connection.
- **Go's `x509.Verify`** does no network revocation lookup at all. It exposes `OCSPServer` on the certificate and a response parser, then leaves the decision to you.

That is a defensible engineering trade. It also has a structural consequence: a revoked intermediate keeps signing working leaf certificates until something outside your process decides otherwise. When nothing decides otherwise, the compromise is invisible to every client that trusts the parent root.

## The OS bundle was never a blocklist

I ran the check on the machine I wrote this on. `/etc/ssl/certs/ca-certificates.crt` holds 121 certificates in 178 KB, and every one of them is a root trust anchor.

Root anchors are exactly the layer that was not compromised. The eight certificates here are intermediates, signed by emSign roots that remain trusted. A refreshed root bundle cannot express the sentence "this intermediate is bad", because the bundle has no vocabulary for intermediates at all.

Windows and macOS keep their own intermediate revocation data, which is the part of the ecosystem Linux servers simply do not have. Even there, the Go patch still had to drop chains by hand. Whether those platform stores would have caught these eight is a question nobody had to answer.

## Recompiling is the actual invoice

In a statically linked binary, chain validation is whatever `crypto/x509` code you compiled against. Updating the host's `ca-certificates` package changes which roots get loaded at runtime, and that is where the benefit stops. It cannot revoke an intermediate, and it cannot touch a hash list compiled into your binary.

```bash
# which toolchain built the thing that is actually running?
go version -m ./service | grep goversion

# the same question for every binary in an image
for b in /app/bin/*; do go version -m "$b" | head -2; done
```

Anything built on go1.27.2, go1.26.9 or earlier needs a rebuild and a redeploy before the filter exists in its process. Not a restart. A rebuild, followed by a redeploy of every image that carries a Go binary making outbound TLS connections.

## What I would do this week

- Read `go version -m` on the deployed artifact rather than trusting `go.mod` in the repository.
- Subscribe to golang-announce and treat toolchain patch releases as a security channel, because that is what they are.
- Inventory outbound TLS calls: which of your services terminate at third-party endpoints whose chains could contain a freshly revoked intermediate?
- For services you cannot rebuild quickly, terminate TLS in a proxy you can reconfigure without touching the binary.
- Watch the CCADB public revocation log directly. It reported this on October 18, before any release note existed.

Certificate automation buys less insulation than platform teams assume. ACME rotation replaces your own leaf, and it does that well. `cpach` on the Hacker News thread pointed at ACME with ARI (RFC 9773), where the CA tells the client that a replacement is due, as the client-side answer to this class of event. None of it removes a compromised intermediate from someone else's chain.

The thread also produced the sharpest joke of the week. `accountrequired` called it a `"Sir, this is a Wendy's" moment where my compiler thought it was a root certificate authority`. `TheDong` corrected the framing: the certificates live in the standard library's TLS packages, not in the compiler, and Go ships both in one release.

Fine, and the operational result is identical. A toolchain upgrade is a certificate policy change.

The uncomfortable part is not that Go hardcoded eight hashes. It is that a language toolchain was the last place this could be enforced at all.

The trust root of a Go service is not a file you configure. It is a commit baked into every binary you have already shipped, and it only refreshes when you rebuild. That used to be a philosophical point about supply chains. Now it is a line in `verify.go` with a hash in it.
