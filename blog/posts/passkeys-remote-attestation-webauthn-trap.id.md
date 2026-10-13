---
title: "Jebakan Remote Attestation di Passkeys: Kenapa WebAuthn Bisa Mengancam Kendali Pengguna"
slug: passkeys-remote-attestation-webauthn-trap
date: 2026-10-12
excerpt: Passkey dipromosikan sebagai pengganti password yang kebal phishing. Masalahnya, standar WebAuthn menyimpan mekanisme remote attestation yang bisa mengunci pengguna ke ekosistem raksasa teknologi.
tags: security, authentication, webauthn, privacy, architecture
---

## Janji manis passkey dan realitas di balik kodenya

Narasi yang dijual ke publik terdengar meyakinkan: lupakan password yang gampang ditebak, beralihlah ke kriptografi kunci publik.

Lo nggak perlu lagi pusing mikirin serangan phishing. HP lo bakal otomatis nyinkronkan kredensial antar perangkat, dan semuanya terasa instan.

Sekilas, teknologinya mirip lompatan besar kayak TOTP di RFC 6238. Kita membayangkan standar terbuka yang bisa dijalankan di aplikasi pengelola password mana pun yang kita percaya.

Tapi kalau lo buka spesifikasi resmi W3C WebAuthn Level 3, ada cerita lain yang jarang dibahas.

Di dalam protokol itu, tersimpan satu fitur bernama remote attestation. Begitu pemilik website mengaktifkan opsi ini, fungsi passkey langsung bergeser. Kredensial ini bukan lagi milik pengguna seutuhnya, melainkan sertifikat perangkat yang terikat mati ke Apple, Google, atau Microsoft.

## Cara kerja remote attestation di balik layar

Setiap kali browser memanggil `navigator.credentials.create()`, server mengirimkan sejumlah opsi pendaftaran. Sebagian besar website saat ini memang masih memakai opsi default:

```js
const options = {
  publicKey: {
    challenge: new Uint8Array([/* ... */]),
    rp: { name: "Dagango" },
    user: { id: new Uint8Array([/* ... */]), name: "merchant@dagango.com" },
    pubKeyCredParams: [{ alg: -7, type: "public-key" }],
    authenticatorSelection: {
      authenticatorAttachment: "platform",
      userVerification: "required"
    },
    attestation: "direct" // Parameter penentunya ada di sini.
  }
};
```

Kunci permasalahannya ada pada parameter `attestation` tersebut.

Secara default, nilainya disetel ke `"none"`. Tapi begitu server menyetelnya ke `"direct"` atau `"enterprise"`, browser nggak bisa cuma mengirim public key biasa.

Perangkat lo diwajibkan mengirim sertifikat attestation yang ditandatangani langsung oleh chip keamanan bawaan pabrik:

- Apple Secure Enclave buat perangkat iOS dan macOS.
- Android StrongBox atau Google Titan buat ekosistem Android.
- Chip TPM fisik buat laptop atau PC Windows.

Server bukan cuma memverifikasi apakah lo memegang private key yang cocok. Server bakal memeriksa tipe perangkat lo, keaslian sistem operasinya, dan apakah kuncinya dikunci permanen di dalam silikon fisik yang nggak bisa diekspor.

## Nasib aplikasi seperti KeePassXC

Di sinilah letak benturan utamanya. Aplikasi pengelola password open-source seperti KeePassXC sebenarnya sangat mampu menyimpan passkey.

KeePassXC tinggal menghitung kurva kriptografi ECDSA atau Ed25519 di memori, lalu menyimpan private key di file database terenkripsi lokal. File database ini bebas lo salin, lo backup ke hard disk eksternal, atau lo sinkronkan ke server pribadi.

Kebebasan mengekspor kunci inilah yang menjadi dasar kedaulatan data pengguna.

Namun, di bawah aturan remote attestation yang ketat, skenario ini langsung tumbang.

KeePassXC cuma aplikasi biasa di ruang pengguna (userspace). Aplikasi ini mustahil memalsukan sertifikat chip buatan Apple atau Google.

Kalau sebuah bank atau layanan e-commerce menolak authenticator tanpa attestation hardware, brankas KeePassXC lo otomatis ditolak saat registrasi. Server bakal ngotot meminta authenticator dari sistem operasi arus utama.

## Pola lama yang berulang dari dunia mobile

Bagi developer mobile, manuver ini bukan barang baru. Kita sudah melihat pola yang sama persis lewat Google Play Integrity dan Apple App Attest di smartphone.

Awalnya, fitur pengecekan integritas ini cuma dipakai buat mencegah kecurangan di game online.

Lalu aplikasi perbankan mulai ikutan.

Sekarang, siapa pun yang memakai custom ROM bersih seperti LineageOS atau GrapheneOS harus pasrah: aplikasi bank, transportasi online, sampai portal resmi pemerintah menolak berjalan sama sekali.

Pihak server mengambil alih hak untuk menentukan lingkungan komputasi apa yang boleh mengakses layanannya. Kalau sistem lo nggak masuk daftar putih mereka, lo disingkirkan.

WebAuthn attestation membawa model DRM perangkat keras ini langsung ke dalam browser web. Padahal selama tiga dekade, kekuatan terbesar web adalah independensi klien: peramban apa pun yang memahami HTTP dan HTML dianggap warga kelas satu. Attestation membalik filosofi itu sepenuhnya.

## Titik buta di otomasi dan agen mandiri

Bukan cuma privasi pengguna rumahan yang terancam. Passkey yang terkunci di hardware juga merusak alur kerja otomasi perangkat lunak.

Di Dagango.com, kita menjalankan test suite end-to-end, pipeline CI/CD, dan bot pengadaan barang yang berinteraksi langsung dengan dashboard web. Server runner di cloud tentu nggak punya sensor sidik jari manusia atau chip Secure Enclave fisik.

Sistem passkey yang mewajibkan attestation membikin browser headless lumpuh:

- Mesin runner otomatis nggak bisa mensimulasikan sentuhan biometrik tanpa emulator khusus dari vendor tertentu.
- Worker latar belakang nggak bisa memegang kunci perangkat keras yang sifatnya non-transferable.
- Agen AI mandiri yang berjalan di server Linux headless bakal gagal menembus autentikasi berbasis web.

Kalau website menolak login tanpa passkey hardware, tim engineer akhirnya terpaksa membuat jalur belakang darurat: API key statis, token rahasia tanpa rotasi, atau bypass di environment staging. Upaya menyingkirkan password malah melahirkan tumpukan kredensial baru yang lebih rawan bocor.

## Sikap yang perlu diambil developer backend

Kriptografi kunci publik di WebAuthn memang terbukti ampuh menangkal phishing. Yang bermasalah adalah ketika proses login dipakai untuk menyortir perangkat keras yang sah.

Kalau lo bertanggung jawab membangun sistem autentikasi aplikasi web, ada tiga prinsip yang perlu lo pegang:

- **Selalu pakai `attestation: "none"`.** Jangan meminta bukti attestation hardware kecuali regulasi hukum benar-benar memaksa. Izinkan pengguna mendaftar pakai alat apa pun yang mereka pilih, termasuk KeePassXC atau extension browser.
- **Dukung authenticator lintas platform.** Jangan mengunci opsi ke `authenticatorAttachment: "platform"`. Berikan ruang buat kunci fisik mandiri seperti YubiKey lewat jalur cross-platform.
- **Pertahankan opsi fallback terbuka.** Tetap sediakan 2FA berbasis TOTP (RFC 6238). TOTP bisa diekspor, bekerja offline, mudah diotomasi di pipeline pengujian, dan nggak bergantung pada chip buatan korporasi tertentu.

Autentikasi semestinya melindungi akun pengguna dari penyusup di jaringan. Fungsinya bukan untuk melindungi dominasi vendor teknologi dari pengguna yang ingin mengontrol perangkat mereka sendiri. 😅
