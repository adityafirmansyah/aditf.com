---
title: "Kenapa next/font/google Bikin CI Kita Jebol: Self-Host 13 Subset Font biar Build Nggak Butuh Internet"
slug: nextjs-self-host-font-subsets-zero-network-builds
date: 2026-10-07
excerpt: Master CI kita mati dua kali dalam dua belas jam, di commit yang kode font-nya sama persis. Ini cara Dagango.com nyimpen 13 subset font di disk biar next build nggak nembak internet.
tags: nextjs, frontend, performance, webdev, architecture
---

## `next build` itu bukan perintah offline

Dulu gue pikir `next/font/google` udah ngurusin semua soal font, titik.

Kalau di sisi browser, urusan font sebenarnya udah beres: nggak ada layout shift, pengunjung situs nggak pernah ikut nembak server Google, dan semua file dilayanin dari origin kita sendiri.

Yang jadi masalah itu mesin yang ngejalanin `next build`, bukan browser.

Loader itu tetap buka koneksi HTTPS ke fonts.googleapis.com. Tiap kali build jalan, nggak cuma sekali doang pas setup.

Jadi deploy kita diam-diam gantung ke CDN orang lain. Dan kita baru nyadar pas lagi apes-apesnya.

## Dua kali merah dalam dua belas jam

Master CI kita mati di tengah fetch itu, dua kali, jaraknya cuma sekitar dua belas jam.

Nggak ada satu baris pun kode font yang ikut diubah di dua commit itu.

Dua run yang kena merah itu `36935742623` (merge `42875bb`) sama `36851269872` (`f6b3627`), dua kejadian yang beda tapi gejalanya identik. Dua-duanya nunjukin error yang sama, `An error occurred in next/font`, terus jatuh ke sini:

```
TypeError: Cannot read properties of null (reading '1')
    at @next/font/dist/google/loader.js
```

Commit sebelum dan sesudahnya, kode fontnya sama persis. Build-nya hijau.

Jadi dua kejadian merah itu false alarm. Tapi tetap kena triage, tetap makan waktu tim.

Dan ini yang bikin gue parno: pipeline yang suka boong soal "ada yang rusak" itu juga pipeline yang bisa nyembunyiin kerusakan yang beneran.

## Request itu dari mana asalnya

File yang nembak keluar itu `@next/font/dist/google/fetch-resource.js`.

Kalau CDN Google lagi ngambek atau nge-throttle, loadernya nunggu response yang nggak pernah datang. Pas dapet null, dia nyoba baca properti dari situ, dan meledak.

Ketergantungan ke CDN luar kayak gini yang bikin apes: lo nggak nyentuh kode font sama sekali, tapi build lo bisa tiba-tiba merah.

## Latin doang? Nggak bisa

Jalan paling gampang: vendor-in file woff2 latin aja, kelar. Buat situs marketing yang isinya cuma latin, ini udah lebih dari cukup.

Tapi Dagango.com itu multi-tenant.

Merchant kita nulis konten storefront-nya dalam macem-macem bahasa:

- Vietnam
- Cyrillic
- Yunani
- Devanagari

Semuanya bercampur sama latin, tergantung tokonya.

Buang subset non-latin, karakter-karakter itu jatuh ke font sistem. Metriknya beda, dan beberapa glyph malah nggak ada sama sekali.

Buat tiga family platform kita, Google sebenarnya nyediain:

- **Baloo 2** (buat display): `latin`, `latin-ext`, `vietnamese`, `devanagari`.
- **Public Sans** (buat body text): `latin`, `latin-ext`, `vietnamese`.
- **JetBrains Mono**: `latin`, `latin-ext`, `vietnamese`, `cyrillic`, `cyrillic-ext`, `greek`.

Itung-itung semua, jadi 13 file, totalnya 225 KB. Lengkap buat tiga family ini, nggak ada subset yang disisihin.

## `next/font/local` diam-diam buang `unicodeRange`

`next/font/local` nggak punya opsi `subsets`. Titik, nggak ada negosiasi.

Lo juga nggak bisa nempelin unicode range di tiap entry `src`. Loader bawaannya cuma ambil `{ path, style, weight, ext, format }` dari tiap entry, property sisanya diabaikan sama loader bawaan Next.

Untungnya ada `declarations`. Semua yang lo taruh di situ bakal ke-copy utuh ke `@font-face` yang dihasilkan.

Jadi solusinya: satu call `localFont()` per kombinasi family dan subset, dan tiap call bawa unicode range masing-masing lewat `declarations`.

```ts
export const baloo2LatinExt = localFont({
  src: [{ path: "./Baloo2-latin-ext-700.woff2", weight: "700", style: "normal" }],
  variable: "--font-baloo-2-latin-ext",
  display: "swap",
  preload: false,
  adjustFontFallback: false,
  declarations: [
    { prop: "font-family", value: "Baloo 2" },
    { prop: "unicode-range", value: "u+0100-02ba,...,u+a720-a7ff" },
  ],
});
```

Perhatiin baris `font-family` di `declarations` itu.

Theme tenant yang udah tersimpan nyari nama family platform default lewat NAMA itu sendiri, nggak lewat variable (`lib/theme/derive.ts`). Storefront shell-nya sengaja nggak minta stylesheet terpisah buat nama itu.

Kalau sampai nama family-nya ke-scope jadi nama generated Next, tenant itu diam-diam bakal render pakai fallback font, dan nggak ada yang notice sampai ada komplain.

## Jangan sampai fallback font-nya numpuk

`next/font` bikin satu fallback font yang metriknya dicocokin otomatis, per call `localFont()`.

Kalau default-nya dibiarin nyala di semua 13 call, kita bakal punya 13 keluarga fallback font yang beda-beda. Padahal yang perlu cuma tiga.

Makanya kita set dua hal:

- `preload: true` cuma di tiga call latin. Cuma tiga file itu yang di-preload build.
- `adjustFontFallback: false` di sepuluh call sisanya, biar nggak nambah family fallback baru.

Ketiga belas call itu akhirnya digabung jadi satu string `fontVariables`, dipasang di `<html>`.

Rantai ini harus utuh, nggak boleh ada yang kelupaan. Call `localFont()` yang class-nya nggak kepasang bakal kena tree-shake, dan `@font-face` plus file-nya ikut hilang.

## Buktiin build-nya beneran nggak nembak internet

Cuma ngandelin config lokal belum bikin gue tenang. Config bisa aja benar di atas kertas tapi salah di eksekusi.

Jadi kita jalanin build-nya di bawah `strace`:

```
strace -f -e trace=connect -o /tmp/build-conn.log ./node_modules/.bin/next build
```

Terus kita hitung lalu lintas connect-nya:

```
BUILD_EXIT=0
CONNECT_LINES=0
HTS443=0
DNS_LINES=0
```

Nol koneksi keluar. Nggak ada DNS lookup. Nggak ada satu pun koneksi ke port 443.

Build-nya beneran jalan tanpa sentuh internet sama sekali.

## Satu hal yang berubah, dan gue nggak nutupin

Byte font-nya identik sama yang di-generate sama loader Google selama ini. Nggak ada yang gue sembunyiin di sini.

Yang beda cuma tiga fallback font yang masih dipertahankan: angka `size-adjust`-nya berubah dikit setelah migrasi.

Alasannya teknis. Loader Google baca tabel capsize yang udah dihitung Next duluan. Loader lokal malah ngukur file-nya sendiri pakai fontkit.

Ini cuma kena teks yang sempat render pakai fallback font, yaitu sebelum font aslinya selesai ke-load (`display: "swap"`), sama dua glyph panah yang dari dulu emang nggak dipegang subset mana pun.

Teks yang udah pakai webfont asli, nggak kena imbas apa-apa.

## Yang gue saranin kalau lo mau niru

Kalau `next build` lo masih ngobrol sama internet, berarti build lo bukan build offline. Sesederhana itu.

Caranya:

1. Vendor-in woff2 yang loader lo udah keluarin.
2. Kasih satu call per subset, pakai `declarations` buat unicode range.
3. Buktiin kalau beneran nggak ada traffic keluar, pakai `strace`.

Terakhir, bikin test yang bakal gagal kalau ada call font yang nggak kepakai. Soalnya ini mode gagal yang paling diam-diam: satu `localFont()` tanpa class di `<html>`, dan yang ke-ship cuma tiga face, bukan 13, tanpa ada yang teriak.

Bagi gue intinya simpel. Font itu cuma aset statis, dan aset statis nggak seharusnya bisa bikin pipeline jebol gara-gara internet lagi males. 😅

Dua belas jam, dua kali merah, itu udah cukup buat gue pindah dari `next/font/google`. Sampai sekarang build kita nggak pernah nembak Google lagi.
