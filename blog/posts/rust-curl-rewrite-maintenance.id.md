---
title: Maintenance Kode AI Lebih Berat daripada Rewrite curl ke Rust
slug: rust-curl-rewrite-maintenance
date: 2026-11-18
excerpt: Maintenance kode hasil AI jadi ujian sebenarnya untuk rewrite curl ke Rust. Build pertama yang lolos test belum membuktikan kompatibilitas, perbaikan bug, dan release bisa terus dijaga.
tags: rust, ai agents, software maintenance, open source
keywords: AI-generated code maintenance, Rust rewrite of curl, software rewrite risks, memory safety vs maintenance, agent-generated code review
---

Agent bisa menerjemahkan codebase C yang besar ke Rust lalu bikin test-nya hijau. Keren buat demo. Tapi itu belum cukup buat bilang project hasil rewrite siap menggantikan curl. Ujian sebenarnya justru maintenance kode hasil AI: setelah build pertama, apakah timnya sanggup menangani bug report, menjaga kompatibilitas, dan rutin merilis perbaikan?

Daniel Stenberg menulis tentang dua rewrite curl ke Rust pada 17 November. Gue pernah bikin side project dengan Rust, dan setelah 13 tahun ikut shipping software, gue melihat rewrite dari satu sudut: apakah project baru ini bisa ikut masuk ke siklus maintenance yang sudah berjalan? Pilihan bahasa tetap penting. Tapi kerja setelah implementasi awal biasanya jauh lebih menentukan.

## Yang ditunjukkan oleh rewrite curl

Stenberg menyebut dua project: `urlx` dan `kov/curl`. Project kedua mengklaim biaya sekitar $8.600. Itu klaim yang dikaitkan dengan project tersebut, bukan audit biaya independen. Jadi, angka itu jangan dipakai sebagai patokan ongkos rewrite.

Menurut Stenberg, agent menerjemahkan 185.000 baris C menjadi 340.000 baris Rust. Dalam rentang sekitar tiga minggu lebih yang sama, curl merge lebih dari 300 commit dan menyelesaikan sedikit di atas 200 bug fix. Angka-angka ini menggambarkan jenis kerja yang berbeda: membangun snapshot baru versus terus merawat software yang sudah dipakai banyak orang.

Hasil awal yang kelihatan meyakinkan gampang bikin kita lupa bedanya. Test suite yang lolos cuma membuktikan implementasi memenuhi test yang tersedia. Belum tentu semua kontrak kompatibilitas, platform, atau bug yang baru ditemukan sudah terwakili di sana.

## Kenapa maintenance kode hasil AI lebih susah diukur?

Project yang sudah lama dipakai punya tanggung jawab di luar source code. User mengandalkan perilaku tertentu, maintainer perlu menyelidiki laporan, dan release harus sampai ke platform yang dipakai orang. Rewrite baru baru mewarisi tanggung jawab itu kalau ada tim yang memang mengambil alih.

Gue nggak terlalu tertarik pada pertanyaan “berapa banyak code yang agent hasilkan?” Yang lebih penting: ada nggak proses yang bisa mengubah laporan masalah menjadi fix yang direview dan release yang bisa diandalkan? Proses itu perlu owner yang jelas. Tanpa owner, repo bisa tampak selesai sementara user sendiri yang harus menemukan batas-batasnya.

Aturan yang sama berlaku di multi-agent setup seperti fleet Hermes yang gue operasikan. Agent bisa menghasilkan perubahan dengan cepat. Tapi throughput tinggi nggak menggantikan test, review gate, triage issue, atau manusia yang bertanggung jawab atas hasil akhirnya. Check hijau hanya bukti bahwa satu check tertentu lolos, bukan garansi perilaku production sudah benar.

## Apakah rewrite Rust menghapus risiko keamanan curl?

Nggak. Memilih satu bahasa saja nggak menghilangkan semua jenis bug. Stenberg melaporkan ada 81 kerentanan curl yang terkonfirmasi pada 2026. Dari jumlah itu, 14 atau 17,3% kemungkinan terkait memory safety.

Menurut argumennya, rewrite ke Rust tidak otomatis menghapus 67 kerentanan lainnya.

Ini bukan alasan untuk menganggap Rust percuma. Type system dan ekosistem Rust bisa membantu developer membuat desain yang memory-safe, dan sebagian bug mungkin tidak akan muncul dengan bentuk yang sama setelah rewrite. Tapi ketepatan implementasi protokol, kompatibilitas, dan penanganan error tetap perlu dikerjakan dengan serius.

Bedakan manfaat memory safety dari pekerjaan maintenance; jangan jadikan diskusi ini perang C lawan Rust. Rewrite mungkin mengurangi risiko memory tertentu, tetapi juga bisa membawa celah kompatibilitas baru. Project itu pun bisa kehilangan proses security response yang berkelanjutan. Dampak-dampak ini perlu dinilai satu per satu.

## Source code bukan keseluruhan project

Dalam diskusi Hacker News, seorang commenter menyebut curl punya 1.306 kontributor dan 99 versi. Ia juga melaporkan sekitar 17.000 pull request yang ditutup serta 5.700 issue yang ditutup.

Itu angka dari commenter tersebut, bukan hasil audit independen dari gue. Meski begitu, laporan itu mengingatkan kita pada banyaknya kerja yang menumpuk di sekitar project lama.

Riwayat itu mencakup keputusan, laporan, fix, dan ekspektasi user. Semua itu nggak ikut pindah hanya karena file source diterjemahkan. Buat organisasi, pertanyaannya: sanggup nggak fungsi support itu dibangun kembali, bukan cuma menyalin output program saat ini? Buat Dagango.com, implementasi yang kompatibel dengan API tetap kurang berguna kalau nggak bisa mengikuti perilaku production dan kebutuhan support.

## Checklist untuk menilai rewrite buatan agent

Sebelum menganggap rewrite sebagai pengganti, gue bakal minta bukti untuk enam hal:

- **Kompatibilitas:** Ada test untuk perilaku dan protokol yang diandalkan user?
- **Bug lama:** Tim bisa mereproduksi dan mencegah bug penting dari project asal?
- **Jadwal release:** Siapa yang merilis update, dan seberapa cepat fix sampai ke user?
- **Dukungan platform:** OS, arsitektur, dan kombinasi dependency mana yang dirawat?
- **Owner keamanan:** Siapa menerima laporan vulnerability dan mengoordinasikan respons?
- **Paritas jangka panjang:** Ada rencana realistis buat mengikuti perubahan upstream dan menutup gap perilaku?

Demo bisa menjawab apakah agent mampu membuat implementasi awal yang besar. Checklist ini menjawab apakah tim sungguh berniat merawatnya. Dalam review, taruh batasnya dengan jelas: code hasil agent itu bahan kerja engineering, bukan pengganti tanggung jawab atas software.

## FAQ Teknis

### Apakah lolos test suite asli membuktikan rewrite kompatibel?
Belum. Itu hanya membuktikan implementasi lolos test yang dijalankan. Tim tetap perlu menguji perilaku yang benar-benar dipakai user, platform yang didukung, dan kasus yang muncul dari bug report berikutnya.

### Apa Rust mencegah semua vulnerability di project C?
Nggak. Rust bisa membantu mencegah bug memory safety, tetapi tidak otomatis menyelesaikan kesalahan protokol, regresi kompatibilitas, atau masalah di dependency dan proses respons operasional.

### Apa yang perlu ditanyakan sebelum memakai pengganti buatan agent?
Tanya siapa yang memegang release dan laporan keamanan. Pastikan juga ada cara menguji bug historis serta rencana menjaga kompatibilitas. Kalau owner dan prosesnya belum jelas, code itu belum jadi pengganti yang benar-benar didukung.
