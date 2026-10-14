---
title: Kenapa Fleet Coding AI Gue Mandek Waktu Jalan Bareng
slug: multi-agent-concurrency-bottleneck
date: 2026-10-14
excerpt: Tiga coding agent di satu repo berhenti gagal karena kualitas model. Gagalnya jadi file lock, port yang bentrok, dan race di database. Ini isolasi yang beresin semuanya.
tags: ai-agents, devops, software-engineering, architecture, git
---

## Fleet lo mandek, dan itu bukan soal reasoning

Waktu lo baru pakai satu coding agent, setiap kegagalan biasanya kelihatan kayak masalah reasoning. Wajar kalau reflek pertama kita adalah ngutak-atik prompt, nambahin context, atau upgrade ke model yang lebih pintar.

Tapi dinamika ini berubah total begitu lo mulai menjalankan beberapa agent sekaligus dalam satu repo.

Di fleet kita, dispatch automated review tiba-tiba mati pas jam 05:35 pagi. Log-nya cuma ninggalin satu baris: `duplicate session: main`. Model LLM-nya nggak ada masalah sama sekali. Masalahnya murni ada di runtime: session write guard mendeteksi turn lain yang masih aktif di session yang sama, lalu langsung nolak request baru.

Di titik ini lo bakal sadar: ketika agent lo bertambah banyak, bottleneck utamanya bukan lagi kepintaran model, melainkan sistem operasi di bawahnya.

Fleet agent kita sehari-hari bekerja untuk Dagango.com, monorepo dengan frontend Next.js App Router dan backend FastAPI.

Berikut catatan lapangan dari beberapa bottleneck yang sempat bikin pipeline kita macet parah, beserta lapisan isolasi yang akhirnya membereskan semuanya.

## 1. Satu session cuma boleh punya satu penulis

Platform agent biasanya punya kecenderungan mengarahkan semua task ke satu session chat kanonikal. Buat interaksi personal atau chatting biasa, pendekatan ini memang praktis. Tapi buat sistem fleet yang berjalan paralel, ini resep bencana.

Semua request yang datang bersamaan bakal berebut satu write guard yang sama. Nama error-nya bakal cepat lo hafal di luar kepala:

- `SessionActiveWriteGuardError`
- Response HTTP 409 pada turn terkait
- State error `session_active_turn`
- Pesan mental `duplicate session: main`

Mekanisme locking ini sebenarnya benar karena satu session memang nggak boleh ditulis oleh dua proses sekaligus. Yang keliru adalah arsitektur kita: menaruh banyak agent mandiri di belakang satu session tunggal.

Masalah ini nggak bisa diselesaikan cuma dengan retry loop. Melempar retry ke guard yang masih terkunci cuma bikin antrean baru yang buang-buang token.

Solusinya adalah membuat ephemeral session sekali pakai untuk setiap task yang di-dispatch, dengan penamaan unik:

```bash
SESSION_ID="${PROFILE}-pr${PR_NUM}-$(date +%s)"
hermes -p "$PROFILE" chat -Q --oneshot \
  --session "$SESSION_ID" \
  --query-file "$BRIEF_FILE"
```

Kita sempat membayar mahal untuk kesalahan sepele ini. Review yang macet sempat dikira cuma proses lambat biasa. Begitu dicek, agent-nya cuma meninggalkan file catatan 1.114 byte yang terputus di tengah jalan, dan PR yang harusnya diaudit malah lolos tanpa review sama sekali.

## 2. Port jaringan adalah shared resource

File dan folder di disk bisa lo pisah per agent, tapi network socket nggak bisa.

Awalnya, proses QA otomatis kita memakai port statis yang di-hardcode. Satu run memakai backend di port 8012 dan frontend di 3312, sementara run berikutnya memakai port 8003 dan 3303. Setup ini aman selama pengujian dijalankan bergiliran satu per satu.

Begitu ada dua QA run jalan berbarengan, cuma ada dua kemungkinan yang terjadi:

- Server kedua langsung crash dengan error `EADDRINUSE`.
- Skenario yang jauh lebih berbahaya: server kedua gagal bind, tapi diam-diam numpang ke server pertama yang sudah jalan.

Skenario kedua ini jebakan paling licin. Laporan QA keluar dengan status hijau dan semua test lulus, padahal kode yang baru saja diuji adalah build lama milik task sebelumnya.

Solusinya, turunkan port server secara deterministik dari nomor PR atau ID task:

```bash
BACKEND_PORT=$((8100 + PR_NUM))
FRONTEND_PORT=$((3400 + PR_NUM))
```

Pola jebakan serupa juga sering muncul di config Playwright lewat flag `reuseExistingServer`. Di lingkungan multi-agent, flag ini cuma bikin agent lo ngetes server random yang kebetulan lagi nyala. Kunci port-nya ke port unik masing-masing, atau matikan opsi itu sama sekali.

## 3. Dua runner, satu database

Ini jenis kegagalan yang paling banyak membuang waktu investigasi, karena gejalanya mirip banget sama bug aplikasi.

Bayangkan dua runner QA mulai bekerja di detik yang sama. Keduanya menjalankan migration, lalu keduanya menyuntikkan data fixture ke satu instance PostgreSQL staging yang sama.

Eksekusinya langsung jadi non-deterministik. Test yang jam 10:00 lulus bisa mendadak gagal jam 10:05 tanpa ada satu baris kode pun yang berubah. Penyebabnya sepele: runner sebelah baru saja menjalankan `TRUNCATE` pada tabel yang lagi dibaca runner pertama.

Lo bisa habis seharian mengira kode lo yang bermasalah.

Solusinya adalah memberikan database terisolasi untuk setiap run. Database dibuat otomatis sebelum agent mulai, dan di-drop begitu verifikasi tuntas:

```bash
TEST_DB_NAME="dagango_test_${PR_NUM}"
createdb "$TEST_DB_NAME"
```

Satu catatan penting: sekadar menyalin file `.env` ke direktori baru belum cukup. Connection string di dalamnya wajib diarahkan ke database per-run tadi, kalau nggak agent lo bakal diam-diam tetap nyambung ke database shared.

## 4. Satu repositori, satu git index

Ini titik di mana kerjaan lo bisa hilang tanpa ada jejak suara.

Kalau lo membiarkan dua agent bekerja di dalam satu working tree yang sama, mereka bakal tabrakan di hampir semua operasi Git. File index `.git/index` adalah shared state tunggal. Perintah `git checkout` di satu agent bisa langsung menimpa uncommitted change milik agent lain, dan `reflog` jadi satu-satunya harapan buat menyelamatkan kode lo.

Daftar bencananya panjang banget kalau direktori kerja dibagi barengan:

- `git checkout` menimpa file yang belum sempat di-commit agent lain.
- Perintah `git stash` saling bertumpuk dan rawan salah pop.
- `npm ci` atau install package nulis ke folder `node_modules` barengan sampai lockfile rusak.
- Build frontend paralel mencampur source code dua branch ke dalam satu bundle output.

Jawaban struktural untuk masalah ini adalah `git worktree`. Repositori tetap memakai satu object database Git yang sama, tapi tiap agent mendapatkan working directory, file index, dan branch terpisah:

```bash
git worktree add --detach /home/aditf/e2e-verify/wt-pr105 fix/gate-checkout
```

Git punya satu aturan bawaan yang sangat membantu: satu branch cuma boleh di-checkout di satu worktree. Artinya, filesystem itu sendiri yang mencegah dua agent mengutak-atik branch yang sama.

Dua hal yang perlu diperhatikan saat memakai worktree:

- File yang ada di `.gitignore` seperti `.env` nggak otomatis ikut disalin ke worktree baru, jadi harus di-copy manual saat inisialisasi.
- Worktree bakal terus menumpuk di disk kalau nggak dirapikan. Pastikan ada proses cleanup otomatis atau pruning berkala setelah PR selesai.

## Lapisan yang sering terlewat: browser session

Verifikasi visual via browser adalah lapisan kelima, dan ini sering kali memproduksi bukti palsu tanpa kita sadari.

Dua agent yang mengontrol Chrome lewat Chrome DevTools Protocol (CDP) secara default bakal berbagi cookie jar dan local storage yang sama. Keduanya juga berbagi daftar tab aktif. Ketika Agent B membuka halaman login admin, assertion milik Agent A yang lagi menguji landing page storefront bisa nyasar ke tab milik Agent B.

Solusinya, isolasi sesi browser secara eksplisit di level perintah pengujian:

```
browser_exec(session="pr-<PR_NUM>")
```

Perubahannya cuma satu parameter, tapi dampaknya masif. Tanpa isolasi ini, audit accessibility atau screenshot UI yang lo anggap valid bisa jadi cuma memotret halaman milik task lain.

## Kesimpulan: isolasi itu paket lengkap

Arsitektur untuk mengatasi semua ini sebenarnya sederhana dan bisa diringkas ke dalam satu script dispatch:

- Session ID sementara yang unik per dispatch.
- Port server yang dihitung dari nomor PR.
- Database terisolasi per pengujian.
- Git worktree khusus untuk tiap agent.
- Browser session terpisah untuk visual QA.

Kelima lapisan ini menangani jenis shared resource yang berbeda, tanpa ada yang tumpang tindih. Kalau lo cuma membereskan tiga di antaranya, lapisan keempat bakal tetap jebol dan bikin pipeline lo mogok lagi.

Sebelum lo menambah agent baru ke dalam tim, bereskan dulu isolasi infrastrukturnya dari awal. Jauh lebih murah menyiapkan lima baris bash script di awal daripada menghabiskan waktu berhari-hari mendebug race condition yang cuma muncul saat dua agent jalan barengan. 😅
