---
title: "Ada yang Daftar .lan ke ICANN: Kenapa DNS Router Homelab Lo Bisa Bocor"
slug: dot-lan-gtld-openwrt-dns-leak-risk
date: 2026-10-09
excerpt: ICANN lagi proses pengajuan gTLD .lan, domain yang udah 20 tahun jadi default OpenWrt. Ini yang kejadian kalau domain yang lo pikir privat itu ternyata bisa dibeli orang lain.
tags: dns, networking, homelab, self-hosting, security
---

## Domain yang lo kira punya lo sendiri, ternyata bisa didaftarin orang lain

7 Oktober 2026, ICANN publish daftar aplikasi gTLD baru buat tahun 2026. Salah satunya buat `.lan`.

Nomor aplikasinya CD2694T-T26351, dari perusahaan bernama Coffee Danger, LLC, dan statusnya lagi pre-evaluation. Kalau lolos, `.lan` nggak lagi sekadar konvensi informal yang router lo pakai diam-diam. Itu bakal jadi zone DNS publik yang beneran, yang resolve ke server milik orang lain, bisa dibeli siapa aja.

Gue sendiri jalanin box Celeron J4105 di belakang CGNAT Biznet fiber, pakai Caddy sebagai reverse proxy, dan tiap hari ngetik `nas.lan` di HP tanpa pikir panjang. Jutaan orang lain ngelakuin hal yang sama, kebanyakan nggak sadar risikonya.

## `.lan` nggak pernah resmi, tapi dipakai di mana-mana

Nah ini bagian yang bikin kasus `.lan` beda dari perebutan gTLD biasa: domain ini emang dari awal nggak pernah di-reserve siapa pun secara resmi.

Gue cek langsung `dhcp.conf` di repo OpenWrt, dan dua baris itu masih ada sampai sekarang: `option domain 'lan'` dan `option local '/lan/'`. Udah segitu lama konfigurasi default `dnsmasq`-nya kayak gitu. DD-WRT sama router travel GL.iNet ikutan konvensi yang sama. Dua dekade jadi default pabrikan, tanpa ada reservasi resmi apa pun di baliknya.

Bandingin sama domain-domain yang justru lewat proses standar beneran:

- `.local` di-reserve khusus buat multicast DNS lewat RFC 6762, biar discovery link-local nggak nabrak root publik.
- `home.arpa` diusulin RFC 8375 sebagai suffix "resmi" buat jaringan rumahan.
- `.internal` malah di-reserve langsung sama board ICANN sendiri, lewat resolusi yang disahkan 29 Juli 2024.

Masalahnya, `.lan` nggak dapet perlindungan apa pun dari semua itu, padahal justru itu yang paling banyak dipakai praktisi di lapangan. Thread HN yang bahas ini (116 poin, 140 komentar) banyak ngomongin ironi ini: badan standar sibuk ngelindungin nama yang orang jarang pakai, sementara nama yang dipakai semua orang malah dibiarin kebuka.

## Kenapa `home.arpa` kalah padahal secara aturan dia menang

`home.arpa` sembilan karakter. `.lan` cuma tiga. Beda segitu kecil, tapi coba ngetik `plex.home.arpa` di URL bar jam 11 malem dibanding `plex.lan`, dan lo bakal ngerti kenapa orang males.

RFC 6762 ngunci `.local` khusus buat mDNS doang, jadi kalau ada lookup unicast ke `.local`, dia bisa nyangkut nunggu balasan multicast yang nggak bakal pernah datang. Itu timeout, bukan error, dan itu lebih nyusahin. `home.arpa` emang lolos dari jebakan itu, tapi dia kena masalah lain: nggak ada yang mau repot ngetiknya, jadi ya nggak ada yang pakai. `.internal` malah baru di-reserve ICANN tahun 2024, pas `.lan` udah 20 tahun duluan jadi standar de facto yang nggak bisa diganti cuma dengan nerbitin alternatif yang lebih bersih.

Standar-standar itu kalahnya bukan di aspek keamanan. Mereka kalah di soal kenyamanan ngetik, bertahun-tahun sebelum ada yang kepikiran minta ICANN reserve string yang udah dipakai semua orang.

## Ini bukan risiko teoretis, ini risiko struktural

Tiap device yang jalan-jalan keluar dari jaringan rumah lo, bawa serta search domain DNS-nya, setidaknya sampai ada yang ngereset settingan itu. Laptop yang di-suspend di rumah terus dibuka lagi di hotel, atau konek ke hotspot HP, bakal tetep nembak query buat `nas.lan` atau `router.lan` sebelum ada apa pun yang ngoreksi.

Sekarang, query itu nyampe ke resolver publik, dapet NXDOMAIN, terus diem gitu aja. Tapi begitu `.lan` resmi delegated, query yang sama bakal resolve ke apa pun yang registry Coffee Danger pasang di situ. Dan HP yang bocorin `plex.lan` itu nggak cuma bocorin satu request web doang.

Yang bocor biasanya lebih serius dari itu:

- Cookie session.
- Token autentikasi.
- Header auth yang sebenernya cuma dimaksudin buat server yang ada di dalem rumah lo.

Flag `bogus-priv` di `dnsmasq` emang nge-block reverse lookup buat alamat RFC 1918, dan rebind protection-nya nahan domain luar biar nggak bisa resolve ke IP internal. Tapi dua-duanya nggak ngelakuin apa-apa buat query `.lan` yang ditembak dari LUAR jaringan lo sepenuhnya, yang justru itu skenario yang kejadian tiap hari pas device lo roaming.

## Kita udah pernah ngalamin ini, namanya `.dev`

Google beli `.dev` tahun 2014, dan selama tiga tahun nggak kejadian apa-apa karena belum ada yang di-delegate. Terus 2017, Chromium ngaktifin HSTS preload buat seluruh TLD itu sekaligus.

Semua environment dev lokal yang diam-diam ngasumsiin `myapp.dev` nggak akan pernah resolve di internet publik, langsung rusak bareng-bareng. Soalnya `.dev` sekarang domain beneran, dan Chrome maksa HTTPS buat semuanya tanpa pengecualian. Issue GitHub dari Pow sama Laravel Valet jaman itu masih kebuka sampai sekarang, jadi bukti berapa banyak setup yang ternyata nebak-nebak doang tanpa pernah dicek.

`.lan` itu `.dev` versi dua dekade lebih dulu dipakai. Basis penggunanya pun jauh kurang sadar keamanan dibanding developer web yang biasa baca GitHub issue. Orang homelab nggak lagi-lagi mantengin laporan risiko name collision dari ICANN.

## Solusinya bukan konvensi, tapi domain yang beneran lo punya

TLD privat itu sifatnya cuma privat sementara. Begitu ada yang ngurus paperwork buat jadiin dia publik, status itu ilang. `.lan` lagi ngalamin itu sekarang, tapi `home.arpa` atau `.internal` juga bisa aja kena nasib serupa kalau sampai praktisi rame-rame adopsi salah satunya duluan.

Makanya fix yang kepake jangka panjang itu bukan nyari nama lain yang "lebih aman". Yang kepake itu split-horizon DNS, di atas domain yang beneran lo pegang registrasinya. Punya gue sendiri `*.internal.aditf.com`, dan caranya sederhana.

- Resolver internal jawab query `internal.aditf.com` pakai alamat RFC 1918, nggak pernah nyentuh internet publik.
- Resolver eksternal nggak liat apa-apa buat subdomain itu, atau dapet jawaban yang sengaja dibuat nggak resolve.
- Let's Encrypt tetep nerbitin sertifikat asli ke zone publiknya, jadi service internal tetep dapet TLS valid tanpa warning self-signed.

Nggak ada satu pun pelamar gTLD yang bisa beli string dari bawah domain yang udah lo registrasiin sendiri duluan.

## Yang bisa lo lakuin minggu ini, sebelum pre-evaluation-nya kelar

Nggak usah nunggu hasil review ICANN kelar dulu buat mulai pindah. Risiko collision-nya udah ada dari sekarang, nggak peduli aplikasi Coffee Danger itu nanti ditolak atau diterima.

Pindahin hostname internal lo ke subdomain dari sesuatu yang lo punya sendiri. Arahin resolver DNS internal ke situ, terus otomatisin penerbitan sertifikatnya langsung ke zone yang asli, bukan ke `.lan`.

Satu sore ngerapihin config `dnsmasq`, plus beberapa dolar setahun buat domain. Itu ongkosnya. Bandingin sama skenario sebaliknya: kredensial NAS lo nyasar ke registry punya orang asing, dan lo baru ngerti pas semuanya udah kejadian. 😅

Dan percaya deh, nyesel belakangan itu jauh lebih mahal daripada ongkos domain setahun.
