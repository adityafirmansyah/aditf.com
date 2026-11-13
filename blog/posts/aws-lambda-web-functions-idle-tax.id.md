---
title: AWS Lambda Web Functions dan Jebakan Biaya Memori Idle 7 Menit
slug: aws-lambda-web-functions-idle-tax
date: 2026-11-13
excerpt: AWS Lambda Web Functions menjanjikan argo CPU aktif, tapi durasi memori idle selama 7 menit menyumbang 88% biaya komputasi untuk arsitektur multi-tenant.
tags: serverless, aws, nextjs, architecture, ecommerce
keywords: aws lambda web functions, serverless idle memory, multi-tenant monorepo, nextjs self hosting, lambda cost optimization
---

Waktu AWS merilis AWS Lambda Web Functions pada Oktober 2026, janji manisnya terdengar seperti mimpi para developer web. Lo bisa menjalankan server Hypertext Transfer Protocol (HTTP) standar langsung di arsitektur serverless, cuma bayar Central Processing Unit (CPU) yang aktif memproses request, tanpa pusing urusan server.

Buat aplikasi dengan traffic sporadis, fitur ini digadang-gadang bakal memangkas biaya kapasitas menganggur sampai habis.

Kenyataannya jauh dari ekspektasi itu.

Hasil benchmark independen dari tim Easel.sh pada 11 November 2026 membongkar jebakan argo yang cukup mahal. Walaupun AWS cuma menagih CPU saat ada request masuk, argo Random Access Memory (RAM) ternyata terus berjalan selama 313 sampai 411 detik setelah traffic berhenti.

Untuk aplikasi dengan pola kunjungan loncat-loncat, jeda idle tanpa konfigurasi selama 5 sampai 7 menit ini menyedot sekitar 88% tagihan cloud lo. Uang lo habis cuma buat bayar kapasitas fiktif.

## Jomplangnya Durasi 1.700× pada Serverless Idle Memory

Akar masalah arsitektur ini ada di disparitas waktu eksekusi yang luar biasa jomplang.

Ketika seorang pengunjung membuka halaman toko, server web biasanya merespons dalam hitungan milidetik. Masalahnya, container di balik layar nggak langsung dimatikan begitu response terkirim.

Berdasarkan pengujian Easel.sh pada enam environment di region us-east-1, AWS membiarkan instance tetap nongkrong di memori selama 5 sampai 7 menit buat menunggu request berikutnya.

Begini dampaknya buat web app ringan berukuran 160 sampai 210 MB:

- Request yang masuk cuma butuh waktu komputasi aktif selama 200 milidetik.
- Setelah selesai, environment tetap menyala dalam status idle selama 345 detik.
- AWS menghitung argo memori selama total 345,2 detik penuh.

Dalam skenario ini, durasi memori yang ditagih melebihi waktu komputasi aktif hingga 1.700 kali lipat.

Bahkan dengan harga standar AWS, biaya siluman ini yang mendominasi invoice lo. Biaya CPU aktif dan hitungan request cuma jadi recehan kecil. Sisa 88% tagihan komputasi lo tersedot habis buat membayar serverless idle memory.

Diskusi para software engineer di Hacker News (HN) langsung membenarkan hitungan ini lewat 29 komentar teknis. Kalau pola traffic aplikasi lo bukan aliran stabil tanpa jeda, tagihan memori serverless bakal berubah jadi jebakan argo berjalan.

## Kenapa AWS Sengaja Menahan Container Tetap Nyala 7 Menit?

Untuk memahami alasan di balik keputusan ini, kita perlu melihat siklus hidup environment yang dirancang AWS.

Dokumentasi resmi AWS membagi siklus hidup Web Function ke dalam tiga tahap:

- Initialization, ketika runtime container mulai boot dan mengunduh seluruh dependensi aplikasi.
- Ready, saat proses web siap mendengarkan port dan langsung memproses request HTTP.
- Shutdown, ketika AWS berhenti meneruskan request dan membersihkan container setelah masa tenang internal.

AWS sengaja menahan container tetap menyala demi menghindari cold start. Kalau setiap request baru harus menunggu inisialisasi container dari nol, pengunjung web lo bakal kabur karena loading yang lelet.

Sayangnya, AWS membebankan biaya penahan jeda ini langsung ke kantong pengguna.

Bisa nggak kita memotong durasi ini secara paksa lewat kode sendiri? Para engineer sudah mencoba trik itu di production.

Ketika developer sengaja memanggil `process.exit(0)` setelah 10 detik tanpa request, sistem AWS langsung menolaknya. Setiap proses yang mati secara sengaja dicatat AWS sebagai crash atau kegagalan runtime.

Keputusan sistem ini langsung merusak seluruh metrik operasional kita:

- Notifikasi error di CloudWatch bakal terus berbunyi tanpa henti.
- Dashboard deployment langsung berubah warna jadi merah.
- Tim engineer lo bakal kesulitan membedakan mana proses shutdown normal dan mana bug aplikasi asli.

Ujungnya, AWS sama sekali nggak menyediakan opsi lambda cost optimization untuk mengatur durasi idle ini. Pilihan lo cuma dua: ikhlas bayar denda 7 menit itu, atau rombak total arsitektur hosting lo.

## Next.js Self Hosting Lebih Kencang dari Cold Start Serverless

Jebakan biaya tadi mungkin masih bisa dimaklumi kalau performa mentah AWS Lambda Web Functions terbukti luar biasa.

Sayangnya performanya juga kalah telak.

Easel.sh menguji aplikasi Next.js 16 identik secara langsung antara AWS Lambda Web Functions melawan server yang di-manage sendiri. Hasilnya, server mandiri menang mutlak di semua pengujian.

Pada warm request, server mandiri merespons 1,5 sampai 3 kali lebih kencang:

- Rute JSON Application Programming Interface (API) selesai dalam 9,3ms di server mandiri dibanding 27,0ms di Lambda.
- Halaman Server-Side Rendering (SSR) tuntas dalam 12,2ms di server mandiri dibanding 26,0ms di Lambda.

Ketika mengukur cold start, jurang performanya makin kelihatan jelas. Setelah 12 menit nggak ada traffic, server mandiri sanggup boot dan melayani request dalam 216 sampai 250 milidetik.

Sementara itu, Lambda Web Functions butuh waktu antara 810 sampai 854 milidetik untuk menyelesaikan inisialisasi yang sama.

Pelajaran teknisnya sangat gamblang. Lewat Next.js self hosting, lo nggak perlu keluar uang lebih mahal cuma buat dapat respons lambat dan cold start yang lamban.

## Kenapa Multi-Tenant Monorepo Mengalahkan AWS Lambda Web Functions

Di Dagango.com, kita menjalankan platform e-commerce multi-tenant yang menampung ratusan website toko Usaha Mikro, Kecil, dan Menengah (UMKM).

Pola traffic toko merchant lokal ini jadi skenario paling buruk buat arsitektur serverless:

- Tiap toko merchant menerima traffic sporadis dari sebaran link WhatsApp dan promosi Instagram.
- Pengunjung datang dalam lonjakan singkat, lalu toko sepi selama berjam-jam.
- Ratusan subdomain toko merchant duduk diam di sepanjang hari.

Kalau kita memetakan tiap toko merchant ke fungsi serverless terpisah, kita bakal memicu ratusan argo memori idle 7 menit setiap harinya. Toko yang cuma dibuka lima kali dalam sejam bakal kena tagihan 35 menit RAM idle untuk satu detik komputasi riil.

Bayangkan pemborosan itu kalau dikalikan ke ratusan tenant toko. Tagihan cloud kita bakal meledak tanpa memberikan nilai tambah apa pun buat pemilik toko.

Karena itulah Dagango.com dibangun sebagai satu multi-tenant monorepo yang utuh. Kita menjalankan satu aplikasi gabungan Next.js dan FastAPI di balik reverse proxy Caddy pada satu Virtual Private Server (VPS) Linux dan server bare-metal, semuanya dikelola lewat systemd.

Pilihan arsitektur ini memberi kita tiga keunggulan konkret:

- Pooling memori: Satu proses berjalan melayani seluruh domain merchant tanpa menduplikasi beban runtime.
- Bebas cold start: Aplikasi selalu aktif di memori dan langsung menyambar setiap request yang masuk.
- Biaya perangkat keras pasti: Total tagihan hosting kita tetap flat di kisaran $10 sampai $20 per bulan tanpa peduli sebaran traffic.

Serverless memang masuk akal kalau lo punya satu endpoint dengan traffic raksasa yang nggak bisa diprediksi. Tapi untuk arsitektur multi-tenant dengan pola traffic yang panjang dan jarang (long-tail), serverless malah mengisolasi tiap tenant ke dalam siklus tagihan idle masing-masing.

Monorepo terpadu menyatukan kapasitas memori di tempat serverless memecah belahnya.

## FAQ Teknis

### Apakah provisioned concurrency bisa menghapus biaya memori idle di Lambda Web Functions?
Nggak bisa. Fitur provisioned concurrency memang menjaga container tetap hangat, tapi AWS menagih kapasitas yang disiapkan itu selama 100% waktu berjalan. Cara ini mencegah cold start, tapi malah bikin tagihan dasar lo melambung tinggi.

### Apakah penggunaan ulang container bisa menambal jebakan biaya di web bertraffic padat?
Bisa. Kalau aplikasi lo menerima aliran request konstan dengan jeda kurang dari lima menit, container bakal terus aktif melayani traffic tanpa terkena penalti idle. Masalah biaya 88% ini murni menghantam aplikasi dengan traffic sporadis dan jeda panjang.

### Bagaimana cara monorepo satu proses mencegah satu tenant menghabiskan seluruh resource?
Kita memasang pembatasan traffic per tenant langsung di layer reverse proxy Caddy dan middleware aplikasi. Pengelola proses seperti systemd bakal me-restart aplikasi secara otomatis kalau batas konsumsi memori terlewati.
