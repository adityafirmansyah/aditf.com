---
title: Bug 14 Tahun di Core PHP Mendadak Bikin 70% Web Kena RCE Pre-Auth
slug: a-14-year-old-bug-in-php-shattered-pre-auth-security
date: 2026-10-27
excerpt: Celah di parser request PHP yang umurnya sejak 2012 bikin penyerang tanpa login bisa eksekusi kode di konfigurasi default. PHP sendiri jalan di sekitar 70% web dunia.
tags: security, php, devops, vulnerability, software-engineering
---

Tanggal 21 Oktober 2026 PHP ngelepas perbaikan buat dua celah kritis, CVE-2026-109618 dan CVE-2026-109619.

Dua-duanya dapat skor 9.2 di versi 4.0 Common Vulnerability Scoring System (CVSS).

Orang nyebutnya PHP2Shell, dan CISA masukin keduanya ke katalog Known Exploited Vulnerabilities tanggal 26 Oktober.

PHP jalan di 69,2% dari semua situs yang bahasa server-side-nya diketahui W3Techs. Itu angka di balik semua judul "sekitar 70% web".

Yang bikin gue nggak tenang bukan skornya. Ini bukan soal plugin jelek atau framework yang lupa nge-filter parameter.

Eksekusinya di dalam parser request milik engine-nya sendiri, tepat saat body multipart masih diterjemahin jadi `$_POST` sama `$_FILES`.

Di titik itu router lo belum ada. Belum sempat jalan.

Makanya ini urusan yang wajib dipatch sekarang juga, bukan sekadar hardening santai. Semua filter input dan middleware yang kita pasang posisinya baru jalan setelah kode C engine-nya telanjur jebol.

## Parser jalan duluan, modulnya belum aktif

PHP harus bikin `$_POST` sama `$_FILES` sebelum ada script yang bisa baca isinya, jadi parsing-nya masuk fase request startup.

Urutannya di `main/main.c` seperti ini, dikutip dari disclosure Calif:

```c
PG(modules_activated) = 0;
/* ... */
php_hash_environment();   /* Parses request variables and multipart input. */
zend_activate_modules();  /* Calls normal module RINIT functions. */
PG(modules_activated) = 1;
```

Dari situ keluar dua akibat:

- request multipart tetap diparsing walau endpoint-nya nggak pernah nerima upload,
- fatal error di tengah parsing itu bukan error aplikasi, dan handler lo nggak pernah kepanggil.

Di konfigurasi default jalur ini kebuka. `session.upload_progress.enabled` bawaannya `On`, yang bikin extension session buka dan update session selagi body dibaca.

## Hitungan dinaikkan dulu, alokasi belakangan

Tim Calif nelusuri mekanismenya sampai ke rutin insert hash table `_zend_hash_str_add_or_update_i`. Hitungan elemen dinaikkan sebelum bucket selesai diinisialisasi:

```c
idx = ht->nNumUsed++;
ht->nNumOfElements++;
p = ht->arData + idx;
p->key = zend_string_init(str, len, persistent); /* may zend_bailout() */
```

Pas alokasi key kena `memory_limit`, PHP nggak unwinding rapi. Dia loncat keluar lewat `longjmp()` level C dengan hitungan yang telanjur naik.

Terus waktu teardown, PHP jalanin `ht->arData` sampai batas `nNumUsed` dan nganggep bucket setengah jadi itu data hidup.

Bikin PHP jebol batas memori ini gampang banget, bahkan tanpa kirim file raksasa. Penyerang cukup kirim form multipart berformat RFC 1867 dengan nama file kosong. Trik ini bikin payload lolos dari saringan `max_file_uploads`, tapi engine PHP tetap dipaksa bikin enam entri metadata `$_FILES`.

Kalau nama field-nya dibikin bersarang kayak `files[a][b][c]`, hierarki hash table tadi bakal dibangun ulang enam kali lipat. Ratusan entri kosong begini gampang banget ngabisin heap 128 MiB, padahal ukuran request HTTP-nya masih jauh di bawah batas 8 MiB `post_max_size`.

Body chunked HTTP/1.1 atau HTTP/2 tanpa length lewat batas sama. PHP cuma bandingin `Content-Length` yang dideklarasi, bukan byte yang benar-benar dikonsumsi.

## mod_php vs PHP-FPM: Dampak dan Alurnya Beda Jauh

Dua-duanya memparsing body secara identik. Bedanya ada di nasib worker setelah kena fatal error pas startup.

Di Apache pakai `mod_php`, startup yang gagal tetap nyampe ke `php_request_shutdown()`. Heap request dibebasin, child process Apache-nya selamat buat layani request berikutnya.

Session globals yang masih nunjuk ke heap itu dimakan request multipart berikutnya. Hasilnya RCE ke script PHP apa pun, tanpa aplikasinya ikut main.

PHP-FPM ambil cabang lain. Startup gagal berarti `php_module_shutdown()` dipanggil dan `FPM_EXIT_SOFTWARE` dikembalikan. Worker-nya mati, pointer basi ikut mati.

Artinya di FPM fatal-nya harus mendarat setelah startup sukses, saat aplikasi udah mulai ngedecode sesuatu.

Rantai kedua itu butuh pemicu dari alur aplikasi:

- aplikasi memproses data serialisasi saat alokasi memori sengaja dimanipulasi penyerang sampai mepet limit,
- proses decode berjalan lewat `session_start()`, `session_decode()`, `unserialize()`, atau fungsi wrapper kayak `maybe_unserialize()` di WordPress,
- error fatal bikin fungsi `php_var_unserialize_destroy()` terlewat, sehingga pointer `BG(unserialize).data` dan status nesting di extension Basic tetap menggantung,
- heap request langsung dibebaskan sementara worker PHP-FPM tetap dibiarkan hidup,
- request multipart berikutnya masuk ke handler upload progress sebelum extension Basic diinisialisasi ulang, memanfaatkan sisa struktur decoder tadi buat nulis `zval` buatan penyerang ke blok memori yang dialokasikan ulang.

Calif sukses mendemokan skenario ini di server nginx. Syarat serangannya sama sekali nggak muluk-muluk: penyerang cukup kirim session ID custom ke endpoint yang manggil `session_start()`, sesuatu yang dibuka secara wajar oleh ribuan aplikasi PHP.

## Cara Patch Ini Merombak Penanganan Error PHP

Perbaikannya jauh lebih cerdas ketimbang sekadar nambahin validasi batas array biasa.

Kondisi out-of-memory sekarang nggak langsung menghentikan eksekusi secara brutal di tengah jalan. Error OOM diubah jadi soft error yang baru dieksekusi di safe point VM berikutnya, sehingga proses cleanup tetap jalan dan pointer dibersihkan sebelum memori dilepas.

Kalau konsumsi memori melewati batas ambang darurat yang lebih tinggi, barulah proses dimatikan langsung lewat pemanggilan `_exit()`.

Fase shutdown engine sekarang juga membersihkan semua variabel global persisten yang sebelumnya sempat lolos:

- session globals,
- error backtrace,
- shared memory OPcache.

Selain itu, objek yang diproses handler upload progress dikunci dalam status `__PHP_IncompleteClass`. Trik ini ampuh memastikan fungsi autoload maupun `__destruct()` nggak bisa dieksekusi diam-diam di fase parsing awal.

Daftar tambalan ini ngebuktiin satu hal penting: sistem isolasi yang cuma ngandelin mekanisme jump `longjmp()` dengan harapan cleanup-nya bakal mendarat mulus itu bukan isolasi sejati.

Itu murni taruhan untung-untungan, dan keberuntungannya baru jebol sekarang setelah belasan tahun.

## Kalau lo belum bisa patch hari ini

Upgrade kadang nunggu jadwal maintenance. Semua langkah di bawah parsial, nggak ada yang gantikan rilis yang dipatch.

```ini
; emergency only, revert after upgrading
session.upload_progress.enabled = 0
fatal_error_backtraces = 0        ; PHP 8.5.x
memory_limit = -1
```

Lima detail yang nentuin baris itu beneran nolong atau nggak:

- restart semua worker setelah ngubah `php.ini`, karena child Apache dan worker FPM yang jalan pegang nilai lama,
- set `pm.max_requests = 1` selama masih kebuka, ini yang mecah syarat satu worker nanganin dua request berurutan,
- matiin `session.upload_progress` sambil sadar itu nggak nutup cabang OPcache maupun backtrace,
- jangan ganti `memory_limit` pakai `RLIMIT_AS` atau `RLIMIT_DATA` karena limit OS ngelewatin jalur cleanup PHP,
- terima kalau `memory_limit = -1` menukar eksekusi kode jadi denial of service karena kehabisan memori.

Kompromi terakhir ini yang paling berisiko kalau server lo dipakai barengan (shared hosting). Penyerang yang gagal mengeksekusi kode tetap bisa dengan mudah membombardir form kosong bersarang buat nguras habis sisa RAM server lo.

## Bagian tersusah itu justru inventarisasinya

Yang bawa perbaikan cuma empat rilis ini:

- PHP 8.5.12,
- 8.4.27,
- 8.3.36,
- 8.2.35.

Di bawah 8.2 nggak dapat apa-apa, padahal jalur paling tua yang kena balik ke PHP 5.4.0 dari Maret 2012.

Saran CISA buat yang masih di 8.1 atau lebih lama: tarik offline.

Masalah terbesarnya justru bukan proses patch, melainkan melacak inventaris server lo. Runtime PHP sering kali nyelip di tempat-tempat yang nggak kelihatan secara kasat mata:

- proses `php-cgi` dan server LiteSpeed,
- image build FrankenPHP,
- base image container yang di-build berbulan-bulan lalu dan nggak pernah di-refresh,
- appliance dari vendor pihak ketiga yang konsol adminnya sama sekali nggak nyebut kalau mereka pakai PHP di baliknya.

Yang gue ubah di stack sendiri:

- tolak `multipart/form-data` di ingress buat route yang nggak pernah terima upload, biar body-nya nggak nyampe PHP,
- build ulang image pakai versi yang udah dipatch dan di-pin, bukan ngedit `php.ini` di host yang jalan,
- sandbox worker-nya biar proses yang udah dijebol nggak bisa exec shell atau download tool, aktivitas yang CISA minta dipantau,
- anggap pemanggilan `session_start()` dengan ID dari penyerang sebagai attack surface berbahaya, karena di arsitektur PHP-FPM alur inilah yang jadi celah masuk eksploitasi.

Hampir semua panduan hardening yang biasa kita buat berasumsi kalau celah keamanan selalu berasal dari kode aplikasi kita sendiri.

PHP2Shell membuyarkan asumsi itu tepat di jantung engine runtime. Setiap request HTTP sebenarnya diproses dua babak: pertama di parser C milik engine, baru kemudian di kode framework lo.

Masalahnya, semua firewall, filter WAF, dan middleware yang lo banggakan cuma berdiri menjaga babak yang kedua.
