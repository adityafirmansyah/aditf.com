---
title: Keamanan SSH AI Coding Agent Butuh Batas Identitas
slug: ai-agent-ssh-identity-boundary
date: 2026-11-25
excerpt: AI coding agent SSH security bukan cuma soal menyimpan private key dengan aman. Pisahkan identitas agent dari akun lo, lalu batasi akses repo dan credential sesuai kebutuhan.
tags: ai-agents, ssh, security, linux, developer-tools
keywords: AI coding agent SSH security, SSH agent key constraints, least privilege for coding agents, separate Linux user for AI agents, short-lived SSH certificates
---

Gue bisa menghapus semua file private key Secure Shell (SSH) dari disk, tapi coding agent berbasis kecerdasan buatan (AI) tetap bisa bertindak memakai identitas gue. Jadi, AI coding agent SSH security bukan berhenti di pertanyaan “key-nya disimpan di mana?” Yang lebih menentukan: proses agent jalan sebagai siapa, dan hak akses apa yang dia pegang?

Diskusi Hacker News tentang post Larsson sampai 163 points dan 107 komentar bertingkat saat dicek pada 25 November. Banyak perhatian tertuju ke risiko agent yang jalan sebagai developer lalu mewarisi akses developer itu. Itu juga titik awal gue: jangan samakan key yang aman disimpan dengan proses yang aman dijalankan.

Kalau agent berjalan sebagai user harian gue, dia bisa punya jalur ke file, token, atau SSH agent yang sama. Key nggak perlu disalin dulu supaya aksesnya bisa dipakai.

## AI coding agent SSH security perlu memisahkan identitas

Di post 23 November berjudul “You Can’t Afford SSH Keys on Disk,” Johanna Larsson cerita pindah memakai SSH agent dari Bitwarden dan menghapus salinan key lokal. Interval approval-nya disamakan dengan vault yang terkunci setelah empat jam. Pilihan itu mengurangi key yang tersimpan di disk. Batas akses prosesnya tetap perlu dirancang terpisah.

SSH agent menyimpan key dan menyediakan operasi signing atau autentikasi untuk client. Kalau sebuah proses bisa mengakses socket agent, proses itu mungkin bisa meminta autentikasi, bergantung pada konfigurasi dan approval yang aktif. Jadi, mencegah pencurian file key belum tentu mencegah pemakaian key yang sedang tersedia.

Request for Comments (RFC) 9987 menjelaskan batas ini. Tujuan desain protokol SSH agent ialah mencegah penyerang tanpa hak istimewa mengambil salinan key yang sudah di-load. RFC yang sama mengingatkan bahwa pemakaian key tetap bisa dicuri kalau key tersedia tanpa konfirmasi.

Bedanya praktis: satu skenario mengambil rahasia, satu lagi meminta autentikasi lewat agent yang masih bisa diakses. Kalau agent lo jalan sebagai user biasa, anggap dia bisa menggunakan hak akses user itu sampai ada kontrol yang sudah lo uji. Instruksi prompt supaya agent “hati-hati” bukan pembatas di level sistem operasi.

## Kontrol apa yang diberikan SSH agent key constraints?

Manual `ssh-add` OpenSSH mencatat beberapa opsi untuk membatasi penggunaan key. Tiga kontrol yang relevan:

- **Lifetime** mengeluarkan key dari agent setelah waktu tertentu.
- **Confirmation** meminta persetujuan saat ada permintaan autentikasi.
- **Destination constraints** membatasi tujuan yang boleh memakai key.

Kontrol itu mempersempit jalur autentikasi. Tapi cakupannya bukan sandbox untuk seluruh proses. Opsi tersebut nggak otomatis membatasi direktori yang bisa dibaca agent, akses ke credential Git, atau file di luar project yang bisa dia ubah.

Thread Hacker News untuk post Larsson tercatat punya 163 points dan 107 komentar bertingkat saat dicek pada 25 November. Salah satu kekhawatiran yang muncul: agent yang jalan sebagai developer bisa mewarisi akses developer itu. Sejumlah komentar menyarankan akun user terpisah dengan permission minimum, yang juga membantu membedakan aksi agent dari aksi manusia.

## Terapkan least privilege untuk coding agents di Linux

Di tim yang menjalankan banyak agent Linux seperti fleet Hermes yang gue operasikan, gue pisahkan dua pertanyaan: agent berjalan dengan identitas OS apa, dan repo mana yang boleh dia tulis? Saat mereview batasnya, cek user yang menjalankan proses lalu tes akses tulis akun itu ke tiap repo yang dibutuhkan. Ini rekomendasi desain, bukan klaim bahwa semua permission di fleet gue sudah diukur atau seragam.

Agent yang cuma mengubah satu repo nggak perlu otomatis membaca semua direktori home atau memakai seluruh credential developer.

Checklist awalnya:

- **Identitas service terpisah.** Jalankan agent memakai akun OS sendiri, bukan akun interaktif lo.
- **Akses repo secukupnya.** Batasi ke working tree atau repository yang memang perlu disentuh.
- **Token dengan scope sempit.** Jangan berikan credential yang nggak dibutuhkan tugasnya.
- **Hindari forwarding yang nggak perlu.** Jangan buka akses SSH agent ke host atau proses lain tanpa alasan.
- **Log yang bisa diaudit.** Bedakan aktivitas agent dari perubahan yang dilakukan manusia.

Ini rekomendasi desain, bukan klaim bahwa satu konfigurasi fleet tertentu sudah diuji dengan benchmark. Batasnya baru berarti kalau bisa diperiksa. Cek file apa yang bisa dibaca akun service, repo mana yang bisa ditulis, dan apakah agent bisa menjangkau socket SSH pribadi lo. Kalau ada akses yang nggak bisa dijelaskan oleh kebutuhan tugasnya, cabut dulu sebelum agent dipakai untuk kerja rutin.

Setelah itu, pilih credential sesuai risiko dan kemampuan infra. Untuk tugas lokal berisiko rendah, passphrase dengan `ssh-agent` yang punya batas waktu bisa cukup. Tambahkan confirmation atau destination constraints kalau approval tambahan dan pembatasan tujuan sepadan dengan friksinya. Hardware-backed key atau short-lived SSH certificate masuk akal kalau infrastruktur mendukungnya dan biaya operasionalnya bisa diterima.

Credential berumur pendek juga bukan tombol ajaib. Masa berlaku yang pendek mengecilkan jendela pemakaian, tapi agent yang berwenang tetap bisa bertindak selama credential itu aktif. Scope dan identitas tetap harus dibatasi.

## Bikin batas akses yang bisa diuji dulu

Isolasi menambah pekerjaan setup. Akun terpisah butuh pengaturan permission repo, cara menyediakan credential, dan alur review perubahan. Kalau batasnya terlalu merepotkan untuk dirawat, orang akan mencari jalan pintas.

Gue akan mulai dari satu perubahan yang gampang diverifikasi: jalankan agent dengan user khusus, lalu tes akses file dan credential-nya sebelum workflow diperluas. Setelah itu, pasang key constraints atau credential berumur pendek kalau threat model memang membutuhkannya. Jangan biarkan akun manusia masuk ke environment agent kecuali ada kemampuan tertentu yang memang harus diberikan.

Dengan begitu, tim punya titik awal yang bisa diaudit. Pengecualian akses juga terlihat jelas, bukan berubah jadi izin tak terbatas hanya karena kalimat “agent butuh akses.” Sebelum dipakai rutin, jalankan satu task percobaan lalu periksa log dan perubahan file-nya. Kalau agent menyentuh sesuatu di luar repo yang disetujui, batasnya belum benar.

## FAQ Teknis

### Kalau private key dihapus dari disk, apakah agent masih bisa autentikasi sebagai gue?
Bisa. Menghapus file key mengurangi risiko key dicuri langsung dari disk. Tapi proses yang bisa mengakses SSH agent mungkin tetap meminta operasi autentikasi. Confirmation dan destination constraints bisa mempersempit jalurnya.

### Apakah SSH agent key constraints mengisolasi coding agent?
Nggak. Batas itu mengatur penggunaan key, misalnya masa berlaku, persetujuan, atau tujuan. Permission sistem operasi dan scope repository tetap dibutuhkan untuk membatasi akses proses lainnya.

### Kapan short-lived SSH certificate berguna?
Pakai kalau infra lo bisa menerbitkan dan memvalidasinya, serta masa berlaku pendek memang membantu threat model. Identitas agent dan hak aksesnya tetap perlu dipisahkan.