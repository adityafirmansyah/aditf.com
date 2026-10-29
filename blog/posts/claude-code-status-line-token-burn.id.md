---
title: Kenapa Claude Code Menghabiskan 20% Request API Cuma Buat Status Terminal
slug: claude-code-status-line-token-burn
date: 2026-10-29
excerpt: Audit OpenTelemetry membongkar kalau Claude Code menghabiskan hampir 20% request API cuma buat tiga kata di status terminal. Polling frontier model buat urusan UI jelas jadi kebocoran arsitektur yang fatal.
tags: ai agents, claude code, prompt engineering, developer tools, software architecture
---

Ketika audit OpenTelemetry membongkar bahwa satu dari lima panggilan Application Programming Interface (API) di Claude Code cuma dipakai buat bikin status terminal tiga kata, sebuah kebocoran biaya terungkap ke publik.

Flamerix AI menganalisis metrik request dari event `claude_code.api_request` yang dikelompokkan berdasarkan `query_source`. Hasilnya bikin kaget. Rutinitas polling di background bernama `agent_summary` menyedot 16,4 persen konsumsi token dan 19,7 persen dari seluruh panggilan request.

Beban rutin di background itu bahkan mengalahkan obrolan interaktif utama user, yang cuma menghabiskan 15,7% token. Audit telemetri ini menyoroti sejumlah angka gila:

- 96% dari seluruh query status dikirim langsung ke Claude 3 Opus.
- Rasio token input banding output menyentuh angka sekitar 9.000 : 1.
- Setiap tiga puluh detik, client menyodorkan 50.000 sampai 100.000 token ke model hanya demi menghasilkan tiga kata di layar terminal.
- Animasi spinner di terminal ternyata bersaing langsung dengan pekerjaan coding utama untuk berebut kuota request model.

## Loop Polling 30 Detik yang Terkunci Mati

Biang keroknya ada di implementasi Claude Code versi 2.1.257 sampai 2.1.312.

Developer yang membongkar binary client menemukan timer `setInterval` yang dipatok kaku di angka tiga puluh detik.

Cara kerjanya benar-benar boros. Client bakal menyapu bersih seluruh transkrip percakapan subagent aktif, lalu mengunggah tumpukan teks raksasa itu ke model frontier.

Semua kerepotan jaringan itu cuma demi satu hal sepele. Client cuma ingin memperbarui teks status di pojok CLI, seperti "menganalisis repo" atau "menjalankan test".

Yang bikin developer jengkel, jalur buat mematikan fitur ini dikunci mati.

Di dokumentasi resmi memang tertulis opsi `agentProgressSummaries`. Tapi di baris kode aslinya, opsi itu dibungkus ekspresi OR yang memaksa nilainya selalu `true`.

Akibatnya, kalau lo menyalakan tiga subagent sekaligus di terminal:

- Transkrip percakapan tetap dikirim meski agent lagi bengong menunggu proses shell.
- Riwayat obrolan makin panjang, sehingga payload prompt polling berikutnya otomatis makin membengkak.
- Koneksi internet lokal lo dipaksa mengunggah puluhan kilobyte teks duplikat tiap setengah menit.

Engineer Anthropic, Edwin Arbus, akhirnya mengonfirmasi mekanisme ini di Hacker News pada thread #50284255.

Dia menyebut kalau query status ini rata-rata memakan sekitar 6% dari seluruh pengeluaran terminal pengguna yang menyalakan telemetri. Arbus juga merinci rencana perbaikan prompt cache di versi 2.1.311+ serta mode ringkasan pendek memakai model yang lebih kecil.

## Ilusi Murah dari Prompt Cache

Banyak orang awalnya mengira kebiasaan polling ini nggak bakal bikin dompet jebol karena ada diskon prompt cache.

Secara teori, membaca transkrip yang sudah nangkring di cache memang cuma kena tarif 10% dari harga input normal.

Tapi diskon 90% itu cuma manis di atas kertas.

Begitu lo hitung beban armada agent secara riil, angkanya langsung bikin sesak napas:

- Transkrip sepanjang 100.000 token dengan diskon 10% tetap ditagih setara 10.000 token tiap tiga puluh detik.
- Tiga subagent aktif bakal menghasilkan 360 query status dalam kurun satu jam.
- Rutinitas latar belakang ini membakar 3,6 juta token input per jam cuma demi memoles tiga baris teks terminal.
- Kalau dikali jam kerja seharian, saldo API lo terkuras puluhan juta token tanpa menghasilkan baris kode baru.

Itu baru hitungan kalau semua request dapat cache hit.

Ceritanya langsung beda begitu ada cache miss.

Masalahnya, entri prompt cache punya masa kedaluwarsa Time To Live (TTL) selama lima menit.

Kalau subagent lo berhenti sejenak menunggu build yang berat atau respons jaringan yang lambat, jendela cache ini bakal hangus tanpa aba-aba. Belum lagi setiap kali agent menulis file baru, awalan prompt otomatis berubah dan memicu miss baru.

Di sinilah letak jebakannya.

Audit Flamerix AI membuktikan bahwa 2% kegagalan cache ternyata menyumbang lebih dari sepertiga total biaya fitur ringkasan status. Sekali saja Opus terkena cold miss, seluruh penghematan diskon yang dikumpulkan berjam-jam langsung lenyap seketika.

## Menjinakkan Bytecode Bun Saat Runtime

Niat buat mematikan timer ini di lokal ternyata terhalang cara distribusi Claude Code.

Paket CLI ini dikirim dalam format bytecode Bun yang sudah dikompilasi, bukan file JavaScript biasa di `node_modules` yang gampang dipotong pakai editor teks.

Tim Flamerix AI mengakali batasan ini lewat preload hook milik Bun dengan memanfaatkan variabel environment `BUN_OPTIONS=--preload`.

Script `no-agent-summary.js` buatan mereka mencegat pendaftaran timer saat startup:

```javascript
// Hook setInterval untuk melumpuhkan loop agent_summary
const originalSetInterval = globalThis.setInterval;

globalThis.setInterval = function (callback, delay, ...args) {
  const fnStr = Function.prototype.toString.call(callback);
  if (fnStr.includes("agentProgressSummaries") || fnStr.includes("agent_summary")) {
    // Tunda timer ke 2^31 - 1 milidetik (~24,8 hari)
    return originalSetInterval.call(this, callback, 2147483647, ...args);
  }
  return originalSetInterval.call(this, callback, delay, ...args);
};
```

Trik ini memanfaatkan `Function.prototype.toString` buat mengintip isi callback milik `agent_summary`.

Begitu fungsi target terdeteksi, interval timer langsung dilempar ke 2147483647 milidetik.

Loop polling status pun praktis lumpuh selama 24 hari ke depan tanpa memicu error apa pun di CLI.

Anthropic belakangan merilis versi 2.1.311+ buat membenahi breakpoint cache agar biaya cold miss nggak melonjak liar.

## Telemetry Harus Push dan Lokal

Kasus ini menyodorkan pelajaran arsitektur yang sangat mahal bagi siapa pun yang membangun sistem agent.

Di homelab pribadi gue, armada agent Hermes berjalan di atas server Celeron J4105 hemat daya dan beberapa VPS Linux. Agent kita mengurus penulisan kode, pengetesan Quality Assurance (QA), dan review Pull Request (PR).

Kalau harness kita sampai polling Opus tiap tiga puluh detik cuma demi muter animasi spinner di CLI, saldo API kita bakal ludes sia-sia.

Dan kita memang nggak boleh merancang pipeline yang gampang bocor seperti itu.

Desain User Experience (UX) terminal seharusnya murni bekerja secara lokal dan digerakkan oleh event.

- Kirim status berbasis transisi deterministik. Terbitkan status saat tool selesai jalan atau langkah kerja berganti tanpa bergantung pada timer interval.
- Serahkan ringkasan ke model lokal. Kalau butuh merangkum riwayat obrolan, delegasikan ke Small Language Models (SLMs) lokal atau parser string yang gratis.
- Pisahkan tampilan terminal dari konsumsi token berbayar. Antarmuka cuma perlu memantau status mesin state lokal, bukan rutin memanggil cloud.

Harness agent yang dibuat oleh penyedia model sering membawa insentif tersembunyi.

Polling berkala yang dibiarkan longgar bakal diam-diam melipatgandakan konsumsi token pengguna, sambil menutupi kebocoran itu lewat animasi terminal yang kelihatan sibuk.

Sebagai developer, kita butuh arsitektur yang transparan dan berbasis event.

Berhenti memanggil Opus cuma demi pemanis tampilan terminal.
