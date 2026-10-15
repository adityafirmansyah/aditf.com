---
title: systemd --user Nggak Beneran Nge-sandbox Agen Gue, dan Nggak Ada yang Ngasih Tahu
slug: systemd-user-sandbox-fails-open
date: 2026-10-15
excerpt: Para pakar keamanan bener soal containment jadi akar masalahnya. Masalahnya, di box yang jalanin fleet gue, direktif yang mereka resepin itu diterima, dilaporkan kepasang, dan diam-diam nggak ngapa-ngapain.
tags: systemd, agent-safety, sandboxing, apparmor, self-hosting
---

Berita soal agen AI yang disebut "ngamuk" minggu ini udah nunjuk penyebab yang bener. Insiden Hugging Face, Anthropic, Meta, dan Gemini itu soal containment dan monitoring yang gagal.

Modelnya bukan lagi punya pikiran sendiri.

Gue jalanin delapan belas profil agen dan satu `hermes-gateway.service` yang multiplex di bawah `systemd --user`, semuanya di satu host Ubuntu.

Jadi daripada cuma ngutip para pakarnya, gue coba lakuin apa yang mereka resepin. Pasang sandbox-nya.

Hasilnya: tiap direktif filesystem dan egress yang bisa diset unit tanpa privilege itu diterima, dipajang `systemctl show` seolah udah kepasang, terus diam-diam nggak ngapa-ngapain.

## CSO bilang containment, dan thread-nya nambahin satu hal

Rob T. Lee dari SANS Institute nggak muter-muter di artikel CSO Online itu:

> "The Hugging Face incident definitively showed that it wasn't the fact that the agents were super smart. It's that there literally was a hole that was exploited because it was not configured correctly on the containment side."

Dan Wallach dari RAND nambahin sisi monitoring-nya. Insiden itu "went on for days, and nobody noticed", katanya.

Bagi gue itu bagian yang paling nyantol. Orang ngejalanin eksperimennya, tapi nggak ada yang nonton.

Thread-nya nambahin konteks yang penting. User HN `ahupp` nyodorin kalimat dari laporan insidennya sendiri:

> Agents "exploited a separate, previously unknown vulnerability in Artifactory to move beyond their sandbox environment."

Terus `root_axis` nyerang dari arah sebaliknya. Pakai Artifactory aja udah salah, apalagi tanpa airgap dan tanpa blokir egress.

Dua-duanya bisa bener sekaligus. Zero-day-nya yang buka pintu, tapi egress yang nggak diawasi dan kredensial yang nggak ada batasnya yang bikin pintunya kebuka berhari-hari.

Nah, bagian itu yang bisa lo ukur sendiri di mesin lo.

## Isi unit yang jalanin fleet gue

Begini bentuknya di unit gateway yang jalanin semua agen gue:

```
NoNewPrivileges=no    PrivateTmp=no
ProtectSystem=no      ProtectHome=no
IPAddressDeny=        RestrictAddressFamilies=~
UMask=0002            MemoryMax=infinity
```

`MainPID`-nya jalan sebagai Uid 1000, dengan `NoNewPrivs: 0` dan `Seccomp: 0`.

Semua profil agen pakai UID yang sama. Jadi radius ledakannya seluas apa pun yang bisa dibuka UID 1000:

- `~/.ssh/id_ed25519`, 420 B
- `~/.hermes/.env`, 29.367 B
- `~/.hermes/config.yaml`, 9.393 B
- `~/.hermes/auth.json`, 1.288 B

Nggak ada yang aneh di situ. Itu cuma bentuk default dari fleet yang tumbuh satu worker setiap kali.

User HN `novaRom` nulis soal pola dari sisi sebaliknya. "I always see attempts to cat ~/.ssh/*", katanya. Agen-agennya udah tahu mereka di dalam sandbox, dan tetap nyoba.

## Gue coba satu-satu, dan hasilnya nol

Satu transient unit per properti. Tiap probe nulis file canary ke `$HOME/.hermes`, terus nyetak mount namespace-nya sendiri:

```bash
systemd-run --user --wait -p ProtectHome=yes \
  /bin/sh -c 'touch $HOME/.hermes/canary; readlink /proc/self/ns/mnt'

systemd-run --user --wait -p IPAddressDeny=any \
  /bin/sh -c 'curl -s -o /dev/null -w "%{http_code}\n" https://example.com'
```

Hasilnya di box gue, Ubuntu 26.04.1, kernel 7.0.0-38-generic, systemd 259.5:

- `ProtectHome=yes` tetap nulis canary dan lapor `mnt:[4026531832]`, sama persis kayak parent-nya
- `ReadOnlyPaths=/home/aditf/.hermes` nggak beda sama sekali
- `PrivateUsers=yes` yang ditumpuk sama `ProtectHome=yes` juga sama
- `IPAddressDeny=any` balikin `200` dari `example.com`, dan `301` dari `http://1.1.1.1` mentah

`systemctl show` tetap lapor `IPAddressDeny=::/0 0.0.0.0/0`. Karena propertinya memang dibaca dan dipajang, mau ada yang ngejalanin atau nggak.

Yang ngasih tahu cuma satu baris journal, dan munculnya cuma sekali tiap boot:

```
systemd[1277]: run-p1951633-i14538200.service: unit configures an IP firewall, but not running as root.
systemd[1277]: (This warning is only shown for the first unit using IP firewalling.)
```

Ada dua kerusakan di sini dan jangan digabung. Yang satu nggak didukung di user unit. Yang satunya lagi justru didukung dan ditawarin, tapi tetap nggak jalan.

## Kernel bilang kenapa dia pilih ngalah, bukan error

`journalctl -k` nyebut penyebabnya. Ada transisi profil AppArmor, terus langsung ditolak:

```
apparmor="AUDIT" operation="userns_create" ... target="unprivileged_userns"
  execpath="/usr/lib/systemd/systemd-executor"
apparmor="DENIED" operation="capable" ... capability=21 capname="sys_admin"
```

Sandboxing filesystem butuh `CAP_SYS_ADMIN` di dalam user namespace baru. Itu yang dipakai systemd-executor buat nyusun mount-nya.

Ubuntu kirim `kernel.apparmor_restrict_unprivileged_userns = 1` lewat `/usr/lib/sysctl.d/10-apparmor.conf`. Profil `unprivileged_userns`-nya isinya baris `audit deny capability,`.

Jadi systemd-executor milih ngalah daripada gagal. Service-nya jalan di mount namespace host tanpa sandbox, dan statusnya tetap `active (running)`.

Ini bukan keanehan lokal. Issue 25014 di systemd nyatet `ProtectHome=true` memang nggak jalan di mode `--user`.

Fleet worker di block ngalamin penolakan `sys_admin` yang persis sama, terus filed issue 5670. Laporannya: sandbox-nya "silently does not apply", dan unit-nya "has full read/write access to `$HOME`", termasuk folder secret mana pun.

Di issue 38588, seorang maintainer nutup pertanyaan firewall-nya sebagai by design:

> "The firewall feature support is only for system services, and we have never supported that on user services."

Program BPF nggak bisa dipasang dalam keadaan unprivileged, tambahnya.

Balasan pelapornya yang paling gue setujui. Limit yang dibiarin diam-diam lebih bahaya daripada unit yang nolak jalan dari awal.

## Tiga knob yang beneran nempel

Di luar semua itu ada tiga knob yang beneran kerja di unit tanpa privilege. Gue ukur satu-satu:

- `NoNewPrivileges=yes` lapor `NoNewPrivs: 1` dengan `CapEff: 0000000000000000`
- `SystemCallFilter=@system-service` masang filter seccomp, dan `~@mount` bikin `mount` mati dengan `Bad system call (core dumped)`
- `RestrictAddressFamilies=AF_UNIX` bikin `curl` exit `6` tanpa HTTP code, jadi DNS dan connect dua-duanya gagal

Baris terakhir yang paling menarik. Itu satu-satunya tombol matiin network yang bisa dipasang unit tanpa privilege.

Masalahnya tombol itu matiin AF_INET, alias jalur API modelnya. Buat fleet agen, itu tombol yang nggak mungkin kita tekan.

## Yang bisa lo pasang hari ini

Ada tiga yang bisa lo kerjain sekarang:

- **Pindahin titik kontrol egress-nya keluar dari user manager.** Slice milik root yang bawa `IPAddressDeny=` plus `IPAddressAllow=` per service itu pola allow-list yang direkomendasiin man page. Proxy keluar yang wajib dilewatin fleet juga sama hasilnya.
- **Pasang carve-out AppArmor-nya biar direktif filesystem-nya punya kesempatan jalan.** Versi di laporan block cuma ngasih izin ke satu binary, bukan seluruh box. Isinya `/etc/apparmor.d/systemd-executor-userns` dengan `profile systemd-executor-userns /usr/lib/systemd/systemd-executor flags=(unconfined) { userns, }`, habis itu `apparmor_parser -r`.
- **Bikin sandbox-nya gagal tertutup.** Canary di `ExecStartPre=` ngecek path paling berbahaya, dan `exit 1` kalau ternyata masih bisa ditulis. Sandbox yang degradasi jadi nggak pernah ikut jalan.

Bentuk canary-nya begini:

```ini
ExecStartPre=/bin/sh -c 'if touch %h/.hermes/.sandbox-canary 2>/dev/null; then \
  rm -f %h/.hermes/.sandbox-canary; \
  echo "sandbox DEGRADED (secrets writable)" >&2; exit 1; fi'
```

Satu direktif muncul di `systemctl show` bukan berarti dia kepasang. Canary itu cara paling murah buat bedain dua keadaan itu.

## Containment doang nggak cukup, backup-nya juga harus diuji

Thread front page satunya minggu ini nunjukin kenapa backup masuk di kalimat yang sama. Di Swedia, satu rumah produksi harus nunda tayang satu acara setelah season yang udah diedit hilang.

Program director TV4 bilang ke Sveriges Radio nggak ada agen AI yang ngehapus materi itu. Yang gagal sistem backup-nya.

Konsensus di thread-nya lebih tajam dari headlinenya. User HN `jve` nulis lo nggak berhak nyalahin AI kalau dia ngehapus data lo secara permanen. Karena pilihan lo cuma dua, nggak punya backup sama sekali, atau nggak pernah ngekang agennya di tempat yang nggak bisa bikin kerusakan permanen.

`Ekaros` nebak akar masalahnya lebih masuk akal. Restore-nya kemungkinan besar nggak pernah dites.

Penghapusan baru jadi bencana kalau lapisan cadangan di bawahnya nggak ada yang pernah ngecek. Itu kelas kerusakan yang sama dengan sandbox yang gagal terbuka.

Dua-duanya kelihatan kayak kontrol, dan dua-duanya bukan.

## Posisi gue

Di fleet agen yang jalan tanpa privilege, direktif-direktif itu cuma bahasa konfigurasi. Bukan batas.

Cari tahu yang mana yang beneran nempel di host lo, dan uji pakai probe, bukan pakai `systemctl show`.

Di mesin gue hasilnya ternyata cuma dekorasi. Setidaknya gue tahu sebelum ada yang nemuin sendiri.
