---
title: Jebakan Pod 46 vCPU: Apa yang Dipelajari PostHog Setelah Lepas dari DuckDB
slug: posthog-duckdb-46-vcpu-pod-trap
date: 2026-11-03
excerpt: PostHog jalanin DuckDB sebagai warehouse multi-tenant lima bulan, lalu membongkarnya. Pelajarannya soal di mana engine single-node berhenti jadi pilihan murah.
tags: duckdb, architecture, databases, posthog, devops
---

Tanggal 2 November 2026, PostHog nerbitin tulisan "Why we're moving our warehouse off DuckDB". Tulisan yang justru berisi alasan pindah ke DuckDB terbit 29 Juni 2026, lima bulan sebelumnya.

Tim yang sama. Data yang sama-sama nyampe petabyte. Kesimpulannya kebalikan.

Menurut gue ini bukan kegagalan DuckDB. Ini kegagalan batas.

PostHog ngambil engine analytics yang jalan in-process dan didesain buat ngurus satu mesin, terus dijual sebagai warehouse multi-tenant di cloud dengan skala 2 PB. Engine-nya nurut. Yang nggak nurut itu semua yang dibangun di sekelilingnya.

## DuckDB bukan biang keroknya

PostHog sendiri bilang DuckDB mungkin tool single-node terbaik buat analisis data banyak, dan node itu bisa jadi laptop lo. Gue juga pakai begitu, buat baca file Parquet di NVMe lokal.

Justru sifat yang bikin dia hebat di lokal itu yang bikin dia jebol di produk cloud:

- Nggak ada network hop antara query engine dan byte yang dia scan.
- Satu proses pegang satu budget memori, jadi keputusan spill ke disk tetap lokal.
- Cuma ada satu tenant, yang pola query-nya masih bisa lo tebak.

Tiga sifat itu semuanya milik mesin. Bukan milik database-nya. Nggak ada satu pun yang bisa lo beli terpisah dari hardware yang menjalankannya.

## Bayar resource-nya duluan, query-nya belakangan

Angka paling penting di cerita ini justru nggak ada di blog post-nya. Datangnya dari komentar penulisnya di Hacker News.

Mayoritas pod pelanggan jalan di 46 vCPU dan 360 GB RAM di Elastic Kubernetes Service (EKS). Dan pelanggan masih minta tambah.

Satu tenant. Satu node raksasa.

Engine terdistribusi kayak Trino atau Snowflake nentuin ukuran worker setelah query-nya masuk. Query di-parse dulu, dipecah jadi stage, baru tiap stage dikasih worker sebanyak yang dia butuh. Mesin mahalnya hidup cuma selama query-nya jalan.

Engine single-node nggak punya kemewahan itu. Ukurannya harus diputusin sebelum query datang. Artinya lo provisioning buat query terburuk yang mungkin masuk, terus berharap yang berikutnya lebih ringan.

Contoh dari penulisnya udah cukup buat nutup debat. Satu query jalan 12 jam. Datang lagi kerjaan 10 jam dari pelanggan yang sama. Dua query panjang, dan pod 46 vCPU lo berubah jadi antrean mahal yang nggak bisa dipakai siapa-siapa.

## Katalog yang baca ulang dirinya tiap commit

Kalau DuckLake, kegagalannya lebih menarik daripada DuckDB. Ini soal tradeoff desain, bukan bug.

Skema katalog DuckLake harus tetap portable di banyak database SQL, dan itu otomatis membatasi optimasi yang bisa dipakai engine-nya. Di skala PostHog, satu write ke satu tabel bisa lewat tiga menit. Penyebabnya, tiap commit baca ulang statistik seluruh katalog.

Lebih dari 99% baris statistik itu punya tabel yang udah nggak ada. Dibersihin, write-nya jadi 30 sampai 50 kali lebih cepat. Barisnya tetap tumbuh lagi.

Data yang mereka dogfood waktu akhirnya nyerah besarnya segini: sekitar 2 PB. Isinya kira-kira 1 triliun baris dan 15,3 juta snapshot.

Perbaikan itu hidup di fork DuckLake milik mereka sendiri. Format yang dibikin buat portability malah maksa patch yang nggak bisa diterima siapa pun di luar tim. Justru keunggulan utama format itu yang hilang di tengah jalan.

## Port 5432 itu janji, bukan protokol

Bagian paling enak dari pitch bulan Juni: tooling lo udah ngomong Postgres. Arahin dbt, Metabase, atau psql ke port 5432 dan langsung jalan.

Masalahnya, semua yang bikin janji itu enak juga yang bikin operasionalnya mahal.

- Koneksi itu stateful, jadi L4 network load balancer (NLB) cuma bisa meneruskan TCP mentah ke satu pod tertentu.
- L7 load balancer (ALB) bisa routing berdasarkan header HTTP dan cek kesehatan per request.
- Koneksi idle dan TTL berubah jadi hitungan biaya per tenant begitu jumlah pelanggannya nambah.
- Tiap client Postgres punya ekspektasi perilaku sendiri, dan daftar kasus khususnya nggak ada habisnya.

PostHog akhirnya pakai NLB, karena pgwire yang stateful memang nggak ninggalin banyak pilihan. Satu keputusan itu langsung menghapus routing per header dan health check per request. Connection draining juga hilang. Padahal tiga hal itu yang bikin pod ephemeral di belakang load balancer terasa biasa aja.

## Habis itu formatnya dibangun ulang. Ini yang gue pertanyakan

Penggantinya: Trino versi mereka sendiri, plus table format baru bernama HogLake. Tiga arsitektur dalam enam bulan buat permukaan produk yang sama. Thread HN-nya nggak ramah sama keputusan ini.

Ada satu koreksi yang perlu disebut, karena thread-nya berkali-kali salah paham dan penulisnya harus turun tangan sendiri. PostHog nggak ninggalin ClickHouse. ClickHouse masih jalanin product analytics. Yang pindah cuma warehouse pelanggan.

Di komentar, mereka bilang sempat coba Apache Iceberg dan write-nya terlalu lambat. Gue percaya angkanya. Tapi itu belum tentu jawaban buat diagnosisnya. Write path yang lambat justru gejala yang biasanya bikin format diganti, bukan diprofil.

## Aturan yang gue pakai sendiri

Engine embedded pantas dipakai di production kalau batas eksekusinya sama dengan batas hardware-nya. SQLite buat OLTP, DuckDB buat OLAP. Dua-duanya bagus banget ketika proses, data, dan disk ada di satu mesin. Apalagi kalau cuma satu tenant yang punya semuanya.

Dagango.com jalan di atas monorepo multi-tenant, di VPS Linux dan bare metal. Tiap request masuk lewat batas L7 pakai HTTP dan stateless. Tenant-nya dibaca dari request itu sendiri.

Tenant itu baris data plus policy. Bukan container yang berpura-pura jadi mesin.

Kalau butuh isolasi keras, kita isolasi di batas proses dengan plafon memori yang angkanya jelas.

Sebelum naruh engine embedded di belakang API yang lo jual, ini pertanyaan yang gue mau jawab dulu secara tertulis:

1. Query-nya dikirim tenant, atau kode gue sendiri yang bikin?
2. Gue bisa resize antar-query, atau cuma sebelum query?
3. Query terburuk satu pelanggan biayanya ke pelanggan lain berapa?
4. Kalau gue kasih wire protocol, dia selamat lewat proxy L7 nggak?
5. Plafon memorinya dijaga di mana, dan kalau jebol dia gagal nutup atau gagal buka?

Ada satu tes murah yang bisa lo jalanin minggu ini juga, sebelum mikirin arsitektur besar. Buka spesifikasi pod atau VM yang lo kasih ke satu pelanggan. Terus tanya ke diri sendiri: kalau besok pelanggan ini ngirim satu query dua kali lebih berat, gue ngapain?

Kalau jawabannya naikin ukuran mesin, lo udah ada di jalur yang sama dengan PostHog. Kalau jawabannya nambah worker selama query-nya jalan, berarti batas eksekusinya udah kepisah dari batas mesin. Yang kedua bukan soal pilihan engine. Itu soal lo ngukur kapasitas per query, bukan per pelanggan.

Gue sendiri lebih suka jawaban kedua, karena biayanya ikut panjang query. Bukan ikut seberapa besar pelanggannya hari itu.

## Yang sebenernya jebol

Retrospektif PostHog ini salah satu tulisan engineering paling jujur yang terbit tahun ini. Mereka nyebut ukuran pod, latency write, dan betapa banyak client yang perilakunya nggak sama satu sama lain. Bukan nyalahin benchmark.

Intinya lebih sempit dari "DuckDB nggak bisa scale", tapi jauh lebih berguna. Instance per tenant itu kedengarannya multi-tenancy, padahal bukan.

Tagihannya datang belakangan. Bentuknya spesifikasi pod: 46 vCPU dan 360 GB. Buat satu pelanggan. Buat satu query.

Dan yang paling bikin gue nggak nyaman, mereka sendiri udah nulis di bulan Juni bahwa masalahnya multi-tenancy. Lima bulan kemudian masalah yang sama balik lagi, cuma kali ini pakai nama engine yang lain. 😅
