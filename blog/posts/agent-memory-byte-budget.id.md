---
title: Memori Agent Nggak Butuh Skema, Butuh Plafon Byte
slug: agent-memory-byte-budget
date: 2026-11-09
excerpt: Standarisasi format memori agent menyelesaikan lapisan yang salah. Yang bikin model bodoh itu store yang nggak pernah membuang apa pun, dan plafon byte plus skills on-demand lebih ampuh daripada skema bersama.
tags: ai-agents, llm-tooling, system-architecture, devops
---

Memori agent itu butuh momen OpenTelemetry-nya. Itu argumen Mads Thines di tulisan yang terbit 7 November 2026.

Dia memetakan sembilan format yang nggak bisa saling baca, lalu menarik paralel ke observability pra-2019.

Diagnosisnya benar.

Resepnya nyasar ke lapisan yang salah. Yang bikin orang ngamuk soal memori agent itu sebagian besar soal eviction, bukan soal serialisasi.

Agent nulis satu keputusan debugging yang cuma berlaku seminggu, store-nya nggak pernah lupa, terus sesi berikutnya baca balik sebagai aturan tetap. Itu bisa lo hentikan malam ini juga pakai plafon byte. Skema bersama cuma menyeragamkan bentuk kekacauannya.

## Yang sebenarnya disepakati OpenTelemetry

Bagian paling berguna dari tulisan itu justru tabelnya. Sembilan keluarga memori diurutkan, dari file Markdown di path tetap sampai graph dengan dua timeline. Baca kolom Forgetting:

```
format                        unit memori                   lupa kapan
AGENTS.md / CLAUDE.md         satu file Markdown utuh       nggak pernah, diedit manusia
memory tool Anthropic         file di bawah /memories       hanya kalau model menghapusnya
Copilot Memory                fakta plus sitasi kode        28 hari nggak dipakai
Letta core memory             block berlabel, ada batas     nggak pernah
Mem0                          fakta hasil ekstraksi         tanggal kedaluwarsa opsional
LangGraph BaseStore           nilai JSON di namespace+key   TTL opsional
MCP reference memory server   entitas dan relasi            nggak pernah
Graphiti / Zep                fakta di edge graph           di-invalidate, bukan dihapus
LoreKit                       record dengan scope dan key   hanya kalau TTL dipasang
```

Empat dari sembilan punya mekanisme kedaluwarsa, permanen atau opsional. Yang kelima, Graphiti, membatalkan fakta tanpa menghapusnya. Sisanya empat lagi nggak pernah lupa, kecuali ada manusia atau model yang balik dan mencabut entrinya satu per satu.

OpenTelemetry dulu menyepakati empat lapisan: data model, semantic conventions, protokol wire, dan SDK referensi. Vendor tetap bersaing di storage dan query. Data model-nya yang berhasil, dan alasannya nggak keren sama sekali.

Span dibaca mesin yang mengindeksnya, sementara catatan memori dibaca oleh atensi model. Jadi setiap token metadata tambahan itu langsung memakan jatah buat bernalar.

## Keluhannya sebenarnya soal eviction

Thread Hacker News-nya sampai 105 komentar, dan isinya soal operasional semua. Nggak ada yang berdebat soal estetika.

`slopinthebag` yang buka suara: "at this point i'm pretty convinced agent memory is strictly harmful. it remembers the wrong things, and then turns them into an inane focus for each task."

`SwellJoe` setuju: "Everybody builds one, and then eventually realizes it makes the model stupid and confused."

`Kwpolska` yang paling jelas menyebut mekanismenya. Claude Code sering nulis keputusan sekali pakai dan masalah sesaat ke memori, terus sesi berikutnya bertindak berdasarkan konteks yang sebenarnya nggak pernah berlaku umum.

`nonethewiser` nyebut efeknya confirmation bias, dan menaksir catatan yang nggak pernah ditinjau itu paling banter 90% benar.

Nggak ada satu pun dari mereka yang minta wire format. Semuanya lagi mendeskripsikan satu entri yang seharusnya sudah dibuang tapi masih hidup.

## Anthropic kasih angkanya

Tulisan riset Anthropic soal komponen memori agent cukup blak-blakan: "Injected memories use up valuable tokens, and an incorrect note can be carried into every session."

Di bagian yang sama mereka nambahin satu hal yang sering dilewatkan. Catatan yang berhasil dimuat belum tentu dipatuhi, karena file instruksi yang makin panjang justru menurunkan tingkat kepatuhan model.

Mitigasinya ada di dalam produk. Claude Code cuma memuat 200 baris pertama atau 25 KB dari MEMORY.md. `troupo` mengutip batas itu di thread buat nunjukin bahwa file-file ini lebih sering diabaikan daripada dipatuhi.

Dua mode kegagalan, satu obat: jaga lapisan yang di-inject tetap kecil.

## Tiga tingkat di satu mesin

Fleet gue jalan di sembilan belas profil agent di mesin ini, dengan 1.392 file SKILL.md, antara 58 sampai 166 per profil. Tiga belas dari sembilan belas juga punya `memories/MEMORY.md`. Ukurannya dari 594 byte di viral-researcher sampai 8.985 byte di cto, dan store profil root ada di 9.040 byte.

Konteksnya dibagi tiga tingkat:

```
SOUL.md              identitas dan aturan keras, dimuat tiap sesi
skills/**/SKILL.md   runbook prosedural, dimuat saat trigger cocok
memories/MEMORY.md   fakta, dibatasi dan dikonsolidasi saat ditulis
```

Yang menahan semuanya ya plafonnya. Bukan skemanya dan bukan nama field-nya.

Kalau store penuh, penulisan gagal. Agent jadi harus mengonsolidasi atau menghapus dulu sebelum bisa menambah apa pun. Tiga profil di sini pasang batas eksplisit 6.000 atau 9.000 karakter. Sisanya jalan di default 2.200 karakter.

Di 2.200 karakter, kosakata satu sesi cepat habis. Itu justru intinya. Model dipaksa memutuskan apa yang layak bertahan, dan keputusan itu diambil selagi tugasnya masih ada di depan mata.

Satu efek samping yang nggak kelihatan dari luar: penuh itu nggak terasa sampai ada penambahan yang ditolak. Di titik itu isi store-nya dikirim balik utuh ke agent. Pilihannya cuma dua, dan dua-duanya nggak nyaman: rapikan sekarang atau nggak menyimpan apa pun sama sekali.

Menurut gue justru momen dipaksa itu yang bikin kualitasnya naik. Selama store masih longgar, agent bakal hafal semua hal sepele karena nggak ada biaya untuk itu.

## Plafon byte lebih penting daripada metadata

Record LoreKit menambahkan persis field yang dibutuhkan format bersama: address, key, lifecycle, dan written_by.

written_by ide paling tajam di proposal itu. Pembaca jadi bisa menimbang sebuah catatan dari siapa yang menulisnya, dan fakta hasil ekstraksi service jelas lebih lemah daripada direktif yang diketik manusia.

Masalahnya, metadata nggak bisa mengeksekusi apa pun. Record yang mendeklarasikan tanggal kedaluwarsa tetap butuh sesuatu yang menegakkan tanggal itu. Nggak ada format yang bisa memutuskan sendiri bahwa shortcut debugging bulan lalu sudah nggak berlaku.

Plafon byte memaksa penilaian itu terjadi di saat penulisan. Itu satu-satunya momen ketika konteksnya masih utuh di depan model.

Tapi plafon juga bukan pengganti kurasi manual. Sesekali file-file ini tetap harus dibuka dan dibaca dari atas ke bawah oleh manusia, bukan cuma dipercaya ke agent yang menulisnya.

Kalau nggak pernah dibuka, agent cuma mengonsolidasi isi yang sudah salah sejak awal, dan hasilnya sampah yang lebih rapi. Rapi tapi tetap salah.

Bagian ini yang paling susah dijual sebagai fitur, karena nggak bisa diotomatiskan penuh.

## Yang gue ambil sekarang, standar atau belum

Ada tiga bagian proposal yang layak dibangun dari sekarang:

- Konvensi untuk level address dan namespace atribut, supaya dua tool bisa mendeskripsikan repo yang sama tanpa lapisan penerjemah.
- Conformance test sebagai pengganti implementasi referensi, karena test suite tetap hidup walau lapisan storage-nya ditulis ulang.
- Live addressing antar tool yang jalan bersamaan, bagian yang lebih sulit dan yang paling sering dilewatkan proposal yang sudah ada.

Soal poin ketiga, karya yang ada sekarang jujur soal cakupannya. Bundle `.mem` dari MacPaw, draft Open Memory Protocol, dan COGX dari Cognee semuanya fokus di export: memindahkan memori satu orang dari vendor A ke vendor B. CI job, editor agent, dan review bot yang baca record yang sama di waktu bersamaan masih belum ada jawabannya.

Jadi seragamkan kosakatanya, jangan storage-nya. Pasang plafon byte untuk apa pun yang di-inject ke tiap sesi, dan pindahkan prosedur ke file yang baru dimuat saat trigger-nya kena.

Format memori yang nggak punya jalur lupa itu ya format yang mengirim context rot sebagai bawaan. Menurut gue itu yang perlu distandarkan lebih dulu, sebelum kita sibuk sepakat soal nama field. 😅
