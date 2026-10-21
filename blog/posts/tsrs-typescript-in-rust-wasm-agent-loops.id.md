---
title: Kenapa Cloudflare Porting TypeScript ke Rust Demi Wasm, Bukan Demi Kecepatan
slug: tsrs-typescript-in-rust-wasm-agent-loops
date: 2026-10-21
excerpt: tsrs dari Cloudflare sampai 8x lebih cepat dari TypeScript 7.0 dengan memori ~70% lebih hemat. Angka itu bonus. WebAssembly alasan sebenarnya port ini dibuat.
tags: typescript, rust, webassembly, ai-agents, performance
---

Waktu Microsoft memindahkan compiler TypeScript dari JavaScript ke Go, sebagian besar alasan performa sudah selesai di situ. `tsc` jadi sekitar 10x lebih cepat dan jauh lebih hemat memori.

Selama beberapa waktu, ceritanya kelihatan berhenti di titik itu.

Terus tanggal 20 Oktober 2026, Cloudflare dan VoidZero ngumumin `tsrs`. Ini port compiler TypeScript ke Rust, dikerjain bareng Max Schwenk dari Owner.com dan diinkubasi di dalam toolchain Oxc.

Benchmark awalnya sampai 8x lebih cepat dari TypeScript 7.0, dengan pemakaian memori sekitar 70% lebih sedikit.

Gue baca angka itu dua kali, terus tetap ngerasa ada yang kelewat.

Yang bikin port ini masuk akal bukan kecepatannya. Compiler Rust bisa di-compile ke WebAssembly tanpa ikut bawa garbage collector.

Dan properti itu yang nentuin typechecker lo boleh hidup di mana.

Gue pegang beberapa monorepo TypeScript, dan ada fleet agent yang jalanin typecheck di dalam loop. Jadi buat gue ini perubahan infrastruktur, bukan perang bahasa.

## Cloudflare sendiri yang nulis batasan angkanya

Dua angka itu datang dengan kontrol. Jumlah worker-nya sama, dan konfigurasinya disepakati bareng tim TypeScript.

Bagian kedua itu yang bobotnya lebih berat.

Benchmark port compiler selama ini campur aduk. Angkanya sering diambil dari mesin lebih besar dengan flag lebih longgar. Cloudflare nyebut pola itu duluan.

Yang gue catat buat evaluasi sendiri:

- 8x itu plafon di satu suite benchmark, bukan angka tetap di repo lo,
- `tsrs` secara default pakai konfigurasi adaptif yang makan memori lebih banyak demi jalan lebih cepat,
- TypeScript 7.1 beta sudah sampai 2.5x lebih cepat dari 7.0, dan sebagian perbaikan itu datang dari kerjaan `tsrs`.

Jadi buat tim yang masih di TS 7.0, pembanding jujurnya 7.1. Ini yang bikin angka 8x itu terasa lebih besar dari kenyataannya.

## Masalah Go di Wasm itu GC yang ikut nebeng

Compile program Go ke WebAssembly, dan garbage collector Go ikut masuk. Nggak ada build flag yang bisa buang itu.

Collector-nya ada di dalam module, dan dia ngatur memori yang nggak bisa dilihat host.

Rust nggak punya masalah itu. Module yang bisa ngobrol langsung sama memori host lebih murah dijalanin, dan pola aksesnya bisa diprediksi.

Module-nya jadi lebih kecil dan resident footprint-nya turun. Nggak ada collector yang muter di dalam Worker lo.

Ukuran, misalnya. `jerf` di HN lebih blak-blakan daripada announcement-nya: waktu Go dikirim ke Wasm hasilnya "very large WASM packages for small amounts of code".

Compiler jelas bukan kode sedikit, jadi pengalinya juga nggak sedikit.

Buat gue ini bagian yang paling sering kelewat. Yang dibandingin biasanya waktu eksekusi.

Padahal yang lebih penting: seberapa besar barang itu setelah dijadikan module dan dikirim ke tempat di luar server.

## Yang bikin port ini masuk akal itu target deploy-nya

Worker sudah bisa jalanin Wasm sejak lama.

Dukungan Rust native di Worker sendiri baru mendarat beberapa minggu sebelum pengumuman ini. Jalurnya lewat target Emscripten baru buat `wasm-bindgen`, dan itu yang bikin hitungannya berubah.

Kalau dua fakta itu digabung, satu development toolchain bisa jalan dari awal sampai akhir tanpa keluar dari sandbox. Dan nggak ada satu pun container terpisah yang perlu di-shell-out.

Tempat-tempat yang jadi kebuka, gue urutin dari yang paling cepat gue pakai sendiri:

- typecheck lengkap di dalam Worker, buat preview build per PR,
- toolchain yang sama di tab browser, jadi kontributor tanpa setup lokal tetap dapat diagnostics asli,
- compiler di perangkat embedded atau langkah build IoT, tempat runtime Go plus collector-nya kegedean.

Buat yang jalanin agent, kasus browser itu yang paling menarik. Kalau compiler-nya muat di satu tab, dia juga muat di batas isolasi yang sudah dipakai agent. Satu shared volume hilang dari desain. Satu kategori kejutan antar-tenant ikut hilang.

## Satu agent tiap pagi, satu matrix tiap malam

Cloudflare tegas soal satu hal: ini bukan fork. Tim TypeScript tetap pegang kendali desain bahasa.

Wajar. Tapi bagian maintenance-nya yang bikin gue berhenti sekadar baca cepat.

Modelnya nyontek dari Vinext, reimplementasi Next.js mereka. Tiap pagi satu agent nge-review perubahan upstream dan buka tracking issue buat apa pun yang bisa ngaruh ke port-nya. Tiap malam compatibility matrix di-regenerate dengan jalanin test suite Next.js ke Vinext.

Kalau ada yang jebol, agent nyari perubahannya di dua codebase sekaligus. Dia bikin reproduction, port test yang relevan, terus ngajuin fix. Proses yang sama sekarang dipakai buat TypeScript.

Buat port downstream, ini ngubah bentuk kegagalannya. Project kayak gini biasanya mati pelan-pelan karena parity sama ribuan test upstream itu kerjaan manusia yang nggak ada yang mau bayar.

Kalau parity jadi job malam yang draft fix-nya disiapin agent, biayanya jadi pos anggaran biasa. Bukan lagi sumber kelelahan tim.

Ada satu bagian di postingan itu yang gampang dilewatin. Cloudflare sendiri yang bilang bahwa slopfork (clone cepat hasil AI yang nggak teliti) dan port besar sekarang bisa dikerjain model frontier dalam hitungan hari. Di antara semua itu, yang nentuin `tsrs` bukan angkanya. Dua hal ini yang bikin dia beda:

- dia ngikutin keputusan desain tim TypeScript,
- dan temuan performanya dikirim balik ke upstream.

Tanpa keduanya, dia cuma satu lagi fork cepat.

Dua detail kecil nunjukin timnya paham di mana titik rawannya. Theo Browne lagi nggabungin `tsc-rs` dan `tsrs` jadi satu package yang nutup semua fitur TypeScript, LSP dan content mappers termasuk. Divergensi yang mereka akui sempit, contohnya urutan diagnostics yang dicetak.

## Ujian sebenarnya ada di upstream

Hubungan sama Microsoft lebih akur daripada perang fork biasanya. Dan Rosenwasser dari tim TypeScript muncul di thread Hacker News (383 poin, 184 komentar) buat ngomong bagian yang biasanya disimpan: "a lot of the speed does not just come down to language choice".

Dia juga konfirmasi kalau sebagian yang bikin TS 7.1 lebih cepat dan lebih ringan datang dari optimasi yang ketemu waktu port Rust dikerjain.

Contoh konkretnya PR #64476 dari `maschwenk`. PR itu bikin checker berhenti bikin intersection property yang nggak mungkin menyusut jadi `never`. Angka di body PR-nya yang menarik.

Di benchmark `mui-docs` dengan empat checker: heap turun 41,8% dan waktu check turun 38,9%. Semua itu dari perubahan nyata sekitar 80 baris.

PR itu ditutup tanpa di-merge, dan kalimat itu lebih penting daripada semua benchmark tadi. Temuan jalan ke upstream lebih cepat daripada patch-nya. Anggap saja hasilnya bakal mendarat di TypeScript, tapi jangan anggap diff-nya ikut mendarat.

## Yang gue ubah duluan

Ekonomi inner loop beda sama ekonomi CI. Lima belas detik typecheck di pipeline itu nggak ada rasanya.

Agent yang ngejalanin loop edit, typecheck, test puluhan kali buat satu task bayar biaya itu puluhan kali juga. Dan dia bayarnya sambil nahan container tetap hidup.

```
npm install tsrs
npx tsrs
```

Yang lebih dulu nendang buat gue justru memori. Tiap checker paralel punya heap sendiri. Jadi di box yang jalanin empat container agent, hemat 70% RSS per checker itu yang nentuin apakah container kelima muat.

Empat langkah yang gue ambil sekarang:

- catat peak RSS per typecheck bareng wall time, karena di situ kemenangan memorinya kelihatan,
- taruh `tsrs` sebagai job pelaporan di samping gate yang asli selama masih eksperimental,
- biarin urutan diagnostics dipegang `tsc` versi Go sampai divergensinya menutup,
- taruh loop-nya di dalam sandbox agent sendiri, jangan di shared build volume.

Dua implementasi, satu bahasa, dan nggak ada yang jadi fork. Go ngembalikin kecepatan TypeScript di CLI. Rust ngasih tempat kedua buat hidup, dan itu yang bakal tetap relevan nanti waktu compiler-nya harus jalan di sesuatu yang jauh lebih kecil dari VM.

Bedanya cuma satu, dan ini yang gue pegang: pertanyaan "ini berapa kali lebih cepat" bakal cepat basi. Pertanyaan "compiler ini harus bisa hidup di mana" nggak.

Yang gue nggak akan lakuin: mindahin semua gate ke `tsrs` minggu ini cuma karena angkanya bagus di mesin orang lain.
