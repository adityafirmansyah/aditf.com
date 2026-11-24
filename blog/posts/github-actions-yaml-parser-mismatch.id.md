---
title: "GitHub Actions YAML Parser: Kenapa Runner dan Linter Beda Membaca Workflow"
slug: github-actions-yaml-parser-mismatch
date: 2026-11-24
excerpt: GitHub Actions YAML parser bisa membuat scanner gagal membaca workflow yang tetap dijalankan runner. Gue lebih percaya CI yang melaporkan audit gagal daripada check hijau tanpa analisis.
tags: ci, github-actions, yaml, application-security, ai-agents
keywords: GitHub Actions YAML parser, GitHub Actions security scanning, zizmor workflow audit, CI pipeline validation, pull_request_target security
---

Workflow yang jalan di GitHub belum tentu bisa dibaca tool yang harus mengauditnya. Buat gue, perbedaan GitHub Actions YAML parser dengan linter ketat bukan debat soal spasi. Ini celah di kontrak CI: kode yang dieksekusi runner harus bisa diperiksa scanner juga.

Apalagi kalau agent ikut bikin atau mengubah workflow. Check hijau belum berarti aman kalau scanner bahkan belum membaca file yang sama.

## Kenapa GitHub Actions YAML parser menerima file yang ditolak linter?

Laporan yossarian.net pada 22 November membahas reproducer dengan selisih indentasi satu spasi. Di YAML 1.2.2 §8.2.3, flow node yang berada di dalam block collection harus menjorok lebih jauh daripada parent-nya. Nilai multiline berpetik tunggal di contoh itu meleset dari syarat tersebut.

GitHub Actions tetap menerima workflow itu, sementara parser ketat yang dipakai zizmor menolaknya. Artinya runner bisa mengeksekusi file yang gagal dibaca analyzer. Garis merah editor bukan pokok masalahnya; celahnya ada saat dua tool memberi status berbeda untuk input yang sama.

Kalau workflow repo sering dihasilkan atau diedit agent, dampaknya lebih terasa. Job bernama “security” bisa selesai hijau walau sebagian file belum dianalisis. Catat dulu workflow mana yang seharusnya diperiksa, lalu cocokkan dengan daftar input scanner.

Ini juga berlaku saat kita mengubah konfigurasi linter. Jangan cuma cek apakah job selesai; lihat apakah file yang relevan masuk ke analisis dan hasilnya tercatat.

## Parse error berarti audit belum punya hasil

Issue zizmor #1116 bermula sebagai kegagalan parser atau tooling. Dalam investigasi yang dijelaskan penulis, masalahnya mengarah ke parser GitHub yang menerima sintaks di luar aturan YAML, bukan bukti bahwa semua scanner mesti permisif terhadap YAML invalid.

Nah, pilihan fix-nya perlu hati-hati. Melonggarkan grammar bisa bikin analyzer menerima input tanpa memastikan maknanya sama dengan yang dipakai GitHub. Kalau parse error cuma jadi catatan informasi, workflow bisa di-merge padahal audit keamanannya belum terjadi.

Di workflow agent kita, “check selesai” beda dengan “check lolos”. Job yang mencetak parse error lalu exit sukses bukan gate keamanan. Kalau workflow wajib gagal diparse atau pemeriksaannya dilewati, pipeline harus merah.

## Status CI harus jujur soal audit

Tampilkan kondisi pemeriksaan di konfigurasi check dan status pull request. Kita perlu membedakan tiga hasil:

- **Sudah dianalisis:** file workflow yang diharapkan terbaca dan policy check selesai.
- **Ditolak:** parser atau sintaks menghalangi audit, jadi perubahan belum boleh merge.
- **Tidak relevan:** tak ada workflow terkait yang berubah dan alasannya tercatat.

Jangan satukan “ditolak” dengan “warning” atau “no findings”. Yang pertama berarti belum ada hasil yang bisa dipercaya. “No findings” baru pantas muncul setelah analisis selesai.

Terus, di setiap pull request simpan ringkasan file yang diperiksa dan versi analyzer. Reviewer jadi bisa membedakan perubahan workflow dari perubahan perilaku tool, bukan menebak-nebak lewat checkmark hijau.

## Jangan merge sebelum status audit jelas

Jadikan hasil audit sebagai required check di branch protection. Bukan sekadar job yang nongol di log. Reviewer perlu melihat semua workflow yang berubah ikut dianalisis, dan scanner mesti menyebut file yang dilewati beserta alasannya.

Pin versi parser dan security tool di konfigurasi repo. Waktu dependency diperbarui, jalankan ulang fixture yang ada dan bandingkan hasilnya sebelum mengganti policy. Kalau interpretasi berubah, review sebagai perubahan security, bukan housekeeping rutin.

## Reproducer kecil lebih berguna daripada fix tebakan

Simpan contoh minimal dari mismatch satu spasi itu, lengkap dengan nilai multiline berpetik tunggal dan nested flow node. Sebelum linter, parser, atau grammar diubah, jalankan semua tool terhadap fixture yang sama.

Fixture-nya perlu mencatat ekspektasi setiap consumer. Tujuannya bukan cuma membuktikan satu parser bisa menerima file. Kalau parser atau aturan kompatibilitas zizmor berubah, test perlu menunjukkan apakah tool mengikuti perilaku GitHub, menolak input sesuai policy, atau masih menemukan mismatch yang belum beres.

Kalau agent ikut mengubah workflow, taruh fixture di test repo dan minta agent menjaga perilaku runner-versus-analyzer yang sudah disepakati. Syntax check yang lolos belum menjamin security tooling bisa membaca hasil generate-nya.

## Proteksi trigger menangani risiko lain

GitHub mengumumkan default baru untuk 2 Desember: `pull_request_target` diblokir secara default di repository publik. Perubahan ini membatasi risiko dari trigger itu, tapi tidak memperbaiki parser mismatch.

Makanya, review izin trigger dan status audit sebagai dua kontrol terpisah. Pipeline tetap harus gagal kalau analisis workflow nggak selesai. Default baru mengurangi satu paparan; ia nggak membuktikan scanner sudah memeriksa file.

## Gate workflow buatan agent: syarat sebelum merge

Perubahan workflow belum siap cuma karena satu job hijau. Pastikan perilaku runner dipahami dan scanner menuntaskan audit. Untuk setiap parser mismatch, simpan fixture dan keputusan policy yang bisa dicek reviewer.

Gue juga akan pin versi parser dan security tool, lalu jalankan fixture lagi setiap kali dependency berganti. Kalau hasil interpretasinya berubah, perlakukan itu sebagai perubahan security. Langkah ini memberi tim jejak yang jelas saat cara audit membaca workflow ikut berubah.

Makanya, tentukan dulu kapan audit memang nggak relevan. Perubahan dokumentasi saja mungkin nggak perlu memicu pemeriksaan workflow. Tapi kalau scanner luput membaca file gara-gara path filter keliru, itu bukan pengecualian yang aman. Catat alasan skip di status check supaya reviewer bisa membedakannya.

## FAQ Teknis

### Haruskah scanner menerima YAML yang diterima GitHub tapi ditolak spesifikasi YAML?
Nggak otomatis. Scanner perlu menyatakan dan menguji kompatibilitasnya dengan GitHub. Kalau file ditolak, required audit harus gagal dengan jelas, bukan memberi kesan pemeriksaan bersih.

### Apa job CI hijau membuktikan workflow sudah diaudit?
Cuma kalau job itu gagal ketika parsing atau analisis dilewati. Cek exit status dan aturan branch protection. Job yang menganggap parse error sebagai pesan informasi belum membuktikan audit berjalan.

### Apakah default `pull_request_target` pada 2 Desember menyelesaikan parser mismatch?
Nggak. Itu safeguard trigger untuk repository publik. Perubahan tersebut nggak membuat parser ketat menerima workflow atau membuktikan scanner menyelesaikan analisisnya.
