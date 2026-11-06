---
title: Empat Dekade Workaround Defensif, Satu Bypass OpenSSH
slug: openssh-musl-password-bypass-sshole
date: 2026-11-06
excerpt: Di host Alpine tanpa PAM, password sepanjang 257 sampai 1024 karakter bisa membuka akun yang seharusnya terkunci. Enam perbaikan wajar selama 46 tahun yang membangun lubang itu.
tags: openssh, security, musl, alpine, ai-agents
---

Di host Alpine yang gue pegang, password 300 karakter itu sama dengan bypass autentikasi. Bukan buffer overflow, bukan juga race condition.

Yang dikirim cuma string `a` panjang ke akun yang field `/etc/shadow`-nya isinya `*`. Itu sudah cukup.

Özgün Kültekin menamai bug ini *sshole, lalu menulis seluruh timeline-nya di sshhole.com dalam bentuk pelajaran sejarah. Menurut gue framing itu memang pas.

Alasannya sederhana: nggak ada satu orang pun yang salah di sini.

Enam keputusan defensif terpisah disambung selama puluhan tahun, dan tiap potongan jalan persis sesuai tujuan awalnya.

Setiap lapisan itu benar kalau dilihat sendiri. Yang salah justru hasil akhirnya. Ini bukan cerita soal satu bug yang lolos review, tapi soal susunan yang nggak pernah dites bareng.

## Enam keputusan, satu lubang

Urutannya begini, mengikuti kapan tiap potongan disambung:

- Tahun **1980**, Bill Joy nulis `*` di `/etc/passwd` buat akun `daemon`, supaya nggak ada password yang bisa cocok. Konvensi itu masih kepakai di `/etc/shadow` sampai sekarang.
- Tahun **1997**, Single Unix Specification mewajibkan `crypt()` membalikin NULL kalau gagal nge-hash. Banyak program nggak pernah ngecek, jadi ujungnya segfault, bukan login gagal.
- **Agustus 2012**, commit musl `b3c4cc12` berhenti membalikin NULL. Kalau hashing gagal, hasilnya `"*"`, jadi pemanggil ceroboh tetap ditolak tanpa crash.
- **Dua puluh hari kemudian**, commit `88bf5a8a` memasukkan SHA-512 crypt dengan batas keras 256 byte (`KEY_MAX`), supaya password kepanjangan nggak bikin CPU tetap sibuk.
- Tahun **2016**, `pick_salt()` masuk buat CVE-2016-6210. OpenSSH membocorkan keberadaan akun lewat selisih waktu `crypt()`, dan fix-nya nge-hash pakai salt pinjaman kalau akunnya nggak punya hash asli.
- Tahun **2022**, commit Alpine 3.16 `fbe926af` mengembalikan field root yang terkunci dari `!` ke `*`, karena tanpa pluggable authentication modules (PAM) tanda `!` juga mematikan login public key.

Taruh keenamnya di satu garis waktu, tabrakannya kelihatan jelas. Nilai kegagalan musl itu `"*"`. Penanda akun terkunci di shadow juga `*`. Dan fix timing 2016 justru ada supaya `crypt()` tetap dijalankan buat akun yang nggak punya hash.

## Perbandingan yang menentukan

Pengecekan password normal itu cuma tiga langkah:

- sshd ambil salt dari field yang tersimpan,
- password yang lo ketik di-hash pakai salt itu,
- hasilnya dibandingkan dengan isi field.

Akun yang dikunci pakai `*` nggak punya salt sendiri. Jadi `pick_salt()` minjam salt dari user lain yang punya password asli.

Bypass ini butuh ada akun lain yang punya password asli di mesin yang sama. Tanpa user ber-password asli, nggak ada salt yang bisa dipinjam.

```c
/* bentuk alurnya, bukan source literal */
hash  = crypt(password, borrowed_salt);   /* musl: "*" kalau input > 256 byte */
match = strcmp(hash, shadow_field) == 0;  /* "*" vs "*" -> 0, diterima */
```

Dua syarat harus ketemu bareng. Password yang dikirim harus lewat dari batas 256 byte musl, dan field shadow-nya harus persis `*`.

Di demo browser Kültekin, rentang yang bisa dipakai 257 sampai 1024 karakter.

## Separuh lainnya dari Alpine

Alpine bukan yang menciptakan field `*`, tapi mereka punya alasan bagus buat memakainya.

Tahun 2019, CVE-2019-5021 membongkar image Docker yang ternyata nggak punya password root sama sekali. Alpine mengunci root pakai `!`, yang di sistem ber-PAM itu keputusan benar.

Tanpa PAM, `!` juga menolak login public key buat akun itu. Image cloud masuk pakai key, jadi fix-nya malah merusak user sendiri.

Alpine 3.16 mengganti field-nya ke `*`, dan key jalan lagi.

Di image resmi Alpine untuk AWS dan Azure, user default `alpine` dapat `*` plus `doas` tanpa password. Jadi bypass ini nggak berhenti di shell user biasa. Berhentinya di root.

## Sepuluh tahun nyaris

Kenapa lubang ini diam dari 2016 sampai 2026? Sebagian besar jawabannya soal siapa yang menguji apa.

Test login OpenSSH jalan di OpenBSD dan glibc. Hampir semua distro melewatkan autentikasi password lewat PAM, yang sudah menolak `*` sebelum `crypt()` sempat dipanggil. musl nggak menguji sshd. sshd juga nggak menguji musl.

Ada tiga orang yang sudah sangat dekat:

- Bug Debian #714219 tahun 2013 minta glibc meniru `"*"` punya musl. Enam tahun kemudian Debian pindah ke libxcrypt yang membalikin `"*0"`, dan laporannya ditutup. Selisih satu karakter.
- Thread di mailing list musl Desember 2024 melaporkan BusyBox `passwd` rusak kalau dikasih password 257 karakter. Sentinel-nya sama, batas 256 byte-nya sama, dan nggak ada yang menyebut sshd.
- Tanggal 30 Oktober 2026, sebuah security review menyentuh `pick_salt()` di OpenSSH. Bug-nya cuma empat baris di bawah perubahan itu, empat hari sebelum Kültekin menemukannya.

## Embargo ikut mati di situ

Damien Miller mengumumkan 10.6p2 pada 5 November 2026, sehari setelah laporan masuk ke dia. Alasan yang dia tulis sendiri ternyata lebih panjang umurnya dari CVE-nya:

> We have recently observed multiple cases of rapid bug rediscovery by AI agents, sometimes within hours, and so now consider long embargo periods to be a dangerous practice that primarily benefits attackers.

Di release notes, pesannya sama, cuma dengan suara proyek. Kalau bug temuan AI bisa ditemukan ulang secara independen oleh peneliti kedua, penyerang yang nggak pernah melapor pun kemungkinan besar bisa menemukannya juga.

Soal penemuannya, ada satu detail menarik. Kültekin mem-build sshd dalam matriks libc, PAM, dan layout shadow, lalu menembakkan 17.600 percobaan login ke semua build itu. Hash rusak, akun cacat, password kepanjangan.

Di situsnya dia bilang jelas: bagian repetitif itu dikerjakan agent swarm.

Gue menjalankan fleet serupa buat runbook dan code review di Dagango.com. Jadi bagian itu bukan hal baru buat gue.

## Yang gue ubah di host sendiri

Cakupan terdampak lebih sempit dari yang terdengar di judul berita. Distro glibc aman, dan apa pun yang lewat PAM juga aman. Tapi host musl tetap harus di-patch:

```bash
# Host Alpine dan musl lain: upgrade, lalu pastikan build-nya
apk upgrade openssh
apk list -I openssh   # harusnya openssh-10.6p2-*

# Belum bisa patch sekarang? Matikan password auth sekalian.
printf 'PasswordAuthentication no\n' > /etc/ssh/sshd_config.d/00-no-passwords.conf
rc-service sshd restart
```

Host yang dari awal pakai `PasswordAuthentication no` nggak pernah punya pintu buat dibuka. Baris itu kerja lebih keras dari yang kita kira.

Buat triage, proyeknya menyediakan pengecek log di github.com/oz9un/sshole. Yang dicari tanda password diterima untuk akun yang seharusnya nggak punya password sama sekali.

Satu hal yang gampang terlewat: `apk upgrade openssh` cuma berguna kalau repo image-nya hidup. Container yang di-build setahun lalu nggak akan pernah menyentuh paket ini. Buat itu, matikan password auth di image lalu rebuild.

## Yang sebenarnya berubah

Gue nggak menaruh kasus ini di rak "masalah Alpine". Kegagalan yang menarik justru di antarmuka antara komponen.

Konvensi penguncian di file teks dan sentinel error di libc sama-sama ide bagus. Cuma nggak ada satu pun yang dirancang sebagai batas autentikasi. Dan nggak ada bagian mana pun di stack yang dibangun buat menyadari dua nilai itu sudah jadi sama.

Pelajaran operasionalnya lebih membosankan, tapi lebih berguna. Kalau upstream sekarang merilis emergency release dalam hitungan jam karena agent menemukan ulang bug secepat itu, ritme patch kita harus tahan.

Jendela maintenance bulanan itu taruhan bahwa jarak antara disclosure dan eksploitasi masih diukur dalam bulan.

Di host yang gue pegang, taruhan itu berhenti murah minggu ini.

Jadi catat daftar host terdampak sebelum lo butuh daftarnya. Punya gue masih berupa shell history, dan itu bukan inventaris.
