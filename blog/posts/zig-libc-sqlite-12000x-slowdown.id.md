---
title: Libc Rewrite Zig Bikin SQLite Jadi 12.000x Lebih Lambat
slug: zig-libc-sqlite-12000x-slowdown
date: 2026-11-05
excerpt: Service Rust hasil cross-compile kehilangan 12.000x performa di insert SQLite gara-gara libc versi Zig mindai seluruh string di tiap panggilan strchr. Test lokal di macOS hijau semua.
tags: rust, zig, sqlite, performance, compilers
---

Insert 40.000 record JSON ke SQLite itu kerjaan milidetik. Yang dialami Dennis Forbes beda jauh. Satu core penuh nyala selama beberapa menit, terus angka yang dia tulis di postingannya kebaca kayak salah ketik: 12.000x lebih lambat.

Bukan lock contention. Bukan fsync. Bukan disk I/O, bukan juga index yang kelupaan. Binary-nya di-cross-compile ke Linux lewat `zig cc`, dan C standard library (libc) di bawahnya diam-diam mengubah parser SQLite jadi kuadratik.

Yang menurut gue penting justru bukan bug Zig-nya, karena itu sudah dibetulkan upstream. Yang penting: satu kelas regresi kayak gini sama sekali nggak kelihatan di test suite yang biasa kita jalankan.

## Libc yang nggak pernah kesentuh test lo

Yang Forbes uji: payload JSON 1,2 MB yang dimasukkan ke SQLite sebagai batch 40.000 record. Di macOS, tempat integration test dia jalan. Di situ workload yang sama selesai di bawah satu milidetik.

Yang beda bukan hardware-nya, tapi linker yang dipakai.

`cargo-zigbuild` menyerahkan proses linking ke `zig cc`, yang punya implementasi C library sendiri. Itu justru alasan tool ini ada: bikin binary Linux dari Mac atau dari CI runner tanpa perlu nyalain container Docker buat build. Kenyamanannya nyata. Biayanya juga nyata.

Build native di laptop lo nge-link libc punya Apple, sementara artefak yang lo deploy nge-link `libzigc`. Itu versi Zig sendiri buat `strchr`, `strspn`, `strstr`, dan semua keluarga yang sama.

Test lo jalan di atas versi Apple. Yang dikirim ke server versi Zig.

## Shlemiel the Painter, kejadian lagi

String di C bukan string. Dia cuma pointer plus janji bahwa ada satu byte nol di suatu tempat di depannya. Slice di Zig lain: pointer plus panjang.

Masalahnya, tiap jembatan antara dua representasi ini butuh panjangnya. Satu-satunya cara mendapatkannya dari `char*` telanjang adalah jalan terus sampai ketemu terminator.

Kalau belum pernah baca, cari esai Joel Spolsky dari 2001, "Back to Basics". Shlemiel di esai itu ngecat satu meter per kuas, lalu jalan balik ke kaleng buat tiap kuas. Makin panjang pagarnya, makin kuadratik waktunya. Esainya umur dua puluh lima tahun dan masih jago menebak insiden produksi.

Kira-kira begini bentuk yang terjadi di `libzigc`:

```zig
// sketsa, bukan patch aslinya
const n = std.mem.len(ptr);           // mindai sampai byte NUL dulu: O(sisa string)
const s = ptr[0..n];                  // baru dapat slice
const idx = std.mem.indexOfScalar(u8, s, ':');  // terus cari: O(sisa string) lagi
```

Fungsi yang harusnya berhenti di titik dua pertama malah baca sampai ujung buffer dulu, dan sekali dua kali nggak ada yang sadar. Tapi jalankan itu di dalam loop atas dokumen 1,2 MB, dan loop-nya berubah jadi kuadratik.

Petunjuknya sederhana: `strchrnul` itu ada. Fungsi itu balikin pointer ke terminator, bukan panjang string, justru karena pemanggil C sering nggak butuh tahu sisa stringnya berapa panjang. Rewrite yang ngitung panjang di depan sudah membuang alasan kenapa API-nya dibentuk begitu.

PR #37417 membetulkan `strchr`, `strchrnul`, dan fungsi sekitarnya. Fix-nya nggak keren, dan itu memang yang lo mau dari sebuah libc: cari dengan scan yang berhenti di hasil pertama, jangan hitung panjang kalau pemanggilnya nggak minta.

## Tokenizer yang kena paling parah

Mekanismenya lebih penting daripada nama fungsinya. Lexer SQLite memproses JSON dan SQL dengan menggeser pointer di sepanjang buffer, manggil `strchr` dan `strspn` buat lewatin spasi dan nemuin delimiter berikutnya.

Loop itu dari dulu linear. Tiap panggilan menggeser kursor beberapa byte, jadi total kerja sebanding dengan panjang input. Sekarang tiap panggilan tetap jalan sampai ujung buffer, mau ketemu hasilnya di mana pun. Hasilnya: N langkah tokenisasi, masing-masing O(N), totalnya O(N²).

Di 1,2 MB itu sekitar satu triliun perbandingan byte, padahal build lama cuma sekitar satu juta. Angka 12.000x langsung nggak misterius lagi.

## Reproduksinya lurus banget

Issue Zig #37402 isinya loop `strchr` sintetis, dikompilasi pakai `zig cc -target x86_64-linux-musl`:

- 1 MB: 2,8 detik
- 2 MB: 11 detik
- 4 MB: 46 detik

Input dua kali lipat, waktu empat kali lipat. Perbandingan kayak gitu sidik jari pertumbuhan kuadratik. Jauh lebih berguna daripada angka absolut mana pun.

Loop yang sama, kalau di-build pakai `musl-gcc`, selesai di bawah 5 milidetik di ketiga ukuran itu. Bukan cuma agak lebih cepat, tapi empat orde besaran lebih cepat. Di mesin yang sama, ngelakuin hal yang sama.

## Yang gue ubah di build sendiri

Gue cross-compile service Rust dan worker pipeline Dagango.com untuk VPS Linux dan bare metal pakai `cargo-zigbuild`, dengan alasan bebas container yang sama kayak di atas. Ada empat hal yang gue ubah setelah baca kasus ini:

1. **Benchmark di libc target, bukan di host.** Test performanya jalan di toolchain yang sama yang menghasilkan artefak, terhadap binary musl, bukan build debug native.
2. **Uji pertumbuhannya, bukan latency-nya.** Di CI, parse 1 MB dan 4 MB, lalu cek rasionya masih sekitar 4x. Waktu absolut gampang goyang di shared runner. Rasio 16x nggak bisa bohong.
3. **Anggap bump versi Zig sebagai perubahan dependency.** Pin dulu, lalu wajibkan bench jalan sebelum bump-nya di-merge. `zig cc` sekarang dependency produksi dari proses build, dan dia layak diperiksa sekeras crate.
4. **Simpan satu build `musl-gcc` sebagai pembanding.** Begitu ada angka yang bergeser, lo butuh implementasi kedua buat tahu apakah yang berubah kodenya atau toolchain-nya.

Nggak ada yang muluk-muluk di daftar itu. Ini disiplin biasa yang sudah lo pakai buat database driver dan allocator. Bedanya cuma satu: sekarang diterapkan ke sesuatu yang selama ini kita anggap flag linker yang membosankan.

## ABI juga kontrak performa

Zig sedang menulis ulang libc, Rust sedang menulis ulang coreutils. Dua-duanya usaha yang layak. Tapi kesamaan fungsional plus test suite yang hijau itu cuma separuh pekerjaan.

Separuh yang susahnya begini: sebuah C library itu empat puluh tahun asimptotik yang nggak pernah didokumentasikan. Pemanggil menulis loop yang bergantung pada `strchr` berhenti di hasil pertama. Nggak ada yang mencatat syarat itu, karena semua orang sudah tahu. Jadi syarat itu nggak pernah masuk ke test.

Kalau lo mengganti primitif berumur tiga puluh tahun, pertanyaan "apakah hasilnya benar?" itu yang gampang. Yang menentukan: biayanya masih sama atau nggak dengan yang diasumsikan pemanggilnya. Pertanyaan kedua nggak punya compiler warning dan nggak punya unit test. Cuma ada benchmark, dan itu pun kalau lo ingat menjalankannya terhadap binary yang benar-benar lo kirim.
