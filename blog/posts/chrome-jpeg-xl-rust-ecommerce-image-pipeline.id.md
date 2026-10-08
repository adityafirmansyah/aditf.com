---
title: "Chrome 155 Akhirnya Dukung JPEG XL Pakai Rust: Ini Dampaknya buat Pipeline Gambar E-Commerce"
slug: chrome-jpeg-xl-rust-ecommerce-image-pipeline
date: 2026-10-08
excerpt: Chrome 155 balik dukung JPEG XL setelah dicabut 2022, kali ini decodernya ditulis ulang pakai Rust. Buat platform yang pernah kena masalah encoding AVIF, format ini layak dilirik ulang.
tags: web-performance, rust, ecommerce, browsers, architecture
---

## Google nge-hapus format ini di 2022, sekarang balikin lagi

Chrome nyabut JPEG XL tahun 2022. Alasan resminya waktu itu, katanya ekosistemnya kurang peminat.

6 Oktober 2026, Chrome 155 ngebalikin dukungan itu.

Thread di HN yang bahas ini tembus 500+ poin dan 350+ komentar. Salah satu komentar paling nyelekit nebak isi dapurnya: eksekutif Google nggak butuh diyakinin lewat argumen teknis, mereka nyerah aja begitu semua browser lain udah dukung duluan.

Safari udah dukung JPEG XL sejak September 2023. Firefox lagi nyusul. Chrome tinggal satu-satunya browser tier-1 yang belum, dan itu yang bikin beda: format yang cuma jalan di Safari itu curiosity doang, bukan format yang bisa dipakai buat katalog produksi.

## Kenapa Chrome butuh Rust buat bilang iya

Yang nahan Chrome bukan soal kualitas kompresinya. Yang nahan itu `libjxl`, reference decoder C++ sepanjang kurang lebih 100.000 baris.

Chromium ngejalanin byte yang nggak dipercaya dari internet lewat decoder-decoder itu di dalam renderer process.

Ini persis skenario yang bikin dokumen keamanan Chromium sendiri bunyi alarm. Dokumen itu namanya "Rule of Two": maksimal boleh pilih dua dari tiga hal berikut.

- Input yang nggak dipercaya.
- Bahasa implementasi yang nggak aman.
- Privilege yang tinggi.

Decoder gambar C++ yang baca byte dari internet terbuka, jalan di privilege renderer, itu kena ketiganya.

Jawaban Google: `jxl-rs`, decoder yang ditulis ulang total pakai Rust.

Pengumuman resmi Chrome sendiri jelas soal tradeoff yang nggak mau mereka ambil:

> "Memory safety is crucial, but a memory-safe decoder that is approximately as fast as the best non-memory-safe alternative is a much more obvious choice than a choice with a significant performance compromise."

Buat nyampe situ, Rust-nya butuh `target_feature_11`, fitur yang harus di-stabilize dulu, biar akselerasi SIMD bisa jalan tanpa blok `unsafe`. Nah ini bagian yang menurut gue paling menarik, bukan sekadar "Rust itu bagus". Ini satu fitur compiler spesifik yang baru landing justru biar tim keamanan bisa ngirim decoder sekritis ini tanpa jalan pintas ke kode unsafe.

## Format yang seharusnya jadi peran AVIF buat katalog

Nah ini bagian yang sering kelewat di benchmark compression yang biasa dipamerin frontend. Angka 30-50% lebih kecil dari JPEG yang AVIF klaim itu angka di sisi browser.

Dapetin angka itu di server, ceritanya beda.

Encoding AVIF itu berat di CPU, apalagi di quality setting yang masuk akal buat di-ship. Kita ngerasain ini langsung: merchant di Dagango.com bulk upload ratusan foto produk dalam satu kali import, dan itu jadi ledakan job encode yang nabrak worker pool yang sama, dalam waktu bersamaan.

Encode JPEG buat batch yang sama kelar dalam sepersekian waktu yang dibutuhin AVIF, di quality target yang sebanding. Kali-in gap itu sama beberapa ratus gambar yang masuk dalam lima menit yang sama, dan job AVIF-nya numpuk di queue, bukan di sisi decode yang jadi arena pertarungan browser.

Itu biaya server-side yang nggak pernah keliatan di benchmark compression, karena benchmark cuma bandingin ukuran byte hasil, bukan berapa detik CPU yang kepake buat ngehasilin byte itu.

JPEG XL nggak ngilangin biaya itu. JPEG XL cuma bikin biaya itu nggak perlu dibayar dari awal.

## Lossless JPEG transcoding, ini jalan migrasi yang sebenarnya

JPEG XL bisa repack koefisien DCT dari JPEG yang udah ada, bit demi bit, langsung masuk container `.jxl`.

- Nggak perlu re-encode.
- Nggak ada degradasi kualitas antar generasi, yang biasanya numpuk tiap kali gambar lossy di-decode terus di-save ulang.
- Pengurangan ukuran nyata sekitar 20%, dari hasil transform, bukan dari compress ulang.

Buat platform multi-tenant yang nyimpen foto merchant selama bertahun-tahun, ini jalan migrasi yang sebenarnya kepake. Kita nggak nyuruh background worker ngulang encode katalog dari piksel. Kita cuma ngerepack bitstream-nya.

Bandingin sama jalan AVIF: tiap gambar di katalog butuh satu putaran penuh decode-lalu-encode buat dapet file lebih kecil, kena biaya CPU AVIF, dan gambar lossy-nya dikit lebih jelek tiap kali lewat putaran itu. Transcode lossless JPEG XL skip semua itu sekaligus, buat setiap JPEG yang udah nangkring di storage.

## Progressive decode tanpa butuh pipeline thumbnail

Bitstream JPEG XL itu progresif dari desainnya sendiri. Browser bisa render preview resolusi rendah dari potongan byte pertama, terus makin nyempurnain seiring sisanya datang, tanpa server perlu bikin aset thumbnail terpisah.

Buat pembeli yang koneksinya dibatasin, kayak di Asia Tenggara, itu beda antara kartu produk kosong sama kartu produk yang udah bisa dikenali walaupun gambarnya masih streaming. Ini juga ngilangin satu kelas infrastruktur sekaligus: nggak perlu matrix ukuran thumbnail yang harus di-generate, disimpan, terus dijaga sinkron sama originalnya.

Satu komentator di HN nutup diskusi paling tajam di thread itu dengan versi paling simpel dari kemenangan ini. Situs art dan katalog yang paling untung dari JPEG XL, karena mereka bisa ngerepack ulang semua JPEG yang udah mereka punya secara lossless, hampir tanpa biaya.

## Yang bakal gue pakai

Jangan buru-buru buang AVIF. Tetap pakai di tempat biaya encode-nya udah ke-amortisasi, kayak foto editorial atau hero image yang di-encode sekali tapi dilayanin jutaan kali.

Arahin JPEG XL khusus ke masalah yang justru dibikin lebih parah sama AVIF: jalur upload katalog merchant, tempat ribuan JPEG masuk dalam ledakan dan harus diproses murah, cepat, tanpa kehilangan kualitas.

Dukungan browser akhirnya nyampe tier-1 itu headline-nya. Keputusan yang beneran relevan buat platform kayak kita lebih sempit dari itu: pakai transcode lossless JPEG XL buat berhenti bayar pajak encode AVIF buat konten yang dari awal nggak perlu di-encode ulang.

Buat gue sendiri, cerita JPEG XL ini ngingetin satu hal. Keputusan format gambar itu bukan soal mana yang paling kecil di atas kertas, tapi mana yang nggak bikin worker pool lo kebakar pas lagi musim merchant rame-rame upload katalog. 😅

