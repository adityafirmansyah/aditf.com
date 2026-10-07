---
title: "Kenapa next/font/google Bikin CI Kita Jebol: Self-Host 13 Subset Font biar Build Nggak Butuh Internet"
slug: nextjs-self-host-font-subsets-zero-network-builds
date: 2026-10-07
excerpt: Master CI kita mati dua kali dalam dua belas jam, di commit yang kode font-nya sama persis. Ini cara Dagango.com nyimpen 13 subset font di disk biar next build nggak nembak internet.
tags: nextjs, frontend, performance, webdev, architecture
---

## `next build` itu bukan perintah offline

Gue dulu nganggap `next/font/google` udah beresin semua urusan font. Di sisi browser iya: nggak ada layout shift, request ke Google nggak pernah datang dari mesin pengunjung, dan filenya dilayanin dari origin lo sendiri.

Yang sering kelewat, mesin yang ngejalanin `next build` tetap buka koneksi HTTPS ke fonts.googleapis.com. Tiap kali.

Jadi deploy lo sekarang nempel ke CDN orang lain, dan lo baru sadar pas momennya paling nggak enak.

## Dua build merah dalam dua belas jam

Master CI kita mati di dalam fetch itu dua kali dengan jarak sekitar dua belas jam, dan nggak ada satu baris kode font pun di diff-nya.

Dua run merah itu `36935742623` (merge `42875bb`) dan `36851269872` (`f6b3627`).

Semuanya muncul sebagai `An error occurred in next/font`, terus mendarat di sini:

```
TypeError: Cannot read properties of null (reading '1')
    at @next/font/dist/google/loader.js
```

Commit sebelum dan sesudah masing-masing run merah isinya kode font yang sama persis, dan dua-duanya hijau.

Artinya semua kejadian itu false red yang tetap aja nyita waktu buat ditriage. Pipeline yang suka nangis palsu juga pipeline yang bisa nyembunyiin break asli.

## Sumber fetch-nya di mana

Permintaan waktu build itu datang dari `@next/font/dist/google/fetch-resource.js`.

Kalau CDN Google ngambek atau nge-throttle panggilan itu, loader-nya nyoba baca response yang nggak pernah datang, terus error di `null`. Dependensinya nyata dan letaknya di luar, posisinya persis di antara lo dan build yang hijau.

## Latin doang nggak cukup

Jalan pintasnya: simpan file woff2 latin, selesai. Buat situs yang isinya cuma latin, itu memang cukup.

Masalahnya Dagango.com itu multi-tenant. Merchant nulis copy storefront-nya dalam bahasa Vietnam, Cyrillic, Yunani, dan Devanagari, campur sama latin.

Begitu subset non-latin dibuang, karakter-karakter itu jatuh ke font sistem yang metriknya beda dan glyph-nya bolong.

Untuk tiga family platform kita, Google nyediain set ini:

- **Baloo 2** (display): `latin`, `latin-ext`, `vietnamese`, `devanagari`.
- **Public Sans** (body): `latin`, `latin-ext`, `vietnamese`.
- **JetBrains Mono**: `latin`, `latin-ext`, `vietnamese`, `cyrillic`, `cyrillic-ext`, `greek`.

Totalnya 13 file dan 225 KB. Semua subset yang Google sediain buat ketiga family itu ada di situ, nggak ada yang disisihin.

## `next/font/local` buang `unicodeRange` yang nempel di `src`

`next/font/local` nggak punya opsi `subsets`.

Subset juga nggak bisa dikasih lewat range di entry `src`: loader bawaan cuma destructure `{ path, style, weight, ext, format }` dari tiap entry, sisanya dibuang diam-diam.

Jalan keluarnya lewat `declarations`. Loader nyalin tiap declaration ke `@font-face` yang dia bikin, jadi satu call per (family, subset) bisa nenteng range persis punya subset itu.

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

Perhatiin `font-family` di situ. Theme tenant yang udah tersimpan nyari family default platform berdasarkan NAMA (`lib/theme/derive.ts`), dan storefront shell-nya sengaja nggak minta stylesheet buat family itu. Kalau namanya di-scope ke nama generated Next, tenant itu bakal render lewat fallback face tanpa kita sadar.

## Jangan biarin fallback face beranak

`next/font` bikin satu face `... Fallback` yang metriknya disamain, per call. Kalau defaultnya dibiarin, tiap subset nambah family fallback sendiri.

Jadi kita set dua hal:

- `preload: true` cuma di tiga call latin, karena cuma file itu yang di-preload build.
- `adjustFontFallback: false` di sepuluh call sisanya, biar nggak ada family `... Fallback` tambahan.

Ketiga belas call itu dirangkai jadi satu string `fontVariables` yang dipasang di `<html>`.

Rangkaian ini jangan sampai bolong. Call `localFont()` yang class-nya nggak pernah kepasang bakal di-tree-shake, sekalian `@font-face` dan file-nya.

## Cara mastiin build-nya beneran nggak nyentuh internet

Config yang keliatan air-gapped belum tentu bukti. Jadi build-nya kita jalanin di bawah `strace`:

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

Nol socket keluar, nggak ada DNS lookup, nggak ada koneksi ke port 443. Build-nya jalan penuh tanpa internet.

## Satu delta yang gue catat

Semua di atas byte-nya identik dengan yang selama ini udah dipancarin loader Google. Bedanya cuma di tiga face `... Fallback` yang masih ada: angka `size-adjust`-nya berubah setelah pindah.

Penyebabnya, loader Google baca tabel capsize yang udah dihitung Next, sementara loader lokal ngukur filenya sendiri pakai fontkit. Ini cuma kena teks yang digambar dari fallback face, artinya jendela sebelum swap dan dua glyph panah yang nggak dipegang subset mana pun. Teks yang pakai webfont tetap sama.

## Yang gue saranin buat lo copy

Kalau `next build` lo masih ngobrol sama internet, build lo bukan build offline.

Simpan woff2 yang loader-nya udah keluarin, kasih satu call per subset, terus buktiin senyapnya pakai `strace`.

Terakhir, tambahin test yang gagal begitu ada font call nggak kepakai. Soalnya itu mode gagal yang lolos dari build hijau: satu `localFont()` tanpa class di `<html>` bikin yang ke-ship cuma tiga face, bukan 13.

Kalau gue harus rangkumin, build itu tempat di mana lo pengen satu-satunya yang bikin merah ya kode lo sendiri.

Selama masih ada layanan pihak ketiga yang bisa bikin pipeline lo merah tanpa lo sentuh apa-apa, itu artinya lo belum punya build yang bisa dipercaya.

Dan font cuma soal kecil. Kalau yang kecil aja bisa goyangin pipeline, bayangin yang besar.

Jadi ya, gue nggak nyesel ngebuang `next/font/google`. Dua belas jam sama dua run merah itu udah cukup buat gue pindah, dan sampai sekarang build kita nggak pernah nembak Google lagi.

Dan buat gue sendiri, intinya sederhana: font itu cuma aset, dan aset nggak seharusnya bisa ngebobol pipeline cuma gara-gara internet lagi males. 😅
