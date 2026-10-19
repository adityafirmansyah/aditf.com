---
title: Kenapa Pipeline AI Kita Bikin Halusinasi Kubernetes (Dan Cara Tangkal Context Poisoning)
slug: why-our-tooling-hallucinated-kubernetes
date: 2026-10-19
excerpt: Pipeline tooling developer kita mendadak meloloskan spesifikasi arsitektur yang nyebut Dagango.com jalan di Kubernetes. Ini investigasi teknis dan solusi kami.
tags: ai-agents, software-architecture, devops, prompt-engineering, software-engineering
---

## Tumpukan arsitektur yang nggak pernah kita bikin

Di Dagango.com, kita ngejalanin fleet agent otonom buat bantu bikin dokumentasi internal, review kode, dan nulis spesifikasi sistem. Pada 17 Oktober 2026, pipeline internal ini dengan percaya diri meloloskan dokumen arsitektur yang mengklaim platform kita jalan di atas cluster Kubernetes. Gue sempat bengong bacanya, karena sejak hari pertama dibangun, Dagango.com sama sekali nggak pernah nyentuh Kubernetes buat production.

Arsitektur server kita di dunia nyata jauh lebih bersahaja:

- unit service systemd biasa buat ngawasi proses background,
- reverse proxy nginx buat terminasi SSL dan routing traffic,
- dan worker antrean yang jalan langsung di bawah user Linux lokal.

Repositori kita bersih total dari pod, manifest Helm, maupun ingress controller. Anehnya, dokumen yang lolos review internal itu nggak cuma nyenggol Kubernetes sepintas lalu, melainkan ngejelasin kebijakan scaling cluster sampai siklus restart pod secara meyakinkan lewat beberapa paragraf panjang.

## Asal muasal racun konteks di level periset

Setelah gue telusuri run log-nya, biang keroknya ternyata ada di luar agent generator ataupun verifier. Kerusakan dimulai jauh di hulu, tepatnya di berkas ringkasan `brief.md`. Model LLM pas disuruh merangkum catatan sistem itu sering kali kebablasan mengolah informasi mentah, karena mereka punya kecenderungan bawaan buat merangkum dan menghubung-hubungkan titik informasi yang sebenernya terpisah:

- agent periset baca profil bio gue yang nyebut pengalaman masa lalu megang microservices,
- terus dia baca catatan terpisah soal Dagango.com yang pakai monorepo Next.js dan FastAPI,
- nah, dari dua info itu dia langsung narik kesimpulan sendiri kalau Dagango.com jalan di cluster container Kubernetes.

Klaim palsu ini kemudian ditulis ke dalam brief riset sebagai fakta fondasi. Di sinilah letak jebakan arsitekturnya bekerja.

Dalam desain tooling kita, dokumen brief hasil riset diperlakukan sebagai pegangan fakta mutlak yang pantang digugat oleh agent tahap berikutnya tanpa ada kontradiksi eksternal yang nyata. Kerusakan ini murni hasil sintesis semantik agresif dari agent hulu yang mencemari seluruh konteks kerja ke bawahnya.

## Ilusi audit independen antar-LLM

Kita sengaja masang verifier mandiri di pengujung pipeline demi mencegah masuknya klaim teknis fiktif ke spesifikasi internal kita. Tugas reviewer ini galak: dia wajib nolak spesifikasi yang ketahuan ngarang metrik atau bikin cerita fiktif.

Tapi pas dokumen Kubernetes itu diverifikasi, skornya malah keluar bersih tanpa cacat kritis sama sekali:

- verifier ngecek apakah tulisan yang digenerate cocok sama arahan berkas brief riset,
- dia nemu kalau kata Kubernetes emang udah tertulis jelas di brief dari awal,
- ya udah, verifier langsung nyimpulin kalau generator cuma ngejalanin tugasnya dengan patuh.

Ini ilusi paling berbahaya pas kita numpuk LLM buat saling ngoreksi. Verifier yang cuma disuruh ngecek keselarasan teks terhadap konteks hulu nggak bakal pernah bisa tahu kalau konteks hulunya sendiri murni karangan bebas.

Reviewer kita cuma bertindak sebagai pemeriksa kepatuhan alih-alih penguji kebenaran faktual. Karena kebohongan arsitektur tadi udah hadir di prompt awal, verifier otomatis nganggepnya sebagai fakta yang sah.

## Tebakan masuk akal vs kepastian arsitektur

Verifier pipeline kita sebenernya terbukti sangat jeli kalau urusannya mendeteksi fabrikasi angka performa maupun rekayasa statistik. Di run sebelumnya, sistem ini langsung nolak draf yang nyelipin angka hit ratio cache 91% tanpa rujukan jelas.

Angka statistik punya sifat yang gampang diverifikasi lewat log dan data riil:

- nilai numerik biasanya punya tautan sumber primer yang konkret,
- angka persentase harus sinkron sama rekaman telemetri di server,
- dan metrik pengujian bakal langsung gugur kalau nggak tertulis di URL referensi.

Masalahnya, klaim arsitektur punya karakter yang beda total. Di mata LLM, wajar-wajar aja kalau monorepo Next.js dan FastAPI ditaruh di Kubernetes. Kalimat itu terdengar sangat masuk akal secara statistik, meski faktanya nol besar buat infrastruktur kita.

LLM cuma mengukur tingkat kewajaran kalimat ketimbang kebenaran empiris di server nyata. Tanpa adanya aturan mutlak yang dikunci lewat kode, kebohongan yang terdengar canggih bakal selalu lolos sensor otomatis.

## Jebakan konsensus palsu di ruang gema multi-agent

Numpuk beberapa agent dalam satu pipeline tooling sering dikira menghasilkan pengujian yang objektif. Nyatanya, susunan bertingkat begini gampang banget menjelma jadi ruang gema tertutup.

Ketika sebuah premis palsu terlanjur merayap ke dalam konteks prompt bersama, model-model setelahnya justru sibuk mempercantik kebohongan itu dengan rincian teknis. Bukannya curiga dan memvalidasi kebutuhan server, agent generator malah asyik mengarang detail operasional seputar siklus hidup pod agar dokumennya terkesan canggih.

Rantai konsensus palsu ini bergulir mulus melewati empat babak:

- periset mengarang tumpukan stack dari sintesis profil yang keliru,
- generator mengembangkan premis itu dengan rincian arsitektur yang meyakinkan,
- verifier memberi lampu hijau lantaran naskahnya patuh terhadap brief,
- dan otomatisasi alur kerja bersiap menyerahkan dokumen ke tim internal.

Semua model kompak mengamini narasi fiktif ini tanpa ada satu pun yang memeriksa kondisi server fisik kita. Menyamakan tiga giliran LLM dengan tiga lapis verifikasi manusia jelas kekeliruan fatal dalam rekayasa sistem otonom.

## Benteng pertahanan buat tangkal racun konteks

Buat beresin celah ini, kita nggak bisa cuma ngandelin revisi prompt yang sifatnya imbauan halus. Di tooling produksi kita, solusi instan yang langsung kita eksekusi cukup jelas:

- **Aturan arsitektur mutlak di berkas SOUL.** Kita nambahin batasan negatif yang tegas di prompt dasar. Kontrak agent periset dan auditor sekarang mengunci aturan mutlak: Dagango.com cuma jalan di VPS Linux dan bare-metal pakai systemd serta nginx, dan haram hukumnya nyebut Kubernetes.
- **Pemisahan validasi fakta dari isi brief.** Verifier nggak boleh lagi nganggep teks brief riset sebagai sumber kebenaran mutlak tanpa verifikasi batas arsitektur sistem yang nyata.
- **Peran krusial pengawasan manusia.** Agent otonom emang hebat buat urusan riset, nulis spesifikasi, sampai ngecek format, tapi insting manusia tetap mutlak diperlukan buat nyetop halusinasi semantik yang lolos dari sensor bot.

Batasan negatif di profil prompt ampuh buat ngeblok halusinasi yang polanya udah ketahuan. Tapi buat jangka panjang, intinya jangan pernah nelen mentah-mentah output teks dari LLM hulu sebagai kebenaran mutlak.

## Catatan lapangan buat arsitek sistem AI

Arsitektur multi-agent sekarang lagi naik daun dan mulai banyak dipakai di sistem tooling developer. Tapi kalau kita ngasih mandat besar ke kawanan agent tanpa mitigasi racun konteks, sistem verifikasi kita tinggal nunggu waktu buat jebol. Begitu agent penguji lo bergantung pada prompt yang di-generate sama agent lain, rantai validasi lo sebenernya udah rusak dari dalam.

Pelajaran mahal dari insiden ini ngasih kita tiga pegangan operasional:

- anggap semua output teks dari LLM hulu sebagai data mentah yang belum tentu benar,
- kunci batasan arsitektur penting lewat kode pengujian deterministik daripada sekadar bisikan prompt,
- dan pertahankan peran manusia sebagai pemegang kendali akhir di gerbang deployment.

Agent cerdas emang jago nulis dan ngerapihin dokumentasi dengan kecepatan luar biasa. Tapi memastikan sistem tetap berpijak pada arsitektur server yang nyata tetap jadi tanggung jawab kita sebagai engineer.
