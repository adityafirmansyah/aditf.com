---
title: "Chrome 155 Akhirnya Dukung JPEG XL Pakai Rust: Ini Dampaknya buat Pipeline Gambar E-Commerce"
slug: chrome-jpeg-xl-rust-ecommerce-image-pipeline
date: 2026-10-08
excerpt: Chrome 155 balik dukung JPEG XL setelah dicabut 2022, kali ini decodernya ditulis ulang pakai Rust. Buat platform yang pernah kena masalah encoding AVIF, format ini layak dilirik ulang.
tags: web-performance, rust, ecommerce, browsers, architecture
---

## Google jilat ludah sendiri soal JPEG XL

2022, Chrome nyabut dukungan JPEG XL. Alasannya waktu itu: katanya nggak ada yang minat.

6 Oktober 2026, lewat Chrome 155, Google balik lagi ke format yang sama.

Thread HN yang ngebahas ini tembus 500+ poin, 350+ komentar. Satu komentar yang paling nancep nebak apa yang sebenernya kejadian di internal Google: eksekutifnya nggak butuh diyakinin pakai argumen teknis. Begitu semua browser lain udah dukung, mereka tinggal nyerah aja.

Masuk akal sih. Safari udah pegang JPEG XL sejak September 2023, Firefox juga lagi nyusul.

Jadi Chrome itu tier-1 terakhir yang nahan. Dan itu yang penting: format yang cuma idup di Safari doang, itu cuma trivia. Begitu Chrome ikut, baru format itu bisa dipakai buat katalog produksi sungguhan.

## Rust jadi syarat, bukan bonus

Yang bikin Chrome dulu nggak mau pakai JPEG XL bukan soal kualitas kompresinya. Soalnya ada di `libjxl`, reference decoder-nya, yang ditulis dalam C++ sepanjang kurang lebih 100.000 baris.

Masalahnya, decoder gambar itu kerjanya baca byte dari internet yang nggak dipercaya sama sekali, dan dia jalan di dalam renderer process yang privilege-nya tinggi.

Chromium punya dokumen keamanan sendiri buat kasus kayak ini, namanya "Rule of Two". Aturannya: lo cuma boleh pegang maksimal dua dari daftar berikut.

- Input yang nggak dipercaya.
- Bahasa implementasi yang nggak aman.
- Privilege yang tinggi.

Decoder gambar C++ yang baca byte sembarangan dari internet, jalan di privilege tinggi. Itu udah melanggar semua tiga syarat sekaligus. Nggak ada cara buat lolos dari aturan itu selain ganti salah satu dari tiga variabelnya.

Makanya Google bikin `jxl-rs`, nulis ulang total decoder-nya pakai Rust. Soal kenapa mereka nggak mau kompromi di performa, pengumuman resmi Chrome bilang gini:

> "Memory safety is crucial, but a memory-safe decoder that is approximately as fast as the best non-memory-safe alternative is a much more obvious choice than a choice with a significant performance compromise."

Jadi logikanya: Rust aman, tapi kalau lambat, orang bakal tetap milih C++ yang berisiko. Makanya targetnya bukan "aman tapi lambat", tapi "aman dan secepat yang nggak aman".

Buat nyampe situ, mereka butuh `target_feature_11`, fitur Rust yang baru di-stabilize, biar SIMD bisa jalan tanpa blok `unsafe`. Ini bagian yang gue anggap paling menarik dari seluruh cerita ini. Bukan "Rust itu keren", tapi satu fitur compiler yang landing tepat waktu buat ngirim decoder sekritis ini tanpa harus buka jalan pintas ke kode unsafe.

## Benchmark compression nggak pernah ngomong soal CPU server

AVIF selalu dipromosikan 30-50% lebih kecil dari JPEG. Itu benar, tapi angka itu diukur di sisi browser, pas lagi download.

Masalahnya nggak ada yang ngomong soal biaya nge-encode-nya di server.

Kita ngerasain ini langsung di Dagango.com. Merchant bulk upload ratusan foto produk dalam satu kali import, dan itu artinya ratusan job encode AVIF nabrak worker pool yang sama, dalam waktu bersamaan.

Encode JPEG buat batch yang sama kelar jauh lebih cepat dibanding AVIF, di quality target yang sebanding. Kalikan gap itu dengan beberapa ratus gambar yang masuk dalam lima menit yang sama. Yang numpuk itu queue job encode di server kita sendiri, bukan traffic decode di browser.

Itu biaya yang nggak pernah keliatan di benchmark compression manapun, karena benchmark cuma bandingin ukuran file hasil, bukan berapa detik CPU yang kepake buat ngehasilin file itu.

JPEG XL nggak nolong di titik ini juga, kalau lo encode dari nol. Tapi untungnya, buat katalog yang isinya JPEG lawas, lo nggak perlu encode dari nol sama sekali.

## Transcoding, bukan re-encode: ini jalan migrasi yang kepake

JPEG XL bisa ngambil koefisien DCT dari JPEG yang udah ada, terus langsung masukin ke container `.jxl`, bit demi bit, tanpa decode-encode ulang.

Tiga hal yang kita dapet dari ini:

- Nggak ada proses re-encode.
- Nggak ada degradasi kualitas antar generasi, yang biasanya numpuk tiap kali gambar lossy di-decode terus di-save ulang.
- Potongan ukuran nyata sekitar 20%, hasil dari transform, bukan dari compress ulang.

Ini jalan migrasi yang kepake buat platform multi-tenant yang nyimpen foto merchant bertahun-tahun. Kita nggak nyuruh background worker ngulang encode seluruh katalog dari piksel. Kita cuma ngerepack bitstream-nya aja.

Bandingin ini sama jalan AVIF, yang butuh satu putaran penuh decode-lalu-encode buat tiap gambar, kena biaya CPU-nya lagi, dan gambar lossy-nya malah dikit lebih jelek tiap kali lewat putaran itu. Transcode lossless JPEG XL skip semua masalah itu, buat semua JPEG yang udah nangkring di storage kita dari dulu.

## Progressive loading gratis, tanpa pipeline thumbnail

Bitstream JPEG XL itu progresif secara desain. Browser bisa langsung render preview resolusi rendah dari potongan byte pertama yang nyampe, terus makin nyempurnain seiring sisanya datang. Server nggak perlu bikin aset thumbnail terpisah buat ini.

Buat pembeli yang koneksinya pas-pasan, kayak banyak pengguna di Asia Tenggara, bedanya kerasa banget: antara liat kartu produk yang masih kosong, sama liat kartu produk yang udah bisa dikenalin walaupun gambarnya masih lagi streaming.

Satu komentator di HN nutup diskusi paling tajam di thread itu dengan kesimpulan yang paling pas. Situs art dan katalog yang paling untung dari JPEG XL, karena mereka bisa ngerepack ulang semua JPEG yang udah mereka punya secara lossless, hampir tanpa biaya.

## Yang bakal gue pakai, dan satu hal yang gue sadar belakangan

AVIF nggak usah dibuang. Tetap pakai di tempat biaya encode-nya udah ke-amortisasi, kayak foto editorial atau hero image yang di-encode sekali tapi dilayanin jutaan kali.

JPEG XL kita arahin khusus ke jalur yang paling kena masalah gara-gara AVIF: upload katalog merchant, tempat ribuan JPEG masuk dalam ledakan dan harus diproses murah, cepat, tanpa kehilangan kualitas.

Dukungan browser yang akhirnya nyampe tier-1 itu cuma headline-nya doang. Keputusan yang beneran kepake buat platform kayak kita lebih sempit dari itu. Pakai transcode lossless JPEG XL biar berhenti bayar biaya encode AVIF yang sebenarnya nggak perlu lo keluarin, buat konten yang dari awal nggak butuh di-encode ulang.

Dan ini yang gue sadar belakangan: masalah format gambar itu nggak pernah soal format mana yang paling efisien di atas kertas. Yang nentuin itu di mana biaya komputasinya jatuh, di CPU server lo, atau di layar HP pembeli lo. 😅
