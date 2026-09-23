---
title: Self-Hosting di Belakang CGNAT Pakai Bridge WireGuard
slug: self-hosting-behind-cgnat-wireguard-bridge
date: 2026-09-23
excerpt: Port forwarding tiba-tiba nggak jalan, dan itu bukan salah router lo. Ini pola tunnel WireGuard outbound yang bikin homelab bisa diakses publik lagi meski kena CGNAT.
tags: self-hosting, homelab, networking, wireguard, cgnat
---

Port forwarding tiba-tiba nggak jalan, dan itu bukan salah router lo. Masalahnya ada di ISP: mereka diam-diam naruh koneksi lo di belakang lapisan NAT kedua yang nggak kelihatan dan nggak bisa diapa-apain dari sisi lo. Namanya CGNAT, dan kalau lo pakai fiber residensial di Indonesia, kemungkinan besar lo udah kena ini tanpa sadar itu yang bikin homelab lo nggak bisa diakses dari luar.

Tulisan David Álvarez Rosa soal topik ini sempat nangkring di posisi #1 lobste.rs minggu ini, terus rame juga di HN. Wajar, soalnya masalahnya struktural: stok IPv4 makin menipis, jadi makin banyak ISP yang pindah ke CGNAT buat ngirit alamat. Gue sendiri ngerasain ini langsung, jalanin box Celeron J4105 di Biznet fiber, dan CGNAT itu bukan hal langka di ISP residensial Indonesia.

## Kenapa Router Lo Nggak Bisa Nolongin

Port forwarding di router lo sekarang percuma, titik. Alasannya: CGNAT nambahin satu NAT lagi di infrastruktur ISP, jauh sebelum traffic apapun sempat nyampe ke router lo. Router lo emang masih punya "alamat WAN", tapi itu cuma alamat private yang dishare rame-rame sama satu kompleks pelanggan lain. Traffic dari luar nggak pernah mampir ke router lo buat dicek aturan port forwarding-nya, jadi ngoprek settingan router selama berjam-jam pun nggak bakal ngefek. Yang perlu dibenerin ada di luar jaringan rumah lo, bukan di dalam, dan itu nggak ada tombolnya di admin panel router manapun.

## Balik Arah: Tunnel Keluar, Bukan Nunggu Masuk

Kuncinya justru berhenti nunggu koneksi masuk. Homelab lo yang harus mulai duluan, bikin tunnel WireGuard ke luar menuju VPS murah yang punya IP publik beneran. CGNAT cuma ngeblokir yang arahnya masuk, jadi begitu ada tunnel yang dibuka dari dalam, semua traffic bisa numpang lewat jalur itu tanpa nabrak pemblokiran sama sekali.

Begitu tunnel-nya jalan, VPS-nya berperan neruskan traffic yang dia terima balik ke homelab lewat DNAT di iptables. Enaknya DNAT, dia cuma ganti alamat tujuan doang, alamat pengirim aslinya tetep utuh, jadi log di homelab lo tetep nunjukin IP client yang beneran, bukan cuma IP si VPS berulang-ulang. Detail kecil ini gunanya baru kerasa kalau lo pernah butuh rate limiting, geo-blocking, atau nge-track abuse berdasarkan IP. Soal performa, latensi tambahan gara-gara lewat bridge kayak gini cuma sekitar 39ms round-trip menurut pengukuran di tulisan aslinya, angka yang kecil banget buat kebanyakan service self-hosted walaupun game server mungkin bakal ngerasainnya.

```
# Kecualiin dulu port WireGuard dan SSH-nya VPS dari DNAT
iptables -t nat -A PREROUTING -i ens3 -p udp --dport 51820 -j RETURN
iptables -t nat -A PREROUTING -i ens3 -p tcp --dport 2222 -j RETURN

# Baru semua sisanya diteruskan ke homelab lewat tunnel
iptables -t nat -A PREROUTING -i ens3 -j DNAT --to-destination 10.0.0.2

# Izinin traffic yang udah diteruskan lewat dua arah
iptables -A FORWARD -i wg0 -o ens3 -s 10.0.0.2 -j ACCEPT
iptables -A FORWARD -i ens3 -o wg0 -d 10.0.0.2 -j ACCEPT
```

Dua rule RETURN di atas itu bukan sekadar formalitas, karena kalau lo skip, rule DNAT catch-all-nya bakal ikutan nelen handshake WireGuard sama sesi SSH lo sendiri ke VPS itu, dan ujung-ujungnya lo malah kekunci keluar dari box yang lagi lo setup sendiri. Makanya kebiasaan amannya, pindahin dulu SSH VPS ke port nggak standar kayak 2222 sebelum sentuh iptables sama sekali, biar port 22 tetap khusus buat homelab.

## Detail Routing yang Sering Bikin Orang Gagal di Percobaan Pertama

Nah, ini yang sering bikin orang mentok. Kalau tunnel-nya udah nyala tapi balasan dari homelab masih nyasar keluar lewat koneksi rumah biasa, bukan balik lewat tunnel, ya jelas nggak nyambung. Client bakal nerima balasan dari IP yang beda sama yang dia hubungin, terus koneksinya nge-hang gitu aja tanpa ada error yang jelas.

Cara benerinnya kombinasi dua hal: `Table = off` di config WireGuard homelab biar dia nggak masang default route sendiri, plus satu routing table terpisah (table 200 di tulisan aslinya) yang khusus nanganin traffic dari service yang diekspos lewat tunnel. Aktivitas lain di box itu, sesi SSH biasa, update apt, dan lain-lain, tetep jalan normal lewat koneksi rumah kayak biasa, nggak kena rule ini. Tambahin `PersistentKeepalive = 25` biar mapping NAT-nya CGNAT nggak keburu expired gara-gara dianggap idle.

## Itung-Itungan: Worth It Nggak Sih

Di Spanyol, IP statis dari ISP-nya si penulis kena sekitar €20 sebulan. Bandingin sama VPS yang punya IP publik dan bandwidth cukup buat bridge, harganya cuma secuil dari itu, sering di bawah $5. Di Indonesia polanya mirip: paket IP statis bisnis dari ISP residensial biasanya lebih mahal per bulan dibanding VPS basic, dan itu biaya yang lo bayar terus-terusan cuma buat ngebalikin sesuatu yang dirusak CGNAT secara cuma-cuma. Cek dulu angka pastinya di ISP masing-masing, tapi buat kebanyakan homelabber di sini, bridge udah menang duluan dari sisi harga, belum dihitung enaknya punya box Linux beneran yang bisa diutak-atik di tengah jalur traffic sendiri.

Soal ketahanan sistemnya, ada tiga titik yang bisa bikin semuanya berhenti kerja: homelab-nya sendiri mati, VPS bridge-nya down, atau tunnel-nya putus, tapi untungnya ketiganya punya solusi murah sekaligus: cron job yang rutin ngecek SSH homelab dan reboot otomatis kalau nggak jawab, satu jalur masuk cadangan kayak Tailscale atau Cloudflare Tunnel langsung ke homelab yang nggak gantung ke hidup-matinya bridge, dan WireGuard yang emang udah didesain buat re-handshake sendiri kalau putusnya cuma sebentar.

## Kapan Lo Nggak Perlu Ribet-Ribet Pakai Bridge

Kalau kebutuhan lo cuma akses pribadi ke service sendiri dari device sendiri, Tailscale udah lebih dari cukup, gratis buat pemakaian personal, dan nggak perlu VPS sama sekali karena sifatnya private mesh, bukan buat diekspos ke publik. Kalau lo cuma mau ekspos web app lewat HTTP atau HTTPS, Cloudflare Tunnel juga gratis, nggak perlu VPS, nggak perlu ngoprek iptables. Ada juga Pangolin, alternatif open-source yang belakangan dapet 500 poin di HN, cocok kalau lo suka kemudahan Cloudflare Tunnel tapi nggak mau semua traffic lo lewat infrastruktur mereka.

Bridge WireGuard baru kepake kalau kebutuhan lo spesifik: port TCP sembarang yang harus bisa diakses dari internet publik meski kena CGNAT, semacam game server, protokol yang bukan HTTP, atau service yang emang butuh client ngeliat IP publik asli. Di luar kebutuhan itu, mendingan pakai yang lebih simpel aja. Kalau memang butuh, total waktu setup-nya paling sejam kalau iptables-nya udah bener, dan biaya VPS-nya lebih murah dari sekali makan siang.
