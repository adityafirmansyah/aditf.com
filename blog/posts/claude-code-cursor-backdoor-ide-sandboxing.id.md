---
title: Backdoor Claude Code di Cursor: Kenapa Extension IDE Wajib Di-sandbox
slug: claude-code-cursor-backdoor-ide-sandboxing
date: 2026-10-31
excerpt: Proxy marketplace Cursor kebobolan selama 11 jam dan menyuntikkan backdoor reverse SSH ke Claude Code. Tool developer nggak boleh dibiarkan jalan tanpa sandbox di sebelah kredensial mesin lokal.
tags: security, ai-agents, developer-tooling, supply-chain
---

Banyak developer masih nganggep pasang extension di editor itu aman kayak download aplikasi di smartphone. Padahal kenyataannya ngeri: begitu lo klik install, extension bakal jalan sebagai proses Node.js biasa di bawah user akun lo sendiri tanpa perlindungan sandbox sama sekali.

Nah, tanggal 29 Oktober 2026 kemarin, ilusi rasa aman ini langsung bubar jalan.

Selama sebelas jam penuh, developer yang memasang atau memperbarui extension resmi Claude Code dari Anthropic di Cursor malah disusupi backdoor jahat. Implant tersebut nancepin public key penyerang ke file authorized keys laptop, lalu ngebuka jalur reverse Secure Shell (SSH) tunnel langsung ke server luar.

Intinya, ketika runtime extension dibiarin telanjang tanpa isolasi, proxy marketplace yang jebol bakal langsung nyeret seluruh workstation lo ke tangan hacker.

## Jendela Serangan Sebelas Jam

Insiden ini berlangsung antara pukul 02.27 sampai 13.35 PT pada 29 Oktober kemarin, dengan korban utama paket extension `Anthropic.claude-code` versi 2.1.312 dan 2.1.313.

Menariknya, server upstream milik Anthropic sama sekali nggak kena bobol. Begitu juga Microsoft Visual Studio Marketplace dan Open VSX resmi. Pelakunya justru menyusup lewat proxy caching Cursor di `marketplace.cursorapi.com`, yang bertugas menyimpan cache Open VSX sekaligus menyajikan paket custom editor mereka.

Penyerang berhasil menembus pipeline proxy ini dan menukar bundle file asli dengan versi modifikasi sebelum scanner otomatis Cursor sempat menyadarinya.

Perusahaan endpoint security Phorion langsung membongkar analisis teknisnya ke publik, memicu diskusi hangat di Hacker News (857 poin) dan Lobste.rs (149 poin). Dua security engineer Anthropic, David Dworken dan Felix Rieseberg, buru-buru klarifikasi di forum kalau sistem mereka bersih. Pihak Cursor langsung mematikan marketplace buat rotasi signing key dan take down server Command and Control (C2) penyerang, sebelum Anthropic merilis versi 2.1.314 yang bersih.

## Anatomi Payload: Dari IIFE Sampai Reverse SSH

Serangan ini berjalan sangat mulus karena penyerang sama sekali nggak butuh klik dari developer. Mereka menyelipkan teknik Immediately Invoked Function Expression (IIFE) persis di pucuk file `extension.js`.

```javascript
// IIFE diselipkan di baris pertama extension.js
(function() {
  const fs = require('fs');
  const { exec } = require('child_process');
  // Langsung jalan begitu file dibaca oleh Node
})();
```

Begitu Cursor me-load file ini ke memori, script langsung jalan sebelum lifecycle hook `activate()` sempat dipanggil. Diam-diam, tanpa popup.

Begitu payload aktif di background, kodenya langsung melancarkan aksi berikut:

- Nyari dan ngebaca sampai 40 environment variable lokal yang namanya mengandung kata sensitif seperti `AWS`, `GCP`, `KEY`, atau `SECRET`.
- Ngirim laporan data mesin seperti hostname, username, IP publik, dan email git lewat HTTP POST ke `134.209.82.225:8099/beacon` serta `127.0.0.1:8099/beacon`.
- Bikin folder `~/.ssh` kalau belum ada di laptop, lalu nyuntik public key Ed25519 dengan komentar `svc-telemetry` ke file `~/.ssh/authorized_keys` berizin 0600.
- Nembus keluar lewat reverse SSH tunnel (`-R *:0:localhost:22`) ke IP `134.209.82.225:22` pakai private key yang udah ditanam.

Terus, biar aksesnya nggak hilang pas laptop dimatikan, malware ini masang persistensi otomatis:

- Di Linux: nambahin cron job `@reboot ~/.config/.smt`.
- Di Windows: bikin scheduled task `SysMon` dan naruh script di folder Startup.
- Di macOS: bikin file LaunchAgent di `~/Library/LaunchAgents/com.apple.sysmond.plist`.

Ada cerita konyol di balik malware ini. Khusus di macOS non-root, serangannya sempat mandek gara-gara bug logika di script penyerang.

Mereka ngecek status SSH pakai command `systemsetup -getremotelogin` yang butuh akses root. Karena gagal dengan error permission tapi exit code-nya tetap 0, script penyerang malah batal ngejalanin perintah buat ngaktifin remote login SSH.

Tapi ya jangan senang dulu. Soalnya data credential cloud dan identitas laptop lo tetap aja udah keburu disetor ke server mereka.

## Masalah Arsitektur: Runtime Tanpa Isolasi

Akar penyakit sesungguhnya melampaui insiden proxy Cursor. Lubang terbesarnya ada di model eksekusi IDE modern zaman sekarang.

Selama dua puluh tahun terakhir, browser internet udah mati-matian ngebangun tab sandbox dan capability security. Sistem operasi smartphone juga ngurung setiap aplikasi di ruang isolasi masing-masing.

Anehnya, VS Code dan kawan-kawannya malah santai-santai aja. Di editor berbasis Node.js ini, extension yang lo pasang bakal jalan dengan privilege penuh User Identifier (UID) akun lo.

```
+---------------------------------------------------------------+
| Workstation Developer (UID 1000)                              |
|                                                               |
|   +-------------------+       +---------------------------+   |
|   | Extension IDE     | ----> | Akses ~/.ssh/id_ed25519   |   |
|   | Tanpa Sandbox     | ----> | Sedot ~/.aws/credentials  |   |
|   | (Node.js runtime) | ----> | Intip env var & shell     |   |
|   +-------------------+       +---------------------------+   |
+---------------------------------------------------------------+
```

Extension tema atau linter yang lo install bisa dengan bebas ngebaca private key SSH, ngintip history bash, atau nge-clone repo private kantor lo tanpa perlu izin sama sekali.

Cursor sempat percaya diri mengandalkan scanner otomatis di proxy mereka. Tapi ya percuma.

Scanner statis nggak bakal pernah cukup buat ngelindungin runtime yang dari sananya telanjang bulat. Begitu kodenya lolos masuk ke mesin lokal, tamat riwayat workstation lo.

## Cara Kita Membatasi Ruang Gerak AI Agent di Produksi

Di setup gue sendiri, baik waktu nanganin sistem di GOSG Consulting maupun operasional harian Dagango.com, armada AI agent jalan tiap jam. Kita pakai tool mulai dari Claude Code sampai Hermes buat ngebantu coding otomatis.

Dari awal, prinsip gue nggak pernah berubah: semua tool AI wajib diperlakukan sebagai kode asing yang nggak boleh dipercaya. Jangan pernah ngasih mereka akses langsung ke mesin utama yang nyimpen kunci produksi.

Buat mencegah insiden serupa, kita memasang empat lapis pertahanan:

- **Kunci koneksi outbound lewat firewall.** Kita blokir semua traffic keluar yang mencurigakan dari lingkungan kerja agent, termasuk port 22 buat cegah reverse SSH tunnel.
- **Batasi socket SSH lokal.** Pantang buat kita nge-mount atau forwarding `SSH_AUTH_SOCK` dari host ke dalam container agent.
- **Pakai kredensial berumur pendek.** Kita nggak pernah naruh static API key jangka panjang; semua token dibikin ephemeral dengan scope yang sangat sempit.
- **Kurung proses di namespace terisolasi.** Semua agent wajib jalan di Linux container unprivileged atau Virtual Machine (VM) sementara yang terpisah total dari filesystem laptop.

Aturan `iptables` berikut biasa kita pasang buat nahan tunnel liar dari worker container:

```bash
# Buang koneksi SSH keluar dari user proses worker agent
iptables -A OUTPUT -p tcp --dport 22 -m owner --uid-owner agent-worker -j DROP
```

Dengan aturan ini, andai ada extension yang nekat buka reverse tunnel, paketnya langsung mental di level kernel. Koneksinya mati sebelum sempat nyentuh server C2 penyerang.

## Sandbox Itu Bukan Pilihan Tambahan

Tim Cursor memang cepat beres-beres. Anthropic juga langsung ngerilis patch bersih hari itu juga.

Tapi kalau lo cuma nganggep insiden ini sebagai apesnya Cursor doang, lo salah besar.

Besok-besok celahnya bisa datang dari mana saja: supply chain npm yang keracunan, akun developer di marketplace yang dibajak, atau extension populer yang dijual ke pihak ketiga.

Intinya, selama editor belum nerapin capability-based security, kita sebagai engineer harus jaga diri sendiri.

Mulai sekarang, kurung tool AI lo di container, pisahkan private key kantor lo, dan jangan pernah biarin extension apa pun jalan bebas tanpa sandbox di laptop lo.
