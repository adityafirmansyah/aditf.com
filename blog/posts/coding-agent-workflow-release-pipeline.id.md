---
title: Coding Agent Workflow: Prompt Bagus Nggak Bisa Gantikan Pipeline Rilis
slug: coding-agent-workflow-release-pipeline
date: 2026-11-17
excerpt: Coding agent workflow yang bisa dipercaya harus menjalankan test dan menyimpan buktinya, dengan human approval di batas risiko yang nyata. Prompt membantu, tapi nggak membuktikan rilis aman.
tags: ai-agents, software-delivery, code-review, testing, self-hosting
keywords: coding agent workflow, AI coding agent human approval, repeatable software delivery, agent testing and code review, self-hosted coding agents
---

Pada 17 November, LoopForge dari Tencent masuk peringkat #3 di snapshot GitHub Trending untuk proyek artificial intelligence (AI), dengan tambahan 1.020 stars hari itu. GitHub Trending menyebutnya workflow self-hosted untuk delivery coding agent. Buat gue, angka itu sinyal minat, bukan sertifikat siap production.

Soalnya, agent yang bilang “test passed” belum membuktikan apa-apa kalau kita nggak tahu command yang jalan dan hasilnya. Coding agent workflow yang dipakai buat delivery harus mengatur proses verifikasi, bukan cuma mengandalkan rasa percaya diri model.

## Kenapa coding agent workflow perlu gate rilis yang deterministik?

Repo LoopForge menjelaskan workflow berbasis node Standard Operating Procedure (SOP), agent executor, script deterministik, dan gate approval manusia. Analisis Tessera Press juga mengulas model SOP dan pertimbangan deployment.

Nah, yang perlu ditiru bukan menambah prompt makin panjang. Agent boleh menilai apakah patch masuk akal. Untuk hasil yang bisa diuji pass/fail, command yang jalan dan exit code-nya jadi bukti yang bisa diperiksa.

Di workflow, perannya bisa dipisah begini:

- Plan menetapkan perubahan yang diminta dan dampaknya.
- Implement dikerjakan coding agent di workspace terisolasi.
- Test menjalankan script dari repository dan menyimpan output.
- Review memeriksa diff serta bukti test secara terpisah.
- Approve memberi manusia hak menentukan kapan perubahan siap dikirim.

Stage-stage ini nggak harus jadi lima produk atau lima agent. Cukup pastikan tiap peran ninggalin artefak buat tahap berikutnya. Saat test gagal, tunjukkan error-nya dan izinkan retry yang terkendali. Jangan tutup kegagalan dengan ringkasan ceria.

## Pisahkan yang menulis dari yang memeriksa

Orang sering susah melihat asumsi yang ia bawa sendiri ke dalam perubahan. Agent juga nggak bisa jadi penilai independen atas patch yang baru ditulisnya.

Di fleet Hermes gue, coding, quality assurance (QA), dan pull request (PR) review punya tanggung jawab berbeda. Claude Code Command Line Interface (CLI) termasuk tool yang dipakai. QA menjalankan check dan melaporkan hasil mentah, sementara reviewer membaca diff, kebutuhan, dan bukti test.

Kalau agent implementasi bilang patch aman, itu belum bukti. Dua agent pun bisa berbagi blind spot, apalagi kalau konteksnya sama persis. Pembagian ini membantu mengumpulkan bukti yang lebih independen dan memperjelas siapa memutuskan apa. Tambahan panggilan model bukan security boundary.

## Repeatable software delivery lebih penting daripada prompt lama

Prompt memang bisa membantu satu task. Tapi kebijakan rilis tim jangan cuma tersimpan di chat yang lama-lama tenggelam. Kalau anggota tim harus mengandalkan ingatan untuk menjalankan urutannya, prosesnya belum repeatable software delivery.

Simpan praktik yang konsisten sebagai stage reusable dan script berversi. Biar gampang ditelusuri, rekam:

- Permintaan perubahan dan patch yang dihasilkan.
- Command beserta exit status-nya.
- Keputusan reviewer.

Saat ada run gagal, siapa pun di tim seharusnya bisa mengulang tahap itu tanpa merangkai lagi isi percakapannya.

Masalahnya, kegagalan bisa tertutup kalau catatan berantakan. Test merah harus tetap tercatat merah, bukan berubah jadi “hampir beres” gara-gara agent percaya diri saat merangkum. Retry juga harus ada batas dan jejaknya. Kalau test flaky diulang terus, satu check hijau belum tentu sinyal yang lebih kuat.

Tiap repository punya alur berbeda. Pilih satu jalur yang sekarang bikin tim menebak-nebak, lalu otomatisasi bagian yang hasilnya bisa dicek. Jangan script-kan semua keputusan engineering; keputusan desain yang masih butuh konteks tetap perlu orang.

## Pasang human approval di batas risiko

Human approval ada gunanya kalau melindungi sesuatu yang penting. Kalau setiap langkah kecil harus diklik, lama-lama orang menyetujui tanpa membaca. Gate sebelum perubahan menyentuh data customer atau hak akses memberi jeda yang lebih berarti.

Di sistem commerce multi-tenant seperti Dagango.com, yang perlu diuji itu batas tenant dan authorization. Request tenant A nggak boleh membawa order tenant B. User tanpa role yang sesuai juga harus ditolak, termasuk saat agent menambahkan jalan pintas.

Sebelum release, bukti yang perlu dilihat misalnya:

- Request satu tenant nggak bisa membaca record tenant lain.
- Authorization menolak user tanpa role yang dibutuhkan.
- Test mencakup jalur yang berubah, bukan happy path yang nggak relevan.

Contoh ini membahas praktik engineering, bukan klaim tentang kondisi LoopForge atau Dagango.com sekarang. Manusia tetap perlu menilai apakah perilaku yang diminta sudah benar dan bukti test-nya cukup. Test bisa bantu kita fokus ke hasilnya; yang memutuskan tetap reviewer.

## Self-hosted coding agents tetap perlu diperiksa keamanannya

Self-hosted bukan berarti aman otomatis. Repo Tencent LoopForge menyebut fitur sandbox dan delivery. Tessera Press menyoroti hal-hal yang perlu diperiksa saat deployment. Jadi cek konfigurasi yang dipakai tim sendiri, jangan menyimpulkan aman atau bermasalah hanya dari nama fiturnya.

Empat pertanyaan awal buat setup kita:

- Apa yang bisa dibaca atau diubah agent dari sandbox?
- Credential mana yang bisa dipakai selama run, dan berapa lama?
- Runner punya jalur ke service internal atau jaringan production?
- Siapa yang bisa memicu workflow, dan bagaimana default deployment-nya?

Perlakukan coding agent self-hosted seperti otomasi lain yang punya akses repository atau credential. Kecilkan permission, jelaskan jalur network, lalu uji sandbox dengan akses yang memang mau diberikan.

Nggak perlu langsung bongkar seluruh pipeline. Mulai dari satu check rilis yang selama ini hidup di chat, ubah jadi command yang bisa diulang, lalu simpan output-nya. Minta orang lain meninjau bukti itu dan pasang human gate saat dampak ke customer mulai terasa.

Prompt bagus tetap berguna, tapi bukan bukti bahwa test benar-benar berjalan. Nah, kalau output test hilang setelah run selesai, siapa yang bisa memastikan keputusan release kita punya dasar?

## FAQ Teknis

### Apakah agent reviewer yang berbeda cukup untuk menyetujui merge?
Nggak cukup. Agent kedua masih bisa memakai asumsi yang sama dengan agent pembuat patch. Simpan hasil test dari command, lalu minta manusia menilai perubahan yang menyentuh batas risiko penting.

### Haruskah semua aksi agent menunggu human approval?
Nggak. Approval perlu dipasang sebelum delivery berisiko atau perubahan permission. Langkah rutin yang mudah dibatalkan bisa otomatis kalau akses dan check-nya dibatasi.

### Self-hosting bisa melindungi credential repository dengan sendirinya?
Nggak. Periksa cakupan credential, sandbox, akses network, dan siapa yang bisa menjalankan workflow. Lokasi server nggak menjelaskan batas aksesnya.
