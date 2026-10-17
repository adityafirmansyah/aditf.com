---
title: Ilusi 30.000 PR: Kenapa Numpuk AI Reviewer Malah Ngerusak Arsitektur
slug: the-30000-pr-illusion
date: 2026-10-17
excerpt: Anthropic nge-merge 30.000 pull request per hari pakai bot yang nge-review bot tanpa manusia. Tapi review serba otomatis ini cuma mindahin diskusi arsitektur jadi bom waktu di production.
tags: ai-agents, code-review, software-engineering, devops, software-architecture
---

## Ledakan 30.000 PR dan hilangnya kebiasaan baca diff

Tanggal 15 Oktober 2026, tim Claude Code ngerilis tulisan teknis yang langsung ramai dibahas orang. Addy Osmani, Morgan Westlee Lunt, bareng Qing Wang ngebedah cara mereka nge-review code di Anthropic.

Angka skalanya luar biasa gila.

Bulan Mei 2026 mereka baru nge-merge 2.500 perubahan per hari. Pas masuk September 2026, volumenya melonjak sampai tembus 30.000 perubahan tiap hari.

Kalau diff masuk sebanyak itu, baca code baris demi baris pakai mata manusia jelas mustahil. Ditambah lagi, Claude sendiri yang nulis sekitar 90 persen codebase Claude Code. Anthropic akhirnya milih ngotomatisasi seluruh alur review mereka dari ujung ke ujung.

## Cara kerja mesin review enam lapis di Anthropic

Biar sanggup nelen puluhan ribu diff harian, Anthropic ngebangun jalur perakitan otomatis. Tiap perubahan disaring lewat enam filter berurutan:

- Pengecekan author dan verifikasi fresh-context sebelum PR dibuka.
- Rangkaian test suite CI lintas platform yang wajib hijau.
- Bot pemburu bug paralel yang dipasangkan bareng voting verifiers.
- Security scan otomatis yang langsung ngeblok merge kalau nemu celah.
- Approval berjenjang berbasis risiko, di mana kategori Low jalan tanpa reviewer manusia.
- Antrean merge otomatis yang punya mekanisme canary rollback.

Bagian pembagian risiko ini yang paling nunjukin arah filosofi mereka. PR risiko tinggi butuh dua persetujuan manusia, dan risiko sedang butuh satu.

Khusus kategori Low, kodenya langsung meluncur ke trunk tanpa pernah dilihat engineer manusia sama sekali.

## Paradoks regresi di balik 15.155 issue terbuka

Data internal yang dipamerin Anthropic kelihatan meyakinkan banget. Antara Juni sampai September, jumlah PR yang ke-merge naik dua kali lipat. Hebatnya lagi, angka revert malah turun lebih dari 40 persen.

Di atas kertas, pipeline ini kelihatan kayak kemenangan mutlak otomatisasi.

Tapi komunitas engineer di Hacker News ngeliat sisi sebaliknya. Pada thread 50122951 yang dapet 297 poin dan 278 komentar, para praktisi langsung nunjuk repository anthropics/claude-code di GitHub. Proyek dengan 151k stars itu ternyata nyimpen 15.155 issue terbuka.

Di titik ini paradoks regresi review berbasis bot mulai kebongkar. Bot verifier emang jago banget nangkep error mekanis kayak sintaks typo, unit test patah, atau salah tipe data. Masalahnya, bot gampang buta kalau udah urusan semantic drift, perubahan perilaku CLI, atau ekspektasi user yang mendadak rusak.

## Review kode dari awal punya dua peran berbeda

Anthropic mandang code review murni sebagai adu cepat throughput pabrik. Di kepala mereka, review cuma saringan pencegah bug sebelum kode nyentuh branch utama. Kalau mesin bisa nemuin error lebih cepat dari manusia, campur tangan engineer dianggap cuma bikin lambat rilis.

Sudut pandang kayak gitu keliru nangkep esensi review code di tim engineering. Di sistem nyata, review kode megang dua peran yang beda jauh:

- Deteksi kerusakan mekanis, mulai dari sintaks error, kegagalan regresi, sampai pelanggaran tipe data.
- Penjajaran arsitektur, yang ngebangun pemahaman bersama dan jagain batas domain antar engineer.

Mesin emang luar biasa buat urusan verifikasi mekanis. Begitu bot nge-review kode buatan bot lain tanpa campur tangan manusia, fungsi penjaga arsitektur langsung lenyap. Reviewer otomatis ngasih approval ke diff terisolasi tanpa ngerti arah besar dari sistem kita.

## Kenapa zero-human review bikin utang teknis makin numpuk

Di Dagango.com, stack kita jalanin frontend Next.js App Router bareng backend FastAPI di atas server Linux. Buat ngebantu tim, ada armada agen mandiri Hermes di Linux bare-metal yang kerja tiap hari nulis kode dan QA. Tapi pengalaman 13 tahun lebih ngerilis software production ngajarin gue satu batasan mutlak: jangan pernah biarin mesin nge-merge ke production tanpa approval manusia.

Persetujuan serba bot emang kerasa kayak mukjizat di hari pertama. Agen bikin patch, bot verifier ngasih centang hijau, terus dalam hitungan menit PR udah merge. Nggak ada engineer yang perlu mecah fokus cuma buat melototin diff pendek beberapa baris.

Tapi di production nyata, tumpukan perubahan kecil yang lolos tanpa dicek manusia ini pelan-pelan berubah jadi bom waktu. Kita udah kenyang ngeliat penyesuaian sepele yang ujungnya bikin sistem rontok berjamaah:

- Perubahan TTL cache yang kelihatan aman di lokal, tapi langsung nguras connection pool database pas traffic puncak.
- Poller background yang lupa pasang exponential backoff terus ngehajar microservice sendiri lewat thundering herd.
- Helper mutasi data yang ngerusak isolasi multi-tenant tanpa bikin satu pun unit test gagal.

Ngehemat lima menit waktu review di PR terisolasi sering kali dibayar mahal dengan begadang semalaman buat debugging darurat. Kalau solusinya nggak ketemu cepet, ops bakal langsung rollback ke versi stabil sementara tim engineer pontang-panting bikin hotfix di hari yang sama. Kodenya lolos semua saringan bot, tapi nggak ada satu pun manusia yang paham gimana kepingan baru itu nyambung. Itu bukan kecepatan kerja, tapi utang arsitektur yang sengaja lo tunda.

## Playbook realistis buat review di era agent

Jalan keluarnya jelas bukan nolak otomatisasi secara membabi buta. Baca 30.000 PR pakai mata manusia itu mustahil, dan manusia emang linter yang buruk. Kuncinya ada di pembagian batas yang tegas antara verifikasi mesin dan pengawasan arsitektur oleh manusia.

Di tim kita, pipeline review berbasis agen ditata lewat empat aturan operasional:

- Manfaatkan bot otomatis buat bikin matriks reproduksi bug, jalanin linter, dan ngecek invarian tipe statis.
- Wajibkan agen bikin ringkasan markdown mandiri yang ngejelasin alasan teknis kenapa perubahannya aman.
- Wajibkan persetujuan manusia buat setiap perubahan kontrak API publik, migrasi database, dan batas domain antar service.
- Jangan pernah ngasih izin zero-human review ke pull request yang ngerubah shared state sistem kita.

Serahin aja tugas mekanis ke agen: tes kasus ekstrem, buru memory leak, dan pastiin compliance di semua environment. Tapi urusan arsitektur tetap butuh mata manusia. Kalau tim lo sendiri udah nggak paham gimana sistemnya bekerja, ngebut nge-merge puluhan ribu PR cuma bakal nganter lo ke satu tempat: insiden besar berikutnya. 😅
