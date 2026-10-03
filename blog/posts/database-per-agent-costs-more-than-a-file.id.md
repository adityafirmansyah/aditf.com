---
title: Satu Database per Agent Itu Nggak Semurah File
slug: database-per-agent-costs-more-than-a-file
date: 2026-10-03
excerpt: Supabase bilang agent harus bisa bikin database semurah bikin file. Di mini-PC gue udah jalanin satu database per agent, jadi gue hitung. Bikinnya emang murah; semua yang setelahnya itu baru tagihannya.
tags: sqlite, databases, ai-agents, infrastructure, self-hosting
---

## Pitch-nya, pakai kalimat mereka sendiri

Supabase lagi ngakuisisi Turso, dan framing-nya seputar agent. Mereka ngaku udah launch lebih dari satu juta database tiap minggu, dan agent, kata mereka, "spinning up millions of databases to power the prototypes, explorations, dashboards, and apps they're building."

Janjinya sederhana: agent "should be able to create a database as easily as creating a file, with just as little concern about cost". Dan gue udah hidup di masa depan itu.

Di mesin ini jalan 16 profil agent, masing-masing punya `state.db` sendiri. Mesinnya mini-PC Celeron 10 watt, bukan slide deck. Jadi gue hitung.

Bikin database-nya emang semurah bikin file, tapi yang setelahnya nggak.

## Yang sebenernya dibeli Supabase

Mesin di balik pitch itu punya Turso. SQLite ditulis ulang pakai Rust. Platform cloud-nya "can manage millions of databases, loading them when needed and suspending them when they're not."

Kalimat terakhir itu intinya, dan post rewrite Turso sendiri jujur soal alasannya. Setelah dua tahun libSQL, katanya, "Independent usage of libSQL as a SQLite replacement remained low". Kebanyakan user, tambahnya, lebih butuh SQLite-over-the-wire daripada perbaikan database intinya.

Jadi Supabase nggak beli storage engine yang lebih cepat, tapi control plane-nya: mesin yang nge-suspend, nge-resume, nge-checkpoint, dan nge-backup sejuta database kecil. Format file-nya bukan bagian yang susah.

## Tagihannya, satu per satu

Cakupannya: direktori home gue, `node_modules` dan isi VCS di-skip, diukur 2026-10-03.

- **16 profil agent**, masing-masing punya `state.db` sendiri, dan kalau ditambah database root totalnya jadi 17 `state.db`, 633 MB.
- **259 file `.db` lain**, 61 MB.
- **16 file `runs_idempotency.db`**, 0,6 MB.
- **71 file `.db-wal`**, 108 MB.
- **71 file `.db-shm`**, 2 MB.
- **11 snapshot `state.db.bak`** bertanggal 24–27 September, 292 MB.

Totalnya 449 file, sekitar 1,1 GB. Database tunggal paling besar itu `eng-frontend/state.db`. Ukurannya 158 MB.

## Database itu bukan satu file, tapi tiga

SQLite sendiri ngomong gini di dokumennya: "There is an additional quasi-persistent '-wal' file and '-shm' shared memory file associated with each database," yang bikin SQLite "less appealing for use as an application file-format". Peringatan itu soal database yang dipakai sebagai format file serbaguna, dan itu bukan soal pemakaian embedded-nya.

Semua database di sini jalan di mode WAL. Jadi tiap satu itu tiga file di disk. Write-ahead log-nya nyimpen transaksi yang udah commit tapi belum dilipat balik ke file utama.

Di mesin ini, 17 file `state.db-wal` nahan 60 MB, dan tiga paling gede (cto, pr-reviewer, branding) pas 6 MB masing-masing. SQLite cuma auto-checkpoint tiap 1.000 halaman, jadi agent yang sibuk bisa nyimpen banyak data ter-commit di file sampingan.

## Dua biaya yang nggak pernah masuk slide

Pertama, akses baca. Database WAL nggak bisa dibuka oleh proses yang cuma punya izin baca. Proses pembukanya butuh akses tulis ke file shared memory `-shm`. Jadi jalan pintas yang kelihatan jelas itu gagal: copy `.db`-nya ke tempat lain terus dibaca.

Kedua, backup. Sebelas salinan bertanggal dari empat hari di September jumlahnya 292 MB, seperempat dari seluruh footprint, dari 16 agent, tanpa retention policy dan nggak ada yang minta.

Skalain salah satunya ke sejuta database per minggu. Angkanya langsung berhenti jadi pembulatan.

## Argumen lawannya perlu dibawa juga

Rewrite-nya menuai penolakan nyata, bukan cuma tepuk tangan. Thread-nya sampai 202 poin dan 105 komentar. CEO maupun cofounder Turso ikut jawab di situ.

arnath nanya, kenapa harus nulis ulang software yang menurut dia "widely considered one of the best written and tested pieces of software in the world".

smt88 malah bilang, keuntungan utama nulis ulang pakai Rust itu ngurangin "serious security vulnerabilities and memory bugs", bukan nambah kecepatan atau stabilitas.

Soal performa lebih parah lagi. Alexey Milovidov buka issue ClickBench #336 dengan judul "Add Turso (it is unbelievably slow) (it also does not work)", dan satu pull request setelahnya bunyinya: "Turso - it is ridiculously slow, can't believe that".

Komentator f311a nyatet percobaan benchmark berulang yang, katanya, "each time new bugs were found". Ada juga menaerus. Dia lapor loader-nya nyangkut di "4 kilobytes per second".

Cofounder Turso, penberg, jawab di thread. "It's all in the ingestion before the benchmark," tulisnya, dan "we do intend to improve it but not the highest priority right now".

CEO glommer jawab sendiri soal akuisisinya. "We were doing fine," ujarnya. "This is a strategic acquisition," dan Turso "grew revenue > 5x this year", full MIT.

Itu versi jujurnya. Engine-nya masih kasar di beberapa tempat. Yang jadi aset justru control plane-nya.

## Yang bakal gue lakuin

Di 16 agent, gue masih bisa beresin ini manual:

1. Checkpoint write-ahead log-nya, biar 60 MB-nya balik ke file utama.
2. Bikin retention policy, terus hapus backup September itu.
3. Jauhkan database profil yang nganggur dari jalur panas.

Di sejuta database per minggu, nggak ada yang manual. Mesin checkpoint, backup, dan retention itu produknya. Dan persis itu yang dibeli Supabase.

Model-nya bener: satu database per agent itu bentuk yang masuk akal.

Yang salah cuma kalau lo ngehargainnya dari biaya bikin.