---
title: "Gue Reproduce Serangan .git Hook: git status Ternyata Jalanin Kode Penyerang"
slug: reproducing-the-git-hook-attack
date: 2026-10-05
excerpt: Penyerang ngirim folder Dropbox berisi .git tersembunyi, terus minta "pindah ke branch NDA". Satu git checkout itu cukup buat jalanin kode mereka. Gue reproduce semuanya di git 2.53.0, dan mitigasi populer-nya nggak sekuat kelihatannya.
tags: git, security, ai-agents, supply-chain, devtools
---

## Permintaannya sendiri yang jadi payload

Frank Wiles dapet tawaran proyek yang kelihatan biasa banget. Aplikasi web buat Ed Tech, NDA dulu sebelum meeting, spec-nya nongkrong di folder Dropbox.

Dia buka foldernya.

Terus "klien"-nya bilang: NDA-nya ada di branch NDA, tinggal pindah ke situ. Pindah ke branch NDA itu ya artinya `git checkout`.

Di situ seluruh serangannya.

Tulisannya sekarang jadi item paling atas di lobste.rs, dengan 129 poin dan 39 komentar.

Ini bukan cerita soal satu kontraktor yang kurang hati-hati. Ini soal satu perintah yang semua orang anggap aman.

Kita pikir `git checkout` cuma baca, padahal dia jalanin kode.

## Yang jalan waktu dia pindah branch

Wiles kelewat folder `.git` yang nyempil di Dropbox itu.

Di dalamnya ada hook `post-checkout`.

Kata dia sendiri, hook itu nyambung ke app Vercel buat command and control dan bakal "download an OS specific binary", jalanin, terus hapus dirinya sendiri.

Dia lapor ke tim security Dropbox dan Vercel, sambil menduga targetnya akun GitHub plus akses ke klien-kliennya.

Nggak ada bug git di sini. Dokumentasinya bilang gamblang: `post-checkout` "is invoked when a git-checkout or git-switch is run after having updated the worktree."

File di `.git/hooks/` itu kode yang git siap jalanin buat lo.

## Reproduksi 1: checkout jalanin hook-nya

Gue penasaran seberapa nyata ini di git versi sekarang, jadi gue bikin sendiri. Satu repo, satu branch, satu hook yang nyatet argumennya:

```sh
# .git/hooks/post-checkout
#!/bin/sh
echo "ran: args=$# prev=$1 new=$2 flag=$3" >> hook.log
```

Terus gue jalanin langkah yang persis diminta penyerang:

```
$ git checkout nda
Switched to branch 'nda'
$ cat hook.log
ran: args=3 prev=3dfc32704f4b... new=3dfc32704f4b... flag=1
```

Jalan di git 2.53.0. Tiga argumen, sama kayak di dokumentasi: HEAD sebelumnya, HEAD baru, dan flag checkout branch.

Yang penting justru yang nggak kelihatan.

`git status` tetap bersih. `git ls-files` cuma nunjukin `README.md`.

Hook-nya hidup di dalam `.git`, jadi dia nggak akan pernah muncul di diff, di review, atau di listing folder.

## Reproduksi 2: git status juga jalanin config lo

Hook butuh lo buat pindah branch. Tapi komentar paling atas di thread lobste.rs malah sama sekali nggak butuh aksi dari lo.

User agwa nulis soal nyimpen `.git/config` dengan `core.fsmonitor` diarahin ke sebuah command. Command itu terus jalan di "very basic ones like `git status`."

Gue juga tes sendiri di repo gue. Path script di `.git/config`, terus `git status` biasa:

```
$ git config core.fsmonitor /path/to/fsmon.sh
$ git status
$ cat fs.log
FSMONITOR EXECUTED args=2 1791180551388075699
```

Ini yang lebih bahaya, karena `git status` itu perintah yang editor, build script, dan agent lo jalanin tanpa mikir.

Daftar agwa tegas: IDE, `go build`, dan integrasi shell prompt, semuanya jalanin itu diam-diam.

Dokumentasi git ngasih tahu kenapa path itu bahaya: `core.fsmonitor` "was extended to allow boolean values in addition to hook pathnames."

Artinya sebuah path itu command. Dan client versi lama bisa salah baca bahkan `true` sebagai command.

## Kenapa clone aman dan folder Dropbox nggak

Ada satu batas yang nentuin lo kena atau nggak, dan batasnya lebih sempit dari yang orang kira.

git nggak mau naruh path `.git/` di dalam tree. Gue coba lewat jalur plumbing:

```
$ git update-index --add --cacheinfo 100755,<blob>,.git/hooks/post-checkout
error: Invalid path '.git/hooks/post-checkout'
fatal: git update-index: --cacheinfo cannot add .git/hooks/post-checkout
```

`git add` biasa malah nggak ngapa-ngapain, diam-diam aja. Jadi hook nggak bisa ikut lewat commit.

Clone baru dari repo gue yang udah dijebak cuma dapet file `*.sample`. Checkout di situ nggak jalanin apa-apa.

agwa narik garisnya persis kayak gimana proyek git narik garisnya. Cloning itu "in fact the only safe way to get a repo from an untrusted source."

Clone yang jahat dihitung sebagai vulnerability. Tarball yang jahat dihitung sebagai masalah lo sendiri.

Jadi ada tiga kasus:

- **Clone dari URL.** git yang checkout buat lo, aman.
- **Ekstrak zip atau tarball.** `.git`-nya udah ada di dalam. Ini jalur yang berbahaya.
- **Buka folder kiriman orang.** Kasus Wiles. Nggak ada clone, nggak ada pengecekan.

z3bra di thread itu nabrak tembok yang sama dari sisi lain. Clone dari repo yang nyoba ngirim `.git/hooks/post-checkout` mati dengan `fatal: unable to checkout working tree`.

vifon nambahin satu pengecualian yang perlu lo tahu. `git bundle` asli itu aman, karena clone dari situ nggak akan checkout file-file itu.

## Mitigasi paling populer ternyata bisa diakalin

Fix yang paling banyak di-upvote itu dari arialdo. Matiin hook sepenuhnya pakai `git config --global core.hooksPath /dev/null`.

Niatnya bagus, tapi nggak nahan.

oger udah nebak lubangnya duluan, dan gue reproduce sendiri di repo gue. Dengan setting global itu terpasang, hook-nya diam. Terus satu baris di config repo:

```
[core]
    hooksPath = .git/hooks
```

Hook-nya jalan lagi. Config repo ngalahin config global, jadi repo yang jahat bisa nyalain ulang dirinya sendiri.

Yang nahan itu bentuk per-command. Config dari command line dipakai paling akhir:

```
$ git -c core.hooksPath=/dev/null checkout nda
$ git -c core.fsmonitor=false status
```

Dua-duanya berhasil ngeblok eksekusi di repo yang jahat. Dokumentasi git-config malah nyaranin bentuk ini langsung, ditulis sebagai `git -c core.hooksPath=/dev/null`.

## Kenapa agent lo lebih rentan

Gue jalanin fleet 17 profil agent. Agent coding, QA, dan PR-review nge-clone repo terus jalanin `git status` dan `git checkout` tanpa diawasi, dengan kredensial git nempel di environment.

Itu persis yang dicari penyerang: akses ke akun dan klien-kliennya.

Serangan ini lebih cocok buat agent daripada buat manusia. Agent sering dikasih repo dalam bentuk folder atau tarball, bukan hasil clone.

Dia jalanin `git status` terus-terusan. Dan nggak ada apa pun di konteksnya yang lagi nyari folder `.git`.

Harden-nya singkat:

- **Clone, jangan copy.** Kalau memang harus mindahin repo, clone terus hapus sumbernya.
- **Suntik dua flag itu.** Taruh `-c core.hooksPath=/dev/null -c core.fsmonitor=false` di git wrapper agent lo.
- **Sandbox kredensialnya.** Jalanin git agent di container dengan token yang scoped dan umurnya pendek.
- **Periksa dulu sebelum command pertama.** Cek `.git/hooks` dan `.git/config` di setiap repo yang datang dari pihak ketiga.

Kalimat loldot di thread itu jadi default yang bener: "I just consider everything project someone sends me as a malicious."

benoliver999 nyatet bentuk yang sama juga nongol di bundle take-home interview yang bawa `.git`.

## Intinya

`git checkout` bukan operasi baca. Dia program loader dengan tampilan yang familiar, dan `git status` juga bisa jadi begitu.

Solusinya bukan flag global yang pintar, karena sebuah repo bisa ngelawan lo buat ngerebut config-nya sendiri.

Clone apa pun yang nggak lo percaya. Jangan pernah copy.

Dan kalau ada yang bilang NDA-nya ada di sebuah branch, tanya kenapa dia butuh lo buat jalanin checkout.

Kalau gue tarik ke konteks gue sendiri: fleet agent gue nge-clone repo tiap hari, dan hampir semuanya datang dari sumber yang nggak gue periksa satu-satu. Yang bikin gue tenang cuma satu hal, yaitu semua clone-nya lewat jalur yang bener.

Begitu ada satu saja yang dikasih dalam bentuk zip atau folder Dropbox, dan ada agent yang jalanin `git status` di situ, seluruh aturan mainnya berubah.

Jadi aturan gue sekarang sederhana: apa pun yang nggak datang dari `git clone`, gue anggap asing sampai gue periksa sendiri.

Sisanya gue perlakukan seperti kode asing. Diperiksa dulu, baru dijalanin. Nggak ada yang namanya "cuma lihat-lihat dulu" di repo yang nggak lo percaya.