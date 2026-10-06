---
title: Jebakan Session Poisoning di SQLAlchemy saat Bulk Import CSV
slug: sqlalchemy-session-poisoning-bulk-csv-import
date: 2026-10-06
excerpt: Satu baris gagal di bulk import bisa ngerusak session SQLAlchemy yang dipakai bareng dan ngebunuh 497 baris berikutnya. Ini fix siklus hidup session yang sebenarnya, lengkap angka dari PostgreSQL 18.6 asli.
tags: python, sqlalchemy, postgresql, backend, architecture
---

## Baris gagal nggak boleh ngejatuhin baris lain

Baris ke-3 dari import CSV 500 baris kena unique constraint.

Insert-nya error, lo catat, terus lanjut ke baris ke-4. Baris ke-4 balik bawa error session. Baris ke-5 juga.

Semua baris setelahnya ikut mati. Import "partial success" lo berubah jadi gagal total, dan database cuma nyimpen dua produk padahal 497 harusnya masuk.

Itu jebakannya. Dan buat keluar dari situ lo nggak butuh Celery, Redis, atau background worker.

Ini cuma bug siklus hidup transaksi, dan obatnya lebih kecil daripada kerusakan yang dia bikin.

Gue kena waktu bangun fitur bulk import CSV produk buat Dagango.com, platform e-commerce Next.js/FastAPI.

Daripada langsung lari ke async queue, gue jalanin spike lawan PostgreSQL 18.6 asli. Gue mau tau apakah batching synchronous dengan session recovery yang bener bakal tahan. Ternyata iya.

## Yang di-abort Postgres itu transaksinya, bukan statement-nya

Satu statement yang error di dalam transaction block bukan cuma bikin statement itu gagal. PostgreSQL nandain seluruh transaksinya aborted.

Semua command setelahnya dapet ini:

```
25P02: current transaction is aborted, commands ignored until end of transaction block
```

Kelas 25 itu `invalid_transaction_state`, dan `25P02` itu `in_failed_sql_transaction`. Ini perilaku Postgres yang terdokumentasi, bukan flag yang bisa lo matiin.

Errornya ada di level transaksi, bukan level statement, dan justru itu alasan blok `try` per statement nggak bisa nyelametin lo.

Error yang lo liat berikutnya tergantung cara lo ngomong ke database. Detail ini penting:

- **Loop `Session.execute()` mentah:** statement berikutnya naikin `sqlalchemy.exc.InternalError` dengan sqlstate `25P02`, ngebungkus `psycopg.errors.InFailedSqlTransaction`.
- **Loop ORM `add` + `commit`:** `commit()` berikutnya naikin `sqlalchemy.exc.PendingRollbackError`.

Dua-duanya masalah yang sama, "lo belum rollback".

Nggak ada yang `IntegrityError`. Jadi `except IntegrityError: continue` nggak akan pernah nangkep, dan import-nya mati di baris ke-4.

## rollback() itu udah cukup, satu baris

Fix-nya satu baris. Beneran cuma satu:

```python
db.rollback()
```

Itu panggilan yang pentingnya nyata, dan dia ngerjain dua tugas sekaligus. Dia nurunin status transaksi Postgres dari aborted jadi sehat, dan dia buang graph objek yang masih pending.

Di SQLAlchemy 2.0, `Session.rollback()` ngejalanin `SessionTransaction._restore_snapshot`, yang nge-expunge state baru session dan nandain mereka transient:

```python
to_expunge = set(self._new).union(self.session._new)
self.session._expunge_states(to_expunge, to_transient=True)
```

Jadi produk yang gagal, gambar-gambarnya, dan varian-variannya keluar dari session bareng rollback-nya. Nggak ada hantu setengah-pending yang nangkring buat nempel lagi di insert berikutnya.

Di sinilah banyak nasihat, termasuk komentar yang nyempil di kode gue sendiri, salah.

Yang umum dilakukan orang: habis `rollback()` terus tambahin `db.expunge_all()`, dengan teori rollback doang nyisain objek basi. Di SQLAlchemy 2.0 teori itu salah.

Matriks recovery-nya gue konfirmasi di stack asli. Hasilnya begini buat baris berikutnya:

- `rollback()` doang → **OK**.
- `expunge_all()` doang → GAGAL (`PendingRollbackError`).
- `rollback()` + `expunge_all()` → OK.
- Nggak dua-duanya → GAGAL (`PendingRollbackError`).

Dua hal langsung kelihatan dari situ:

- `expunge_all()` sendirian nggak bahkan nurunin status transaksi yang aborted, makanya gagal sendiri.
- Begitu lo udah rollback, nambahin `expunge_all()` nggak ngubah apa-apa.

Itu cuma kehati-hatian ekstra. Mau dipertahanin silakan, tapi dia bukan fix-nya, dan nggak dipakai pun baris berikutnya lo nggak akan keracunan.

Setelah rollback, session-nya terverifikasi bersih. Ini angka yang dicek di spike:

- `is_active=True`
- `in_transaction=False`
- `new`, `dirty`, `deleted` semuanya nol
- `identity_map` nol

Itu syaratnya biar baris ke-4 bisa sukses.

## Biaya nyata 500 baris di Postgres 18.6

Gue jalanin loop importer asli lawan PostgreSQL 18.6 asli di schema sementara, dengan baris multi-relasi yang realistis: produk, kombinasi varian, URL gambar. Habis itu schema-nya gue drop.

Recovery yang dipakai cuma `rollback()` polos. Enam dari enam skenario lolos.

Kasus gagalnya pakai pelanggaran unique constraint asli dari Postgres, bukan simulasi:

- 1 baris gagal dari 10 → tepat 9 produk kebentuk
- 2 baris gagal dalam satu jalan → tepat 8 produk kebentuk
- nol gambar atau varian yatim di dua kasus itu

Tiap produk yang selamat bawa gambar dan kombinasi varian dari barisnya sendiri.

Sengaja gue tambahin steelman: partial flush di mana INSERT produk induknya sukses tapi anaknya gagal kena check constraint, dan `identity_map`-nya tetap nol. Cerita serem yang mungkin pernah lo denger, di mana baris ke-8 diam-diam mewarisi anak-anak baris ke-3, nggak muncul di konfigurasi mana pun yang gue tes.

Lalu angka throughput yang nyelesain pertanyaan arsitekturnya:

- 500 baris commit secara synchronous dalam sekitar 5 detik
- min ≈ 8 ms/baris, p50 ≈ 10 ms, p95 di kisaran puluhan ms bawah
- 500/500 commit, 0 error

Lima detik kerja synchronous masih nyaman di dalam timeout HTTP request normal. Cap import-nya sengaja dibatasi 500 baris data dan body 2 MiB, dan itu ditolak sebelum ada baris yang ditulis. Jadi ini kerjaan beberapa detik, bukan risiko timeout.

## Tabrakan slug yang ternyata nggak bikin gagal

Gue awalnya ngira judul produk duplikat di CSV bakal meledak di unique constraint slug. Spike-nya mengoreksi gue.

`slugify.unique_slug` baca ulang slug tenant yang udah kepakai di tiap percobaan, terus tambahin `-2`, `-3`, `-4`, tanpa batas. Judul duplikat, bukan error, dia jadi produk kedua dengan slug bernomor.

`SlugAllocationFailed` itu hasil dari race concurrency. Buat ngehabisin tiga percobaan alokasi, set slug tenant harus berubah di antara pembacaan dan INSERT. Itulah race concurrent-create-nya.

Jadi laporannya nunjukin slug yang beneran dialokasikan ke operator, termasuk yang bersufiks `-2`, daripada ngegagalin baris yang sebenarnya sehat.

## Kebocoran upstream yang layak disebut

Ada satu batasan yang nggak gue tutupi. Retry di creator-nya membungkus `except IntegrityError` yang nggak difilter per constraint.

Semua kegagalan integritas di INSERT itu, entah foreign key, NOT NULL, atau unique constraint lain, di-retry tiga kali terus muncul sebagai `SlugAllocationFailed`.

Importer-nya nglaporin kode itu apa adanya dan nggak ngeklaim lebih dari yang diketahui creator. Mempersempitnya itu tanggung jawab `create_product`, bukan unit import. Jadi gue sebutin terang-terangan daripada disembunyiin.

## Intinya

Ini bagian yang layak lo bawa ke importer lo sendiri.

Recovery-nya nggak eksotis, dan bukan dua baris. Cukup `db.rollback()`, sekali per baris gagal, dan SQLAlchemy 2.0 ngerjain bersih-bersih graph-nya buat lo di dalam panggilan itu.

Ukur dulu biaya per baris lo sebelum lari ke background queue. Import synchronous lima detik dengan plafon baris yang jelas itu barang yang lebih ringan diurus daripada sekawanan worker.

State session lo sendiri satu-satunya hal yang wajib lo benerin.
