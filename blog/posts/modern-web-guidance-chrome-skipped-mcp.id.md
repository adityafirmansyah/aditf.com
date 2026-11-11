---
title: "Modern Web Guidance 1.0: Kenapa Chrome Nggak Pakai MCP buat Nyetop Agent Nulis JavaScript 2019"
slug: modern-web-guidance-chrome-skipped-mcp
date: 2026-11-11
excerpt: "Modern Web Guidance 1.0 ngirim 200+ guide browser primitive sebagai skill CLI offline 7MB. Alasan mereka nolak MCP justru pelajaran buat ai coding agents."
tags: ai-agents, web-development, javascript, devtools
keywords: modern web guidance, ai coding agents, browser primitives vs javascript, agent skills vs mcp, legacy-scan web modernization
---

Kalau lo minta coding agent bikin modal dialog, keluarannya hampir selalu sama.

Tumpukan `<div>` plus focus trap manual yang nggak ada hubungannya sama platform, terus ditutup hack scroll lock yang jatuh di iOS.

Padahal browser udah punya `<dialog>` dan `showModal()` sejak bertahun-tahun, tapi agent tahu namanya doang dan hampir nggak pernah benar-benar dipakai.

Modal kayak gini sering gue temuin di PR yang masuk ke repo Dagango.com. Test-nya hijau dan diff-nya rapi, tapi primitifnya salah.

Nah, Modern Web Guidance 1.0 ini jawaban Chrome buat masalah itu. Rilis 10 November 2026 lewat tulisan Philip Walton di blog Chrome for Developers.

Yang bikin beda: Firefox, Edge, dan MDN ikut masuk jadi steward. Bukan cuma Chrome sendirian.

Guidenya sendiri bagus. Yang bikin gue nulis soal ini justru keputusan pengemasan di baliknya.

## Kenapa coding agent masih nulis JavaScript 2019?

Korpus latihannya ya isi Stack Overflow sebelum 2022, jadi model ngulang jawaban lama.

Solusi div overlay plus focus trap bikinan sendiri itu yang dia hafal. Nggak ada bagian dari training-nya yang ngasih nilai lebih buat milih jalan platform.

Hasilnya, code-nya tetap lolos review. Di situ jebakannya. Bot lihat modal jalan, terus lanjut ke file berikutnya.

Nggak ada satu metrik pun yang nyatet kalau modal "jalan" itu isinya 50 baris JavaScript, buat fitur yang browser bisa handle cuma dengan satu atribut.

Yang didorong guide-nya malah ini:

- `<dialog>` dan `showModal()` gantiin overlay div plus urusan inert manual,
- `field-sizing: content` gantiin listener resize textarea,
- CSS anchor positioning gantiin loop `getBoundingClientRect()` yang nempel di scroll,
- dan scroll-snap di navigation drawer buat gantiin hitungan drag pakai pointer event.

Substitusi terakhir itu yang paling gue suka.

Di guide `navigation-drawer`, gesture swipe dipindah ke container yang bisa scroll dengan snap stop di posisi buka dan tutup. Momentum, velocity, dan gesture yang keburu kepotong di tengah jalan semuanya diurus browser. Hasilnya nggak ada tracking pointer sama sekali.

Coba baca daftar itu sekali lagi sebagai satu paket. Semua barisnya jawaban buat pertanyaan browser primitives vs javascript, dan arahnya selalu sama.

## Modern Web Guidance dikirim sebagai skill 7MB, bukan server MCP

Yang menarik, keputusan paling pentingnya justru nggak ada di guide. Ada di thread Hacker News.

Di situ Paul Irish cerita dia habisin sembilan bulan buat mikirin satu hal. Gimana caranya "ship this as an agent skill + (Agentic RAG) CLI tanpa bikin context window jebol".

Pilihan yang ada di meja waktu itu server Model Context Protocol (MCP). Masalahnya server MCP itu nyala terus. Skema tool-nya nangkring di context tiap turn, mau lo lagi ngutak-ngutik layout atau nggak.

Yang akhirnya dikirim:

- stack retrieval native 500MB dipadatkan jadi paket pure-JS sekitar **7MB**,
- pencarian offline pakai BM25 (fungsi ranking leksikal) plus model embedding lokal, jawabnya sekitar **10ms di CPU**, tanpa network call dan tanpa API key,
- dan deskripsi skill sekitar **205 token** yang harus berebut aktivasi di task frontend.

Alurnya pendek. Skill aktif dulu. Agent jalanin `search "<use case>"`, terus `retrieve <guide-id>` narik tepat satu guide masuk context. Nggak ada yang nebeng.

Inilah bentuk paling bersih dari perdebatan agent skills vs MCP. Progressive disclosure menang karena sumber daya yang langka itu perhatian, bukan bandwidth.

Simon Willison usul alternatif lain: index markdown di GitHub Pages yang bisa di-grep, jadi nggak perlu install apa-apa. Irish setuju buat pemakaian sesekali, tapi jujur bilang biaya token index itu sendiri kemahalan buat dipakai harian.

Gue suka cara dia ngejawab: kompromi diakui, angkanya disebut.

Server yang nyala terus itu mirip langganan semua tool tiap turn, padahal yang kepakai cuma satu. Di fleet gue sendiri prinsipnya sama: skill yang nggak relevan tetap bayar ongkos context walaupun nggak ngapa-ngapain.

Makanya angka 205 token itu bukan detail kecil. Itu harga buat bilang "kalau ada kerjaan layout, panggil gue".

## Angka di balik lompatan 55% ke 92%

Chrome ngejalanin Codex, Claude, dan Antigravity di 200 task. Penilaiannya pakai sekitar 1.700 assertion Playwright dan abstract syntax tree (AST).

Tanpa skill, agent lolos 55%. Setelah skill-nya dipasang, 92%.

Data dari partner nunjuk ke arah yang sama. note inc. ngejalanin evaluasi 180 putaran di codebase Next.js produksi mereka, dari 61% jadi 94% di pengecekan web modern. Di 431 pull request yang ke-merge, prioritas loading gambar Largest Contentful Paint (LCP) naik 28%.

MetaMask malah pakai ini sebagai bot review di tiap PR extension mereka, konfigurasinya cuma prompt tiga baris.

Lima minggu pertama, bot-nya review sekitar 480 PR dan komen di 64. Engineer-nya benerin 43 temuan, dengan median 15 menit dari komen sampai fix.

Temuannya numpuk di aksesibilitas, semantik HTML, dan form. Itu persis area yang selama ini lolos dari linter yang gue pasang di continuous integration (CI).

Tool cuma nangkep yang ada aturannya. Bagian tengah yang membosankan tetap nggak kelihatan.

## legacy-scan sengaja dibikin deterministik

CLI-nya bawa workflow `legacy-scan` yang dilatih di 30.000 repo GitHub. Menurut Irish, precision rata-ratanya 92% di repo yang nggak dipakai buat latihan.

Pengumumannya jujur soal cakupan. Scan-nya analisis statis atas HTML, CSS, JavaScript dan `package.json`, dengan daftar pola yang sengaja dibatasi. Sempit dulu, audit ala agent nyusul.

```shell
# pasang ke dalam project
npx modern-web-guidance@latest install

# scan codebase lama buat cari kandidat upgrade
npx modern-web-guidance@latest legacy-scan .
```

Determinisme itu inti dari legacy-scan web modernization. Agent yang disuruh modernisasi satu file bakal nulis ulang file itu.

Scanner yang laporin file, baris, dan pola yang cocok itu beda kelas. Batas kerja agent-nya jelas sejak awal, dan diff-nya nggak melebar.

Buat gue ini bedanya besar. Rewrite penuh dari agent itu susah di-review. Yang paling sering ilang justru detail kecil yang nggak nyambung sama tugas.

## Soal Chrome kebanyakan kuasa, kritiknya sah

User HN `advisedwang` ngangkat keberatan paling tajam di thread itu. Menurut dia jalan ini berakhir di web yang cuma boleh dibuka di browser dominan.

Balesannya cepat. `super256` nunjuk daftar kontributor. Philip Walton mastiin Firefox dan Edge memang ikut, tapi ngaku Mozilla baru gabung beberapa minggu terakhir dan belum berpengaruh banyak.

Yang beneran nahan risikonya sih Baseline, standar kompatibilitas lintas browser yang jadi fondasi guide-nya. Fitur yang belum masuk Baseline wajib punya fallback yang didokumentasikan. Guide yang bahas API origin trial malah disembunyiin di balik opt-in lewat file `.mwgrc`.

Itu batasan yang nempel di mesin rekomendasinya. Janji manis lebih murah diucapin, tapi nilainya jauh lebih kecil.

## Kalau gue yang pasang minggu depan

Pasang dengan telemetry mati, terus jalanin scan-nya read-only di branch sebelum ada agent yang nyentuh hasilnya:

```shell
DISABLE_TELEMETRY=1 npx modern-web-guidance@latest install
```

Dua aturan buat putaran pertama:

- anggap temuan `legacy-scan` sebagai kandidat review, jangan langsung dijadiin tiket,
- dan baca bagian fallback di setiap guide yang nyaranin fitur di luar target Baseline lo.

Sisanya, taruh manusia di temuan aksesibilitas. Itu bagian yang selama ini lolos dari semua linter.

Gue jalanin fleet AI coding agents tiap hari di host Celeron, dan yang gue pengen dari mereka justru nahan diri.

Skill yang cuma aktif waktu ada kerjaan layout lalu diem lagi setelahnya jauh lebih berharga buat gue daripada server yang selalu nyala padahal biasanya nggak relevan.

## FAQ

### Skill-nya kepakai tanpa coding agent?

Kepakai. CLI-nya bisa search dan retrieve sendiri, dan pengumuman resminya nyebut kalau developer banyak yang pakai guide-nya buat belajar. Jalanin `npx modern-web-guidance@latest search "..."` sendiri, terus baca hasilnya.

### legacy-scan langsung benerin code gue?

Nggak. Dia cuma nunjuk kandidat lewat analisis statis, terus nyerahin ke agent. Karena rewrite-nya tetap aksi agent, diff-nya wajib lo baca dulu sebelum merge.

### Kalau fiturnya belum masuk Baseline?

Guide buat fitur origin trial dan fitur single-engine yang masih goyang tetap bisa dicari, tapi baru bisa di-retrieve setelah lo opt-in lewat `.mwgrc`. Gate itu ada supaya agent nggak ngadopsi API belum stabil atas nama lo.
