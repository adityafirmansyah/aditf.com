---
title: Kenapa Saya Self-Host Semua di Mini PC
slug: why-i-self-host-on-a-mini-pc
date: 2026-09-22
excerpt: Sebuah Celeron box dengan RAM 14GB di pojok kamar menjalankan toko-toko saya, agent AI, dan blog ini. Ini hitung-hitungan kenapa tagihan cloud tidak lagi masuk akal.
tags: self-hosting, infrastruktur, homelab
---

## Tagihan cloud yang tidak pernah turun

Kebanyakan side project mati dengan cara yang sama: idenya bertahan, tagihan bulanannya tidak. Satu VPS kecil memang murah — sampai kamu butuh tiga, ditambah managed database, dan bucket object storage yang diam-diam membengkak.

Saya ambil arah sebaliknya. Satu box Intel Celeron J4105, RAM 14GB, SSD, dan koneksi Biznet fiber sekitar 280/160 Mbps. Harga belinya: lebih murah dari satu tahun biaya cloud yang setara. Semua di bawah ini jalan di box tersebut hari ini.

## Apa saja yang jalan di box itu

- Platform e-commerce (frontend Next.js, backend FastAPI, PostgreSQL, worker)
- Sekumpulan gateway AI agent yang menulis kode, mereview PR, dan menjalankan QA
- Caddy sebagai reverse proxy untuk semuanya, dengan TLS otomatis
- Blog ini — HTML statis yang digenerate script Python lalu di-push ke GitHub

J4105 bukan prosesor kencang. Dan memang tidak perlu. Workload web di skala proyek pribadi itu I/O bound, dan SSD plus RAM 14GB menutupi lebih banyak dari yang kamu kira.

## Trade-off yang jarang disebut orang

Self-hosting itu tidak gratis. Kamu adalah on-call engineer-nya sendiri. Kalau ISP drop paket jam 2 pagi, tidak ada status page yang bisa disalahkan. Mitigasi saya:

1. **Systemd di mana-mana.** Semua service restart otomatis.
2. **Backup offsite tiap malam.** Box-nya boleh mati; datanya tidak boleh.
3. **VPS murah sebagai wajah publik** untuk workload yang sensitif latensi atau DNS.

## Hitungannya

Empat tahun biaya cloud untuk stack ini akan melebihi harga hardware di tahun pertama. Break-even tercapai sekitar bulan kedelapan, termasuk satu kali ganti SSD yang mati.

Kalau workload kamu bursty dan toleran latensi — CI runner, agent, batch job, tool internal — mini PC bekas di belakang koneksi fiber susah dikalahkan. Kalau kamu butuh availability lima sembilan untuk pelanggan, bayar pajak cloud dan berhenti membaca blog dari orang yang self-host.
