---
title: 'AWS Emulator: 438 API Model, Nol Baris Code Tulisan Manusia'
slug: aws-emulator-agent-fleet-harness
date: 2026-11-12
excerpt: AWS Emulator menutup 438 API model AWS, dan log commit-nya isinya cuma IssueFinderAgent sama IssueFixerAgent. Yang bikin jalan justru desain harness-nya.
tags: ai agents, aws, rust, cloud, software engineering
keywords: aws emulator, autonomous ai agents, rust cargo workspace, localstack alternative, multi-agent coding fleet, smithy api modeling
---

Tanggal 11 November 2026 AWS merilis AWS Emulator ke GitHub dengan public dedication CC0. Isinya 438 API model AWS.

Matthew Goldberg, Sr. Principal Engineer di AWS, bilang di postingan pengumuman bahwa timnya nggak menulis dan nggak me-review satu baris pun code di situ.

Kalimat itu gampang dikutip dan susah dipercaya. Jadi gue baca repo-nya langsung, mulai dari `AGENTS.md`. File itu yang di-load setiap agent sebelum menyentuh tree, dan di situ desain aslinya kelihatan.

## AWS Emulator jalan di antara spec dan oracle cloud asli

Titik awal Goldberg itu hasil riset Anthropic awal 2026. Kasih agent spec yang jelas plus reference implementation, dan agent itu bisa membangun sesuatu yang mengikuti spec-nya dengan setia.

AWS sudah punya dua-duanya. AWS API Models jadi spec-nya, dan cloud AWS yang asli jadi reference implementation-nya.

Tim autonomous AI agents yang pertama mengubah dua hal itu jadi test. Tiap test itu skenario AWS nyata, dan agent memverifikasinya ke AWS live sebelum test itu dikumpulkan.

Setelah itu test bisa di-replay berkali-kali tanpa memanggil AWS lagi. Sekarang suite fidelity-nya berisi puluhan ribu skenario.

Ini bagian yang paling sering dilewat kalau orang baru pasang fleet coding, padahal justru ini yang menentukan fleet-nya mengerucut atau melenceng.

Eksperimen akhir pekan Goldberg jadi contoh paling pas buat ngegambarin loop itu. Goldberg kasih Kiro, tool coding agentic berbasis spec milik AWS, tiga instruksi:

- tulis test dari AWS Command Line Interface (CLI),
- iterasi sampai test-nya lolos ke AWS asli,
- bangun implementasi in-memory yang bikin test yang sama lolos.

Lima belas menit kemudian Goldberg sudah punya Amazon Simple Queue Service (SQS) versi pertama yang lumayan.

## Tiga tim agent, satu loop tertutup

Pembagian kerja per fungsi ini bukan soal rapi-rapian di diagram. Goldberg bilang agent lebih sering berhasil kalau tugasnya dibatasi.

Yang lebih penting, pembagian itu bikin output satu peran bisa dicek peran berikutnya.

- **Test builder** mengubah API model jadi skenario yang sudah diverifikasi ke cloud. Output-nya cuma lolos atau gagal, jadi sistem nggak perlu menilai opini siapa pun.
- **Issue finder** me-replay suite itu secara lokal, mencari divergence, lalu melaporkan issue terstruktur.
- **Issue fixer** mengambil tepat satu issue, checkout code-nya, dan mengedit sampai test yang gagal jadi hijau.

Satu issue untuk satu fixer itu detail yang paling gue tiru duluan. Efek samping tiap edit jadi terbatas, dan kalau fix-nya salah, revert-nya murah.

Issue finder juga diminta mengelompokkan kegagalan yang kemungkinan punya akar masalah sama, sebelum satu pun fixer mulai bekerja.

## Isi workspace AWS Emulator sebenarnya seperti apa

Rust Cargo workspace di sini kasih satu crate per service. Ngubah satu service cuma mengompilasi satu crate, bukan seluruh emulator.

Di situlah bedanya fleet yang jalan paralel dengan fleet yang antre.

```
aws-emulator/
├── Cargo.toml                 # root workspace: agent nggak boleh sentuh
├── services/service-<name>/   # satu crate per service
│   ├── build.rs               # generate dari model Smithy
│   ├── smithy-model/          # <name>.json, penentu wire protocol
│   └── src/ops/               # satu file per operasi
├── core/router/               # di-render ulang tiap ada service baru
├── vendor/engine/             # immutable, satu engine dipakai bersama
└── issues/                    # yang beres dan yang belum, berupa direktori
```

Saat gue cek, direktori `services/` berisi 436 crate `service-*` plus satu crate `common` bersama. Angka 438 di pengumuman itu hitungan API model.

Jadi dua angka itu memang menghitung unit yang beda.

Ada dua batas lain yang penting. `vendor/engine` di-vendor dan tertutup untuk agent, jadi engine in-memory cuma ada satu dan nggak ada yang mem-fork-nya.

Root `Cargo.toml` read-only, dan router di-render ulang. Dua-duanya nggak diedit tangan.

Soal biaya build, ini sisi yang nggak enak. Build debug penuh butuh minimal 100 GB disk kosong. Segitu memang ongkosnya kalau workspace-nya berbentuk begini.

## Kenapa fleet versi lama sampai bikin interpreter Python sendiri?

Di versi lama sistem ini, agent-nya memutuskan menulis interpreter Python sendiri buat mendukung fungsi AWS Lambda.

Nggak ada yang minta itu. Ini cerita kegagalan paling berguna di seluruh pengumuman, karena dari luar kelihatan seperti kreativitas dan dari dalam kelihatan seperti drift.

Cara Goldberg menjelaskannya: agent butuh buku mewarnai. Area yang batasnya jelas, dengan jaminan gambar utuhnya tetap beres.

`AGENTS.md` yang sekarang isinya mirip daftar semua hal yang pernah salah sebelumnya. Tiga aturan di antaranya layak lo salin langsung ke fleet mana pun:

- Kredensial dibuat lewat credential store emulator. Agent nggak pernah menyusun access key atau secret sendiri, dan nggak pernah menulisnya ke log.
- URL yang nanti di-fetch pemanggil harus lewat signer emulator. Agent yang menyusun `X-Amz-Signature` sendiri menghasilkan URL yang menembak service asli atau gagal verifikasi.
- Endpoint resource diambil dari objek context emulator. Nggak ada yang dirakit dari `<service>.<region>.amazonaws.com`, karena itu artinya agent menembak produksi.

Aturan ketiga yang paling menentukan di lapangan. Agent yang bisa mencapai endpoint cloud asli bisa membelanjakan uang asli.

Prompt sopan yang meminta dia untuk nggak begitu nggak dihitung sebagai kontrol.

## Merge gate-nya itu produk yang sebenarnya

Setiap perubahan dari fixer harus lolos gate sebelum masuk. Gate itu memblokir code yang nggak bisa dikompilasi.

Ada juga agent yang me-review standar coding, memeriksa keamanan, dan memastikan fidelity nggak turun. Kalau ada yang gagal, perubahannya balik ke agent untuk dikerjakan ulang.

AWS melaporkan ribuan issue beres per hari, dengan ratusan agent bekerja bersamaan di repo yang sama.

Commit menumpuk di AWS CodeCommit, di-build dan di-test ulang, dan baru masuk ke GitHub di akhir proses rilis.

Buka log commit-nya dan harness-nya kelihatan di kolom author. Entri terbaru bergantian antara `IssueFinderAgent` yang melaporkan issue dan `IssueFixerAgent` yang menutupnya.

Nggak ada nama manusia di situ.

## Jam manusia pindah ke mana

Menghasilkan code pakai large language model (LLM) sekarang murah. Yang nggak murah justru pekerjaan supaya code hasil generate itu bisa dipercaya.

Dan pekerjaan itu nggak menyusut, cuma pindah tempat.

Di AWS jam manusianya pindah ke beberapa titik:

- lapisan Smithy API modeling, tempat operasi tiap service didefinisikan sebelum ada code (Smithy itu interface definition language milik AWS),
- oracle cloud live yang jadi patokan penilaian seluruh fleet,
- batas crate yang mencegah agent saling tabrak,
- merge gate yang nggak bisa dilewati dengan argumen bagus.

Gue juga menjalankan multi-agent coding fleet di monorepo kami, dan yang gue lihat cocok dengan ini.

Kegagalannya hampir nggak pernah soal model bisa menulis Rust atau nggak. Yang sering terjadi: dua agent mengedit manifest root yang sama di waktu bersamaan.

Atau satu agent diam-diam mengarang dependency yang sebenarnya nggak perlu, karena nggak ada yang memberi tahu apa yang sudah ada di repo kita.

Interpreter Python tadi kegagalan yang sama, cuma tagihannya lebih besar.

Semua investasi engineering di batas crate dan oracle live itu yang bikin hasil akhirnya cukup dipercaya buat dijalankan lokal.

Kredibilitas itu juga yang bikin berita LocalStack jadi relevan di sini. LocalStack menghentikan Community edition-nya pada 23 Maret 2026, dan free tier yang tersisa nggak boleh dipakai komersial.

Tim yang kehilangan emulator lokal tanpa auth sekarang mencari yang gratis.

Rilisan CC0 dengan skor fidelity yang dipublikasikan jadi LocalStack alternative yang masuk akal untuk kerja continuous integration (CI), walaupun masih ada celah untuk service yang jarang dipakai.

## FAQ

### Perlu akun AWS untuk menjalankan AWS Emulator?

Nggak perlu. Jalankan binary-nya, lalu arahkan software development kit (SDK) lo ke `https://127.0.0.1:9297`, yang menyajikan sertifikat self-signed.

Request lo nggak pernah keluar dari mesin. AWS nggak memungut biaya emulator terpisah, dan README-nya tegas soal batas pemakaian: ini bukan untuk workload produksi dan bukan untuk menguji keamanan.

### Kenapa gue lihat 436 crate service padahal AWS bilang 438?

Angka 438 itu jumlah API model di pengumuman. Direktori `services/` saat ini berisi 436 direktori crate `service-*` plus satu crate `common` bersama.

Jadi workspace dan pengumuman menghitung unit yang berbeda.

### Bisa dipakai sebagai pengganti LocalStack langsung?

Cek skor fidelity yang dirilis bersama tiap versi sebelum lo mengunci pipeline CI ke situ. Repo-nya jujur soal celah.

Yang belum jalan ada di `issues/things-that-do-not-work/`, dan yang sudah beres dipindah ke `issues/things-that-now-work/`.

Untuk test Rust embedded, AWS Emulator lebih jauh dari LocalStack. Emulator-nya dikompilasi ke dalam binary test lo, jadi nggak ada endpoint atau sertifikat yang perlu diatur.

## Yang gue ambil dari sini

Lo nggak perlu 438 API model untuk dapat manfaat dari bentuknya. Mulai dari oracle yang bisa dipakai menilai fleet, terus potong workspace jadi unit kecil.

Baru setelah itu pasang satu gate di depan branch bersama.

Lewati oracle-nya dan lo dapat fleet yang cepat, percaya diri, dan salah.
