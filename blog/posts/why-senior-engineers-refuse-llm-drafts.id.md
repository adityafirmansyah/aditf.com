---
title: Martin Fowler Soal LLM Voice: Alasan Senior Engineer Menolak Draf AI
slug: why-senior-engineers-refuse-llm-drafts
date: 2026-10-30
excerpt: Martin Fowler mengingatkan bahaya draf tulisan dari LLM yang merusak kredibilitas teknis. Solusinya bukan membuang AI, tapi memisahkan riset fakta dari penulisan kalimat.
tags: ai tooling, software engineering, technical writing, llms, developer experience
---

Tanggal 29 Oktober 2026 kemarin, Martin Fowler nulis esai pendek berjudul "LLM Voice". Pesannya tegas: jangan pernah biarkan Large Language Model (LLM) nulis draf pertama tulisan lo.

Alasannya masuk akal. Tulisan yang dihasilkan AI biasanya mendarat di *uncanny valley*. Kelihatan rapi, tapi hampa dan bikin pembaca cepat muak. Mau diedit sekeras apa pun, irama tulisan yang kaku dan sok sopan itu susah banget dihilangkan.

Gue langsung paham rasa frustrasi itu. Setelah 13 tahun lebih nulis code dan bikin spek arsitektur di sistem produksi, kredibilitas teknis itu aset paling mahal. Dan paling gampang hilang.

Sekali pembaca ngerasa lo cuma menyalin teks mesin tanpa bobot, mereka bakal langsung tutup tab. Tapi menurut gue, kesimpulan Fowler kurang pas. Solusinya bukan berarti kita harus anti sama AI.

Masalah sebenarnya ada di arsitektur pipeline kita. Mesinnya nggak perlu lo buang. Batas kerjanya yang wajib lo tata ulang.

## Akar Masalah Alignment Slop

Di Hacker News (HN) thread 50290177, banyak developer senior ngebahas kenapa tulisan buatan AI kerasa capek banget dibaca. Pembahasannya merujuk ke riset linguistik di arXiv:2410.16107 soal variasi gaya tata bahasa.

Riset itu nemuin fakta menarik. Gaya bahasa AI yang seragam ini bukan bawaan dari fase pretraining web. Sumber masalahnya justru muncul di tahap post-training.

Proses Supervised Fine-Tuning (SFT) dan algoritma alignment bikin variasi kalimat mendadak amblas. Teknik seperti Reinforcement Learning from Human Feedback (RLHF) dan Direct Preference Optimization (DPO) menghukum opini yang tajam demi ngejar skor aman.

Akhirnya, model AI belajar serangkaian kebiasaan defensif:

- Selalu nambahin disclaimer panjang di setiap pernyataan.
- Memasukkan kata transisi yang kelewat sopan.
- Memaksa paragraf punya struktur poin yang simetris.
- Mengganti detail trade-off teknis dengan kalimat klise yang hambar.

Modelnya nulis kayak jubir korporat yang ketakutan bikin salah. Pas lo minta draf teknis, friksi nyata yang bikin tulisan engineering dipercaya malah disapu bersih.

## Aturan Ptacek Buat Review Tanpa Kompromi

Praktisi keamanan Thomas Ptacek punya aturan main yang sangat bersih soal pemakaian model bahasa buat tulisan teknis. Prinsipnya sederhana: pakai AI sebagai kritikus yang galak, jangan jadikan tukang tulis kalimat.

Model bahasa itu jago banget nyari celah logika. Lo bisa tempel draf rancangan arsitektur lo ke dalam prompt, terus kasih instruksi tegas:

- Tunjukkan titik kegagalan sistem yang kelewat dari rancangan ini.
- Catat prasyarat operasional yang lupa gue jelaskan.
- Tunjuk bagian argumen teknis yang lompat ke kesimpulan tanpa bukti.
- Tandai skenario deployment yang berpotensi bikin migration database gagal.

Kunci dari instruksi di atas ada di batasannya. Lo nggak minta dia nulis ulang kalimat lo. Lo bahkan wajib melarang model buat ngasih saran kata pengganti.

Begitu lo izinkan LLM menulis ulang paragraf lo, irama kalimatnya yang simetris bakal langsung nular. Urusan bedah logika serahkan ke mesin. Tapi kata-katanya tetap milik lo sendiri.

## Memisahkan Riset Fakta dari Penulisan di Produksi

Di pipeline multi-agent Field Notes yang jalan tiap hari, kita pakai armada agent Hermes buat otomasi publikasi. Pola arsitektur yang sama juga kita pakai di Dagango.com buat nulis dokumen teknis multi-tenant.

Dulu kita sempat kena jebakan yang sama kayak omongan Fowler. Kalau lo cuma ngasih prompt bebas dan minta model nulis artikel, hasilnya cuma sampah korporat.

Fix-nya adalah memisahkan tanggung jawab riset dari penulisan draf secara total. Kita bagi tugasnya ke tiga agent yang bekerja terisolasi:

- **Research Agent**: Mengumpulkan data mentah dan memverifikasi kode status Hypertext Transfer Protocol (HTTP) 200 di semua link sumber rujukan. Agent ini dilarang keras merangkai kalimat artikel.
- **Drafting Agent**: Mengambil data dari brief terstruktur, lalu menulis artikel dengan aturan batas panjang kalimat yang sangat ketat.
- **Auditor Agent**: Menjalankan script deterministik buat ngukur panjang kalimat dan menghitung kepadatan koma.

Begini gambaran alur kerja di pipeline kita:

```text
[Sumber Primer] ──> (Researcher) ──> [Brief Fakta Terstruktur]
                                              │
                                              ▼
                                     (Typewriter Agent)
                                              │
                                              ▼
[Audit Lolos]    <── (Auditor Linter) <── [Draf Mentah]
       │                      │
       ▼                      ▼
  [Publish PR]         [Revisi Bernomor]
```

Tahap riset cuma menghasilkan fakta yang bisa diuji, seperti angka benchmark atau commit git. Karena researcher nggak bikin narasi apa pun, tahap drafting nggak punya irama AI yang bisa ditiru.

## Negative Constraints dan Register Sebagai Benteng

Alat pembuat draf butuh batasan negatif yang tegas. Kalau lo cuma minta AI nulis dengan gaya santai, hasilnya malah sering kali lebay. Kredibilitas tulisan dijaga dengan melarang apa saja yang nggak boleh dilakukan model.

Di pipeline kita, ada batasan mekanis yang langsung memutus irama bawaan AI:

- Batas maksimal 35 kata per kalimat.
- Maksimal tiga koma dalam satu kalimat supaya klausa nggak bertumpuk.
- Konversi otomatis buat poin yang terdiri dari dua hal menjadi bullet list.
- Larangan keras buat istilah klise dan kata transisi formal yang hampa.

Proteksi ini makin penting di lingkungan teknis bilingual. Kalau lo prompt pakai bahasa Indonesia, model generik biasanya langsung balik ke gaya birokrasi yang kaku. Pilihan katanya bakal dipenuhi kata penghubung formal seperti `adalah` dan `merupakan`.

Buat membabat kebiasaan itu, kita kunci sistem ke register santai ala obrolan developer lewat panggilan *gue* dan *lo*. Kita biarkan istilah teknis tetap natural seperti *deploy*, *runner*, dan *pipeline*.

Kita juga nggak pernah menerjemahkan draf bahasa Inggris kalimat demi kalimat. Kita nulis ulang versi bahasa Indonesia langsung dari intisari teknisnya. Suara praktisi aslinya jadi tetap hidup di kedua bahasa.

## Catatan Praktis Buat Senior Engineer

Kekhawatiran Martin Fowler memang beralasan. Kalau lo malas dan menyerahkan draf pertama ke model bahasa, tulisan lo bakal tenggelam bareng ribuan blog AI lainnya.

Tapi lo nggak perlu mematikan tools AI lo. Anggap saja mereka sebagai third-party library yang belum tentu stabil. Terapkan tiga langkah ini di dokumen teknis lo berikutnya:

1. **Kumpulkan fakta lebih dulu**: Pakai otomasi buat ngecek link eksternal dan menarik metrik mentah sebelum lo mulai merangkai satu kalimat narasi pun.
2. **Pakai review yang galak**: Suruh model mencari celah logika atau kegagalan sistem di tulisan lo, sambil melarang keras dia memberi saran kalimat pengganti.
3. **Kunci draf dengan aturan struktur**: Tulis sendiri draf lo, atau pasang batasan negatif yang melarang kalimat panjang dan jargon korporat.

Developer nggak butuh artikel yang sopan dan netral tanpa nyawa. Mereka baca tulisan lo buat ngeliat luka di lapangan dan angka riil di sistem produksi.

Mereka nyari opini teknis lo yang berani. Jaga hal itu tetap ditulis manusia. 😅
