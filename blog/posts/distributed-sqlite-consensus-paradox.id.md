---
title: Paradoks SQLite Terdistribusi: Lo Bayar Consensus, Terus Tetap Ngantre di Satu Writer
slug: distributed-sqlite-consensus-paradox
date: 2026-10-25
excerpt: SQLite yang direplikasi pakai Raft ngasih failover, tapi nagih millisecond per write. Kebanyakan app cuma butuh WAL streaming ke S3, bukan cluster.
tags: sqlite, distributed-systems, databases, devops, architecture
---

Philip O'Toole nulis retrospektif dua belas tahun rqlite tanggal 23 Oktober. Isinya peta paling rapi soal SQLite terdistribusi yang pernah gue baca. Dan menurut gue, tulisan itu diam-diam ngebantah cara kebanyakan tim mendekati kategori ini.

Jadi gue taruh posisi gue di depan: buat mayoritas aplikasi produksi, SQLite yang direplikasi pakai consensus itu pilihan yang salah.

Itung-itungannya sederhana.

Tiap write harus lewat leader, nyebrang jaringan, terus nunggu mayoritas node ngakuin sudah nulis ke disk.

Selesai semua itu, lo masih nulis lewat lock single-writer punya SQLite. Yang lo tukar: microsecond jadi millisecond. Yang lo dapat: failover, yang sebenarnya juga bisa lo dapat dari file backup di object storage.

## Tiga sudut, tiga pertanyaan

Urutan kemunculannya rapi. Consensus dulu: rqlite September 2014, terus dqlite dari Canonical tahun 2017.

Streaming belakangan, waktu Ben Johnson rilis Litestream awal 2021. Terakhir merge, saat cr-sqlite nambahin CRDT ke engine-nya tahun 2022.

Tiap sudut itu ada karena satu pertanyaan spesifik.

- **Consensus (rqlite, dqlite):** kalau mesinnya mati dan gue nggak bisa nunggu proses restore?
- **Streaming (Litestream, LiteFS):** kalau mesinnya mati aja?
- **Merge (cr-sqlite):** kalau dua mesin sama-sama nerima write selagi offline?

Tiga-tiganya benar, cuma untuk pertanyaan yang beda. Itu sebabnya debat di Hacker News nggak ada ujungnya. Semua orang lagi bela jawaban dari pertanyaan yang nggak sama.

Kalimat O'Toole sendiri yang paling worth dihafal: "The first question is more common, the second is the one people have when they come to rqlite."

Baca dua kali. Pertanyaan yang umum itu nggak butuh cluster. Yang butuh cluster justru pertanyaan yang jarang, dan isinya soal seberapa cepat lo harus balik online.

## Harga yang lo bayar buat consensus

SQLite single-node dalam mode WAL jalan di dalam proses lo. Nggak ada socket antara query dan page cache. Nggak ada layer serialisasi tambahan, nggak ada protokol keanggotaan node.

rapind di thread HN nge-benchmark itu pakai Rust: 193.000 write per detik, dengan lock ditahan sekitar 5 µs per write.

Write lewat Raft nggak mungkin secepat itu. Leader nambahin entry ke log, kirim ke mayoritas node, nunggu mereka bilang sudah masuk disk, baru apply.

Artinya tiap transaksi bayar satu round trip jaringan plus minimal satu fsync ekstra dibanding single-node. Microsecond naik jadi millisecond.

Nah di situ paradoksnya mendarat. Setelah bayar mahal buat replikasi, lo tetap nulis lewat satu writer.

Yang direplikasi consensus itu log-nya. Writer-nya nggak otomatis jadi paralel.

SQLite nggak pernah membiarkan dua write jalan bersamaan, di konfigurasi apa pun. Jadi contention-nya muncul di cluster persis seperti di satu box:

```
SQLITE_BUSY: database is locked
```

Yang berubah cuma ongkos retry-nya. Di satu node, naikin busy timeout dan memperpendek transaksi biasanya cukup buat nyerap retry. Di belakang consensus, tiap retry ikut bayar round trip lagi.

Ada satu batasan lain yang sering kelewat. gregsadetsky nyatet di thread bahwa rqlite secara resmi nggak mendukung BEGIN/COMMIT, jadi transaksi interaktif multi-statement nggak bisa dipakai. Cek dulu ke model data lo sebelum migrasi.

## Cerita dari lapangan

Di thread itu, SQLite ber-cluster nggak terbaca kayak kisah sukses.

- Dqlite di cluster kecil bikin esafak pengin pindah. Alasannya: "Loads of '500 database locked' errors".
- Issue #908 dari Canonical, dibuka 2026-09-28 dan masih terbuka, isinya assertion abort di VFS dqlite setelah berjam-jam retry locked-database.
- Di laporan itu cluster kehilangan satu-satunya voting member, dan abort-nya ikut ngebawa control plane node itu down.
- Menurut piterrro, Cloudflare D1 nggak reliable dibanding Durable Objects mentah, dan unconscionable setuju.
- Terus ruther4d nambahin bahwa database D1 nggak bisa dibikin dinamis, jadi isolasi per tenant jadi lebih susah.

Tapi ada bukti lawan, dan justru ini yang lebih ngajarin. qaq jalanin rqlite di produksi dan puas.

Yang disimpan rqlite cuma registry tenant dan operator, yang di-pull node aplikasi, jadi beban ke database-nya sangat ringan.

Waktu control layer-nya mati, platform cuma nggak bisa provisioning tenant baru. Nggak ikut gelap.

Begitulah bentuk deployment consensus yang gue mau tiru. Write-nya kecil, dan failover-nya memang harus instan.

## Setup yang gue pakai di VPS

Buat platform commerce multi-tenant di VPS Linux, default gue satu database SQLite per tenant di NVMe lokal, dengan Litestream ngalirin WAL ke object storage. Query dan write nggak pernah keluar mesin. Durabilitasnya yang keluar, pakai timer.

Konfigurasi replica-nya segini:

```yaml
dbs:
  - path: /srv/app/tenants/acme/store.db
    replicas:
      - type: s3
        bucket: acme-wal
        path: tenants/acme
        retention: 720h
        sync-interval: 1s
```

Restore-nya satu perintah:

```bash
litestream restore -o /srv/app/tenants/acme/store.db s3://acme-wal/tenants/acme
```

Sisi database-nya butuh tiga pragma waktu dibuka:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
```

Yang lo lepas harus disebut jelas, jangan dibungkus. Titik recovery lo setara sync interval, artinya write yang sudah commit dalam satu detik terakhir bisa hilang kalau mesinnya mati mendadak. Waktu restore-nya sepanjang download object plus restart proses.

Kalau angka itu masih masuk requirement lo, lo nggak butuh consensus. Keputusannya menyempit jadi tiga:

1. Restore puluhan detik masih oke, jadi pakai SQLite single-node plus Litestream.
2. Failover harus otomatis dan jalur tulisnya nyentuh duit, jadi pakai rqlite dan terima write dalam hitungan millisecond.
3. Write harus mendarat di beberapa region sekaligus, berarti berhenti membungkus file dan pindah ke Postgres atau CockroachDB.

## Dua belas tahun kemudian

O'Toole nutup dengan satu hal yang jarang diulang kategori ini: idenya open source delapan tahun sebelum ada yang menjualnya.

Turso ngambil modal venture dari fork engine-nya, terus diakuisisi Supabase tahun 2026. Cloudflare jual D1 sebagai produk managed, dari perusahaan yang nggak merasa perlu menjelaskan isi perutnya.

Pelajaran yang gue ambil lebih sempit dari "terdistribusi selalu menang". Tanya dulu: satu node mati itu sebenarnya biayanya berapa buat lo? Satu jam restore manual, atau outage yang harus lo jelaskan ke customer?

Kebanyakan tim jawab "satu jam", terus tetap jalanin cluster-nya.

Padahal setahun kemudian, waktu habis buat ngurus lock timeout yang ngantre di belakang round trip consensus. Sistem yang requirement aslinya cuma satu: backup yang benar-benar jalan. 😅
