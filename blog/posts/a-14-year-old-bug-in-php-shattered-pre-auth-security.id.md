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

Di titik itu router lo belum ada. Belum lahir.

Makanya ini urusan patch sekarang juga, bukan hardening pelan-pelan. Semua pengecekan input gue duduknya di hilir kode yang udah korup.

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

Nyampein limit-nya murah. Satu part upload RFC1867 boleh bawa filename kosong, jadi lolos dari `max_file_uploads`. Tapi PHP tetap bikin enam entri `$_FILES`.

Kasih nama field bersarang kayak `files[a][b][c]`, hierarkinya dibangun enam kali. Ratusan record kayak gitu muat di `post_max_size` default 8 MiB, padahal heap yang kepakai lewat 128 MiB.

Body chunked HTTP/1.1 atau HTTP/2 tanpa length lewat batas sama. PHP cuma bandingin `Content-Length` yang dideklarasi, bukan byte yang benar-benar dikonsumsi.

## mod_php sama PHP-FPM bukan lawan yang sama

Dua-duanya memparsing body identik. Bedanya nasib worker setelah fatal saat startup.

Di Apache pakai `mod_php`, startup yang gagal tetap nyampe ke `php_request_shutdown()`. Heap request dibebasin, child process Apache-nya selamat buat layani request berikutnya.

Session globals yang masih nunjuk ke heap itu dimakan request multipart berikutnya. Hasilnya RCE ke script PHP apa pun, tanpa aplikasinya ikut main.

PHP-FPM ambil cabang lain. Startup gagal berarti `php_module_shutdown()` dipanggil dan `FPM_EXIT_SOFTWARE` dikembalikan. Worker-nya mati, pointer basi ikut mati.

Artinya di FPM fatal-nya harus mendarat setelah startup sukses, saat aplikasi udah mulai ngedecode sesuatu.

Rantai kedua itu butuh pemicu dari sisi aplikasi:

- aplikasi ngedecode data terserialisasi di bawah tekanan memori penyerang,
- decode-nya lewat `session_start()`, `session_decode()`, `unserialize()` atau wrapper kayak `maybe_unserialize()` milik WordPress,
- fatal-nya bikin `php_var_unserialize_destroy()` keskip, jadi pointer `BG(unserialize).data` dan level nesting di extension Basic tetap hidup,
- heap request dibebasin sementara worker FPM-nya jalan,
- request multipart berikutnya nyampe ke session upload progress sebelum init Basic, pakai ulang bookkeeping decoder yang ditinggal, dan aritmetika destructor list-nya nulis `zval` yang dikendalikan ke memori yang sudah direbut ulang.

Calif mendemokan rantai itu di nginx. Prasyaratnya nggak eksotis: session ID pilihan penyerang plus satu `session_start()` itu permukaan yang dibuka banyak aplikasi PHP.

## Patch-nya ngubah mode kegagalan

Perbaikannya lebih menarik daripada sekadar nambah pengecekan batas.

Out-of-memory sekarang nggak menghentikan operasi di tengah jalan. Dia jadi soft error di VM safe point berikutnya, jadi cleanup tetap jalan dan pointer dikosongin sebelum memori dilepas.

Lewat dari ambang lebih tinggi, dia berubah jadi `_exit()` keras.

Shutdown juga sekarang nge-reset semua state panjang umur yang dulunya selamat:

- session globals,
- error backtrace,
- shared memory OPcache.

Objek yang didecode handler upload progress tetap `__PHP_IncompleteClass`, jadi nggak ada autoload maupun `__destruct()` di fase decode awal itu.

Baca daftar itu sebagai pengakuan. Isolasi yang bergantung pada loncatan non-lokal mendarat di tempat yang masih bisa dicapai cleanup bukan isolasi.

Itu taruhan untung-untungan, dan untungnya baru habis sekarang.

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

Tukeran terakhir itu yang paling gue timbang di mesin sharing. Penyerang yang nggak bisa nulis bucket tetap bisa ngirim payload upload kosong bersarang dan ngabisin RAM.

## Bagian tersusah itu justru inventarisasinya

Yang bawa perbaikan cuma empat rilis ini:

- PHP 8.5.12,
- 8.4.27,
- 8.3.36,
- 8.2.35.

Di bawah 8.2 nggak dapat apa-apa, padahal jalur paling tua yang kena balik ke PHP 5.4.0 dari Maret 2012.

Saran CISA buat yang masih di 8.1 atau lebih lama: tarik offline.

Masalahnya, mendata lebih berat daripada upgrade-nya. PHP sembunyi di tempat tanpa label:

- invokasi `php-cgi` dan LiteSpeed,
- build image FrankenPHP,
- base image container yang di-bake berbulan lalu,
- appliance vendor yang konsol adminnya nggak pernah nyebut runtime.

Yang gue ubah di stack sendiri:

- tolak `multipart/form-data` di ingress buat route yang nggak pernah terima upload, biar body-nya nggak nyampe PHP,
- build ulang image pakai versi yang udah dipatch dan di-pin, bukan ngedit `php.ini` di host yang jalan,
- sandbox worker-nya biar proses yang udah dijebol nggak bisa exec shell atau download tool, aktivitas yang CISA minta dipantau,
- perlakuin `session_start()` dengan ID dari penyerang sebagai permukaan input, karena di FPM memang iya.

Hampir semua saran hardening yang gue tulis buat stack web berasumsi aplikasi kita itu tempat input jadi bahaya.

PHP2Shell mecahin asumsi itu di batas engine. Satu request hidup dua kali: sekali di parser, sekali di kode lo.

Cuma yang kedua punya firewall lo di depannya.
