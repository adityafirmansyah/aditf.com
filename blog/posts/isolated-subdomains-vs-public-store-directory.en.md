---
title: Why We Built Isolated Subdomains Instead of a Public Store Directory
slug: isolated-subdomains-vs-public-store-directory
date: 2026-09-26
excerpt: A public /stores directory would have made ecompy behave like a marketplace. We shipped per-tenant host routing and metadata instead, and the crawl-budget argument is what settled it.
tags: multi-tenancy, nextjs, seo, e-commerce, architecture
---

Every multi-tenant commerce platform hits the same fork. Either every merchant lives behind one storefront directory, or each one gets a domain of their own.

We took the second road in ecompy. PR #50 proposed exactly the first option: a `GET /stores` endpoint plus a `/stores` landing directory listing every registered merchant. The verdict came back short: "PR #50: declined. we do not need public listings for our stores."

## The directory is the marketplace

Shopee, Tokopedia, and Amazon aggregate sellers because buyer aggregation is their actual product. Every checkout routes through their take-rate.

An independent seller platform runs on the opposite economics. Merchants keep their own brand, take bank transfer or WhatsApp orders directly, and never see a competitor's listing underneath their own product page.

A shared public catalog takes all of that back. Put every merchant in one directory and you have rebuilt the marketplace they left, minus the traffic.

That is the trap. A store directory does not read as an architectural choice while you are building it. It reads as a feature you could ship in an afternoon, and it quietly redefines what your platform is for.

For Indonesian UMKM leaving marketplace commissions behind, the relocation is the whole pitch. They already know what the shared catalog costs them. Building a new one on our own platform would have made us the fourth marketplace in their life instead of the exit from it.

## What we shipped instead

PR #51 through #53 replaced the directory idea with host-based tenancy across the monorepo. Four pieces made it work:

- **Dynamic host routing.** `isPlatformHost` decides whether a request lands on the apex platform or on a tenant subdomain or custom domain.
- **Per-host `robots.txt`.** Platform-only and transactional surfaces get disallowed while product pages stay open to crawlers.
- **Per-host `sitemap.xml`.** Each tenant's sitemap points only at that tenant's own origin.
- **Per-tenant metadata.** JSON-LD (`Product`, `Offer`) and OpenGraph tags resolve against the tenant's own domain.

The disallow list is host-independent and covers eight paths:

- `/dashboard`
- `/cart`
- `/checkout`
- `/account`
- `/tenants`
- `/orders`
- `/api`
- `/admin`

`/orders` is disallowed whole, not just the tracking subpage. Every storefront path outside that list stays crawlable, because a product page is exactly what you want indexed.

The split is deliberate. A cart page has no business in a search index, and a checkout page in a search index is a bug report waiting to happen.

## Host-based routing is an SEO decision

Path-based tenancy (`dagango.com/store-a`) shares one hostname, one crawl budget, and one domain authority across every merchant. Host-based tenancy splits all three.

The mechanics are smaller than they sound. The Next.js root layout renders platform branding for the apex, while tenant subtrees resolve a dynamic `metadataBase` keyed to the tenant's own origin. Canonical URLs and OpenGraph tags follow from that automatically.

That last part matters more than it looks. Get `metadataBase` wrong and every tenant page emits a canonical pointing at the platform domain. You would then be telling Google that all merchants are one site, which is the directory problem again, just expressed in metadata instead of a `/stores` page.

Behind the Cloudflare proxy, the host header survives intact, so the routing decision stays a pure function of the request. On the FastAPI side, tenant resolution reads the same host and scopes every query through the tenant column in PostgreSQL. No path parsing, no tenant slug threaded through route params.

## Crawl budget on a young platform

A `/stores` directory paginates. On a platform with a few hundred merchants, that is thousands of thin listing pages, many of them near-empty and some of them soft-404s.

Googlebot spends its allowance there instead of on product pages, and listing pages convert nothing anyway. On a young domain you are already fighting for crawl priority, so handing the crawler a few thousand dead ends is an expensive way to be thorough.

Per-host sitemaps fix the incentive directly. Each sitemap points at `/products/[slug]` on the merchant's own domain, so crawl budget lands where buying intent lives. Each merchant also accumulates domain authority on their own origin rather than donating it to a shared pool.

## A public directory is a scrape target

A platform-wide `/stores` endpoint is an enumeration endpoint. One scraper walks it and comes back with your complete seller list, plus a change feed every time a new store appears.

Competitors do not have to guess who your merchants are, and they do not have to watch for new ones. Poaching becomes a cron job.

I would rather every merchant be discovered because they pushed their own link:

- their Instagram bio,
- their WhatsApp group,
- or their TikTok shop link.

## What I would tell the next team

If you run Next.js App Router plus FastAPI in one monorepo, host-based tenancy is a routing and metadata change, not a rewrite. Ours cost three PRs.

Before launch, check the crawler surface on both host types:

- the platform host's `robots.txt`, from `dagango.com`,
- a tenant host's `robots.txt`, from a live subdomain,
- and confirm each `sitemap.xml` contains only that tenant's own URLs.

If a tenant sitemap lists another merchant, you have leaked your directory through the back door. That check takes two minutes and catches the failure that matters.

The directory question returns every quarter, usually wrapped in a growth argument. The answer does not change, because the economics behind it do not change.

A store directory is what you build when aggregation is your business. When the merchant's own brand is the business, isolation is the only architecture that does not quietly work against them.
