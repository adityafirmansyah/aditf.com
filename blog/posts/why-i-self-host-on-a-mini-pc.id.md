---
title: Kenapa Gue Self-Host Semua di Mini PC
slug: why-i-self-host-on-a-mini-pc
date: 2026-09-22
excerpt: Toko online, agent AI, sampe blog yang lagi lo baca ini jalan semua di satu box Celeron RAM 14GB yang nangkring di pojok kamar. Ini itung-itungan kenapa tagihan cloud udah nggak masuk akal lagi buat gue.
tags: self-hosting, infrastruktur, homelab
---

## Tagihan Cloud yang Nggak Ada Abisnya

Side project itu jarang mati gara-gara idenya jelek. Yang bikin mati biasanya tagihan cloud yang makin lama makin ngelunjak: dari satu VPS kecil yang tadinya murah, terus kepaksa nambah jadi tiga, ditambah managed database, ditambah lagi bucket storage yang diam-diam ngegembung tiap bulan.

Makanya gue milih jalan yang beda. Modal cuma satu box: Intel Celeron J4105, RAM 14GB, SSD, plus koneksi Biznet fiber sekitar 280/160 Mbps. Harganya masih lebih murah dari biaya cloud setahun aja, dan sampai sekarang semua kerjaan gue jalan di situ.

## Isinya Apa Aja

Nih, yang jalan di satu box itu:

- Platform e-commerce (frontend Next.js, backend FastAPI, database PostgreSQL, plus worker-workernya)
- Sekumpulan gateway agent AI yang kerjaannya nulis kode, review PR, sampe jalanin QA
- Satu Caddy buat reverse proxy semuanya, TLS-nya otomatis beres sendiri
- Blog yang lagi lo baca ini, HTML statis digenerate script Python terus tinggal di-push ke GitHub

Soal prosesor, J4105 emang bukan barang kencang. Tapi buat apa juga kenceng-kenceng? Workload proyek pribadi kayak gini kerjanya lebih banyak nunggu I/O, bukan mikir berat di CPU. SSD sama RAM 14GB aja udah cukup buat nutupinnya.

## Ongkos yang Jarang Dibahas Orang

Nah, self-hosting itu ada harganya juga, cuma bukan dalam bentuk duit. Kalau ISP tiba-tiba drop koneksi jam 2 pagi, lo sendiri yang harus bangun benerin, nggak ada status page orang lain buat disalahin. Ini cara gue jaga-jaga:

1. **Systemd di semua service.** Kalau ada yang crash, langsung restart sendiri tanpa gue pencet apa-apa.
2. **Backup ke luar box, tiap malam.** Box-nya boleh koit, datanya nggak boleh ikutan.
3. **VPS murah sebagai endpoint publik** buat kerjaan yang sensitif soal latensi atau DNS.

## Itung-Itungannya

Itung punya itung, biaya cloud buat stack sebesar ini dalam empat tahun bakal jauh ngelewatin harga hardware yang gue keluarin di tahun pertama. Break-even-nya kecapai sekitar bulan kedelapan, udah termasuk sekali ganti SSD yang tiba-tiba mati.

Intinya gini: kalau workload lo sifatnya bursty dan nggak rewel soal latensi (semacam CI runner, agent, batch job, atau tool internal), mini PC bekas dengan koneksi fiber udah lebih dari cukup. Tapi kalau lo butuh uptime 99,999% buat pelanggan beneran, mendingan bayar mahal ke cloud provider managed aja, dan nggak usah pusing baca blog self-hosting kayak punya gue ini.
