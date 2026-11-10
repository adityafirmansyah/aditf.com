---
title: Expo Exact Framework: Bikin App Native Tanpa React dan JSX
slug: expo-exact-framework-no-react-jsx
date: 2026-11-10
excerpt: Expo Exact framework membuang React, JSX, dan bridge JavaScript, lalu bertaruh bahwa jam virtual plus driver sepuluh perintah bikin app native bisa dibangun AI agent.
tags: react, ai-agents, rust, frontend-engineering, architecture
keywords: expo exact framework, agent native ui architecture, expo ditching react, contract dsl rust, ai coding agent frontend testing, deterministic ui testing agents
---

Tanggal 9 November, tim Expo membuka `expo/exact` ke publik. Isinya runtime UI lintas platform buat web, macOS, iOS, dan Linux. React nggak dipakai sama sekali di layer view, dan JSX juga nggak ada.

Frame pertama udah tampil sebelum satu baris pun JavaScript aplikasi jalan. Bukan hasil polesan di akhir, karena seluruh urutan boot-nya memang dirancang begitu dari awal.

Dua hal soal Expo Exact framework ini sama-sama benar. Ini infrastruktur frontend paling jujur yang gue baca tahun ini. Tapi ini juga taruhan yang melawan hal yang bikin model sekarang jago nulis frontend.

Kalau lo ngirim software pakai agent, dua-duanya penting.

## Apa aja yang dibuang sama Expo Exact framework ini

Exact bukan React Native. Bukan juga renderer React. Repo-nya bilang langsung di README: "No JSX or React tier." Terus, dengan kejujuran yang jarang ada di postingan launching, mereka nambahin satu kalimat lagi. Pintunya masih terbuka, tapi nggak ada yang lagi ngebangun.

Yang tersisa dari arsitektur ini justru intinya. Ini agent native UI architecture: runtime yang dirancang supaya program bisa langsung periksa dan kendalikan, sementara manusianya cuma ikut lihat hasilnya.

Yang gantiin pohon komponen itu empat lapis.

- **Contract**, bahasa domain-specific (DSL) kecil buat nyusun view. Record type-nya tertutup, list-nya wajib punya key, semua value bertipe, dan nggak ada celah buat nyelipin kode sembarangan.
- **Plan yang di-bake.** Compile-nya lewat empat fase: syntax, types, analysis, lowering. Data konstanta dievaluasi masuk ke plan waktu build, jadi paint pertama nggak butuh apa-apa lagi.
- **Kernel Rust.** `exact-kernel` ngitung layout pakai aturan CSS lewat Taffy yang di-patch, di atas node arena berbentuk kolumnar. Ukur teks pakai CoreText di Apple, cosmic-text di Linux.
- **Painter per host.** AppKit di macOS, UIKit di iOS. Di Linux pakai DRM/KMS (Direct Rendering Manager plus Kernel Mode Setting) dengan input evdev. Di web, runtime sekitar 20 KB yang nulis langsung ke Document Object Model (DOM) asli.

Logika data duduk di balik satu seam. TypeScript di-compile jadi bytecode Hermes waktu build dan baru dimuat setelah pixel pertama. Kalau mau, ganti aja pakai crate Rust.

Tiap jawaban dari sumber data dicek dulu terhadap shape yang dideklarasikan Contract. Nggak ada webview, nggak ada bridge JavaScript.

Intinya begini: hydration mismatch itu bukan bug yang lo perbaiki di arsitektur ini. Itu masalah yang nggak pernah lo kirim.

## Kenapa jam virtual lebih bisa dipercaya daripada `await sleep(500)`?

Hampir semua test UI tulisan agent mati di bagian nunggu. Agent tap tombol, tidur 500 ms, terus screenshot. Animasi masih di 40%. Run berikutnya jadi 60%.

Test kayak gitu nggak flaky karena app-nya rusak. Flaky karena wall-clock bukan hal yang bisa lo observasi dengan stabil.

Exact kasih jam itu ke agent. Di antara dua operasi driver, nggak ada yang bergerak. Jadi daripada tidur, agent bilang `clock +60000` atau `clock settle`, terus baca hasilnya.

Hasilnya deterministic UI testing yang beneran bisa dipegang. Input sama, frame sama, di run mana pun dan host mana pun.

```sh
bun scripts/agent.mjs web tree "tap change-station" "type station-search Palo" \
  "clock +60000" state "screenshot out.png"
```

Total ada sepuluh operasi, dan jumlahnya sendiri keputusan desain: `tree · screenshot · tap · type · state · layout · logs · clock · prefer · perf`. Alasannya ada di README. API agent itu nambah satu perbaikan masuk akal demi satu perbaikan masuk akal, sampai akhirnya nggak ada yang sanggup hafal isinya.

Test-nya jalan pakai primitif yang sama. File `app.test.contract` isinya rangkaian operasi tadi. File yang sama jalan tanpa diubah di web, macOS, iOS Simulator, dan Linux headless. Tiga test Caltrain selesai sekitar dua detik di host web.

## Biaya sebenarnya ada di data latihan

Sampai sini gue berhenti tepuk tangan.

Contract sengaja dibikin kecil supaya satu app muat di dalam context window. Itu kemenangan beneran buat urusan correctness. Semua penulisan state dideklarasikan, semua list punya key, semua value bertipe.

Salah pun dibalas dengan penolakan yang jelasin harus ngapain. Sekali jalan, compiler bisa lapor sampai dua puluh error sekaligus.

Kelemahan itu datang dari tempat yang nggak ada hubungannya dengan Rust. Zero-shot fluency di TSX dan Tailwind CSS itu bukan sifat TSX. Itu hasil triliunan token pengetahuan awal, dan Contract belum punya apa-apa di sana.

Di thread Hacker News, poin ini muncul dari beberapa arah. `doodlesdev` nebak framework-nya bakal jalan bagus sama model frontier dan jauh lebih jelek sama model murah. `btown` nanya dasar lain: DSL yang punya ekspresi matematis bebas itu butuh spec bahasa formal, lexer dan parser hasil generate, plus stdlib yang perilakunya identik di semua target build.

Perbandingan arsitektur juga masuk. `ogoffart`, yang ngerjain Slint, bilang desainnya mirip banget sama framework-nya. Sama-sama Rust, sama-sama DSL deklaratif dengan compiler sendiri, sama-sama naruh logika di bahasa host, sama-sama nyediain tooling yang bisa didrive agent.

Bedanya cuma satu, dan itu yang paling tajam: Slint udah stabil di 1.x sejak 2023. Exact masih pre-1.0 dan berubah tiap hari. `zoom6628` malah mundur lebih jauh, nyebut QML dan Qt.

Terus ada `mrbombastic`, yang nulis bahwa kecenderungan ngutamain agent di atas manusia dalam developer tooling bikin dia "sympathize with the Butlerian jihad". Gue ketawa bacanya, agak kebanyakan. Tapi rasa nggak nyaman di balik komentar itu pantas dijawab serius, dan nggak ada satu pun di thread yang jawab.

## Enam check, 65 detik, lima belas dokumen

Bagian yang beneran mau gue tiru cuma ada di satu file markdown. `rules/RULES.md` nyebut tiap budget itu trade-off. Bukan limit yang sakral.

Konkretnya:

- **Enam blocking check, total 65 detik.** Kalau mau nambah yang ketujuh, satu yang lama harus dihapus di pull request yang sama.
- **Maksimum 1.500 baris per file source.** File hasil generate bebas, karena itu dibangun dan nggak pernah di-commit.
- **Lima belas dokumen di working set.** Dokumen keenam belas artinya lo harus mengarsipkan satu.
- **File rules-nya sendiri dibatasi 700 kata.** Kalau tumbuh, berarti ada yang harus jadi check atau berhenti jadi aturan.

Satu kalimat yang nanggung beban paling besar justru pendek. "A limit gets exceptions. A trade doesn't."

Ini cocok banget sama yang gue lihat tiap hari waktu jalanin fleet agent. Agent perform-nya bagus kalau sistemnya punya permukaan kecil, latency rendah, dan batas yang ketat.

Taruh agent yang sama di repo yang scaffolding build-nya lebih gede dari fitur-nya, dan angka gagalnya berhenti lucu. 😅

Yang sering kelewat justru ini: biaya review kita ikut membengkak bareng permukaan sistemnya. Di stack web lama, gue nggak bisa percaya hasil agent sebelum jalanin sendiri. Di permukaan deklaratif yang sempit, gue bisa baca dan langsung nolak kalau bentuknya salah.

## Yang beneran gue curi minggu ini

Gue nggak bakal mindahin produk ke Exact hari ini. Tiga idenya yang gue ambil minggu ini.

- **Curi jam-nya.** Ganti satu `sleep` di harness lo dengan langkah settle eksplisit, terus ukur. Dari satu test itu lo langsung tahu app lo punya state "selesai" yang bisa diobservasi atau nggak.
- **Hitung verb lo.** Tulisin operasi yang benar-benar dipakai agent lo. Lewat sepuluh, hampir pasti ada beberapa yang sebenarnya satu operasi pakai dua nama.
- **Tiru cara nulis trade-off-nya.** Kalimat "check ketujuh wajib hapus satu yang lama" itu governance yang nggak bisa dibantah reviewer.

Bagian README yang judulnya "What works today, and what doesn't yet" itu yang paling jujur. Parity kontrol di Windows, delivery Android, akses kamera, dan update TypeScript bertanda tangan semuanya masih ada di daftar belum selesai.

Baca bagian itu dulu sebelum lo pertaruhin satu sprint ke sini.

Dan satu hal lagi yang gue syukuri dari proyek ini. Daftar yang belum jalan itu ditulis di halaman depan repo. Jadi lo nggak perlu nemu sendiri lewat error yang muncul tengah malam.

## FAQ Teknis

### Apakah Exact menggantikan React Native buat app Expo?

Nggak. Exact nggak punya React tier sama sekali, dan React Native tetap yang disupport Expo. Anggap ini eksperimen arsitektur UI yang dirancang buat mesin. Jangan dibaca sebagai jalur migrasi produk yang udah jalan.

### Bisa nggak satu app dibangun dan diverifikasi agent tanpa bantuan manusia?

README nyatet satu percobaan. Agent baru di clone bersih, dikasih prompt quick-start, selesai bikin app todo dalam sekitar 57 menit. Test-nya lolos di web, macOS, dan iOS Simulator. Sekitar 25 menit dari waktu itu habis buat build macOS dan iOS pertama, masing-masing kira-kira 13 menit.

### Kenapa JavaScript dibuang dari boot path, bukan cuma dioptimasi?

Karena startup itu sifatnya emergent dan nggak bisa ditempel belakangan. `RULES.md` bilang boot graph dianggarkan dari commit pertama dan dihitung sebagai angka. Jadi nggak diukur pakai timer, dan regresinya gagal di check. Bukan muncul sebagai benchmark yang melambat pelan-pelan.
