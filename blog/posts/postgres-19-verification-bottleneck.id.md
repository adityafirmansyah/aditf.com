---
title: Kenapa Postgres 19 Mundur: Cari Bug Makin Murah, Verifikasi Tetap Mahal
slug: postgres-19-verification-bottleneck
date: 2026-11-02
excerpt: Postgres 19 baru rilis 19 November dan tiga fitur ditarik di akhir beta. Bukan karena kodenya memburuk, tapi karena nemu bug jadi murah sementara verifikasinya tetap kerja manusia.
tags: postgresql, ai-engineering, software-reliability, open-source, database-internals
---

PostgreSQL 19 baru bisa dipakai umum tanggal 19 November 2026.

Buat proyek yang sepuluh tahun terakhir selalu rilis antara pertengahan September dan pertengahan Oktober, itu bukan keterlambatan biasa. Itu jadwal yang selama ini dipegang akhirnya jebol.

Robert Haas, committer PostgreSQL, nulis penjelasannya 30 Oktober. Jawabannya bukan karena kodenya jadi lebih jelek. Masalahnya, banyak orang tiba-tiba jauh lebih jago nemuin kesalahan yang sebenernya udah bertahun-tahun ada di situ.

## Pola rilisnya jebol, tiga fitur ikut dicabut

Aturan rilisnya sederhana dan hampir nggak pernah meleset: paling cepat pertengahan September, paling lambat pertengahan Oktober.

RC 1 keluar 15 Oktober. RC 2 dijadwalkan 12 November, bareng update release kuartalan, supaya tumpukan fix di rilis itu udah masuk sebelum versi barunya keluar. General availability nyusul seminggu kemudian.

Feature freeze tetap 8 April, sama seperti tahun-tahun sebelumnya. Yang beda, antara 27 Agustus dan 15 September proyek ini menarik balik tiga fitur yang sudah terlanjur di-merge:

- UPDATE/DELETE ... FOR PORTION OF, sintaks tabel temporal buat ngedit potongan histori.
- SQL Property Graph Queries (SQL/PGQ), layer query graph yang baru.
- ALTER TABLE ... MERGE PARTITION dan SPLIT PARTITION.

Revert di akhir beta itu biasa. Mencabut tiga fitur yang sudah matang sebulan sebelum RC pertama, itu lain cerita.

## Commit ke master-nya justru turun

Haas bandingin jumlah commit di rentang tanggal yang sama, dari feature freeze sampai 25 September:

- 2025: 1.037 commit ke master, 724 di antaranya di-back-patch ke REL_18_STABLE.
- 2026: 1.443 commit ke master, 1.169 di-back-patch ke REL_19_STABLE.
- Cabang satu versi lebih tua: 248 commit ke REL_17_STABLE di 2025, lalu 433 ke REL_18_STABLE di 2026.

Back-patch itu kerjaan yang muncul ketika sebuah bug ternyata kena versi yang sudah dipakai produksi, bukan cuma versi yang lagi digarap. Jumlah fix di cabang rilis naik 61,5%. Yang di cabang sebelumnya naik 74,6%.

Commit yang cuma mendarat di master turun dari 313 di 2025 jadi 274 di 2026. Jadi kerja baru yang masuk malah lebih sedikit, sementara porsi yang isinya perbaikan jauh lebih besar.

Haas sempat mempertimbangkan kemungkinan committer-nya memang lebih banyak salah tahun ini, lalu membuang kemungkinan itu. Orang-orang yang me-review patch PostgreSQL kurang lebih sama konservatifnya di 2026 dan 2025. Yang berubah cuma seberapa cepat kesalahan mereka ketemu.

## Laporannya bukan sampah

Penjelasan yang paling gampang diterima: ini semua noise dari AI, terlalu banyak laporan jelek, committer tenggelam. Bacaan itu nggak tahan lama begitu laporannya dibuka satu-satu.

HN user tibbar menghabiskan satu musim panas buat bug hunting di Postgres pakai bantuan AI. Soal seberapa banyak temuannya, dia nulis:

> The list got so long that I had to triage what I even had time to report, and settled for a dozen or two out of hundreds of candidates.

Isi tumpukannya bukan hal sepele:

- anomali serialisasi di level SERIALIZABLE, termasuk write skew yang dua transaksinya sama-sama commit,
- pelanggaran integritas foreign key, salah satunya gara-gara lock yang lepas waktu toasting,
- bug planner seperti partition pruning yang membuang RANGE default partition,
- beberapa kandidat yang masuk wilayah CVE.

Laporan write skew itu yang paling gue saranin dibaca, buat siapa pun yang masih nganggep semua ini noise. Tid Range Scan, jalur akses yang masuk sejak PostgreSQL 14, bikin dua transaksi serializable membaca range yang sama dan dua-duanya lolos commit. Jadwalnya pendek:

```sql
-- dua sesi: BEGIN ISOLATION LEVEL SERIALIZABLE;
SET enable_seqscan = off;
SELECT sum(v) FROM trs WHERE ctid >= '(0,0)' AND ctid <= '(0,100)';  -- 0
-- tiap sesi update baris berbeda, dua-duanya COMMIT, total akhir = 2
-- nggak ada urutan serial yang menghasilkan 2; dua-duanya menghasilkan 3
```

Yang bikin laporan ini kepakai justru kontrol di reproducer itu. Matikan `enable_tidscan` di dua sesi supaya pembacaan yang sama dipaksa lewat sequential scan, dan commit kedua gagal dengan pesan "could not serialize access due to read/write dependencies among transactions".

Cuma ninggalin `enable_seqscan` tetap nyala juga nggak cukup, karena planner masih milih Tid Range Scan buat kondisi itu. Catatan pelapornya sendiri tegas: kontrol yang disusun begitu bukan kontrol.

Bug-nya nyata, reproducer-nya juga. Tapi buat memastikan itu benar-benar bug, orangnya harus paham planner cukup dalam sampai bisa nyusun kontrol yang valid.

Nggak semua orang sepakat dengan framing-nya. HN user ltbarcly3 cerita dia pernah nemu bug di beta akhir yang bikin satu cluster mati, jauh sebelum ada LLM. Menurutnya proyek ini mungkin over-reaksi ke cacat yang sebenernya bisa dibenerin saja.

Keberatan itu wajar. Pilihan antara patch atau revert memang keputusan engineering, dan refleks otomatis nggak cukup di situ.

## Nemu cacat itu murah, memastikannya nggak

Soal asimetri ini, Haas nyebutnya dengan nada datar: fix itu tetap harus di-review dan di-commit manusia, dan manusia-manusianya nggak jadi lebih pintar antara 2025 dan 2026.

Satu LLM bisa baca kode C empat puluh tahun dan ngajuin ribuan kandidat cacat, dalam waktu yang dibutuhin satu committer buat me-review satu patch.

Discovery naik beberapa orde, verifikasi nyaris nggak gerak sama sekali.

Sebabnya ada di apa yang sebenarnya dicek waktu review. Patch PostgreSQL nggak diterima cuma karena test-nya hijau. Patch diterima karena ada orang yang nelusuri urutan lock dan ngecek interaksinya sama snapshot MVCC. Baru setelah itu dia memutuskan fix-nya aman dipasang ke cabang stable yang sudah rilis bertahun-tahun sebelumnya.

Patch bikinan LLM yang ngelanggar coding standard cuma bikin repot saat review. Patch yang diam-diam ngubah urutan pengambilan lock, itu outage enam bulan kemudian.

## Tagihannya datang dalam bentuk fitur yang dicabut

Efek turunan kedua yang Haas sebut: jam review yang seharusnya dipakai buat audit fitur rilis malah kepakai buat beresin cabang lama. Akibatnya masalah fitur ketahuan lebih telat, dan ruang buat membetulkannya makin sempit.

Revert itu gejalanya. Penyebabnya antrean yang nggak pernah disiapin kapasitasnya.

Buat proyek dengan jumlah committer yang tetap, hitungannya sesederhana itu. Setiap jam buat memutuskan sebuah laporan itu bug asli atau bukan, itu jam yang nggak dipakai buat rilis.

Kalau volume masuk naik lebih cepat dari kapasitas review, harus ada yang dikorbankan. Yang pertama biasanya kode paling baru, karena justru itu yang paling sedikit punya tahun-tahun mata orang di atasnya.

## Yang bakal gue ubah

Gue jalanin PostgreSQL buat Dagango.com di Linux bare metal. Gue juga jalanin fleet agent yang ngajuin perubahan dan bikin temuan QA ke codebase sendiri.

Pelajaran yang gue dapet dalam seminggu pertama: bagian mahalnya bukan generate perubahan, tapi memutuskan mau percaya atau nggak.

Empat hal yang gue pasang sebelum ngarahin fleet agent ke codebase yang bug-nya beneran penting:

- **Hitung jam review-nya, bukan jumlah generate-nya.** Jam manusia per fix yang diterima jadi metrik utama. Kalau angka itu naik sementara pull request agent naik lebih cepat, throughput-nya nggak membaik.
- **Bikin pertanyaan "ini asli nggak?" jadi murah.** Harness yang bisa nyalain versi persis di container mengubah laporan cacat jadi putusan dalam hitungan menit.
- **Pisahkan berdasarkan dampak.** Data loss dan pelanggaran serialisasi langsung naik antrean. Temuan gaya nunggu dibatch.
- **Simpan semua regresi yang sudah dikonfirmasi.** Tiap bug yang terverifikasi jadi test, dan korpus itu satu-satunya aset yang bikin seribu laporan berikutnya lebih murah ditriase.

## Tahap paling sempit yang nentuin throughput

PostgreSQL kemungkinan besar bakal jawab ini lewat proses dan tooling: bantuan triage, semua reproducer dijalanin otomatis, plus obrolan berat soal berapa banyak yang wajar diserap satu maintainer per minggu. Apa pun yang mereka pilih, isinya bakal verification infrastructure.

Bentuk umumnya berlaku buat tim mana pun yang jalanin agent. Fleet AI melipatgandakan jumlah perubahan dan temuan yang nyampe ke manusia. Jumlah manusianya nggak ikut dilipatgandakan.

Throughput tetap ditentukan tahap paling sempit, dan di hampir semua organisasi tahap itu punya nama dan kalender.

Haas nutup tulisannya dengan bilang dia dan banyak orang lain sedang kerja keras nyari jawabannya. Buat kita yang juga jalanin fleet agent, pertanyaannya sama. Nemu bug sekarang hampir gratis. Fix yang bisa dipercaya masih mahal, dan di situlah semua waktu kita bakal habis.
