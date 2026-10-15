---
title: Sandbox Agen yang Gagal Terbuka: systemd --user Diam-diam Nggak Ngekang Apa-apa
slug: systemd-user-sandbox-fails-open
date: 2026-10-15
excerpt: Pasang ProtectHome=yes, ProtectSystem=strict, dan IPAddressDeny=any di unit systemd --user, terus systemctl show bilang semuanya aktif. Di Ubuntu modern, semuanya gagal terbuka dan nggak ngekang apa-apa.
tags: systemd, agent-safety, sandboxing, apparmor, self-hosting
---

## Sandbox yang disuruh lo pasang

Kalau lo jalanin coding agent otonom, atau daemon apa pun yang jalan tanpa privilege, lewat unit `systemd --user`, saran hardening standarnya selalu sama. Containment.

Set `ProtectHome=yes` sama `ProtectSystem=strict` biar prosesnya nggak bisa baca kunci lo. Tambahin `IPAddressDeny=any` biar dia nggak bisa ngirim kunci itu ke luar. Habis itu `systemctl --user show` bakal lapor semua direktif itu aktif.

Di host Ubuntu modern, nggak ada satu pun yang jalan.

Gue nemu ini dengan cara yang jujur. Gue jalanin delapan belas profil agen di belakang satu `hermes-gateway.service` yang multiplex. Gue coba pasang sandbox-nya, terus gue ukur apa yang beneran nempel.

Hasilnya: tiap direktif filesystem dan egress yang bisa diset unit tanpa privilege diterima, dipajang `systemctl show` seolah kepasang, dan diam-diam nggak ngapa-ngapain.

## Isi unit yang jalanin fleet gue

Begini bentuknya di unit gateway gue:

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

Nggak ada yang aneh di situ. Itu cuma bentuk default dari fleet yang tumbuh satu worker setiap kali. Anggap aja tiap agen yang keluar jalur udah punya akses ke keempat file itu.

## Gue uji satu-satu, dan hasilnya nol

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

## Kenapa dia ngalah diam-diam, bukan error

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

Program BPF nggak bisa dipasang dalam keadaan unprivileged, tambahnya. Buat operator fleet, asimetri inilah masalahnya. Unit yang nolak jalan itu bug report sepele yang beres dalam sejam. Batas yang diabaikan diam-diam itu keyakinan yang lo pelihara sampai ada yang bikin lo salah.

## Tiga knob yang beneran nempel

Di luar semua itu ada tiga knob yang beneran kerja di unit tanpa privilege. Gue ukur satu-satu:

- `NoNewPrivileges=yes` lapor `NoNewPrivs: 1` dengan `CapEff: 0000000000000000`
- `SystemCallFilter=@system-service` masang filter seccomp, dan `~@mount` bikin `mount` mati dengan `Bad system call (core dumped)`
- `RestrictAddressFamilies=AF_UNIX` bikin `curl` exit `6` tanpa HTTP code, jadi DNS dan connect dua-duanya gagal

Baris terakhir yang paling menarik. Itu satu-satunya tombol matiin network yang bisa dipasang unit tanpa privilege.

Masalahnya tombol itu matiin AF_INET, alias jalur API modelnya. Buat fleet agen, itu tombol yang nggak mungkin kita tekan.

## Yang bisa lo pasang hari ini

Ada tiga perubahan, gue urutin dari yang paling besar efeknya:

- **Pindahin titik kontrol egress-nya keluar dari user manager.** Slice milik root yang bawa `IPAddressDeny=` plus `IPAddressAllow=` per service itu pola allow-list yang direkomendasiin man page. Proxy keluar yang wajib dilewatin fleet juga sama hasilnya.
- **Pasang carve-out AppArmor-nya biar direktif filesystem-nya punya kesempatan jalan.** Ubuntu sendiri udah pakai pola ini buat Chrome dan bwrap. Carve-out-nya ngasih izin ke satu binary, bukan seluruh box: `/etc/apparmor.d/systemd-executor-userns` dengan isi `profile systemd-executor-userns /usr/lib/systemd/systemd-executor flags=(unconfined) { userns, }`, habis itu `apparmor_parser -r`.
- **Bikin sandbox-nya gagal tertutup.** Canary di `ExecStartPre=` ngecek path paling berbahaya, dan `exit 1` kalau ternyata masih bisa ditulis. Sandbox yang degradasi jadi nggak pernah ikut jalan.

Bentuk canary-nya begini:

```ini
ExecStartPre=/bin/sh -c 'if touch %h/.hermes/.sandbox-canary 2>/dev/null; then \
  rm -f %h/.hermes/.sandbox-canary; \
  echo "sandbox DEGRADED (secrets writable)" >&2; exit 1; fi'
```

Satu direktif muncul di `systemctl show` bukan berarti dia kepasang. Canary itu cara paling murah buat bedain dua keadaan itu.

## Uji dulu sebelum lo percaya

Di fleet agen yang jalan tanpa privilege, direktif containment itu cuma bahasa konfigurasi, bukan batas. Nggak masalah, asal lo tahu mana yang mana.

Jadi uji aja. Spawn satu transient unit pakai properti yang lo yakini lagi ngelindungin lo, terus coba lakuin hal yang seharusnya dicegah.

Punya gue ternyata cuma dekorasi. Gue lebih milih tahu itu dari canary daripada dari laporan insiden.
