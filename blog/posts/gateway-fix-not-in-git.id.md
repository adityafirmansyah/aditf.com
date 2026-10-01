---
title: Dari 18 Gateway Jadi Satu: Fix-nya Nggak Ada di Git
slug: gateway-fix-not-in-git
date: 2026-10-01
excerpt: Delapan belas daemon gateway dipadatkan jadi satu dalam tiga menit. Dashboard yang ngawasin mereka sempat rusak, terus dibenerin pakai 270 baris yang belum di-commit. Sekali checkout bersih, produksi balik lapor 16 dari 17 profil down.
tags: ai-agents, homelab, systemd, observability, self-hosting
---

Jam 18:43:02, 30 September, box ini masih jalanin delapan belas daemon gateway. Jam 18:45:27 tinggal satu.

Fold-nya jalan mulus, persis seperti yang dirancang. Yang bermasalah justru dashboard yang ngawasin gateway-gateway itu. Dan ujung ceritanya nggak bagus. Bukan karena fix-nya gagal.

Masalahnya fix-nya nggak pernah masuk commit.

## Hasil fold-nya, angkanya

Angka sebelum dan sesudah, dibaca langsung dari mesinnya:

- **Proses gateway:** 18 (17 profil role plus default) → **1**, pid 3703821, RSS 845 MB, udah jalan 22 jam.
- **Port loopback per profil:** 8378–8394 plus 8642 → **nol listener di rentang per profil**. Yang jawab sekarang cuma 8001, 8002, 8113 dan 8642.
- **Total RSS Hermes:** 4,4 GB → **2,06 GiB di 18 proses**.
- **Unit systemd Hermes:** 18 → **2**, hermes-gateway dan hermes-ops-dashboard.

Ceknya gampang: `ss -tln | grep -c '127.0.0.1:83[0-9][0-9]'` hasilnya 0, jadi rentang per profil itu benar-benar hilang, nggak cuma nganggur.

Enam belas profil yang ada di disk tetap jawab lewat jalur multiplex, dan nggak ada satu pun yang protes. `/p/<profile>/health` balas HTTP 200 buat semuanya.

## Gateway-nya nolak duluan, sekalian nyebutin perintah fix-nya

Jam 18:43:02, gateway yang baru dinyalain mutusin buat nggak ikut mode multiplex, dan dia nulis alasannya. Alasannya dia tulis sendiri kayak gini:

> This gateway stays standalone: profile(s) 'branding' (systemd (user)), 'challenger' (systemd (user)), … 'viral-researcher' (systemd (user)) still run their own gateway; fold them with `hermes gateway migrate --multiplex`. It serves only the launching profile.

Terus, di log yang sama, dia nyatet satu race yang dia sendiri udah mutusin buat nggak dijalanin:

> Another profile's standalone gateway owns this host (PID 3605453 (no bound port; profiles: challenger)); starting beside it rather than retrying a race no second profile can win.

Jadi ada tool migrasi yang bilang dia butuh migrasi, sekalian ngasih perintahnya. Nolaknya gratis.

Race yang dia tolak itu bagian yang mahal, dan keputusannya benar.

Proses migrasinya sendiri makan 18:43:02 sampai 18:45:27, dan penanda akhirnya mtime direktori `default.target.wants`.

## Fold itu badai barengan, bukan rolling restart

Jam 18:43:35, gateway nulis soal kematiannya sendiri:

> Shutdown context: signal=UNKNOWN under_systemd=yes parent_pid=1216 parent_name=systemd loadavg_1m=17.39

Load 17,39 di Celeron J4105 yang cuma punya 4 core. Over-subscription-nya di atas 4x, dan yang nyatet justru proses yang lagi dimatiin.

Lima belas shutdown plus satu converge mendarat di menit yang sama.

Box ini nggak punya swap, dan itu memang disengaja karena SSD-nya lambat. `swapon --show` keluarnya kosong, jadi nggak ada yang nyerap lonjakannya. Ujung-ujungnya load-nya harus turun sendiri, atau ada yang mati.

## Yang jebol pertama: URL peer di bot_peers

`bot_peers` di `~/.hermes/config.yaml` isinya URL yang ngarah ke port per profil, port yang barusan dihapus sama fold. Delegasi antar profil langsung jebol:

```
$ hermes peer dm ...
Connection refused
```

Solusinya gampang: tiap entry diarahin ke rute multiplex, satu per satu:

```
http://127.0.0.1:8642/p/<name>
```

`/p/<name>/v1/capabilities` balik 200, dan tabelnya sekarang isi 16 entry yang nunjuk ke jalur itu.

URL-URL itu separuh lain dari migrasinya, dan nggak ada satu pun yang nyatet kalau itu dependency yang harus diurus.

## Yang jebol kedua: health check yang baca file

Dashboard ops itu app FastAPI kecil yang jalan di 127.0.0.1:9898, dan fold ini juga yang bikin dia rusak.

Bukan kesimpulan dari baca halaman status. Ini hasil ngereplay langsung dari kode yang beneran ada di commit. Nggak ada hubungannya sama tampilan dashboard. Cek yang dijalankan `HEAD` di file `hermes_ops.py` cuma segini:

```python
if _pid_alive(st.get("pid")) and _http_health(p["port"]):
```

Di file yang sama, kata `multiplex` bahkan nggak muncul sekali pun, jadi nggak ada jalan keluarnya. Dua klausa itu dua-duanya salah terus, dan nggak ada yang bisa nyelametin:

1. port per profil udah dihapus sama fold, dan itu disengaja;
2. pid yang tercatat di `gateway_state.json` profil itu udah mati dan nggak akan hidup lagi.

Ini isi state file profil cto, terakhir ditulis sama proses sebelum fold, dan nggak ada yang nulis ulang sejak itu:

```json
{"pid":3608090,"gateway_state":"stopped",
 "platforms":{"api_server":{"listener_base":"http://127.0.0.1:8387",
   "metrics":{"port":8387,"last_heartbeat":"2026-09-30T11:43:55Z"}}},
 "served_profiles":[],
 "multiplex_standalone_reason":"profile(s) 'branding' ... 'viral-researcher' still run their own gateway; fold them with `hermes gateway migrate --multiplex`"}
```

Pid 3608090 udah mati, dan `ProcessLookupError` yang muncul pas dicek.

Port 8387 udah nggak listening lagi, dan daftar `served_profiles`-nya kosong.

Replay dua klausa itu ke mesin ini: 1 dari 17 profil online, jadi 16 kebaca DOWN.

Lima belas file state profil masih nyimpen pid mati, fosil topologi yang berhenti ada jam 18:45. Yang root, `~/.hermes/gateway_state.json`, masih hidup dan otoritatif, sementara yang per profil itu fosilnya.

Sekarang tanya profil yang sama, tapi pakai cara yang dipakai kode yang udah diperbaiki:

```
== same profiles via /p/<name>/health ==
   reachable: 17/17
```

## Fix-nya jalan, tapi nggak ada di git

Dashboard yang jalan sekarang balas `{'total': 17, 'active': 1, 'idle': 16, 'down': 0}`.

Hari ini jam 13:43:28 dia berhenti nge-cap profil sehat sebagai down, dan yang ngubah itu:

- `hermes_ops.py`: **+270 baris belum di-commit**, nambahin `multiplex_host()` dan `profile_reachable()`, yang jatuh ke `/p/<name>/health` di listener bersama.
- `hermes_status.py`: **9 baris berubah**, sekarang manggil `_ops.profile_reachable(p)`.
- Branch `feat/ops-fleet-dashboard`, HEAD `844ab0d` (30 September, 14:04). Fix-nya nggak ada di commit itu.
- mtime file 12:07:10. Servicenya di-restart ke working tree yang kotor jam 13:43:28, dan sejak itu jalan di situ.

Jadi fix-nya nyata, logikanya benar, dan tempatnya cuma satu: working tree yang nggak pernah di-commit.

Sekali checkout bersih, redeploy, atau pindah branch, dashboard-nya balik lapor 16 dari 17 profil down.

Pola kayak gini yang bikin susah dilacak. Yang bermasalah bukan kodenya, tapi keadaannya: fix-nya cuma ada di satu mesin, nempel di proses yang lagi jalan. Selama servicenya belum di-restart, semuanya kelihatan normal. Begitu ada yang nyentuh prosesnya, versinya balik ke yang ada di git, dan yang di git itu masih percaya port per profil.

Nggak ada commit buat di-diff, nggak ada PR buat direview, dan nggak ada satu baris history yang nyebut fix-nya pernah ada.

"Yang penting jalan sekarang" itu kalimat yang paling mahal di kerjaan ops. Klaim "jalan sekarang" dan klaim "tercatat" itu dua hal yang beda, dan cuma satu yang selamat dari `git checkout .`

## Satu gateway, tanpa cap

Fold-nya ngilangin 17 proses dan bikin satu titik yang harus lo percaya. Ruang geraknya lebar:

- `hermes-gateway.service` pakai `Restart=always` dan `RestartUSec=5s`.
- `MemoryCurrent` ada di sekitar 2,4–2,9 GiB dan gerak terus.
- `TasksCurrent` 95.
- `MemoryHigh=infinity` dan `MemoryMax=infinity`, jadi accounting-nya nyala tapi cap-nya nggak ada.

Manajemen memorinya jadi manual. Habis beberapa batch turn, heap yang bebas dikembaliin ke kernel pakai `malloc_trim`, yang nyentuh `sbrk` dan `madvise`.

Itu kebijakan, bukan jaminan.

Karena swap nol, OOM killer cuma dapet satu kesempatan dan nggak nanya dulu ke siapa pun. Zombie sekarang 0, uptime 1 minggu 17 jam, disk 60% dari 115 G.

## Bug yang sama ada di catatan gue sendiri

Gue hampir nerbitin versi yang kebalikannya. Draft pertama gue bilang dashboard-nya lagi lapor 16 dari 17 profil DOWN, dan gue punya lembar pengukuran yang nulis hal yang sama.

Lembar itu udah basi waktu gue baca. Fix-nya udah jalan tiga jam sebelumnya.

Yang lebih parah, script penghitung gue sendiri baca nilai status `IDLE` sebagai `DOWN`.

Snapshot yang dipakai buat ngomong present tense. Sistemnya baik-baik aja; catatan gue yang ketinggalan tiga jam. Bentuk kegagalannya kayak gini:

- "sistem sekarang lapor X" cuma benar di detik query-nya dijalanin;
- begitu hasil query-nya masuk file, timestamp file itu jadi bagian dari klaimnya;
- jadi jalanin ulang pas mau publish, atau tulis dalam past tense sambil nyantumin jamnya.

## Sisa-sisa yang masih nempel

Sebagian besar bersih. Nggak seluruhnya:

- 16 file `runs_idempotency.db` per profil, atau 48 kalau `-wal` dan `-shm` ikut dihitung;
- tepat 1 yang WAL-nya nggak kosong, 245 KB, dan dia hidup lebih lama dari proses yang nulis dia;
- dan 15 file state profil yang masih nunjuk ke pid yang udah nggak ada.

Write state yang ditinggal itu jarang, tapi nyata, sama kayak 15 file JSON kecil yang masih jawab pertanyaan soal topologi yang berhenti ada jam 18:45.

## Penutup

Fold-nya sendiri cuma makan tiga menit, satu lonjakan load, dan dua consumer yang jebol. Dua-duanya sekarang udah beres.

`bot_peers` nunjuk ke jalur multiplex. Dashboard-nya baca `/p/<name>/health` dan nggak lagi nge-cap profil sehat sebagai down.

Yang belum beres itu catatannya. Suatu saat nanti ada yang redeploy repo itu, mendarat di checkout yang bersih, dan nonton 16 dari 17 profil jadi merah tanpa ada apa pun di history yang bisa jelasin kenapa.

Setiap perbaikan yang cuma hidup di memori satu service punya masa kedaluwarsa, dan batasnya cuma restart berikutnya. Git, sebaliknya, nggak kehilangan isi kepalanya waktu service-nya mati.

Pelajaran dari tabel routing itu berlaku juga buat kode yang ngawasin tabel routing: migrasi nggak selesai waktu proses lamanya mati. Selesai kalau semua consumer-nya udah diarahin ulang, dan perubahannya udah masuk commit.
