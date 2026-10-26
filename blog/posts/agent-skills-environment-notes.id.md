---
title: Skill Agent Itu Catatan Soal Environment, Bukan Trik Prompt
slug: agent-skills-environment-notes
date: 2026-10-26
excerpt: Argumen "skill AI nggak ada gunanya" itu nembak folklore prompt. Yang jalan di fleet 19 profil lebih mirip catatan operasional, dan tagihan context-nya nyata.
tags: ai-agents, skills, context-engineering, supply-chain, agent-fleet
---

Hari ini tiga repo skill agent naik barengan di GitHub:

- cloudflare/security-audit-skill, 47.315 star
- Nutlope/hallmark, 34.379
- pbakaus/impeccable, 88.034

Angkanya dari GitHub API, gue ambil pagi ini.

Di hari yang sama, satu tulisan berjudul "AI Skills" are worthless in 2026 nyampe ke halaman depan lobste.rs.

Dua-duanya benar. Yang bikin ributnya panjang: orang lagi debat dua benda yang beda.

Yang dijual di marketplace biasanya trik prompt buat model. Yang jalan di fleet gue, 19 profil agent, lebih mirip catatan soal environment tempat model itu eksekusi. Catatan kayak gitu nggak ikut basi waktu modelnya upgrade.

Nah, beda itulah yang nentuin apa yang layak masuk file skill. Sekalian nentuin berapa mahal ongkos yang diam-diam ikut ditagih.

## Ongkos context-nya nyata, dan ada angkanya

Sisi ekonominya nggak salah. Angka di mesin gue malah lebih parah dari keluhannya.

prodigycorp di thread HN soal skill Cloudflare itu nulis begini. "There are way too many skills for the platform." Terus: "The way it is right now pollutes our context window."

Di box ini bentuknya segini:

```bash
find ~/.hermes/profiles -name SKILL.md -not -path '*/.deleted/*' | wc -l
# 1285
```

Sembilan belas profil agent. 1.285 file skill. 13,7 MB markdown.

Total kalau dimuat mentah sekaligus: kira-kira 3,4 juta token.

Nggak ada yang dimuat mentah semua. Harness cuma lihat nama plus satu baris deskripsi dulu, isinya baru dibuka kalau task-nya cocok. Jadi angka jujurnya ada di lapisan deskripsi:

- 77 KB deskripsi
- sekitar 19.000 token
- jarak 177x antara memajang skill dan memakainya

Intinya gini. Rak-nya murah. Label di rak-nya yang mahal.

## Yang nggak bisa ditebak ulang sama model

Tes yang sekarang gue pakai cuma satu pertanyaan. Kalau modelnya lebih pintar, dia bisa nemu sendiri nggak, dengan repo dan pertanyaan yang sama?

Tiga aturan dari pipeline kita sendiri gagal di tes itu:

- Endpoint JSON Reddit di host ini balasnya halaman HTML blokir. Angka komentar yang presisi cuma datang dari HN Algolia, atau nggak sama sekali.
- Tiap URL sumber dicek dulu status HTTP-nya sebelum dikutip. Link mati waktu riset masih bisa dibenerin. Link mati waktu publish udah jadi koreksi publik.
- Nama brand-nya Dagango.com, dieja lengkap tiap kali. Model yang belum pernah lihat codename internal bakal ngarang sesuatu yang kedengeran masuk akal.

Nggak ada satu pun dari itu yang trik buat naklukin model. Semua itu fakta soal host, provider, dan keputusan penamaan. Bobot model nggak bawa informasi itu, dan model yang lebih bagus nggak tiba-tiba jadi tahu.

## Backlash-nya salah alamat, dua lapis

Tulisan Charles Miller lebih bagus dari judulnya.

Contoh pembukanya folklore C: katanya `i++` lebih lambat dari `++i`. Padahal compiler udah bikin itu nggak relevan puluhan tahun lalu.

Dari situ dia geser ke prompt engineering, terus nyampein verdict yang semua orang kutip. Katanya skill yang bisa dipelajari dalam beberapa minggu dan usang beberapa bulan kemudian "has no value outside the moment."

Masalahnya, yang dimaksud Miller dengan "skill" itu bukan file SKILL.md. Di lobste.rs, roryokane angkat tangan dan bilang banyak yang salah tangkap. Yang dimaksud dia skill-nya manusia yang pakai AI.

Jadi argumen yang menyebar itu sebenarnya soal kemampuan orang nulis prompt, cuma kebetulan pakai nama format file.

Setengah tesisnya tetap benar, kok. Apa pun yang cuma soal cara ngerangkai permintaan pasti diserap produk dalam hitungan bulan. Makanya gue berhenti nulis skill yang isinya cara ngomong ke model.

Yang paling berguna di thread itu justru komentar markerz. Skill mestinya ringan. Itu argumen soal budget context, dan itu percakapan yang layak dilanjutin.

## Enam fase, bukan mantra

Skill Cloudflare itu contoh lawannya, dan sayang kalau cuma dibaca sampai angka star-nya.

README-nya bilang terang-terangan. Menurut mereka, skill inilah titik awal harness vulnerability discovery yang sekarang jalan di seluruh fleet.

Alurnya enam fase:

- Rekon: petakan arsitektur, trust boundary, dan input surface ke satu coverage ledger.
- Hunting berbasis coverage: tiap unit di ledger dikasih ke hunter terisolasi.
- Validasi kandidat: tiap temuan diserahin ke verifier baru yang tugasnya nyoba ngebantah.
- Output terstruktur: temuan ditulis sebagai confirmed, needs-validation, atau rejected, lalu divalidasi ke JSON schema.
- Verifikasi independen: agent lain ngecek klaim sumber terakhir.
- Reporting: dokumen diturunin cuma dari record yang udah lewat verifikasi.

Jadi intinya proses review yang ditulis dalam markdown. Prinsip yang bikin proses itu jalan cuma satu kalimat: agent yang ngecek temuan nggak pernah agent yang nemuin.

Pemisahan yang sama gue pakai antara agent coding dan pass QA.

README-nya juga nyatet satu run cuma nemu kira-kira separuh dari yang ditemu beberapa run sekaligus. Itu argumen buat orkestrasi. Bukan argumen buat prompt yang lebih pinter.

## Distribusi bukan berarti percaya

Bagian yang nggak pernah trending: skill itu markdown yang diperlakukan harness sebagai instruksi, dengan privilege lo nempel di situ.

Unit 42 mendokumentasikan versi Juni 2026 dari kegagalan ini di ClawHub.

Satu skill bernama tradingview-ai-indicator-assistant nyisipin blok prasyarat yang nunjuk ke situs paste. User disuruh nempel base64 ke shell. Yang jalan setelahnya infostealer cluw.

Ringkasan laporan mereka sendiri yang layak diinget: "a single malicious skill can grant an attacker full control over the agent's permissions and access to the underlying system."

Synthesia ngasih bukti dari sisi engineering. Percobaan pertama mereka generik.

Satu request polos buat review diff hasilnya, kata mereka, "an OWASP top-ten checklist applied to your code."

Ya udah, mereka bikin skill audit sendiri yang disetel ke stack mereka dan ke jebakan yang khas di codebase mereka.

Orang Synthesia juga lebih rapi ngomongin context daripada thread HN. Scope yang presisi itu bedanya antara agent yang tetap di jalurnya dan agent yang "wandering through unrelated files polluting its context window."

## Yang gue cek sebelum install

Baca filenya itu standar yang rendah, dan tetap aja nyaring hampir semua isi marketplace.

- Baca SKILL.md utuh, jangan cuma deskripsinya. Yang jahat nyimpen payload di langkah setup.
- Grep `curl`, `npx`, dan apa pun yang nulis di luar folder skill.
- Tanya: skill ini aman tanpa sandbox nggak? README Cloudflare bahkan mewajibkan sandbox yang matiin network eksternal sebelum dia berani jalanin kode target.
- Pin versinya, commit ke git. Semua skill yang gue simpen punya riwayat diff.
- Hapus yang dulu lo install buat satu task. Ekor panjang yang nggak kepakai itulah yang ngabisin budget deskripsi.

Aturan yang sama berlaku waktu nulis. Satu pelajaran satu file, dan pelajarannya harus sesuatu yang modelnya pernah salah di mesin ini minimal sekali.

## Yang selamat lewat upgrade model

Skill paling gede di fleet gue 100 KB, sekitar 25.000 token. Isinya jebakan-jebakan dari pipeline riset yang udah jalan berbulan-bulan.

Kelihatan berlebihan buat ukuran prompt pack. Tapi tiap paragrafnya dibayar sama satu kegagalan yang nggak mau gue ulang.

Sebagian besar file skill di fleet itu bakal mati dalam setahun. Dan memang seharusnya.

Yang bertahan justru yang membosankan: host ini ngeblok apa, provider ini nagih apa, produknya namanya apa. Pengetahuan kayak gini lebih cepat basi dibanding compiler, tapi jauh lebih tahan lama dibanding trik prompt mana pun.

Dan kalau model besok pagi jadi jauh lebih pintar, daftar itu nggak berubah. Yang berubah cuma seberapa cepat gue bisa ngecek ulang satu per satu.
