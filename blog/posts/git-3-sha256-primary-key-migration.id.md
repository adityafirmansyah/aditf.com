---
title: Default SHA-256 di Git 3.0 Itu Migrasi Primary Key
slug: git-3-sha256-primary-key-migration
date: 2026-10-02
excerpt: Gue bikin repo SHA-256 pakai git yang udah keinstall di laptop ini. Dua dari tiga hal yang gue lakuin tiap hari ke repo langsung gagal, dan yang ketiga dijamin mati di client lama. Yang mahal bukan hash-nya, tapi key-nya.
tags: git, developer-tooling, migrations, version-control, storage
---

## Ributnya soal hash. Tagihannya soal key.

Post-nya Scott Chacon, "Git 3.0's upcoming SHA-256 default will be a costly mistake", lagi nangkring di front page Hacker News: 364 poin, sekitar 350 komentar. Hampir semua isi thread-nya debat soal fungsi hash.

Bukan di situ duitnya.

Setuju sama hitungan biayanya, tapi nggak setuju dramanya. SHA-256 memang hash yang benar buat jangka panjang, dan cepat atau lambat dia harus jadi default. Tapi yang bikin mahal itu bukan sisi kriptografinya sama sekali.

Commit hash udah lama berhenti jadi sekadar ID internal doang di repo ini. Dia itu primary key, dan foreign key-nya nyebar di semua API forge, config CI, script release, permalink, sampai thread Slack di grup kantor.

Kalau key-nya sekaligus jadi interface publik, ganti key itu bukan migrasi index. Itu migrasi ekosistem.

Biar nggak cuma ngomong dari bacaan, gue luangin satu menit buka shell. Git yang keinstall di mesin ini 2.53.0, dan buat nguji ini udah lebih dari cukup.

## Satu menit di shell, hampir semua argumennya udah kelar

Langkah pertama, bikin repo SHA-256 terus commit satu file:

```bash
git init --object-format=sha256 s256
cd s256 && echo hi > a.txt && git add a.txt && git commit -m first

git rev-parse HEAD
# 5a14a64b8b6e5d545d946d1284b5f422502e8af6fcfde892185d7e6cb1f30e4b
git rev-parse --short HEAD
# 5a14a64
```

Nama lengkapnya 64 karakter hex. Repo SHA-1 di mesin yang sama nyebut commit-nya dengan 40 karakter. Versi pendeknya tujuh karakter di dua-duanya, jadi output `--short` selamat dan yang nggak selamat justru nama lengkapnya.

Terus gue lakuin tiga hal yang tiap hari gue kerjain ke repo.

- **Push.** Ke bare repo yang dibikin pakai `git init --bare --object-format=sha256`, push-nya lancar. Ke `git init --bare` biasa, mati dengan exit 128 dan `fatal: the receiving end does not support this repository's hash algorithm`.
- **Push lintas format.** Repo SHA-256 yang nge-push ke bare repo SHA-1 gagal dengan cara yang sama, exit 128, plus `fatal: the remote end hung up unexpectedly`.
- **Submodule.** Nambahin repo SHA-256 sebagai submodule di superproject SHA-1 gagal dengan `error: cannot add a submodule of a different hash algorithm`.

Dua dari tiga langsung gagal. Yang pertama justru yang paling penting: repo penerimanya harus tahu format hash sejak `init`.

Elo nggak bisa nge-push repo SHA-256 ke repo yang udah berdiri sebagai SHA-1. Format itu bukan sifat object-nya, tapi sifat repo-nya.

## Pintu satu arahnya ada di versi format

Repo SHA-256 nulis dua baris ini ke `.git/config`:

```
[core]
	repositoryformatversion = 1
[extensions]
	objectformat = sha256
```

Dokumen transisinya tegas soal alasan dua baris itu ada. Setelan itu bikin semua versi Git setelah v0.99.9l mati, dan nggak nekat jalan di repo SHA-256.

Antara v0.99.9l dan v2.7.0 errornya `fatal: Expected git repo version <= 0, found 1`. Lewat v2.7.0, pesannya berubah jadi `fatal: unknown repository extensions found: objectformat compatobjectformat`. Nggak ada jalan tengah yang bikin versi lama tadi bisa baca.

Itu bukan feature flag yang bisa dinyalain tiap tim sesuai jadwal sendiri. Client lama nggak bisa baca repo-nya sama sekali, dan itu naruh semua consumer di satu sisi garis.

## Setengah debat di thread itu udah dijawab dokumennya

Klaim "nggak bisa di-push ke mana-mana" di thread kebaca kayak bug report. Dokumen transisinya bilang itu keadaan sementara, dan jembatannya dijelasin cukup detail.

Jembatannya berupa tabel mapping dua arah antara nama object SHA-256 dan SHA-1, dibikin lokal dan bisa dicek pakai `git fsck`, plus setelan `extensions.compatObjectFormat`. Object bisa dipanggil pakai nama 40 karakter atau 64 karakter.

Fetch dari server SHA-1 dikonversi ke bentuk SHA-256 sambil nyatet mapping-nya. Push ke server SHA-1 dikonversi di jalan keluar, jadi servernya nggak pernah tahu client-nya pakai hash apa.

Yang masuk daftar di luar cakupan justru bagian yang kelewat di thread:

- intermixing object yang pakai beberapa fungsi hash dalam satu repo;
- shallow clone dan fetch ke repo SHA-256;
- nge-skip fetch sebagian submodule;
- minjem object dari repo SHA-1 lewat `objects/info/alternates`;
- migrasi tree `git notes` ke nama SHA-256;
- dukungan SHA-256 di protokol Git-nya sendiri.

Jadi yang diperdebatkan bukan ada atau nggaknya keadaan sementara. Yang diperdebatkan biayanya, dan dokumennya nutup bagian itu dengan tegas: "Until Git protocol gains SHA-256 support, using SHA-256 based storage on public-facing Git servers is strongly discouraged."

## Yang sebenernya jebol, dan bukan fungsi hash-nya

Daftar biaya dari Chacon itu yang paling konkret. Baca aja sebagai inventaris titik interface, bukan sebagai teror.

- Tiap repo di forge masuk ke satu keranjang atau keranjang lain, dan dua keranjang itu nggak bisa dicampur.
- Submodule butuh dua sisi yang formatnya sama, persis kayak command ketiga di atas.
- Konversi project yang udah jalan berarti hash ulang semua object dan semua signature lama jadi nggak berlaku.
- Permalink yang bawa hash lengkap di Slack, email dan dokumen berhenti ngebuka.
- Tooling apa pun yang nunggu 40 karakter buat hash harus nebak atau deteksi formatnya.

Yang terakhir itu kalimatnya dia sendiri, dan mesin gue sampel kecilnya. Ada sepuluh repo, semuanya SHA-1, dan nggak ada satu pun yang punya key `objectformat` di `.git/config`.

Di hari Git 3.0, tiap repo jadi satu keputusan. Tiap script, hook, dan integrasi yang baca hash ikut masuk ke keputusan itu.

## Bantahan-bantahannya, sama namanya

`ltbarcly3` nyebut ini "Y2K fud", dan dia bikin kasus terkuat buat sisi seberang. Alternatifnya ya tetep SHA-1 sampai jadi kritis, terus semua orang pindah di hari yang sama, sementara forge yang nggak pernah kepaksa implement SHA-256 ikut kena.

`plorkyeran` nunjuk kalau masalah forge itu soal pilihan implementasi, bukan sifat hash. `GrantMoyer` nyantumin dokumen transisinya dan nyebut beberapa kekhawatiran penulisnya udah dijawab di situ.

`gorgoiler` nyadar hal yang sama dari arah sebaliknya: mapping dua arah itu justru interoperabilitas yang diklaim post-nya nggak ada.

Di sisi trust, `Strilanc` nolak framing-nya mentah-mentah, dan `mort96` ngejelasin kasus mirror plus tooling: "I deal with things which reference commits by hash in repos all the damn time. There are thousands of them in every Yocto project!"

## Usulan yang dilewatin thread

Bagian konstruktif dari post-nya: tree hash yang ditandatangani terpisah. Konten tree di-hash ulang pakai algoritma kedua, terus dua-duanya ikut ditandatangani, jadi SHA-1 tetap buat ambil konten dan hash kedua buat verifikasi.

Git-evtag punya Colin Walters udah kayak gitu sejak 2015: nambahin checksum `Git-EVTag-v0-SHA512` di atas commit, tree, dan tiap blob ke tag-nya sebelum ditandatangani.

`SmasherEpilepti` nyebut ini paling pas di thread: bagian paling menarik dari artikelnya, tapi paling sedikit dapat perhatian. Argumen dasarnya udah dibikin Linus di 2005 dan dikutip Chacon: keamanan yang asli ada di distribusi, bukan di hash-nya.

## Bentuk yang sama, storage yang beda

Cerita front page lain di hari yang sama, "RIP, vector database" dari turbopuffer, itu pelajaran yang sama dari sisi index. Di v1 dan v2, tiap dokumen disimpan di bawah ANN address-nya. Waktu SPFresh nge-balance ulang vektor, seluruh dokumennya ikut pindah, dan update satu vektor bisa mindahin ratusan atribut sekalian index-nya.

Fix di v3 dibilang datar: jangan pakai ANN address sebagai key. ANN index-nya jadi sekadar secondary index. Posting list full-text mereka berubah dari median sekitar 1,5 entri per blok jadi blok tetap sekitar 256, dan index-nya jadi sepuluh kali lebih kecil sementara query-nya sampai dua puluh kali lebih cepat.

Skalanya bikin poinnya soal biaya: 1T+ dokumen, 10M+ writes per detik, 25k+ query per detik, single index 100B+ vektor dengan 200 ms p99 di 1k+ QPS.

Itu tanda terima dari harga sebuah key yang diam-diam udah jadi interface.

## Yang gue lakuin sebelum hari Git 3.0

Intinya bukan "hindari SHA-256", dan bukan juga "tunggu ada yang mutusin duluan". Asumsi soal format hash sekarang jadi inventaris, jadi tulis aja.

- Jalanin reproduksi di atas di direktori sementara, pakai git yang beneran lo pakai.
- Grep pipeline-nya buat asumsi hash 40 karakter, plus kode yang motong atau bandingin hash.
- Cek `git config --get extensions.objectformat` di semua repo dan catet format masing-masing.
- Tanyain consumer mana yang nggak bisa lo update sesuai jadwal lo, karena mereka yang dikunci baris `repositoryformatversion = 1`.

Satu baris config bisa ganti fungsi hash. Tapi key yang dibangun di atasnya itu interface yang dipakai tooling sepuluh tahun.

Yang mahal migrasi yang kedua, dan langkah pintarnya tahu besar tagihannya sebelum default-nya keburu ganti di bawah kita.
