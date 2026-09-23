---
title: Self-Hosting Behind CGNAT: A WireGuard Bridge That Actually Works
slug: self-hosting-behind-cgnat-wireguard-bridge
date: 2026-09-23
excerpt: Port forwarding stopped working and it wasn't your router's fault. Here's the outbound WireGuard tunnel pattern that gets a homelab back on the public internet under CGNAT.
tags: self-hosting, homelab, networking, wireguard, cgnat
---

Port forwarding stopped working and it wasn't your router's fault. Your ISP quietly moved you behind a second NAT layer you can't see, can't configure, and definitely can't port-forward through. This is CGNAT, and if you're running a homelab on Indonesian residential fiber, you've probably already hit it without knowing what it was called.

David Álvarez Rosa's writeup on self-hosting behind CGNAT went to #1 on lobste.rs this week, and the HN thread picked it up too, because the problem is structural and getting worse everywhere IPv4 addresses stay scarce. I run a Celeron J4105 box on Biznet fiber, and CGNAT is common enough on Indonesian ISPs that this isn't a hypothetical for most homelabbers here.

## Why your router can't fix this

Normal NAT happens once, at your router: your devices share one public IP, and port forwarding tells the router which internal machine gets traffic on a given port. CGNAT inserts a second, hidden NAT layer inside your ISP's own network, upstream of your router entirely. Your router's WAN address isn't public anymore; it's a private address, shared with a whole neighborhood of other customers on the same carrier-grade device. Port forwarding rules in your router's admin panel simply never fire, because the inbound packet never reaches your router to trigger them. There's no setting anywhere in your router that changes this. The packet dies upstream, in equipment you don't control and can't log into.

## The bridge: tunnel out, not in

The trick that works under CGNAT is to stop trying to accept inbound connections entirely. Your homelab instead opens an outbound WireGuard tunnel to a cheap VPS that has a real public IP, and once that tunnel is up, the VPS pushes traffic back down it. Outbound connections sail straight through CGNAT without issue, so routing everything through one already-open tunnel sidesteps the entire problem.

On the VPS side, iptables DNAT rules forward incoming traffic to the homelab's tunnel address. DNAT only rewrites the destination; the source address on each packet survives the trip, so your homelab still sees real client IPs in its logs instead of one flat address for every visitor. That matters the moment you need anything IP-based: rate limiting, geo-blocking, abuse tracking. Latency through a bridge like this measures at roughly 39ms of added round-trip time in the original writeup, small enough that most self-hosted services never notice it, though a game server would.

```
# Exempt the WireGuard port and the VPS's own SSH from DNAT first
iptables -t nat -A PREROUTING -i ens3 -p udp --dport 51820 -j RETURN
iptables -t nat -A PREROUTING -i ens3 -p tcp --dport 2222 -j RETURN

# Forward everything else to the homelab over the tunnel
iptables -t nat -A PREROUTING -i ens3 -j DNAT --to-destination 10.0.0.2

# Allow the forwarded traffic through in both directions
iptables -A FORWARD -i wg0 -o ens3 -s 10.0.0.2 -j ACCEPT
iptables -A FORWARD -i ens3 -o wg0 -d 10.0.0.2 -j ACCEPT
```

Skip those RETURN rules and things go wrong fast. The DNAT catch-all doesn't discriminate: it also swallows the WireGuard handshake port and your own SSH session into the VPS, which locks you out of the exact box you're trying to configure. People handle this by moving the VPS's own SSH off port 22 first, onto something like 2222, before touching iptables at all.

## The routing subtlety that breaks most first attempts

Here's where people get bitten. Once the tunnel is up, every reply from your homelab has to travel back down that same tunnel toward the VPS. Send it out through the regular home connection instead, and the client receives a reply from an IP address it never contacted, so the connection just hangs there without ever completing.

The fix is `Table = off` on the homelab's WireGuard interface, which stops WireGuard from installing its own default route, paired with a separate routing table (table 200 in the original writeup) that carries only the traffic for your exposed services back through the tunnel. Everything else on the box, your own SSH session, apt updates, whatever else you're doing, keeps riding the normal home connection untouched. `PersistentKeepalive = 25` sits on top of all that, pinging often enough to keep the CGNAT mapping from expiring on its own schedule.

## Does the math actually work out for you

A static IP from the original author's Spanish ISP runs about €20 a month. A VPS with a public IP and enough bandwidth for a bridge costs a fraction of that, often under $5. The Indonesian comparison lands in the same place: a business-tier static-IP add-on from most residential ISPs costs more per month than a basic low-cost VPS, and you'd be paying that premium indefinitely just to undo something CGNAT did to you for free. For most homelabbers here, the bridge wins on price before you even count the upside of owning a real Linux box sitting in the middle of your own traffic.

Resilience is the part people skip and then regret. Three things can fail here, and each has a cheap fix: the homelab itself can go down, so a cron job that pings SSH and reboots the box if it stops answering catches that. The bridge VPS can go down, so keep a fallback entry point, Tailscale or a Cloudflare Tunnel pointed straight at the homelab, that doesn't depend on the bridge being alive. The tunnel itself can drop, but WireGuard re-handshakes on its own for short blips, and the other two mitigations cover anything longer.

## When you don't need any of this

Not every homelab needs a full bridge. If you only need to reach your own services from your own devices, Tailscale is simpler, free for personal use, and skips the VPS entirely, no public exposure required because it's a private mesh, not a public tunnel. If you're only exposing web apps over HTTP or HTTPS, Cloudflare Tunnel does that for free with zero VPS and zero iptables. Pangolin, the open-source alternative that picked up 500 points on HN recently, sits between the two if you want Cloudflare Tunnel's ergonomics without handing Cloudflare the keys.

The WireGuard bridge earns its complexity specifically when you need arbitrary TCP ports reachable from the whole public internet under CGNAT: a game server, a raw protocol that isn't HTTP, or a service where the client genuinely needs to see a real public IP on its own connection. Everything short of that is better served by Tailscale or Cloudflare Tunnel. Setup for the bridge itself runs under an hour once the iptables rules are right, and the VPS costs less per month than most people spend on lunch twice.
