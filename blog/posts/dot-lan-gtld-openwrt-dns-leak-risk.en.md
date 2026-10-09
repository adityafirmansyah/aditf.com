---
title: "Someone Applied for .lan: Why OpenWrt and Homelab DNS May Leak"
slug: dot-lan-gtld-openwrt-dns-leak-risk
date: 2026-10-09
excerpt: ICANN's 2026 gTLD round includes a live application for .lan, the domain OpenWrt has hardcoded as a router default for two decades. Here's what that means for every homelab using it.
tags: dns, networking, homelab, self-hosting, security
---

## Someone applied to own the thing your router already assumes is yours

On October 7, 2026, ICANN published this year's new gTLD applications. One of them is for `.lan`.

Application CD2694T-T26351, filed by Coffee Danger, LLC, is now in pre-evaluation. If it clears, `.lan` becomes a live, resolvable, purchasable top-level domain in the public DNS root.

Not a convention. Not a default. An actual zone someone else owns.

I run a Celeron J4105 box behind Biznet fiber CGNAT, a Caddy reverse proxy in front of it, and `nas.lan` typed into my phone more times a day than I'd like to admit. So do a few million other people, mostly without knowing it.

## `.lan` was never reserved. It was just everywhere.

Here's the part that makes this different from a normal gTLD land grab: `.lan` was never supposed to work this way, and nobody ever made it official.

OpenWrt's `dnsmasq` config has shipped `option domain 'lan'` and `option local '/lan/'` since the project's early days. I checked the current `dhcp.conf` directly — both lines are still there. DD-WRT and GL.iNet travel routers inherited the same convention. Two decades of hardware defaults, with zero reservation behind any of it.

Compare that to the domains that actually went through a standards process:

- `.local` was reserved for multicast DNS by RFC 6762, specifically so link-local discovery wouldn't collide with the public root.
- `home.arpa` was proposed by RFC 8375 as the "correct" residential naming suffix.
- `.internal` was reserved outright by ICANN's own board, in a resolution passed July 29, 2024.

`.lan` has none of that protection, despite being the one practitioners actually adopted. The HN thread covering this (116 points, 140 comments) spends a lot of its length on exactly that irony. Standards bodies protected the names nobody uses by default, and left the one everybody uses by default completely open.

## Why `home.arpa` lost even though it won on paper

`home.arpa` is nine characters. `.lan` is three. That gap sounds trivial until you've typed `plex.home.arpa` into a URL bar at 11pm instead of `plex.lan`.

RFC 6762 locked `.local` into mDNS exclusively, which means a bare `.local` unicast lookup can sit waiting for a multicast response that's never coming — a timeout, not an error, which is worse. `home.arpa` dodged that specific trap, but it inherited a different problem: nobody wants to type it, so almost nobody did. ICANN's `.internal` reservation came even later, in 2024, by which point `.lan` had a 20-year head start nobody was going to undo by publishing a cleaner alternative.

Standards didn't lose on security grounds. They lost on ergonomics, years before anyone thought to ask ICANN to just reserve the string everyone already used.

## The leak isn't hypothetical, it's structural

Every device that roams off your home network carries its DNS search domain with it, at least until something resets it. A laptop that suspends on your home Wi-Fi and wakes up on a hotel network, or a hotspot, will still fire off a query for `nas.lan` or `router.lan` before anything corrects it.

Right now those queries hit a public recursive resolver, get an NXDOMAIN, and die quietly. If `.lan` gets delegated, those same queries resolve to whatever Coffee Danger's registry decides to put there. A phone leaking `plex.lan` isn't leaking a web request. It's often leaking a cookie, a session token, or an auth header meant for a server that only exists inside your house.

`dnsmasq`'s `bogus-priv` flag blocks reverse lookups for RFC 1918 address space, and its rebind protection stops an external domain from resolving to an internal IP. Neither does anything for a `.lan` query made from outside your network entirely, which is exactly the scenario a roaming device creates every single day.

## We already ran this experiment, with `.dev`

Google acquired `.dev` in 2014, and nothing happened for three years because nothing was delegated yet. Then Chromium shipped HSTS preloading across the entire TLD in 2017.

Every local dev environment that had quietly assumed `myapp.dev` would never resolve on the public internet broke, all at once. `.dev` is a real domain now, and Chrome enforces HTTPS on all of it unconditionally. GitHub issues from that era for Pow and Laravel Valet are still open as a record of exactly how many setups depended on an assumption nobody had checked.

`.lan` is `.dev` with a two-decade head start and a less security-conscious user base. Homelab operators are not reading ICANN's name-collision risk assessments.

## The fix isn't a convention, it's a domain you actually own

A private TLD only stays private until someone files the paperwork to make it public. That's true of `.lan` today, and it would've been just as true of `home.arpa` or `.internal` if practitioners had adopted either one first.

The durable fix is split-horizon DNS on a domain you actually hold a registration for. On my own setup, that's `*.internal.aditf.com`:

- Internal resolvers answer `internal.aditf.com` queries with private RFC 1918 addresses, never touching the public internet.
- External resolvers see nothing for that subdomain, or a response that intentionally doesn't resolve.
- Let's Encrypt issues real certificates against the public zone, so internal services still get valid TLS without a self-signed warning.

No gTLD applicant can ever buy a string out from under a domain you already registered. That's the entire point.

## What to actually do about it this week

Don't wait for the pre-evaluation result. If your router's search domain is `.lan`, you're exposed to the same collision risk whether or not Coffee Danger's application ultimately clears.

Move your internal hostnames onto a subdomain of something you own, point your internal DNS resolver at it, and automate certificates against the real zone. It costs a few dollars a year and an afternoon of `dnsmasq` config. The alternative is finding out your NAS credentials leaked to a stranger's registry the hard way.
