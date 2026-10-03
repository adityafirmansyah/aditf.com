---
title: Dari 18 Gateway Jadi Satu: Fix-nya Nggak Ada di Git
slug: gateway-fix-not-in-git
date: 2026-10-01
excerpt: Delapan belas daemon gateway jadi satu cuma dalam tiga menit. Dashboard yang ngawasin mereka rusak, terus dibenerin pakai 270 baris yang belum di-commit. Sekali checkout bersih, produksi balik lapor 16 dari 17 profil down.
tags: ai-agents, homelab, systemd, observability, self-hosting
---

Jam 18:43:02, 30 September. Box ini masih jalanin delapan belas daemon gateway.

Jam 18:45:27 tinggal satu, dan prosesnya jalan persis seperti rancangannya.

Yang rusak justru dashboard yang ngawasin mereka semua.

Ujung ceritanya nggak bagus, dan itu bukan karena fix-nya gagal. Masalahnya, fix-nya nggak pernah masuk commit.

## Angkanya, sebelum dan sesudah

Semua angka di bawah ini dibaca langsung dari mesinnya:

- **Proses gateway:** 18 (17 profil role plus default) → **1**, pid 3703821, RSS 845 MB, udah jalan 22 jam.
- **Port loopback per profil:** 8378–8394 plus 8642 → **nol listener di rentang per profil**. Yang jawab sekarang cuma 8001, 8002, 8113, dan 8642.
- **Total RSS Hermes:** 4,4 GB → **2,06 GiB di 18 proses**.
- **Unit systemd Hermes:** 18 → **2**, hermes-gateway dan hermes-ops-dashboard.

Gue cek pakai `ss -tln | grep -c '127.0.0.1:83[0-9][0-9]'`, hasilnya 0. Rentang port per profil itu hilang, bukan sekadar nganggur.

Enam belas profil yang ada di disk semuanya jawab lewat jalur multiplex, dan `/p/<profile>/health` balas HTTP 200 buat masing-masing.

## Yang nolak duluan justru gateway-nya sendiri

Gateway yang baru dinyalain jam 18:43:02 mutusin buat nggak ikut mode multiplex. Alasannya dia tulis sendiri:

> This gateway stays standalone: profile(s) 'branding' (systemd (user)), 'challenger' (systemd (user)), … 'viral-researcher' (systemd (user)) still run their own gateway; fold them with `hermes gateway migrate --multiplex`. It serves only the launching profile.

Di log yang sama, dia juga nyatet satu race yang udah dia putusin buat nggak dijalanin:

> Another profile's standalone gateway owns this host (PID 3605453 (no bound port; profiles: challenger)); starting beside it rather than retrying a race no second profile can win.

Jadi ada tool migrasi yang bilang dia butuh migrasi, sekalian ngasih perintahnya.

Nolaknya nggak ada biayanya.

Race yang dia tolak itu yang mahal, dan keputusannya benar.

Proses migrasinya sendiri jalan dari jam 18:43:02 sampai jam 18:45:27. Penanda akhirnya mtime direktori `default.target.wants`.

## Yang terjadi itu badai barengan, bukan rolling restart

Jam 18:43:35, gateway-nya nulis soal kematiannya sendiri:

> Shutdown context: signal=UNKNOWN under_systemd=yes parent_pid=1216 parent_name=systemd loadavg_1m=17.39

Load 17,39 di Celeron J4105 yang cuma punya 4 core. Over-subscription-nya lewat 4x, dan yang nyatet itu justru proses yang lagi dimatiin.

Ada lima belas shutdown plus satu config converge, dan semuanya mendarat di menit yang sama.

Swap di box ini nggak ada, dan itu memang disengaja karena SSD-nya lambat. `swapon --show` keluarnya kosong.

Nggak ada yang nyerap lonjakan itu, jadi load-nya harus turun sendiri, atau ada yang mati.

## Yang jebol pertama: URL peer

`bot_peers` di `~/.hermes/config.yaml` isinya URL yang ngarah ke port per profil. Port-port itu barusan dihapus sama fold, jadi delegasi antar profil langsung mati:

```
$ hermes peer dm ...
Connection refused
```

Solusinya: tiap entry diarahin ulang ke rute multiplex.

```
http://127.0.0.1:8642/p/<name>
```

`/p/<name>/v1/capabilities` balik 200, dan tabelnya sekarang isi 16 entry yang nunjuk ke jalur itu.

Pelajaran yang gue ambil: yang gue urus waktu fold cuma prosesnya. Yang masih ngobrol sama proses itu ada di daftar lain.

URL-URL itu separuh lain dari migrasinya. Nggak ada yang nyatet kalau itu dependency yang mesti diurus.

## Yang jebol kedua: health check yang baca file

Dashboard ops itu app FastAPI kecil di 127.0.0.1:9898, dan dia ikut rusak.

Ini bukan kesimpulan dari baca halaman status. Angka ini keluar dari ngereplay kode yang beneran ada di commit.

`HEAD` di `hermes_ops.py` isinya cek ini:

```python
if _pid_alive(st.get("pid")) and _http_health(p["port"]):
```

Di file yang sama, string `multiplex` nggak muncul sekali pun. Dua klausa itu bakal salah terus, dua-duanya:

1. port per profil udah dihapus sama fold, dan itu disengaja;
2. pid yang kecatat di `gateway_state.json` profil itu udah mati.

Ini state file profil cto, terakhir ditulis sama proses sebelum fold:

```json
{"pid":3608090,"gateway_state":"stopped",
 "platforms":{"api_server":{"listener_base":"http://127.0.0.1:8387",
   "metrics":{"port":8387,"last_heartbeat":"2026-09-30T11:43:55Z"}}},
 "served_profiles":[],
 "multiplex_standalone_reason":"profile(s) 'branding' ... 'viral-researcher' still run their own gateway; fold them with `hermes gateway migrate --multiplex`"}
```

Pid 3608090 udah mati, `ProcessLookupError`. Port 8387 nggak listening. `served_profiles` kosong.

Kalau dua klausa itu dijalanin apa adanya di box ini, cuma 1 dari 17 profil yang balik online, jadi 16 kebaca DOWN.

Lima belas state file profil masih nyimpen pid mati, fosil dari topologi yang berhenti ada jam 18:45.

Yang root, `~/.hermes/gateway_state.json`, masih hidup dan otoritatif. Yang per profil itu fosilnya.

Tanya profil yang sama pakai cara yang dipakai kode yang udah diperbaiki:

```
== same profiles via /p/<name>/health ==
   reachable: 17/17
```

## Fix-nya jalan di produksi, tapi nggak ada di git

Dashboard yang jalan sekarang balas `{'total': 17, 'active': 1, 'idle': 16, 'down': 0}`.

Jam 13:43:28 hari ini dia berhenti nganggep profil yang sehat sebagai down. Ini yang bikin dia berhenti:

- `hermes_ops.py`: **+270 baris yang belum di-commit**, nambahin `multiplex_host()` dan `profile_reachable()`, yang jatuh balik ke `/p/<name>/health` di listener bersama.
- `hermes_status.py`: **9 baris berubah**, sekarang manggil `_ops.profile_reachable(p)`.
- Branch `feat/ops-fleet-dashboard`, HEAD `844ab0d` (30 September, 14:04). Fix-nya nggak ada di commit itu.
- mtime file 12:07:10. Servicenya di-restart ke working tree yang kotor jam 13:43:28, dan sejak itu jalan di situ.

Jadi fix-nya nyata, logikanya benar, dan tempatnya cuma satu: working tree yang nggak pernah di-commit.

Sekali checkout bersih, redeploy, atau pindah branch, dashboard-nya balik lapor 16 dari 17 profil down.

Yang bermasalah bukan kodenya, tapi keadaannya. Fix-nya cuma ada di satu mesin, nempel di proses yang lagi jalan.

Selama servicenya belum di-restart, semuanya kelihatan normal. Begitu ada yang nyentuh prosesnya, versinya balik ke yang ada di git, dan yang di git itu masih percaya port per profil.

Nggak akan ada commit buat di-diff, nggak ada PR buat di-review, dan nggak ada satu baris history yang nyebut fix-nya pernah ada.

"Yang penting jalan sekarang" itu kalimat yang paling mahal di kerjaan ops.

Klaim "jalan sekarang" dan klaim "tercatat" itu beda. Cuma satu yang selamat dari `git checkout .`

## Satu gateway, tanpa cap

Tujuh belas proses hilang, dan yang tersisa cuma satu titik yang harus lo percaya. Ruang geraknya lebar:

- `hermes-gateway.service` pakai `Restart=always` dan `RestartUSec=5s`.
- `MemoryCurrent` ada di sekitar 2,4–2,9 GiB dan terus gerak.
- `TasksCurrent` 95.
- `MemoryHigh=infinity` dan `MemoryMax=infinity`, jadi accounting-nya nyala tapi cap-nya nggak ada.

Titik tunggal kelihatan murah di awal. Baru ketahuan mahalnya waktu ada yang perlu di-restart.

Manajemen memorinya jadi manual. Habis beberapa batch turn, heap yang bebas dikembaliin ke kernel pakai `malloc_trim`, yang nyentuh `sbrk` dan `madvise`.

Itu kebijakan, bukan jaminan.

Swap nol, jadi OOM killer cuma dapet satu kesempatan dan nggak nanya dulu ke siapa pun.

Zombie sekarang 0, uptime 1 minggu 17 jam, dan disk kepakai 60% dari 115 G.

## Bug yang sama ada di catatan gue sendiri

Gue hampir nerbitin versi yang kebalikannya.

Draft pertama gue bilang dashboard-nya lagi lapor 16 dari 17 profil DOWN, dan lembar pengukuran gue nulis hal yang sama.

Lembar itu udah basi waktu gue baca. Fix-nya udah jalan tiga jam sebelumnya.

Script penghitung gue sendiri yang salah: dia baca nilai status `IDLE` sebagai `DOWN`.

Snapshot yang dipakai buat ngomong present tense. Sistemnya baik-baik aja; catatannya yang ketinggalan tiga jam.

Kegagalan kayak gini punya bentuk, dan bentuknya layak kita kasih nama:

- "sistem sekarang lapor X" cuma benar di detik query-nya dijalanin;
- begitu hasil query-nya mendarat di file, timestamp file itu jadi bagian dari klaimnya;
- jadi jalanin ulang pas mau publish, atau tulis dalam past tense sambil nyantumin jamnya.

## Sisa-sisa yang masih nempel

Sebagian besar bersih. Tapi nggak seluruhnya:

- 16 file `runs_idempotency.db` per profil, atau 48 kalau `-wal` dan `-shm` ikut dihitung;
- tepat 1 yang WAL-nya nggak kosong, 245 KB, dan dia hidup lebih lama dari proses yang nulis dia;
- dan 15 state file profil yang masih nunjuk ke pid yang udah nggak ada.

Write state yang ditinggal itu jarang, tapi nyata.

Sama nyatanya kayak 15 file JSON kecil yang masih jawab pertanyaan soal topologi yang berhenti ada jam 18:45.

## Penutup

Total biayanya: tiga menit, satu lonjakan load, dan dua consumer yang jebol. Dua-duanya sekarang udah beres.

`bot_peers` udah nunjuk ke jalur multiplex. Dashboard-nya baca `/p/<name>/health`, dan dia nggak lagi nganggep profil yang sehat sebagai down.

Yang belum beres itu catatannya.

Suatu saat nanti ada yang redeploy repo itu, mendarat di checkout yang bersih, dan nonton 16 dari 17 profil jadi merah tanpa ada apa pun di history yang bisa jelasin kenapa.

Pelajaran dari tabel routing itu kena juga ke kode kita yang ngawasin tabel routing: migrasi nggak selesai waktu proses lamanya mati.

Selesai kalau semua consumer-nya udah diarahin ulang, dan perubahannya udah masuk commit.

Perbaikan yang cuma hidup di memori satu service punya tanggal kedaluwarsa, dan batasnya restart berikutnya.

Git nggak begitu. Apa pun yang udah masuk commit tetap ada, walaupun service-nya udah lama mati.