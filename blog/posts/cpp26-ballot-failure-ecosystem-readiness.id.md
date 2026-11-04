---
title: Yang Bikin C++26 Gagal Bukan Fiturnya, Tapi Gate yang Nggak Bisa Lo Kontrol
slug: cpp26-ballot-failure-ecosystem-readiness
date: 2026-11-04
excerpt: Draft standar C++26 dilaporkan ditolak di ballot ISO gara-gara contracts. Pertanyaan yang lebih berguna: apa bedanya fitur yang lolos semua gate internal dengan fitur yang aman dijadikan sandaran oleh ekosistem?
tags: cpp, software-engineering, standards, systems-design, release-engineering
---

Draft standar C++26 dilaporkan ditolak di ballot ISO akhir Oktober 2026. Prosesnya makan dua belas minggu. Menurut salah satu anggota komite, hasil kayak gini nyaris belum pernah kejadian.

Gue nggak duduk di WG21, working group ISO yang ngembangin standar C++. Soal apakah contract assertion pantas masuk ke bahasa itu, gue nggak punya pendapat kuat.

Yang bikin gue tertarik justru bentuk kegagalannya.

Sebuah fitur udah lewat semua gate yang dipegang komunitasnya sendiri, terus mentok di gate terakhir: gate yang di dalamnya orang luar ikut punya suara.

Nah, itu masalah shipping sebelum jadi masalah bahasa. Tim platform di mana-mana ketemu tembok yang sama, cuma tanpa kemewahan dua belas minggu buat berdebat.

## Isi catatannya sebenarnya apa

Angkanya penting, jadi pelan-pelan aja.

Buat lolos, draft butuh dua pertiga suara participating member alias P-member, dan maksimal seperempat menolak. Draft ini gagal di dua-duanya sekaligus:

- 12 dari 20 suara P-member setuju, padahal dua pertiga dari 20 itu berarti 14.
- 9 dari 22 suara menolak, padahal batasnya cuma 5.

Salah satu kekurangan itu aja cukup buat menggagalkan draft. Penyebutnya beda karena 22 ikut menghitung observer member. Mateusz Pusz menghitung delapan dari sembilan suara negatif itu datang dari P-member, dan Iran yang statusnya observer member ada di sisanya.

Catatan resmi ISO-nya nggak dibuka ke publik.

Angkanya sendiri berasal dari post LinkedIn Robert Seacord dan artikel Pusz tanggal 25 Oktober. Tulisan wro.cpp yang merangkum keduanya menandai semua angka itu sebagai laporan yang belum dikonfirmasi.

Penolakannya solid. Angkanya sendiri masih sebatas klaim yang belum dikonfirmasi.

Jeda itu patut dicermati. Proses yang menentukan nasib sebuah bahasa, tapi hitungan suaranya cuma beredar sebagai kabar. Komentar national body juga tetap nggak dibuka.

Perdebatannya tetap jalan. Sampai 4 November, ceritanya muncul di front page Hacker News dengan 174 poin dan 74 komentar.

Komentarnya mayoritas memperdebatkan sifat keberatan itu. Ada yang melihatnya murni teknis. Ada yang bilang itu soal prosedur atau politik.

Andreas Fertig mewakili suara Jerman di komite. Dia bilang udah nyari di sistem ISO dan cuma nemu satu DIS lain yang pernah ditolak. DIS itu kepanjangan dari Draft International Standard.

Yang dia temukan: spesifikasi C++/CLI tahun 2006. Proyeknya dihentikan.

## Gate yang nggak bisa dipilih orang di ruangan itu

Komitenya sendiri sudah meloloskan draft ini ke tahap berikutnya pada Maret 2026 dengan contracts di dalamnya. Suaranya bahkan lebih dari mayoritas yang dibutuhkan.

Beberapa bulan kemudian, national body bilang no ke teks yang sama.

Artefak yang sama, pemilih yang beda. Yang berubah bukan teksnya, tapi siapa yang pegang suara. Orang yang menghabiskan bertahun-tahun di desainnya nggak punya suara di gate yang akhirnya menentukan.

Menurut Fertig, sejumlah national body menilai fitur ini belum siap rilis. Dia juga berpendapat paper-paper yang menolak cuma mengulang argumen lama tanpa menambah informasi baru.

Bedanya nyata. Kalau sebuah keberatan udah lo dengar dan lo tolak, dengar lagi nggak seharusnya me-reset keputusan. Kalau belum pernah, ya seharusnya dianggap baru.

Yang lebih susah dibantah justru berkas teknisnya. Paper WG21 itu pakai nomor, dan P4334R0 salah satu yang ditandatangani Stroustrup. Isinya menilai desain contracts bermasalah di tiga hal:

- belum diimplementasi,
- belum lengkap,
- belum dicoba dalam skala besar.

Pusz menambahkan satu detail: contract assertion di GCC 16 masih bergantung pada implementasi eksperimental dari bagian yang lagi disengketakan itu.

Baca dua hal itu bareng-bareng, dan lo dapat kondisi persis yang ditolak ballot. Sudah cukup jalan buat dicoba. Belum cukup mapan buat dijadikan sandaran.

## Semua jalan keluarnya tetap makan satu putaran

Direktif ISO yang dikutip di P4388R0 ninggalin empat rute:

- ballot ulang delapan minggu dengan draft revisi,
- committee draft revisi buat dikomentari,
- draft Technical Specification,
- atau proyeknya dibatalkan.

Keempatnya butuh rekomendasi dari WG21 dan keputusan dari ketua SC22. SC22 itu subkomite ISO yang menaungi bahasa pemrograman. Jadi nggak ada kompromi cepat yang bisa langsung diambil. Rapat WG21 berikutnya di Búzios, 16 sampai 21 November.

Terus ada batas waktunya. Proyek ini diregistrasi 2 Januari 2025, dan proyek ISO yang belum sampai tahap approval dalam 36 bulan otomatis dibatalkan. P4388R0 membaca satu perpanjangan yang diizinkan sebagai ruang sampai akhir 2027.

Nggak ada satu pun dari empat rute itu yang jadi rollback. Semuanya cuma menambah waktu.

## Tembok yang sama di dalam platform commerce

Di Dagango.com, perubahan berbahaya biasanya bukan yang susah ditulis. Yang berbahaya justru yang gampang ditulis, tapi nyentuh bagian sistem yang udah dipakai integrasi tenant.

Invariant harga contohnya bagus. Kodenya cuma beberapa baris. Yang susah bukan nulisnya, tapi menjaga artinya buat semua tenant yang invoice-nya membaca dari situ.

Buat nentuin siap atau nggaknya, gue selalu balik ke tiga pertanyaan ini:

- Siapa yang berwenang memutuskan apa yang terjadi ketika invariant-nya jebol buat tenant yang belum pernah kita temui?
- Siapa saja yang membaca output ini, termasuk yang di luar repo kita?
- Apa jalur fallback-nya, dan apakah rollback-nya butuh migrasi data?

Kalau satu pertanyaan belum ada jawaban tertulisnya, perubahan itu cuma tersedia. Belum jadi komitmen.

Buat perubahan kayak gini, gue mau flag file yang sengaja dibikin membosankan:

```yaml
pricing.invariants.enforce:
  default: off              # available to tenants, not committed to them
  enabled_for: [internal-smoke]
  on_violation: reject      # decided once, not left to each caller
  fallback: legacy_pricing_v2
```

Tiap baris menjawab satu pertanyaan tadi. Perilaku enforcement-nya ditulis eksplisit, nggak diwarisi dari yang kebetulan nulis caller-nya.

Kalau lo sudah sempat pakai fitur C++26, catatan Pusz masih berlaku. Belum ada yang perlu dibongkar, dan ballot ini nggak mengubah apa pun yang sudah dikirim compiler sekarang.

## Matang itu kelihatan dari mana

Aturan approval yang menuntut dua pertiga setuju dan membatasi penolakan di seperempat itu memang disengaja.

Logikanya biar minoritas yang punya keberatan serius bisa menghentikan rilis yang harus dijalani semua orang.

Aturan kayak begini mahal, dan C++ baru saja merasakan akibatnya. Kesimpulan Fertig sendiri: yang goyang itu kepercayaannya, sementara konsensus jalan di atas kepercayaan.

Gue mau memperluas sedikit. Gate yang cuma bertahan selama semua orang udah setuju dari awal itu sebenarnya nggak pernah kerja. Baik di komite bahasa, maupun di platform commerce yang lo kelola sekarang.
