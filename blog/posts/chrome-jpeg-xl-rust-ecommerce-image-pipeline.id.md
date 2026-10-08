---
title: "Chrome 155 Akhirnya Dukung JPEG XL Pakai Rust: Ini Dampaknya buat Pipeline Gambar E-Commerce"
slug: chrome-jpeg-xl-rust-ecommerce-image-pipeline
date: 2026-10-08
excerpt: Chrome 155 balik dukung JPEG XL setelah dicabut 2022, kali ini decodernya ditulis ulang pakai Rust. Buat platform yang pernah kena masalah encoding AVIF, format ini layak dilirik ulang.
tags: web-performance, rust, ecommerce, browsers, architecture
---

## Chrome 2026 nelen omongannya sendiri soal JPEG XL

Tahun 2022, Google nyabut dukungan JPEG XL dari Chrome. Alasannya: katanya peminatnya dikit.

6 Oktober 2026, lewat Chrome 155, mereka balik total ke keputusan itu. Format yang sama, dukungan penuh.

Thread HN soal ini rame, tembus 500+ poin dan 350+ komentar. Ada satu komentar yang menurut gue paling nancep nebak apa yang kejadian di internal Google: bukan argumen teknis yang akhirnya ngubah pikiran eksekutifnya, mereka cuma nyerah pas semua browser lain udah dukung duluan.

Masuk akal juga kalau dipikir-pikir. Safari malah udah pegang JPEG XL duluan sejak September 2023, dan Firefox tinggal nyusul. Chrome jadi satu-satunya browser tier-1 yang masih nahan, dan itu yang penting, karena format yang cuma idup di satu browser doang statusnya masih sebatas trivia, belum layak dipakai buat katalog produksi sungguhan.

## Rule of Two: kenapa kompresi bagus doang nggak cukup

Chromium punya satu prinsip keamanan sendiri namanya "Rule of Two". Isinya: kalau kode lo berurusan sama data yang nggak dipercaya lo cuma boleh pegang maksimal dua dari tiga hal berikut.

- Input yang nggak dipercaya.
- Bahasa implementasi yang nggak aman.
- Privilege yang tinggi.

Nah, decoder JPEG XL yang lama kena semua itu sekaligus: baca data gambar langsung dari internet terbuka, ditulis pakai C++, dan jalan di renderer process yang privilege-nya tinggi. Itu akar masalahnya, bukan soal rasio kompresi, yang dari awal emang nggak pernah jadi soal. Decoder referensinya sendiri, `libjxl`, bukan kode kecil: kurang lebih 100.000 baris C++.

Satu-satunya jalan keluar: tulis ulang total pakai bahasa yang aman. Makanya Google bikin `jxl-rs`, decoder penuh versi Rust. Soal tradeoff performa yang mereka tolak, pengumuman resmi Chrome nggak basa-basi:

> "Memory safety is crucial, but a memory-safe decoder that is approximately as fast as the best non-memory-safe alternative is a much more obvious choice than a choice with a significant performance compromise."

Logikanya gini: kalau decoder-nya aman tapi lambat, orang bakal tetep milih versi C++ yang berisiko demi performa. Makanya target Google bukan "aman meski lambat", tapi "aman dan secepat yang nggak aman".

Buat nyampe situ, mereka butuh satu fitur Rust yang namanya `target_feature_11`, yang harus di-stabilize dulu biar SIMD bisa jalan tanpa blok `unsafe`. Ini bagian yang paling menarik menurut gue dari seluruh cerita ini. Bukan soal "Rust itu keren", tapi soal satu fitur compiler spesifik yang landing di waktu yang pas, buat ngirim decoder sekritis ini tanpa harus bikin jalan pintas ke kode unsafe.

## Yang nggak pernah disebut benchmark compression: ongkos CPU di server

Merchant Dagango.com rutin bulk upload ratusan foto produk sekali import. Kalau encoder-nya AVIF, ratusan job itu nabrak worker pool yang sama dalam waktu bersamaan, dan AVIF itu berat banget di CPU, apalagi di setting kualitas yang emang layak di-ship.

Encode JPEG buat batch yang sama bisa kelar jauh lebih cepat dari AVIF, di kualitas yang sebanding. Kalikan selisih itu dengan ratusan gambar yang masuk bersamaan dalam lima menit, dan yang numpuk bukan trafik decode di sisi browser pembeli. Yang numpuk itu queue job encode di server kita sendiri.

Padahal angka yang sering dipamerin itu 30-50% lebih kecil dari JPEG, dan itu beneran benar. Masalahnya, angka itu diukur pas file-nya udah jadi, di sisi browser. Proses bikin file itu di server, ongkosnya nggak pernah ikut dihitung, soalnya benchmark cuma ngukur ukuran file hasil akhir, bukan berapa detik CPU yang kepake buat ngehasilin file itu.

JPEG XL nggak otomatis ngilangin ongkos itu kalau lo tetep encode dari nol. Untungnya, buat katalog yang isinya JPEG lawas, ada jalan yang beda sama sekali.

## Bukan re-encode ulang semua: ini jalan migrasi yang kepake

Coba bandingin dulu sama cara kerja AVIF. Tiap gambar di katalog kudu lewat decode-lalu-encode penuh buat jadi lebih kecil, kena ongkos CPU AVIF lagi, dan versi lossy-nya malah dikit lebih jelek tiap kali lewat proses itu.

JPEG XL punya jalan lain. Dia bisa ngambil koefisien DCT dari file JPEG yang udah ada, terus langsung masukin ke container `.jxl` bit demi bit, tanpa decode-encode ulang sama sekali.

Hasilnya:

- Nggak ada proses re-encode.
- Nggak ada degradasi kualitas antar generasi, yang biasanya numpuk tiap kali gambar lossy di-decode terus di-save ulang.
- Potongan ukuran nyata sekitar 20%, hasil dari transform, bukan dari compress ulang.

Buat platform multi-tenant yang nyimpen foto merchant bertahun-tahun, inilah jalan migrasi yang sebenarnya kepake. Background worker kita nggak perlu ngulang encode seluruh katalog dari piksel. Kita cuma ngerepack bitstream-nya aja.

## Progressive loading: thumbnail pipeline yang nggak perlu dibikin

Pembeli yang koneksinya pas-pasan, banyak banget di Asia Tenggara, ngerasain beda yang kentara antara nunggu kartu produk kosong lama, sama langsung liat preview yang udah bisa dikenalin walaupun gambarnya masih nyempurna.

Bedanya ada di struktur bitstream JPEG XL, yang progresif dari desain. Browser bisa langsung render preview resolusi rendah dari potongan byte pertama yang nyampe, terus makin sharp seiring sisanya ke-load, semua tanpa server perlu bikin aset thumbnail terpisah. Satu kelas infrastruktur hilang begitu aja: nggak perlu matrix ukuran thumbnail yang di-generate, disimpen, dan dijaga sinkron sama originalnya.

Ada satu komentar di HN yang menurut gue nutup argumen ini dengan paling pas. Situs art dan katalog itu yang paling untung dari JPEG XL, karena mereka bisa ngerepack ulang semua JPEG yang udah mereka punya secara lossless, hampir tanpa biaya.

## Yang bakal gue pakai

Headline-nya emang "browser support akhirnya nyampe tier-1". Tapi buat platform kayak kita, keputusan yang beneran kepake itu lebih spesifik. Pakai transcode lossless JPEG XL, biar nggak usah lagi keluar ongkos encode AVIF buat konten yang dari awal nggak butuh di-encode ulang sama sekali.

AVIF sendiri nggak usah dibuang. Dia tetep masuk akal buat tempat yang ongkos encode-nya udah ke-amortisasi, kayak foto editorial atau hero image yang di-encode sekali tapi dilayanin jutaan kali.

Yang berubah itu ke mana JPEG XL diarahin: khusus ke jalur yang paling kena masalah gara-gara AVIF. Jalur itu adalah upload katalog merchant, tempat ribuan JPEG masuk dalam ledakan dan harus diproses murah dan cepat, tanpa kehilangan kualitas.

Dan satu hal yang gue sadar belakangan: masalah format gambar itu nggak pernah soal format mana yang paling efisien di atas kertas. Yang nentuin itu di mana biaya komputasinya jatuh, di CPU server lo, atau di layar HP pembeli lo. 😅
