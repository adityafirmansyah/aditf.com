---
title: Kenapa Kita Bikin Subdomain Terisolasi, Bukan Direktori Toko Publik
slug: isolated-subdomains-vs-public-store-directory
date: 2026-09-26
excerpt: Direktori /stores publik bakal bikin Dagango.com kelakuannya kayak marketplace. Kita pilih per-tenant host routing dan metadata, dan argumen crawl budget yang akhirnya menutup perdebatan.
tags: multi-tenancy, nextjs, seo, e-commerce, architecture
---

Semua platform commerce multi-tenant pada akhirnya ketemu persimpangan yang sama. Entah semua merchant duduk di satu direktori toko, atau tiap merchant dapat domain sendiri. Di Dagango.com kita pilih jalan kedua.

PR #50 justru nawarin opsi pertama: endpoint `GET /stores` plus halaman `/stores` yang nge-list semua merchant terdaftar. Jawabannya singkat: "PR #50: declined. we do not need public listings for our stores."

## Direktori itu ya marketplace-nya sendiri

Shopee, Tokopedia, dan Amazon ngumpulin seller karena aggregasi pembeli emang produk utama mereka. Tiap checkout yang lewat mereka ambil potongan.

Platform seller independen jalanin ekonomi yang kebalikannya. Merchant pengen tiga hal:

- brand sendiri,
- terima transfer bank atau order WhatsApp langsung,
- dan halaman produk yang bersih dari listing kompetitor.

Katalog publik bersama ngambil semua itu balik. Begitu semua merchant masuk satu direktori, lo baru saja membangun ulang marketplace yang mereka tinggalkan. Cuma tanpa traffic-nya.

Nah, inilah jebakannya. Direktori toko itu nggak kerasa kayak keputusan arsitektur waktu lo bangun. Rasanya kayak fitur yang bisa kelar dalam setengah hari. Padahal pelan-pelan dialah yang nentuin platform lo sebenarnya buat apa.

Argumen yang paling sering muncul buat direktori itu soal visibilitas: katanya merchant baru butuh tempat biar ketemu orang. Masalahnya, itu logika marketplace. Platform yang jualannya isolasi punya logika yang beda.

Buat UMKM Indonesia yang lagi lepas dari komisi marketplace, pindah itu justru inti jualannya. Mereka udah tahu berapa mahal harga katalog bersama.

Bikin katalog baru di platform kita sendiri sama aja nambah marketplace keempat di hidup mereka. Itu jelas bukan jalan keluar.

## Yang kita bikin sebagai gantinya

PR #51 sampai #53 gantiin ide direktori dengan host-based tenancy di monorepo. Ada empat potong yang bikin ini jalan:

- **Host routing dinamis.** `isPlatformHost` yang mutusin request mendarat di apex platform atau di subdomain tenant / custom domain.
- **`robots.txt` per host.** Halaman platform dan transaksional diblokir, halaman produk tetap kebuka buat crawler.
- **`sitemap.xml` per host.** Sitemap tiap tenant nunjuk ke origin tenant itu sendiri doang.
- **Metadata per tenant.** JSON-LD (`Product`, `Offer`) dan OpenGraph resolve ke domain tenant masing-masing.

Disallow list-nya sama untuk semua host, dan isinya delapan path:

- `/dashboard`
- `/cart`
- `/checkout`
- `/account`
- `/tenants`
- `/orders`
- `/api`
- `/admin`

`/orders` diblokir utuh, bukan cuma subhalaman tracking-nya. Sisanya di storefront tetap bisa di-crawl, karena halaman produk memang yang mau lo indeks.

Pembagiannya sengaja. Halaman cart nggak ada urusannya sama search index, dan halaman checkout yang masuk index itu laporan bug yang tinggal nunggu kejadian.

## Host routing itu keputusan SEO

Tenancy berbasis path (`dagango.com/store-a`) bikin satu hostname, satu crawl budget, dan satu domain authority dipakai bareng semua merchant. Host-based tenancy mecah ketiganya.

Mekanismenya lebih kecil dari kedengarannya. Root layout Next.js nge-render branding platform buat apex, sementara subtree tenant resolve `metadataBase` dinamis yang dikunci ke origin tenant sendiri. Canonical URL dan OpenGraph otomatis ngikut dari situ.

Bagian ini justru lebih penting dari kelihatannya. Salah setting `metadataBase`, dan tiap halaman tenant ngeluarin canonical yang nunjuk ke domain platform.

Lo lagi bilang ke Google bahwa semua merchant itu satu situs. Itu masalah direktori lagi, cuma kali ini wujudnya metadata ketimbang halaman `/stores`.

Di belakang proxy Cloudflare, host header tetap sampai utuh ke aplikasi, jadi keputusan routing cukup lihat host-nya aja. Di sisi FastAPI, tenant resolution baca host yang sama terus scope semua query lewat kolom tenant di PostgreSQL. Nggak ada parsing path, nggak ada slug tenant yang dibawa-bawa lewat route param.

Buat merchant yang mau pakai custom apex domain sendiri, on-boarding-nya juga cuma urusan DNS. Mereka arahin domainnya ke kita, host routing yang ngurus sisanya tanpa deploy terpisah. Satu kode buat banyak host, dan tiap host punya identitas sendiri.

## Crawl budget di platform yang masih muda

Direktori `/stores` itu paginate. Di platform dengan beberapa ratus merchant, itu artinya ribuan halaman listing tipis. Banyak yang nyaris kosong, dan sebagian berujung soft-404.

Googlebot ngabisin jatahnya di situ, bukan di halaman produk. Halaman listing sendiri nggak ngonversi apa-apa.

Di domain yang masih muda lo udah berjuang buat crawl priority. Ngasih crawler ribuan jalan buntu itu cara mahal buat sok teliti.

Sitemap per host benerin insentifnya langsung ke akarnya. Tiap sitemap nunjuk ke `/products/[slug]` di domain merchant sendiri, jadi crawl budget mendarat di tempat niat beli memang ada. Bonusnya, tiap merchant numpuk domain authority di origin sendiri, nggak nyumbangin ke kolam bersama.

## Direktori publik itu target scraping

Endpoint `/stores` level platform itu ya endpoint enumerasi. Satu scraper jalanin dia, baliknya lo dapet daftar seller lengkap, plus feed perubahan tiap kali ada toko baru muncul.

Kompetitor nggak perlu nebak-nebak siapa merchant lo lagi, dan nggak perlu ngawasin yang baru. Poaching berubah jadi cron job.

Bahkan tanpa niat jahat, daftar kayak gitu tetap masalah. Begitu satu halaman isinya semua toko yang terdaftar, angkanya jadi patokan publik yang gampang dipakai buat ngebandingin diri sendiri sama platform lain. Merchant yang baru mulai nggak butuh itu.

Menurut gue lebih enak tiap merchant ditemuin gara-gara mereka sendiri yang nyebarin linknya:

- bio Instagram mereka,
- grup WhatsApp mereka,
- atau link TikTok shop mereka.

## Buat tim yang bakal ngadepin ini

Kalau lo jalanin Next.js App Router plus FastAPI dalam satu monorepo, host-based tenancy itu perubahan routing dan metadata, bukan rewrite. Punya kita kelar dalam tiga PR.

Sebelum launch, cek crawler surface di dua tipe host sekaligus:

- `robots.txt` host platform, ambil dari `dagango.com`,
- `robots.txt` host tenant, ambil dari subdomain yang udah live,
- terus pastiin tiap `sitemap.xml` isinya cuma URL tenant itu sendiri.

Kalau sitemap tenant malah nge-list merchant lain, berarti direktori lo bocor lewat pintu belakang. Cek ini cuma makan dua menit dan nangkep kegagalan yang paling penting.

Pertanyaan soal direktori itu bakal balik tiap kuartal, biasanya dibungkus argumen growth. Jawabannya nggak berubah, karena ekonomi di belakangnya juga nggak berubah.

Direktori toko itu yang lo bangun kalau aggregasi memang bisnis lo. Kalau brand merchant sendiri yang jadi bisnis, isolasi itu satu-satunya arsitektur yang nggak diam-diam kerja nglawan mereka. Itu bukan pilihan yang romantis atau idealis, cuma pilihan yang konsisten sama model bisnisnya sendiri. Dan buat gue, konsistensi kayak gitu yang bikin keputusan arsitektur bertahan lama.
