---
title: Kenapa Gue Self-Host Semua di Mini PC
slug: why-i-self-host-on-a-mini-pc
date: 2026-09-22
excerpt: Satu box Celeron RAM 14GB di pojok kamar — itu yang jalanin toko gue, agent AI, dan blog ini. Ini hitung-hitungannya kenapa tagihan cloud udah nggak masuk akal.
tags: self-hosting, infrastruktur, homelab
---

## Tagihan cloud yang nggak pernah turun

Kebanyakan side project mati dengan cara yang sama: idenya bertahan, tagihan bulanannya enggak. Satu VPS kecil emang murah, sampai lo butuh tiga, ditambah managed database, dan bucket object storage yang diam-diam membengkak.

Gue milih jalan sebaliknya. Satu box Intel Celeron J4105, RAM 14GB, SSD, dan koneksi Biznet fiber sekitar 280/160 Mbps. Harga belinya lebih murah dari satu tahun biaya cloud yang setara. Semua itu jalan di satu box, sampai sekarang.

## Apa aja yang jalan di box itu

- Platform e-commerce (frontend Next.js, backend FastAPI, PostgreSQL, worker)
- Sekumpulan gateway AI agent yang nulis kode, mereview PR, dan jalanin QA
- Caddy sebagai reverse proxy buat semuanya, dengan TLS otomatis
- Blog ini, HTML statis yang digenerate script Python terus di-push ke GitHub

J4105 bukan prosesor kencang. Dan emang nggak perlu. Workload web di skala proyek pribadi itu I/O bound, dan kombinasi SSD plus RAM 14GB ternyata sanggup nanganin beban yang jauh lebih besar dari dugaan orang.

## Trade-off yang jarang disebut orang

Self-hosting itu nggak gratis. Lo sendiri yang jadi on-call engineer. Kalau ISP drop paket jam 2 pagi, nggak ada status page yang bisa disalahin. Mitigasi gue:

1. **Systemd di mana-mana.** Semua service restart otomatis.
2. **Backup offsite tiap malam.** Box-nya boleh mati; datanya enggak boleh.
3. **VPS murah sebagai endpoint publik** buat workload yang sensitif latensi atau DNS.

## Hitungannya

Empat tahun biaya cloud buat stack ini bakal ngelewatin harga hardware di tahun pertama. Break-even tercapai sekitar bulan kedelapan, termasuk satu kali ganti SSD yang mati.

Kalau workload lo bursty dan toleran latensi (CI runner, agent, batch job, tool internal), mini PC bekas dengan koneksi fiber itu udah lebih dari cukup. Kalau lo butuh uptime 99,999% buat pelanggan, ya udah, bayar mahal ke cloud provider managed dan nggak usah pusing baca blog self-hosting kayak punya gue ini.
