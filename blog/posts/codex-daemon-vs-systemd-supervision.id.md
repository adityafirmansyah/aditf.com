---
title: Kalau Diurus systemd, Daemon Codex Nggak Bakal Seberantakan Ini
slug: codex-daemon-vs-systemd-supervision
date: 2026-10-13
excerpt: Sejak versi 0.157.0, Codex CLI otomatis menyalakan background daemon yang meng-update dirinya sendiri. Pendekatan ini memicu banyak masalah, padahal systemd sudah punya solusi yang jauh lebih bersih.
tags: agents, systemd, self-hosting, coding-agents, linux
---

## Daemon yang menyala diam-diam

Di release notes versi 0.157.0 tanggal 2026-09-25, terselip satu kalimat pendek:

> Enabled automatic background-server startup for eligible interactive sessions, with recovery choices when server settings are incompatible.

Penjelasannya cuma sepotong itu. Nggak ada detail soal proses background yang bakal nongkrong terus. Nggak ada peringatan soal copy file sebesar 374 MB. Apalagi info soal background updater otomatis.

Di hari yang sama, Issue #48195 langsung dibuka. Dua minggu kemudian, pembahasannya tembus front page Hacker News dengan 500-an poin dan lebih dari 250 komentar. Komunitas ramai menanyakan hal yang sama: siapa sebenarnya pemilik proses ini, dan binary mana yang sedang dieksekusi?

Akar masalahnya persis seperti yang diangkat di issue itu. Sejak 0.157.0, setiap kali lo membuka sesi interaktif biasa, CLI otomatis memanggil `codex app-server --managed-daemon`.

Proses ini berjalan di session mandiri tanpa TTY dan langsung di-reparent ke PID 1. Begitu terminal lo tutup, prosesnya tetap hidup di background sampai lo kill manual atau restart laptop.

Prinsip gue cukup tegas: CLI coding agent harusnya menjadi service yang kita supervisi sendiri. Bukan aplikasi yang diam-diam memasang daemon di belakang punggung pengguna.

Ini bukan soal nostalgia masa lalu. Ini murni soal kendali: proses yang punya nama dan batas jelas, lawan proses tersembunyi yang harus lo lacak manual.

## Binary yang dieksekusi bukan yang lo instal

Masalah kedua: proses yang berjalan ternyata bukan binary yang baru lo pasang lewat package manager. Daemon-nya membuat salinan baru terlebih dahulu.

Dokumentasi modulnya sendiri menyebutkan kalau proses `bootstrap` menyalin seluruh paket ke `CODEX_HOME/packages/app-server-daemon` tanpa meminta konfirmasi pengguna sama sekali.

Ukuran salinannya lumayan masif, sekitar 374 MB. Paket ini membundel binary `codex` dan `codex-code-mode-host`, serta dependensi internal seperti `bwrap`, `zsh`, dan `rg`. File-file ini mendarat di `~/.codex/packages/app-server-daemon/releases/<version>/`, persis sama dengan file yang baru saja lo download.

Di titik inilah rantai provenance langsung terputus.

Binary yang lo review bukan lagi binary yang mengeksekusi prompt lo. Versi yang lo kunci di project bukan lagi versi yang memproses data.

Dampaknya langsung muncul di berbagai issue GitHub:

- **Issue #48050:** paket Arch Linux langsung crash kalau nggak dijalankan dengan flag `--no-daemon`.
- **Issue #46468:** setelah lo update versi via npm, background server masih saja menyangkut di versi lama.
- **Issue #41188:** nggak ada konfigurasi resmi buat mengarahkan daemon ke custom executable milik pengguna.
- **Issue #42457:** hook pada mode `--remote` salah membaca direktori kerja daemon, bukan direktori proyek lo.

Empat laporan berbeda, tapi akar masalahnya tunggal: daemon mengisolasi filenya sendiri, sehingga package manager lo kehilangan kendali penuh.

## Updater otomatis dan batas toleransi 60 detik

Selain server, ada satu proses detached lagi: `codex app-server daemon pid-update-loop`. Proses ini mengecek update baru 5 menit setelah start, lalu rutin berjalan tiap jam.

Jadwal ini aktif otomatis begitu sesi pertama dibuka.

Risikonya dirangkum gamblang di Issue #40969. Sebenarnya app-server sudah punya mekanisme graceful shutdown buat menunggu turn selesai. Sayangnya, daemon cuma memberi waktu 60 detik sebelum menembakkan `SIGKILL`.

Si pelapor issue sedang menjalankan 13 thread pengujian berdurasi panjang. Di sana, satu sesi build dan test Go butuh waktu antara 3 sampai 30 menit. Setiap kali auto-update terpicu, seluruh pekerjaan yang sedang berjalan langsung hangus.

Sekarang dokumentasinya memang sudah menambahkan opsi di `settings.json`:

```json
{
  "shutdownGraceSeconds": 60,
  "updater": { "autoUpdateEnabled": false }
}
```

Batas 60 detik itu sekarang resmi terdokumentasi, bukan lagi misteri. Tapi tetap saja, timeout 60 detik mustahil mengejar proses kompilasi 30 menit.

Apalagi waktu issue pertama kali mencuat, opsi buat mematikan auto-update ini belum tersedia sama sekali.

## Perintah stop yang meninggalkan sisa proses

Kelemahan paling fatal dari sistem supervisi rakitan ini terlihat saat lo mencoba mematikannya.

Ketika lo menjalankan `codex app-server daemon stop`, app-server memang mati. Namun background updater-nya tetap tertinggal di memori. Proses `pid-update-loop` masih aktif lebih dari semenit kemudian, sampai harus dimatikan paksa lewat terminal.

Alur pembersihan totalnya jadi sepanjang ini:

```sh
codex features disable daemon_auto_start
codex app-server daemon stop
pkill -f 'app-server daemon pid-update-loop'
rm -rf ~/.codex/packages/app-server-daemon
```

Empat baris perintah hanya untuk mematikan satu tool CLI. Termasuk memanggil `pkill` manual untuk membereskan sisa proses yang tertinggal.

Kalau sebuah service manager masih menyisakan anak proses saat dihentikan, fungsinya sebagai supervisor otomatis gagal.

## Environment variabel warisan sesi pertama

Isu kepemilikan proses ini bertambah parah dengan adanya laporan keamanan baru: kredensial siapa yang sebenarnya tersimpan di dalam daemon?

Laporan Issue #53547 masuk pada 2026-10-13T04:00:03Z, menguji versi 0.162.1 di macOS. Masalah ini mencuat kurang dari sepuluh jam setelah thread Hacker News viral.

Langkah ujinya sangat simpel. Cukup pasang satu variabel rahasia di terminal pertama. Lalu buka Codex dengan daemon aktif, dan periksa sesi lain di direktori terpisah. Hasilnya: sesi kedua bisa membaca variabel dari sesi pertama secara bebas.

README resminya mengakui hal ini secara terbuka: klien yang berbagi daemon bakal mewarisi environment awal saat daemon pertama kali dinyalakan. Membuka terminal baru atau menghapus variabel nggak bakal membersihkan environment daemon yang sedang aktif.

Bagi siapa pun yang mengelola AI agent, ini celah yang sangat riskan.

Variabel seperti `HTTPS_PROXY`, `AWS_PROFILE`, `NODE_EXTRA_CA_CERTS`, sampai API key rahasia bakal terbawa dari sesi yang pertama kali memicu daemon. Pelapor Issue #48195 menjalankan Codex lewat wrapper dengan custom proxy per sesi. Akibatnya, proxy dari sesi pertama terkunci di daemon dan seluruh sesi berikutnya ikut dialihkan ke proxy tadi.

Ini bukan sekadar bug kecil. Ini kebocoran kredensial dan network routing antar project yang harusnya terisolasi rapat.

## Solusi yang sudah lama disediakan systemd --user

Padahal di ekosistem Linux, semua kerumitan ini sudah tuntas diselesaikan oleh user service systemd bertahun-tahun lalu.

Di server homelab yang gue pakai sehari-hari, pola semacam ini ditangani rapi oleh satu service multiplexed. Gue mengelola 17 profil agent plus satu default profil tanpa masalah sama sekali. Konfigurasi intinya cukup sesederhana ini:

```
[Service]
Type=simple
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=70
```

Kalau kita bandingkan, pendekatan systemd jauh lebih masuk akal:

- `Restart=always` dan `RestartSec=5` menggantikan script updater background yang rawan error.
- `KillMode=mixed` memberikan sinyal SIGTERM lalu SIGKILL secara bertahap, membereskan main process terlebih dahulu.
- `TimeoutStopSec=70` menetapkan batas toleransi drain secara transparan di dalam file konfigurasi.
- Alokasi memori terpantau akurat lewat cgroup bawaan kernel, bukan tebak-tebakan via `ps`.
- Seluruh log tersentralisasi rapi di `journalctl`, tanpa perlu folder log khusus.

Di mesin Celeron J4105 tempat tulisan ini dibuat, satu baris perintah `systemctl --user show hermes-gateway.service` langsung menjawab metrik penting yang kita butuhkan:

- `MemoryCurrent` berada di angka 5,9 GiB dengan `MemoryPeak` 8,6 GiB dari total RAM 15 GiB.
- `TasksCurrent` stabil di kisaran 100 task.
- Status restart tercatat rapi (`NRestarts=2`), dengan `MainPID=802421` yang aktif stabil.
- `MemoryAccounting=yes` memastikan nggak ada kebocoran resource yang luput.

Satu pemilik yang jelas. Satu siklus hidup proses yang pasti. Pemantauan memori, restart, dan log bisa dicek dari satu tempat.

## Hitung kapasitas disk sebelum mengadopsi

Menyalin file 374 MB untuk satu instalasi mungkin terasa sepele. Tapi beban itu membengkak cepat ketika lo punya banyak environment kerja.

- 17 profil dikalikan 374 MB memakan ruang sekitar 6,21 GiB.
- Sisa kapasitas disk di storage server gue cuma 17 GiB dari total 115 GiB (pemakaian sudah 86%).

Ini bukan simulasi di atas kertas. Menyerahkan 6 GiB kapasitas penyimpanan cuma buat menyalin binary yang sudah ada jelas pemborosan yang nggak masuk akal.

Komunitas packaging Linux bahkan sudah mengambil tindakan. Repositori nixpkgs menyertakan patch khusus yang membalik konfigurasi default `daemon_auto_start` dari true menjadi false, dengan menyertakan referensi langsung ke Issue #48195.

Dokumentasi resminya malah yang paling lambat beradaptasi. Halaman konfigurasi hanya mencatat parameter `check_for_update_on_startup`, tanpa penjelasan detail soal `daemon_auto_start`. Sementara modul daemon-nya masih dilabeli eksperimental meski sudah diaktifkan secara default.

## Kesimpulan praktis

Untuk lingkungan kerja yang stabil dan minim kejutan, pendekatan gue tetap konsisten:

- Jalankan CLI dengan flag foreground atau `--no-daemon`, atau matikan fiturnya dan buat service unit sendiri.
- Pastikan baris `ExecStart` mengeksekusi binary asli yang lo pasang secara sadar.
- Serahkan urusan restart, batas waktu shutdown, dan pembersihan proses ke supervisor sistem.
- Pantau konsumsi memori dan jejak log langsung dari cgroup serta system journal.

Sebagai developer yang tiap hari bereksperimen dengan berbagai AI tooling dan sistem automasi, gue selalu memegang satu patokan: jangan biarkan kenyamanan instan mengorbankan transparansi sistem lo sendiri. Otomasi yang bagus itu bukan yang bekerja diam-diam tanpa izin, melainkan yang perilakunya bisa lo prediksi, lo pantau, dan lo batasi kapan pun dibutuhkan.

Kalau sebuah developer tool menolak untuk disupervisi secara transparan, tool itu belum siap masuk ke pipeline kerja harian kita. Jangan biarkan background process mengambil alih kendali sistem lo sendiri. 😅
