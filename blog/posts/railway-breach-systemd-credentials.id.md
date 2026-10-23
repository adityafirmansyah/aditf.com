---
title: Railway Bocor Bukan Karena Env Var. Tapi Env Var Tetap Tempat Nyimpen Secret yang Salah.
slug: railway-breach-systemd-credentials
date: 2026-10-23
excerpt: Kebocoran Railway Oktober 2026 ngebongkar isi database secret mereka, bukan sekadar env var. Masalahnya, kebiasaan naruh kredensial produksi di env var yang bikin kerusakannya sebesar itu.
tags: devops, security, linux, self-hosting, cloud
---

Tanggal 21 Oktober 2026 Railway ngasih tahu customer-nya kalau ada pihak luar yang nyasar ke sistem penyimpanan environment variable mereka. Buat sebagian akun, isinya terbaca utuh setelah didekripsi. Build dimatikan total pagi itu juga.

Berita utamanya kebocoran. Pelajaran yang lebih mahal justru soal keputusan desain yang melandasinya.

Yang kena itu database secret mereka. Artinya besar-kecilnya kerusakan sudah ditentukan bertahun-tahun sebelumnya, oleh tiap tim yang nganggep dashboard vendor sebagai tempat nyimpen kredensial produksi.

## Apa yang Railway benar-benar bocorkan

Pengumuman resminya cukup jelas soal mekanismenya. Provider AI inference dihubungi langsung supaya revoke key duluan, sebelum ada yang sempat dipakai.

Deploy beku semua selama investigasi jalan.

Sehari kemudian, 22 Oktober, Railway nambah dua panduan perbaikan. Dua-duanya atas nama Mykal Machon: satu buat AWS access key, satu buat service account key Google Cloud. Yang AWS lebih konkret isinya:

- **Jangan langsung hapus.** Deactivate dulu key yang kena, biar masih bisa dihidupkan sebentar kalau ada service yang lo lupa masih pakai key itu.
- **Cari di CloudTrail pakai access key ID.** Event history nyimpen panggilan management API sampai 90 hari ke belakang.
- **Lihat panggilan yang aplikasi lo nggak mungkin bikin:**

  ```
  RunInstances
  CreateUser
  CreateAccessKey
  AttachUserPolicy
  CreateRole
  PutBucketPolicy
  ```
- **Ulangi di semua Region**, termasuk Region yang lo nggak pernah pakai.

Panduan GCP nambahin satu detail yang gampang kelewat pas panik. Matiin service account key cuma ngeblok login baru. Token yang sudah terbit dari key itu masih berlaku sampai satu jam ke depan. Kalau lo butuh aksesnya putus sekarang, matiin service account-nya sekalian, terus copot juga grant `Service Account Token Creator` yang lo nggak kenal.

Nah, ada satu jebakan yang cuma ada di PaaS. Kata panduan Railway sendiri, ganti key itu berarti edit variable plus redeploy. Deploy-nya lagi beku.

Jadi saran yang paling benar itu ya rotate sekarang. Masalahnya, saran itu nempel sama kalimat kedua yang nggak sempat kebaca siapa-siapa: rotate nggak ada gunanya sampai control plane yang barusan jebol itu hidup lagi.

Urutan kayak gitu bukan detail kecil. Prosedur rotasi yang bergantung ke sistem yang lagi jebol itu bukan prosedur.

## Thread HN-nya nyalahin lapisan yang salah

Diskusi di Hacker News 50188228 (590 poin, 334 komentar) pecah cepat, dan dua-duanya ada benarnya.

Satu kubu pengin env var jadi penunjuk arah, bukan tempat nilai disimpan: *"Use environment variables to point to where secrets are located, not to store their values."* Itu kalimat numbsafari.

tptacek nyerang premisnya langsung: *"there's no reason to believe 'environment variables' were the reason this data was breached."*

Buat insiden ini, gue setuju sama tptacek. Yang diserang database secret, bukan environment proses. Andai semua customer Railway naruh kredensial sebagai file, database itu tetap sama menggiurkan, dan freeze-nya bakal kelihatan persis sama.

Tapi buat insiden berikutnya, numbsafari yang benar. Env var itu wadah yang lemah buat kredensial, siapa pun yang nyimpen.

Masalahnya dua klaim berbeda itu dicampur jadi satu di thread. Campuran itulah yang bikin praktik buruk yang udah berlangsung lima belas tahun tetap jalan lewat kebocoran yang ramai banget.

## Gue tes sendiri: env var bocor lewat mana

Gue nggak mau debat teori, jadi gue tes langsung di mesin ini. systemd 259, unit level user, satu variable:

```bash
systemd-run --user --unit=probe-longrun --collect \
  --property=Environment=PROBE_HMAC=super-secret-value \
  /bin/sleep 12
```

Terus dari shell biasa, user yang sama:

```bash
PID=$(systemctl --user show -p MainPID --value probe-longrun)
tr '\0' '\n' < /proc/$PID/environ | grep PROBE_HMAC
ps eww -p "$PID" | tr ' ' '\n' | grep PROBE_HMAC
```

Dua-duanya ngeprint `PROBE_HMAC=super-secret-value`. Nggak perlu root. Nggak perlu debugger atau container escape. Nggak perlu nembus proteksi `/proc` sama sekali.

Trik yang sama juga berlaku buat proses mana pun yang mewarisi variable itu, termasuk semua child process dan tiap `sh -c` di dalam script deploy.

Twelve-Factor nyuruh simpan config di environment karena config nggak boleh nempel di code. Buat hostname database, alasan itu masuk akal. Buat API key yang masih aktif, nggak pernah masuk akal.

Environment satu proses bisa dibaca siapa pun yang bisa baca proses itu. Jumlah orangnya lebih banyak daripada yang biasanya kita kira.

Bagian yang bikin repot: bocornya nggak ninggalin jejak. Nggak ada file yang berubah, nggak ada log yang aneh, nggak ada alert yang bunyi. Env var yang dibaca dari `/proc` kelihatan persis sama kayak env var yang nggak pernah disentuh siapa-siapa.

## systemd credential itu sebenarnya kerjaannya apa

Credential systemd bukan secrets manager. Tugasnya cuma satu: service manager nyerahin file ke unit. File itu read-only buat unit-nya, dan isinya nggak pernah nongol di `process.env`.

```ini
[Service]
User=dagango-api
LoadCredentialEncrypted=dbpass:/etc/credstore.encrypted/dbpass.enc
ExecStart=/usr/local/bin/api
```

Unit-nya baca `$CREDENTIALS_DIRECTORY/dbpass`. Probe yang sama, cuma variable-nya diganti credential:

```
cred_dir=/run/user/1000/credentials/run-p2707281-i11091151.service
-r-------- 1 aditf aditf 18 dbpass
environ_has_credname=0
touch $CREDENTIALS_DIRECTORY/newfile  ->  Permission denied
NAME   SECURE SIZE PATH
dbpass weak    18B  .../run-p2707281-i11091151.service/dbpass
```

Empat hal kebukti waktu itu juga:

- **Direktori read-only buat unit**, dan posisinya di luar environment sama sekali.
- **File credential mode 0400**, pemiliknya UID unit itu.
- **Isinya nggak muncul** di `/proc/$PID/environ` atau di `ps eww`.
- **Ciphertext-nya terikat ke nama credential.** Gue copy `dbpass.enc` jadi `renamed.enc`, dan dekripsinya ditolak: *"Name in credential doesn't match expectations."*

Poin terakhir itu justru yang nggak mungkin dikasih platform multi-tenant. Platform-nya memang harus megang kunci, itu bagian dari desain mereka.

Kalau lo mau cek sendiri tanpa percaya tulisan gue, jalankan `systemd-creds list` dari dalam unit-nya. Kolom `SECURE` langsung bilang credential lo ditaruh di ramfs, cuma numpang di memory biasa, atau malah kebuka buat user lain. Nggak perlu nebak dari dokumentasi.

## Yang belum kelar

TPM2 bukan barang gratis. `systemd-analyze has-tpm2` di mesin ini jawabnya `partial` dan exit 16. Efeknya jalur encrypt turun ke `/var/lib/systemd/credential.secret`, yang cuma bisa dibaca root.

File itu plus host-nya sudah cukup buat dekripsi. TPM2 yang bikin file itu nggak lagi jadi syarat, dan TPM2 nggak ada di semua mesin.

Lihat juga label `weak` di daftar tadi. Credential level user yang numpang di memory biasa memang jujur ngaku lebih lemah daripada yang dapat ramfs.

Biaya kedua yang jarang disebut: migrasi. Semua service kesentuh, semua secret diterbitkan ulang, tiap unit file dapat baris `LoadCredential=`. Buat fleet kecil, itu satu akhir pekan.

Buat ratusan service, itu dua kuartal dan satu rapat panjang soal siapa yang pegang rencana rollback.

Semua itu bukan alasan buat ninggalin kredensial produksi di database vendor. Yang lebih mendesak justru versi membosankannya:

- rotate semua yang pernah nongkrong di Railway,
- baca CloudTrail dan Cloud Audit Logs buat rentang waktu itu,
- baru habis itu pilih secret mana yang pantas dapat file terikat host, bukan kotak teks.

Yang paling gue bawa dari minggu ini justru satu kebiasaan yang kelihatan rapi. Kotak teks di dashboard yang bikin deploy jadi gampang itu juga pintu yang sama buat orang lain ngambil semua yang lo punya dalam satu malam.

Harga kenyamanan itu nyata, cuma ditagih belakangan. 😅

Kolom di dashboard itu dari dulu titik terlemahnya. Freeze minggu ini cuma bikin orang yang nggak pernah mikirin sejak 2011 akhirnya lihat.
