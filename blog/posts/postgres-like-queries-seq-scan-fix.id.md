---
title: Kenapa Query LIKE di Postgres Diam-Diam Seq Scan (dan Fix Satu Barisnya)
slug: postgres-like-queries-seq-scan-fix
date: 2026-09-25
excerpt: Di Postgres default en_US.UTF-8, index UNIQUE (tenant_id, slug) nggak bisa dipakai buat query LIKE 'prefix%'. Ini angka benchmark di 20.000 baris dan index varchar_pattern_ops yang benerin semuanya.
tags: postgresql, database, backend, performance, optimization, sql
---

Lo punya index `UNIQUE (tenant_id, slug)` dan lo nyangka query `WHERE slug LIKE 'kaos%'` otomatis bakal pakai index itu. Di Postgres standar Ubuntu, anggapan itu salah. Jebakan ini mahal, dan gue udah kena.

Query lo kencang di dev. Unit test berbasis SQLite lo lewat dalam mikrodetik, jadi nggak ada satu pun yang curiga ada yang salah. Semua lampu hijau.

Terus katalog produksi lewat sepuluh ribu baris, dan tiap lookup slug diam-diam berubah jadi full table scan.

Gue kena persis di titik ini waktu bikin slug produk yang readable buat platform e-commerce multi-tenant. Query pengecekan collision-nya jalan normal, di lokal keliatan instan.

Baru pas dites di Postgres 18.6 beneran, dengan 20.000 produk buat satu tenant, yang keluar malah ini:

```
Seq Scan on products
  Filter: tenant_id = 1 AND slug ~~ 'kaos%'
  Rows Removed by Filter: 22000
  Buffers: shared hit=256
  Execution Time: 4.52 ms
```

Semua baris, tiap request. Index-nya ada di situ. Postgres cuma nolak pakai.

## Index-nya Memang Nggak Eligible

Penyebabnya collation. Dan buat jelas dari awal: ini bukan bug Postgres.

Index B-tree standar di kolom `text` atau `varchar` dibangun pakai collation database. Di mayoritas distro Linux, default-nya `en_US.UTF-8`. Itu collation linguistik, artinya dia ngurutin sesuai aturan bahasa, bukan byte mentah.

Nah, `LIKE` itu murni byte-based. Postgres nggak mungkin pakai index yang urutannya linguistik buat jawab pertanyaan soal rentang byte. Jadi ya dia jatuh ke scan penuh.

- Di collation linguistik, huruf besar-kecil dan aksen saling nyempil sesuai aturan budaya, jadi urutan byte beda dari urutan index.
- `LIKE 'prefix%'` butuh rentang byte yang contiguous.
- Begitu urutan index bukan urutan byte, nggak ada rentang yang bisa dijamin, dan planner milih nyerah.

Jadi solusinya bukan "bikin index lagi yang sama". Solusinya ngasih Postgres satu index yang urutannya byte, khusus buat kolom itu. Intinya lo bilang gini: buat kolom ini, urutin pakai byte mentah, biar rentang prefix-nya klop.

## Fix-nya Cuma Satu Baris

Postgres udah nyediain operator class buat kasus ini, namanya `varchar_pattern_ops`.

```sql
CREATE INDEX idx_products_tenant_slug_prefix
  ON products (tenant_id, slug varchar_pattern_ops);
```

Ini bukan pengganti unique constraint lo. Ini index tambahan, dan plan-nya langsung berubah begitu dia dibuat:

```
Index Only Scan using idx_products_tenant_slug_prefix on products
  Index Cond: (tenant_id = 1 AND slug ~>=~ 'kaos' AND slug ~<~ 'kaot')
  Heap Fetches: 0
  Buffers: shared hit=3
  Execution Time: 0.39 ms
```

Perhatiin apa yang planner lakuin ke `LIKE` lo. Dia tulis ulang jadi perbandingan rentang, `slug ~>=~ 'kaos' AND slug ~<~ 'kaot'`. Operator `~>=~` dan `~<~` itu byte-ordering yang dipunya pattern_ops. Scan-nya cuma nyentuh tiga buffer, bukan 256.

Dibandingin Seq Scan tadi, itu **speedup 11,6x**. Yang lebih penting: sifatnya flat. Query lama biayanya naik terus seiring tabel membesar. Yang ini tetap O(log N), berapapun produk yang ditambah tenant.

## Kenapa Test Lo Nggak Pernah Nangkep

Ada dua alasan, dan dua-duanya bareng-bareng nyembunyiin bug itu sampai ke produksi.

Yang pertama soal ukuran. Seq Scan di 50 baris selesai dalam sekitar 0,05 ms. Nggak ada yang lambat di situ. Dia baru lambat pas skalanya udah gede, jadi database dev yang kecil nggak akan pernah nunjukin masalahnya ke lo.

Yang kedua SQLite. Kalau suite FastAPI atau SQLAlchemy lo jalan di SQLite in-memory, lo sebenernya nggak lagi nguji perilaku index Postgres sama sekali. SQLite nggak punya operator class B-tree yang bergantung locale. Query yang di Postgres jadi Seq Scan, di situ jalan lancar-lancar aja.

Test lo hijau, staging lo kosong, dan bug-nya lolos rilis tanpa ada yang sadar.

Pelajaran-nya bukan "Postgres lambat". Pelajaran-nya lebih halus dari itu: index di kolom yang lo query nggak sama dengan index yang bisa jawab query lo. Collation yang nentuin apakah dua hal itu cocok.

## Dua Edge Case yang Nanti Gigit

**Lo tetap butuh dua-duanya.** Index `varchar_pattern_ops` nggak bisa njamin uniqueness di collation linguistik. B-tree standar nggak bisa ngerjain prefix matching. Kerjaannya beda:

- Constraint `UNIQUE (tenant_id, slug)` ngelindungin integritas data.
- Index `varchar_pattern_ops` bikin prefix lookup kencang.

Butuh dua jaminan itu? Ya simpen dua index. Di collation non-C, nggak ada satu index yang bisa ngerjain dua-duanya sekaligus.

**Slug yang di-cap bikin prefix naif kacau.** Misal slug lo dibatasi 70 karakter, terus lo mundur ke hyphen terakhir biar nggak motong kata. Efeknya, kandidat `-2` nggak selalu jadi prefix persis dari base-nya. Jadi query-nya arahin ke batang yang stabil:

```sql
SELECT slug FROM products
WHERE tenant_id = :t AND slug LIKE :stem || '%'
```

Pakai `base[:62]` sebagai `:stem`, bukan base penuh yang udah di-cap. Kalau nggak, pengecekan collision lo nggak bisa lihat kandidat yang seharusnya ketemu, dan lo rilis data duplikat tanpa sadar.

## Yang Bisa Lo Cek Minggu Ini

Cek apakah ada query `LIKE 'prefix%'` di kolom text yang punya index `pattern_ops` pasangannya. Di database `en_US.UTF-8` default, kemungkinan besar nggak ada.

Lo bisa lihat daftar index di kolom slug lo, sekalian mastiin operator class yang kepakai:

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'products';
```

Kalau index unique composite-nya muncul tanpa `varchar_pattern_ops`, artinya query prefix lo nggak pakai dia. Tambahin index operator-class di sebelahnya, terus jalanin `EXPLAIN (ANALYZE, BUFFERS)` sebelum dan sesudah. Plan-nya harusnya pindah dari `Seq Scan` dengan jumlah baris yang naik terus, jadi `Index Only Scan` dengan buffer read satu digit.

Satu baris, satu index, dan scan-nya hilang. Index yang dari awal lo punya memang nggak pernah eligible.

Dan lo nggak akan pernah tau kalau nggak ngecek plan-nya. Query yang tetap "jalan" itu justru yang paling bahaya. Nggak ada error, nggak ada warning. Cuma latency yang naik pelan-pelan seiring katalog lo tumbuh, dan waktu akhirnya ada yang sadar, semuanya udah kelihatan lambat dan nggak ada yang tau kenapa.

Makanya gue sekarang selalu jalanin `EXPLAIN (ANALYZE, BUFFERS)` buat tiap query prefix sebelum naik ke produksi. Bukan pas udah lambat. Sebelum. Kebiasaan kecil, tapi nyelametin banyak insiden tengah malam.
