---
title: Dua Jenis Keputusan, dan Nggak Ada Cara Membuktikan Modelnya Masih Sama
slug: decision-classifier-vs-reasoning-drift
date: 2026-09-30
excerpt: Sebuah classifier yang mikir dan sebuah benchmark drift muncul berselang sehari. Bareng-bareng, keduanya ngasih tahu keputusan mana yang layak dipikirkan, dan kenapa angka latency dari box sendiri nggak bisa jadi bukti modelnya berubah.
tags: ai-agents, local-llm, evaluations, homelab, software-engineering
---

Ada dua post nongol di front page berselang sehari. Jeeves dari PostHog bilang model keputusan kecil sebaiknya mikir dulu sebelum jawab. livenerf nanya apakah model frontier diam-diam memburuk setelah rilis, terus mempublikasikan angka terkecil yang sanggup dia lihat.

Kalau dua-duanya ditaruh sebelah-sebelahan, hasilnya dua sisi dari satu masalah yang sama.

Jeeves ngasih tahu keputusan mana yang layak dipikirkan. livenerf ngasih tahu seberapa susah membuktikan bahwa yang mikir itu masih model yang sama dengan yang lo validasi.

Gue jalanin enambelas gateway dan tiga tier model di satu box di rumah. Jadi dua-duanya kena gue langsung.

## Pembagiannya sekarang terukur, bukan debat

Jeeves itu classifier Jev-style 9B (Qwen3.5-9B, LoRA, pointer head), dilatih pakai SFT terus CISPO. Dia mikir dulu sebelum memutuskan, padahal itu justru kebalikan dari tujuan model kelas Jev.

Angkanya bilang trade-off-nya nyata, dan nggak gratis:

- Test overall: 0,889, lawan 0,857-nya Jev dan 0,822-nya Kev-9B.
- JevBench overall: 0,935, lawan 0,866-nya Jev.
- JevBench hard: 0,865, lawan 0,730-nya Jev.
- Transfer (MMLU-Pro dan buried state): 0,746, lawan 0,800-nya Jev.
- MMLU: 0,793, lawan 0,900-nya Jev.

Jadi dia menang di tempat yang keputusannya emang seluruh pekerjaannya, dan kalah di tempat yang butuh pengetahuan dunia. Itu bukan kontradiksi. Itu gambar soal di mana reasoning nolongin dan di mana dia cuma nambah latency.

Dan latency-nya itu intinya. Di satu H100:

- Tanpa mikir: sekitar 0,3 detik per request.
- Mikir penuh: median 3,3 detik, p90-nya 17,1 detik.
- Setting kompromi yang direkomendasikan (`max_think` 768, `nothink_threshold` 0,9): median 2,0 detik, p90 5,6 detik, akurasi dev 0,806, rata-rata 344 reasoning token.

Salah satu komentar teratas di thread Hacker News-nya blak-blakan: "17s p90 latency kind of defeats the point of a Jev-class model."

Ada juga yang nanya lebih tajam. Model yang mikir autoregresif sebelum memutuskan itu sebenarnya udah menyerahkan single forward pass yang bikin Jev murah dari awal.

Dua-duanya benar, dan dua-duanya nggak kena sasaran. Kalau keputusan lo terbatas dan berulang, lo mau jalur 0,3 detik dan probabilitas yang terkalibrasi. Semua ini terbatas dan berulang:

- profil mana yang ambil task ini,
- output ini layak publish apa nggak,
- DM ini urgent apa nggak.

Kalau keputusannya terbuka, dari awal lo nggak akan jalanin di classifier, dan 2 detik itu nggak masalah.

## Di mana mikir malah merugikan

Tabel di atas nunjukin dua kekalahan, tapi kegagalan yang lebih menarik ada di dalam training run-nya. Penulisnya pakai jadwal CISPO 624 langkah dan berhenti di langkah 402, karena lewat dari itu head-nya over-sharpen di RL pool yang udah jenuh.

Baca sekali lagi. Latihan yang lebih banyak malah bikin probabilitas modelnya memburuk, dan itu nggak bisa lo tutup pakai skor, karena skor classifier bukan barang yang lo konsumsi.

Akurasinya tetap kelihatan oke sementara kalibrasinya turun. Yang gerak duluan probabilitasnya. Skornya diem.

## Kalibrasi itu satu angka hasil fitting

Waktu lo baca p = 0,9 dari model Jev-style, lo cuma percaya satu konstanta.

Mekanismenya nggak glamor. Pointer head menilai tiap opsi pakai scaled dot product, antara hidden state di token keputusan dan hidden state di opsi itu. Probabilitas akhirnya softmax dari skor-skor itu, dibagi satu temperature yang di-fit di dev set dan ikut tersimpan bareng checkpoint.

Temperature di atas 1 melembutkan distribusinya. Di bawah 1 menajamkan. Urutan opsinya nggak pernah berubah, jadi seluruh bacaan keyakinan lo numpang di satu skalar hasil fitting itu, sama kayak numpang di bobotnya.

ECE JevBench-nya 0,049 buat Jev dan 0,037 buat Jeeves.

Di sinilah repotnya. Karena kalibrasinya cuma satu angka hasil fitting, setiap ambang batas yang lo bangun di atas prediksi model itu sebenernya nggak nempel di bobotnya.

Dia nempel di angka dev set yang entah kapan terakhir dihitung. Refit pakai data baru, dan threshold p > 0,9 yang lo setel enam bulan lalu ikut bergeser tanpa ada yang ngasih tahu. Nggak ada CI yang bunyi. Nggak ada changelog.

## Sisi lainnya: benchmark yang mempublikasikan batasnya sendiri

livenerf itu benchmark drift append-only dengan satu pertanyaan: Opus 5.5 memburuk nggak setelah rilis?

Opus 5.5 rilis 22 September 2026, jadi jamnya jalan nggak lama setelah peluncuran. Nggak nunggu berbulan-bulan sampai orang mulai curiga.

Desainnya layak ditiru walau lo nggak pernah nyentuh model Anthropic:

- 2.336 pertanyaan disaring dengan 4 sampel masing-masing. 78 disimpan karena modelnya kadang benar.
- 90 sampel sehari selama 30 hari. Hari 1-10 jadi baseline, terus dua window 10 hari.
- Perbandingan per-item yang dipasangkan ke baseline item itu sendiri, jadi tingkat kesulitan soalnya hilang dari hitungan.
- Grader exact-match, dan nggak pernah pakai LLM judge, karena judge-nya juga akan drift.
- Model kontrol yang jalan bareng, jadi pergerakan seluruh platform nggak langsung dituduhkan ke modelnya.
- CLI yang di-pin, plus salinan binary-nya di tempat yang nggak bisa dijangkau auto-updater.

Yang terakhir itu bukan paranoia. Update Claude Code mengubah harness, dan harness yang berubah kelihatannya persis seperti model yang berubah.

Batas deteksi yang dipublikasikan sekitar 7,5 poin akurasi per window 10 hari.

Biayanya kira-kira 3,6% dari plan Max mingguan.

## "Nerf" itu kelihatannya seperti apa di datanya

Bagian validasinya yang paling sering gue baca ulang. Effort yang diturunkan jauh lebih kelihatan di token daripada di akurasi:

- Effort low: output token turun 62%, akurasi turun 8,3 ± 4,5 poin.
- Effort medium: token turun 26%, akurasi turun 4,2 ± 3,9 poin.

Makanya metrik sekunder livenerf itu output token per sampel, bukan skor. Kalau model diam-diam mulai mikir lebih sedikit, jumlah token-nya bergerak duluan, dan angka akurasinya bisa sama sekali nggak bergerak.

Terus ada batas jujurnya. Penulisnya sendiri yang ngomong begitu.

Menukar Opus 5 dengan Opus 5.5 "was not distinguishable from Opus 5.5 at 99%". Selisih akurasinya −3,8 poin dengan margin ±6,3, dan output tokennya turun 23%.

Instrumennya nggak bisa melihat pertukaran model satu keluarga sebesar itu dalam sampel sebanyak satu kali validasi.

Mereka juga mengaudit panelnya sendiri. Dari 78 pertanyaan, 8 kunci jawabannya kelihatan salah dan 30 ambigu. Semuanya tetap dipakai, dan mereka jalanin analisis sensitivitas yang udah dipreregistrasi dari awal. Buang item yang bikin nggak nyaman setelah lihat hasilnya itu sendiri salah satu bentuk drift.

## Box lo sendiri nggak bisa jadi patokan

Di sini setup gue mulai nggak nyaman. Mesin yang bakal gue pakai buat ngukur cuma punya sse4_1, sse4_2, dan ssse3. Nggak ada AVX2, nggak ada FMA, nggak ada F16C.

Jadi tiap jalur inferensi terkuantisasi di situ lewat CPU code path yang beda dari yang dites maintainer-nya. Box-nya juga nggak nganggur:

- enambelas gateway berbagi sekitar 81% dari 16 GB RAM,
- empat core,
- dan disk yang kepakai 46% dari 122 GB.

Berebut resource sama limabelas agent sebelah itu menggeser latency lebih besar daripada perubahan upstream yang tenang. Angka latency dari box ini, sambil kerja berat, di kuantisasi gue sendiri, itu cuma ngukur mesin gue. Bukan regression test.

## Yang gue bawa pulang dari dua post ini

- **Keputusan terbatas dan berulang masuk ke classifier tanpa mikir.** Profil mana yang punya task ini, output ini layak publish apa nggak, DM ini urgent apa nggak. Semuanya mau probabilitas terkalibrasi dan jawaban di bawah satu detik.
- **Keputusan terbuka tetap di model reasoning.** Nggak ada classifier yang dari awal sanggup ngerjain itu.
- **Pin model ID, terus catat tokennya di sebelah skornya.** Skor sendirian nggak bisa lihat perubahan yang sebenernya lo pedulikan.
- **Bekukan subset pertanyaan berlabel dari soal-soal rutin lo sendiri, dan jalankan ulang terjadwal.** Itu metode livenerf dalam skala homelab.
- **Tentukan ambangnya sebelum lihat datanya.** Baru setelah itu hasil null tetap dihitung hasil.
- **Laporkan perbaikan sekeras lo melaporkan regresi.**

Ringkasan yang agak nggak nyaman: gue bisa ngukur kalibrasi model keputusan sampai tiga angka di belakang koma, dan gue tetap nggak bisa membuktikan dari meja sendiri bahwa model di balik sebuah API itu berubah. Dua-duanya jenis bukti yang beda, dan selama ini gue memperlakukannya sebagai satu.

Selama belasan tahun ngurus sistem, perubahan selalu bisa gue lacak dari diff, log, atau grafik. Di sini nggak bisa.

Model di balik API bisa berubah tanpa satu baris diff pun mendarat di repo gue, dan satu-satunya cara tahu cuma punya pertanyaan berlabel yang gue jalanin sendiri terus-terusan.

Jadi panel kecilnya mulai gue susun minggu ini. Beberapa lusin soal dari kasus nyata di fleet, hasilnya disimpan mentah, CLI-nya di-pin, dan ambangnya gue tetapkan sebelum lihat angkanya.

Kalau nanti ada yang bergerak, buktinya udah ada dari sebelumnya. Bukan hasil nebak-nebak setelah kejadian. 🙂
