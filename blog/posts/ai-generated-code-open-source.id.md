---
title: Kode Buatan AI Harus Open Source? Tim Tetap Perlu Memilih
slug: ai-generated-code-open-source
date: 2026-11-16
excerpt: Perdebatan kode buatan AI open source sering mencampuradukkan hak cipta dengan keputusan rilis. Tim tetap perlu review behavior, menguji batas akses, dan menentukan kode mana yang layak dipublikasikan.
tags: ai-assisted-development, open-source, software-engineering, multi-tenant, code-review
keywords: AI-generated code open source, AI code copyright, human authorship AI, multi-tenant authorization testing, software engineering AI tools
---

Kecerdasan buatan (AI) bisa bikin handler checkout dalam hitungan detik. Yang nggak bisa dia putuskan: boleh atau nggak satu merchant membaca order milik merchant lain.

Buat produk commerce, batas kayak gitu jauh lebih penting daripada siapa yang mengetik tiap barisnya. Debat soal kode buatan AI open source juga jadi lebih berguna kalau kita pisahkan dulu urusan authorship dari tanggung jawab engineering.

Pada 15 November, Jakub Jankiewicz menulis bahwa kode hasil AI sebaiknya dirilis sebagai open source. Dua alasannya: model belajar dari kode open source, dan karya yang sepenuhnya dibuat AI seharusnya nggak punya hak cipta.

Diskusi Hacker News untuk tulisan itu mencapai 1.126 poin dan 175 komentar tingkat atas pada data item yang diambil. Ramai, tapi debat seramai itu belum tentu jadi kebijakan rilis buat tim kita.

## Kode buatan AI open source itu pilihan rilis, bukan kewajiban

Ada tiga pertanyaan yang sering kita campur jadi satu:

- apakah model ikut menulis kode ini,
- siapa yang bisa mengklaim hak cipta,
- dan apakah repo-nya harus dibuka untuk publik.

Ketiganya saling berhubungan. Tapi jawaban satu pertanyaan nggak otomatis menjawab dua lainnya.

Soal istilahnya dulu. Open source itu software yang dirilis dengan lisensi pemberi izin tertentu. Bukan nama lain dari public domain.

Repo publik tetap bisa bawa syarat lisensi. Sebaliknya, kesimpulan bahwa suatu karya nggak punya hak cipta nggak lantas menciptakan lisensi open source.

Perdebatan di kolom komentar tulisan Jankiewicz persis soal ini. Sebagian berpendapat kalau nggak ada hak cipta, ya nggak ada yang bisa dilisensikan. Sebagian lagi menunjuk kontribusi manusia: keputusan engineering dan desain yang spesifik untuk satu produk.

Bedanya bukan sekadar semantik. Tim bisa pakai AI dan tetap menutup produknya. Tim juga bisa memublikasikan perubahan yang dibantu AI, asal memperhatikan hak dan kewajiban yang berlaku pada kontribusi itu beserta dependency-nya.

Nama tool yang dipakai nggak cukup jadi dasar buat memilih.

## Apa kata U.S. Copyright Office soal hak cipta kode AI?

Ringkasan U.S. Copyright Office pada 2025 nggak menetapkan satu aturan untuk semua program yang pernah disentuh model. Ekspresi yang ditulis manusia bisa dilindungi.

Materi yang sepenuhnya dihasilkan AI, atau yang kendali manusianya kurang, nggak dapat perlindungan itu. Cuma memberi prompt juga belum cukup untuk dianggap sebagai penulis.

Laporan Part 2 kantor tersebut membedakan AI sebagai alat bantu dengan AI yang menentukan unsur ekspresif. Intinya lebih sempit daripada klaim "kode AI pasti bebas hak cipta". Laporan itu juga bukan pemeriksaan hukum atas satu pull request. Kalau keputusan rilis tim bergantung pada posisi hak cipta, minta nasihat profesional yang sesuai.

Dari sisi engineering, yang perlu dijaga justru jejak kerja manusianya. Prompt bukan pengganti dokumentasi soal apa yang dirancang dan apa yang sudah diverifikasi orang. Test yang hijau juga nggak membuktikan siapa penulis tiap baris.

## Kenapa batas tenant lebih penting daripada siapa yang menulis handler?

Ambil contoh sistem commerce multi-tenant seperti Dagango.com. Implementasi yang dihasilkan AI cuma satu lapisan dari perubahan itu.

Yang lebih menentukan ada di lapisan lain. Bagaimana identitas tenant masuk ke sebuah request. Record mana yang boleh disentuh satu merchant. Dan di titik mana authorization benar-benar dijalankan.

Sekarang bayangkan handler checkout yang tampak biasa. Dia menerima order ID dari request tanpa memastikan order itu milik merchant yang sedang aktif. Nggak ada yang aneh di kodenya, sampai ada request yang menyentuh data tenant lain.

Di situ letak risikonya. Siapa penulis barisnya hampir nggak relevan.

Jadi review-nya ke behavior, langsung. Kalau perubahan menyentuh data tenant, gue mau lihat:

- scope tenant dipasang di lapisan akses data, bukan cuma di interface;
- authorization untuk operasi baca dan tulis, termasuk jalur yang nggak langsung;
- test yang sengaja nyoba akses lintas tenant pakai ID merchant lain;
- regression test untuk flow checkout dan order yang normal.

Ini contoh praktik engineering, bukan klaim soal insiden terbaru di Dagango.com. Standarnya sama, entah kodenya ditulis engineer, dirancang coding agent, atau dikerjakan bareng.

## Gimana tim menentukan kode mana yang dipublikasikan?

Perlakukan kode buatan AI kayak kontribusi lain. Setelah itu, putuskan rilisnya secara eksplisit, jangan dibiarkan jadi default.

Kebijakan singkat buat reviewer bisa memuat empat pemeriksaan:

1. Diff-nya bisa direview dan tim paham behavior yang ditambahkan.
2. Test authorization dan regression mencakup batas yang relevan.
3. Dependency pihak ketiga dan lisensinya tercatat.
4. Ada orang yang bertanggung jawab memutuskan apakah kode itu masuk repo publik.

Checklist ini rekomendasi gue, bukan aturan resmi dari Copyright Office atau hasil voting di Hacker News. Sumber-sumbernya cuma membuka debat soal authorship dan rilis. Kebijakan operasionalnya tetap urusan tim.

Memisahkan langkah keputusan kayak gini juga bikin pertanyaan etika training data tetap di tempatnya. Apakah model seharusnya dilatih pakai karya open source tertentu? Itu isu serius.

Tapi beda dari pertanyaan apakah satu perubahan aman di-deploy. Beda juga dari apakah produk perusahaan sebaiknya dibuka. Kalau dicampur, dua diskusi itu jadi susah ditindaklanjuti.

Aturan kerja gue sederhana: review behavior-nya di diff, test batas yang bisa membocorkan data pelanggan lain, catat dependency, lalu tentukan apa yang mau dirilis.

Kode sekarang memang lebih murah dibuat. Tanggung jawab atas akibatnya di production tetap milik kita. 😅

## FAQ Teknis

### Apakah bantuan AI otomatis berarti kode harus dibuka?
Nggak. Pakai AI saja nggak menentukan status hak cipta, kewajiban lisensi, atau kebijakan rilis produk. Putuskan berdasarkan kontribusinya, dependency, dan konteks bisnis.

### Apa prompt cukup untuk membuktikan authorship manusia?
Menurut ringkasan U.S. Copyright Office 2025, prompt saja nggak cukup. Kendali manusia atas unsur ekspresif tetap jadi penentu, dan kasus tertentu mungkin butuh nasihat hukum.

### Apa yang perlu dites pada kode multi-tenant?
Coba request pakai ID milik tenant lain, lalu pastikan operasi baca dan tulis ditolak. Cek juga bahwa scope tenant dijalankan di luar interface pengguna.