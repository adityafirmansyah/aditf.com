---
title: "Gue Reproduce Serangan .git Hook: git status Ternyata Jalanin Kode Penyerang"
slug: reproducing-the-git-hook-attack
date: 2026-10-05
excerpt: Penyerang ngirim folder Dropbox berisi .git tersembunyi, terus minta "pindah ke branch NDA". Satu git checkout itu cukup buat jalanin kode mereka. Gue reproduce semuanya di git 2.53.0, dan mitigasi populer-nya nggak sekuat kelihatannya.
tags: git, security, ai-agents, supply-chain, devtools
---

## Permintaannya sendiri yang jadi payload

Frank Wiles dapet tawaran proyek yang kelihatan biasa banget. Sebuah perusahaan Ed Tech mau bikin web app, minta dia tanda tangan NDA dulu sebelum meeting, dan nitip spec-nya di sebuah folder Dropbox.

Dia buka foldernya.

Di dalamnya, si "klien" udah ninggalin catatan: NDA-nya ada di branch NDA, dan dia cuma perlu pindah ke situ. Instruksi itu sendiri yang jadi serangan utuhnya.

Pindah branch artinya jalanin `git checkout`, dan `git checkout` jalanin kode.

Tulisan yang dia publikasiin setelahnya sekarang jadi item paling atas di lobste.rs, dengan 129 poin dan 39 komentar.

Ini bukan cerita soal satu kontraktor yang kurang hati-hati, karena siapa pun bisa kena.

Hampir semua developer baca `git checkout` sebagai operasi baca yang aman, padahal perintah itu bisa jalanin kode di mesin mereka.

## Yang jalan waktu dia pindah branch

Wiles kelewat folder `.git` yang nyempil di folder Dropbox itu, dan justru di situ serangannya bersembunyi.

Di dalamnya ada hook `post-checkout` yang nyambung ke app Vercel buat command and control.

Kata dia sendiri, hook itu bakal "download an OS specific binary" yang cocok sama mesin lo, jalanin, terus hapus dirinya sendiri.

Dia lapor ke tim security Dropbox dan Vercel setelah kejadian itu. Dia menduga targetnya akun GitHub dia plus akses ke klien-kliennya.

Nggak ada bug git di sini, dan dokumentasinya bilang gamblang.

`post-checkout` "is invoked when a git-checkout or git-switch is run after having updated the worktree." File di `.git/hooks/` itu kode yang git siap jalanin buat lo.

## Reproduksi 1: checkout jalanin hook-nya

Gue penasaran seberapa nyata ini masih jalan di git versi sekarang, jadi gue bikin ulang dari nol.

Satu repo, satu branch, satu hook yang nyatet argumennya:

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

Jalan di git 2.53.0, dan dia ngirim tiga argumen persis kayak yang dijelasin dokumentasi: HEAD sebelumnya, HEAD baru, dan flag checkout branch.

Yang penting justru yang nggak kelihatan. `git status` tetap bersih, dan `git ls-files` cuma nunjukin `README.md`.

Hook-nya hidup di dalam `.git`, jadi dia nggak akan pernah muncul di diff, di review, atau di listing folder.

## Reproduksi 2: git status juga jalanin config lo

Hook butuh lo buat pindah branch dulu.

Tapi komentar paling atas di thread lobste.rs ngebahas jalur yang sama sekali nggak butuh aksi dari lo.

User agwa nulis soal nyimpen `.git/config` dengan `core.fsmonitor` diarahin ke sebuah command, yang terus jalan di "very basic ones like `git status`."

Gue juga tes sendiri di repo gue. Satu path script di `.git/config`, terus `git status` biasa:

```
$ git config core.fsmonitor /path/to/fsmon.sh
$ git status
$ cat fs.log
FSMONITOR EXECUTED args=2 1791180551388075699
```

Ini yang lebih bahaya, karena `git status` itu perintah yang editor, build script, dan agent lo jalanin tanpa mikir.

agwa nggak muter-muter: IDE, `go build`, dan integrasi shell prompt, semuanya jalanin itu diam-diam.

Dokumentasi git ngasih tahu kenapa path itu bahaya.

`core.fsmonitor` "was extended to allow boolean values in addition to hook pathnames," jadi sebuah path diperlakukan sebagai command. Client versi lama malah bisa salah baca `true` sebagai command juga.

## Kenapa clone aman dan folder Dropbox nggak

Ada satu batas yang nentuin lo kena atau nggak, dan batasnya lebih sempit dari yang orang kira.

git nolak naruh path `.git/` di dalam tree sama sekali.

Gue coba lewat jalur plumbing buat mastiin:

```
$ git update-index --add --cacheinfo 100755,<blob>,.git/hooks/post-checkout
error: Invalid path '.git/hooks/post-checkout'
fatal: git update-index: --cacheinfo cannot add .git/hooks/post-checkout
```

`git add` biasa buat path yang sama malah nggak ngapa-ngapain, dan nggak ngasih peringatan apa pun. Jadi hook nggak bisa ikut kebawa lewat commit.

Waktu gue clone repo jebakan gue dari nol, hasilnya cuma bawa file `*.sample`, dan checkout di situ nggak jalanin apa-apa.

agwa narik garisnya persis di tempat proyek git narik garisnya: cloning itu "is in fact the only safe way to get a repo from an untrusted source."

Clone yang jahat dihitung sebagai vulnerability di git. Tarball yang jahat dihitung sebagai masalah lo sendiri.

Jadi sisanya ada tiga kasus:

- **Clone dari URL.** git yang checkout buat lo, aman.
- **Ekstrak zip atau tarball.** `.git`-nya udah ada di dalam. Ini jalur yang berbahaya.
- **Buka folder kiriman orang.** Kasus Wiles. Nggak ada clone, nggak ada pengecekan.

z3bra nabrak tembok yang sama dari arah lain. Clone dari repo yang nyoba ngirim `.git/hooks/post-checkout` mati dengan `fatal: unable to checkout working tree`.

vifon nambahin satu pengecualian yang perlu lo tahu: `git bundle` asli itu aman, karena clone dari situ nggak akan checkout file-file itu.

## Mitigasi paling populer ternyata bisa diakalin

Fix yang paling banyak di-upvote itu dari arialdo, yang matiin hook sepenuhnya pakai `git config --global core.hooksPath /dev/null`.

Niatnya bagus, tapi nggak nahan. oger udah nebak lubangnya duluan, dan gue reproduce sendiri di repo gue.

Dengan setting global itu terpasang, hook-nya diam.

Terus gue nambahin satu baris di config repo:

```
[core]
    hooksPath = .git/hooks
```

Hook-nya jalan lagi, karena config repo ngalahin config global, dan repo yang jahat bisa nyalain ulang dirinya sendiri.

Yang nahan itu bentuk per-command, karena config dari command line dipakai paling akhir:

```
$ git -c core.hooksPath=/dev/null checkout nda
$ git -c core.fsmonitor=false status
```

Dua-duanya berhasil ngeblok eksekusi di repo yang jahat. Dokumentasi git-config malah nyaranin bentuk ini langsung, ditulis sebagai `git -c core.hooksPath=/dev/null`.

## Kenapa agent lo lebih rentan

Gue jalanin fleet 17 profil agent.

Agent coding, QA, dan PR-review nge-clone repo terus jalanin `git status` dan `git checkout` tanpa diawasi, dengan kredensial git nempel di environment. Itu persis yang dicari penyerang: akses ke sebuah akun dan klien-klien yang nempel di situ.

Serangan ini lebih cocok buat agent daripada buat manusia, karena agent sering nerima repo dalam bentuk folder atau tarball, dan bukan hasil clone.

Dia jalanin `git status` terus-terusan, dan nggak ada apa pun di konteksnya yang lagi nyari folder `.git`.

Harden-nya singkat:

- **Clone, jangan copy.** Kalau memang harus mindahin repo, clone terus hapus sumbernya.
- **Suntik dua flag itu.** Taruh `-c core.hooksPath=/dev/null -c core.fsmonitor=false` di git wrapper agent lo.
- **Sandbox kredensialnya.** Jalanin git agent di container dengan token yang scoped dan umurnya pendek.
- **Periksa dulu sebelum command pertama.** Cek `.git/hooks` dan `.git/config` di setiap repo yang datang dari pihak ketiga.

Kalimat loldot di thread itu jadi default yang bener: "I just consider everything project someone sends me as a malicious." benoliver999 nyatet bentuk yang sama juga nongol di bundle take-home interview yang bawa `.git`.

## Intinya

`git checkout` bukan operasi baca. Dia bisa jalanin sebuah program, dan tampilannya dibikin biar kelihatan cuma baca. `git status` juga bisa begitu.

Solusinya bukan flag global yang pintar, karena sebuah repo bisa ngelawan lo buat ngerebut config-nya sendiri.

Clone apa pun yang nggak lo percaya dan jangan pernah copy, dan kalau ada yang bilang NDA-nya ada di sebuah branch, tanya kenapa dia butuh lo buat jalanin checkout-nya sendiri.

Kalau gue tarik ke konteks gue sendiri: fleet agent gue nge-clone repo tiap hari, dan hampir semuanya datang dari sumber yang nggak gue periksa satu-satu.

Yang bikin gue tenang cuma satu hal, yaitu semua clone-nya lewat jalur yang bener.

Begitu ada satu saja yang dikasih dalam bentuk zip atau folder Dropbox, dan ada agent yang jalanin `git status` di situ, seluruh aturan mainnya berubah.

Jadi aturan gue sekarang sederhana: apa pun yang nggak datang dari `git clone`, gue anggap asing sampai gue periksa sendiri.

Sisanya gue perlakukan seperti kode asing. Diperiksa dulu, baru dijalanin.

Nggak ada yang namanya "cuma lihat-lihat dulu" di repo yang nggak lo percaya.

Dan itu nggak butuh lo buat pindah branch. Cukup satu `git status` di folder yang salah.