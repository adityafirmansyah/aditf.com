---
title: "Cloudflare Akuisisi Deno: Ini Maksudnya buat Lo yang Lagi Build di JavaScript"
slug: cloudflare-acquires-deno-workerd-durable-objects
date: 2026-10-10
excerpt: Ryan Dahl bakal hentiin development Deno runtime setahun lagi, dan Deno Deploy tutup dalam enam bulan. Tapi ini bukan cerita kekalahan: ini tentang abstraksi yang salah dan kenapa Durable Objects jadi taruhannya.
tags: javascript, cloudflare, deno, distributed-systems, architecture
---

## Dari gudang di Berlin sampai akuisisi Cloudflare

Perjalanan Ryan Dahl di dunia runtime JavaScript udah jalan tujuh belas tahun.

Tahun 2009, dia berdiri di sebuah gudang di Berlin ngenalin Node.js lewat server IRC 500 baris. Idenya sederhana: async I/O bikin server jaringan jauh lebih enteng ditulis. Dan cara itu terbukti jalan.

Sepuluh tahun kemudian, dia bikin Deno buat nambal kelemahan Node: izin akses diperketat, TypeScript jalan langsung tanpa compiler tambahan, dan API ngikutin standar web browser. Eksperimen itu juga terbukti berhasil secara teknis. Deno memang runtime yang jauh lebih bersih.

Semua cerita itu berubah total tanggal 9 Oktober 2026 kemarin pas Cloudflare resmi mengumumkan akuisisi Deno Land.

Skema pensiunnya udah dipatok jelas: runtime Deno cuma dapet patch bulanan setahun lagi sebelum dihentikan permanen, sementara layanan Deno Deploy bakal ditutup total enam bulan dari sekarang. Proyek JSR bakal dipindahin langsung ke infrastruktur Cloudflare.

Di Hacker News, kabar ini meledak sampai lebih dari 1.100 poin dan 580 komentar. Komunitas kaget, tapi kalau baca penjelasan teknisnya, alasannya masuk akal.

## Cacat bawaan server JavaScript yang nggak pernah selesai

Di tulisan bareng Kenton Varda di blog Cloudflare, Dahl ngebongkar ilusi di balik demo IRC tahun 2009 itu.

Server itu kencang cuma karena jalan di satu proses dan satu thread. Begitu pengguna nambah banyak dan aplikasi harus dipecah ke beberapa mesin, runtime async nggak bisa bantu apa-apa lagi.

Masalah aslinya pindah ke koordinasi state:

- sinkronisasi pesan antar channel,
- konsistensi riwayat chat,
- dan pembagian koneksi WebSocket di banyak server.

Ujung-ujungnya, developer dipaksa ngerakit tumpukan infrastruktur sendiri. Lo harus pasang Redis buat pub/sub, Postgres buat nyimpen data, ditambah sticky session di load balancer biar koneksi nggak putus.

Menurut Dahl, situasi itu belum berubah sampai sekarang. Bikin runtime yang lebih cepat di satu mesin nggak nyentuh akar masalahnya. Server modern butuh cara beda buat ngelola state terdistribusi.

## Durable Objects: solusi stateful tanpa ribet rakit Redis

Itu sebabnya Dahl kepincut sama model Durable Objects milik Cloudflare.

Durable Object itu sendiri bentuknya distributed singleton yang nempel langsung sama database SQLite lokal. Tiap object punya ID unik, jalan di lingkungan JavaScript single-threaded, dan bisa nanganin koneksi WebSocket langsung. Baca dan tulis ke SQLite di dalamnya jalan secara sinkron dan super cepat.

Ambil contoh aplikasi chat tadi. Lo cukup bikin satu Durable Object buat tiap channel.

Hasilnya:

- data percakapan langsung terisolasi di SQLite milik channel itu,
- koneksi WebSocket otomatis terkelola di tempat yang sama,
- dan aplikasi lo ter-shard otomatis tanpa butuh distributed lock manual.

Masalahnya, selama ini runtime open-source Cloudflare (`workerd`) cuma bisa ngejalanin Durable Objects di satu mesin lokal. Begitu butuh routing terdistribusi lintas server, kodenya terkunci di infrastruktur internal milik Cloudflare.

## Masuknya celld buat buka gembok self-hosting

Waktu ngejalanin Deno Deploy, Dahl ngerasain sendiri betapa rumitnya arsitektur cloud modern: banyak penyedia cloud, banyak jenis database, dan puluhan service yang saling terkait.

Pengalaman itu yang bikin dia ngerancang `celld`.

Filosofinya dibikin kebalikan dari kerumitan tadi: satu binary utuh berbasis Rust, dengan object storage sebagai satu-satunya ketergantungan eksternal.

Lo cukup jalanin banyak instance `celld` dan arahin semuanya ke satu bucket penyimpanan. Sistemnya yang bakal ngurus penempatan object dan rute jaringan antar mesin secara otomatis.

Peleburan `celld` ke dalam `workerd` inilah inti utama dari akuisisi ini. Cloudflare dan tim Deno pengen model pemrograman Workers dan Durable Objects bisa lo jalanin sendiri di server pribadi, bukan cuma numpang di jaringan edge Cloudflare.

## Langkah realistis buat yang sekarang pakai Deno

Waktu transisi 12 bulan ini bukan sekadar janji di atas kertas. Patch keamanan dan perbaikan bug bakal tetap rilis tiap bulan, tapi penambahan fitur baru udah resmi selesai.

Buat tim yang punya service produksi di atas Deno, petanya cukup jelas:

- Kalau aplikasi lo bertipe standar three-tier, pindah ke Node.js 22+ yang sekarang udah punya fitur bawaan pembersih tipe TypeScript (`--experimental-strip-types`).
- Kalau aplikasi lo butuh koordinasi realtime, WebSocket padat, atau sistem agent AI yang butuh state persisten, pelajari model `workerd`.
- Jangan pernah bikin service baru pakai Deno mulai hari ini.

Di Dagango.com, kita nggak pakai Deno di produksi. Tapi arsitektur multi-tenant toko online kita sekarang masih bergantung sama Redis cluster buat misahin state tiap toko. Model satu database SQLite per toko milik Durable Objects jelas jadi alternatif yang sangat menarik buat kita pantau.

## Perang runtime kelar, tapi pertanyaannya naik kelas

Node.js menang karena inersia ekosistemnya terlalu raksasa buat digeser. Bun menang di kecepatan mentah dan kompatibilitas instan sama ekosistem npm. Deno menang di kebersihan desain, tapi kalah di adopsi pasar.

Tapi menurut Dahl, perang runtime satu mesin itu dari awal memang panggung yang salah.

Abstraksi server single-process udah mentok di batas kemampuannya. Pertanyaan berikutnya: gimana bikin sistem terdistribusi jadi gampang diprogram sejak baris pertama.

Taruhan Dahl sekarang ada di model Durable Objects yang bisa lo self-host di infrastruktur milik lo sendiri.

Bakal kejadian atau nggak taruhannya? Kita butuh waktu lebih dari setahun buat ngeliat hasilnya di lapangan.

Tapi setidaknya, industri mulai sadar kalau nambahin Redis di tiap masalah bukan satu-satunya jalan keluar. 😅
