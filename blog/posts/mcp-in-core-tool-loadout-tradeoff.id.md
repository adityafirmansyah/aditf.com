---
title: Pi Bilang Nggak Akan Pakai MCP, Terus Justru Ditaruh di Core
slug: mcp-in-core-tool-loadout-tradeoff
date: 2026-10-03
excerpt: Setahun Pi ngotot nggak akan dukung MCP, eh rilis terbarunya malah naruh MCP di core. Alasannya bukan karena MCP jadi bagus, tapi karena sandbox di bawahnya yang beres.
tags: ai-agents, mcp, tooling, architecture, self-hosting
---

Tanggal 29 September Earendil nulis post "You Said No MCP!". Thread-nya jadi salah satu debat HN yang jarang-jarang: 351 komentar tapi isinya tetap teknis.

Ceritanya soal pembalikan sikap yang terbuka banget. Setahun lamanya situs Pi dan podcast-podcast-nya bilang hal yang sama: Pi nggak dukung MCP. Sekarang rilis terbarunya malah naruh MCP di core.

Reaksi refleksnya: berarti protokolnya menang. Baca post-nya sampai habis, dan alasannya beda. Nggak ada yang bikin mereka berubah pikiran soal MCP-nya. Yang bikin mereka berubah justru sandbox JavaScript bernama Codemode, yang emang layak dibangun sendiri.

## Ini keputusan refactor, bukan pindah keyakinan

Argumen mereka rapi, dan sayangnya kelewat gampang ditelan headline.

- "The first thing to remember is that the world is not static."
- MCP yang mereka tolak setahun lalu bukan MCP yang mereka rilis sekarang.
- Perubahan kode yang MCP butuh ternyata "generally useful" buat mereka sendiri.

Poin terakhir itu yang paling penting. Masukin MCP ke core butuh hal yang sama dengan yang Pi butuh: "a sandbox to play with in the form of an interpreter."

Jadi sandbox-nya mereka bangun duluan. MCP cuma numpang di lantai yang udah mau mereka bangun.

## Komposisi masih jadi PR yang belum kelar

Mereka nggak pura-pura masalahnya hilang. Baca pengakuannya utuh-utuh, karena di situ mereka memindahkan siapa yang salah:

> "The biggest issue with MCP continues to be that it's hard to compose. Even with codemode, which is just a neat little sandbox to allow composing of tool calls, MCP doesn't fully deliver on this."

Terus kalimat yang kelewat di thread. Kesulitan itu, tulis mereka, "less the problem of MCP but the MCP servers out there."

Nah ini intinya buat yang ngoprek harian. Protokolnya cuma spesifikasi. Servernya kerjaan orang lain, dan kebanyakan dibangun bukan buat kerjaan ini.

## Kontrak tool-nya yang bermasalah

Deskripsi mereka soal MCP server rata-rata pasti familiar buat lo yang pernah lihat context window penuh pelan-pelan:

- servernya "just dump tools into the context,"
- terus balikin prosa "to optimize on their side for token efficiency by returning text."

Yang mereka mau justru kontrak beda. MCP sebaiknya duduk "much closer to OpenAPI with intelligent tool discovery," dengan dua aturan:

1. tool balikin structured data, bukan teks;
2. tool bisa ketemu lewat dokumentasi dan deskripsinya.

Itu sumbu buat ngejudge tool surface apa pun, apa pun nama protokolnya. Tool yang nyemburin satu paragraf cuma buat bilang isi satu field JSON itu pajak yang gue bayar tiap turn.

## Codemode itu pelajaran engineering-nya

Buang dulu bingkai MCP-nya, dan Codemode jadi pola desain yang bisa lo contek sekarang juga, mau lo pakai protokolnya apa nggak.

- Jalan di sisi harness, "where the harness runs," karena loop harness itu trusted sementara tool yang dipanggilnya biasanya nggak.
- Nyusun panggilan pakai JavaScript. Beberapa panggilan jalan bareng, nggak usah satu-satu tiap turn.
- State-nya nyimpen "as part of the session transcript instead of the file system."
- Cerita keamanannya jujur dan sederhana: engine JavaScript kecil bisa dikirim "as WASM binaries and allow reasonable levels of protection."

Semua itu nggak jalan di model lama. Mereka sebut syaratnya gamblang, karena berbulan-bulan sebelumnya kerja buat bikin Pi "make sense with new models that allow deferred tool loading, mid-conversation system messages and reasoning level changes."

Ini bagian yang harusnya dibawa pulang. Ngeluasin tool surface baru aman setelah harness lo bisa nunda tool loading, balikin hasil terstruktur, dan nyusun di dalam sandbox yang umurnya seumur sesi.

Urutannya penting juga, dan sering kebalik. Orang biasanya nambah tool dulu, terus baru panik mikirin sandbox. Cara itu keliatannya cepat, tapi biayanya ketagih di belakang: context bengkak, prompt jadi susah ditebak, dan tiap kali ada tool baru lo ngutak-atik ulang bagian yang seharusnya udah stabil.

Contoh nyatanya loop di atas issue tracker Linear. Empat worker paralel ngklasifikasi nada komentar dan ngeranking reporter paling kesel. Transcript-nya ditutup dengan hitungan "... (331 earlier calls)": satu baris ringkasan mewakili 331 panggilan tool yang nggak perlu dipegang modelnya.

## Loadout gue sendiri sebenarnya berapa mahal

Gue jalanin enam belas profil agent dari satu box, jadi saran "tinggal tambah protokolnya" itu langsung nabrak budget yang nyata. Gue hitung langsung, per platform, di semua profil itu.

- Platform CLI mendeklarasikan 27 builtin toolset, dan 19 di antaranya diaktifin.
- Sisi Discord mendeklarasikan 27 juga, 17 yang diaktifin.
- MCP server yang dikonfigurasi di semua profil itu: nol.

Nol itu bukan kebetulan. Tiap toolset yang lo aktifin langsung makan context tiap turn, dan trik deferred loading yang bikin Codemode aman justru yang bikin Pi bisa ngepasang surface lebar tanpa bayar semuanya sekaligus. Tanpa itu, nambah 27 toolset malah bikin model lebih payah di 19 yang udah ada.

Yang bikin angka itu penting bukan besar-kecilnya, tapi efeknya ke kualitas jawaban. Tool yang nggak pernah kepakai tapi tetap nangkring di context tetap kehitung model tiap turn.

Surface yang gemuk bikin model lebih gampang milih tool yang salah. Bukan karena modelnya tolol. Pilihannya cuma kebanyakan.

Jadi nol MCP server di seluruh profil itu bukan penolakan ideologis. Itu cuma efek samping dari kebiasaan ngukur dulu sebelum nambah.

## Bantahan di thread yang sayang buat dilewat

Bantahan terbaik di thread bukan soal budaya GitHub. Empat yang sayang dilewat:

- `otabdeveloper4` bilang MCP itu "the NIH non-standard version of OpenAPI."
- `_fw` balas pakai ubiquity: MCP memang suboptimal, "but so is USB-C. So is NVME, so is HDMI."
- `ramses0` nunjuk xkcd #927 dan standar-standar yang bersaing di situ.
- `mikeocool` nggambarin setup OpenAPI plus OAuth2 yang harusnya udah lama ada.

Yang paling kuat `wren6991`: "if LLMs want to compose multiple operations, they have the perfect tool for this: bash." Kalau itu bener, Codemode cuma bikin roda baru buat hal yang udah ada.

`hobofan` ngasih balasan yang bikin itu tumbang. "In many scenarios, e.g. running the harness server-side, as is the case for chat interfaces, you don't really want to expose OS shell access as that opens up a huge security attack surface."

Itu inti post-nya cuma dalam satu tukeran. Komposisi butuh isolasi, dan isolasi itu yang emang mau lo bangun.

## Isolasi murah itu yang nentuin batasnya

Migrasi Netlify dari V8 isolate ke Firecracker MicroVM itu pelajaran yang sama, dilihat dari sisi infrastruktur. Angkanya konkret:

- sekitar 5x lebih cepat di median;
- warm invocation ~5-6 ms p50, turun dari 25-40 ms;
- p99 47,4% lebih cepat;
- availability 99,998%;
- cold invocation di sekitar 1,2% request, sekitar 9 ms.

Sisi keamanannya yang perlu dicerna. Kata `phickey`, "the V8 team does not consider them to be a security boundary."

Dua post ini sebenernya ngejawab satu pertanyaan. Seberapa banyak yang aman lo kasih ke model? Jawabannya ditentukan seberapa murah isolasi lo, dan seberapa kuat isolasi itu. Sandbox seumur sesi dan sebuah MicroVM itu taruhan yang sama di dua ukuran beda.

## Yang gue bawa pulang

- **Nilai tool surface dari kontraknya.** Hasil terstruktur dan discoverability yang beneran jalan ngalahin branding protokol.
- **Bangun sandbox-nya sebelum ngeluasin loadout.** Komposisi tanpa isolasi cuma attack surface lebih gede dengan marketing lebih bagus.
- **Tunda tool loading.** Surface lebar cuma murah kalau modelnya nggak harus lihat semuanya.
- **Perhatiin apa yang dilempar tool ke transcript.** Keruntuhan 331 panggilan jadi satu baris itu target desain, bukan hal aneh.

Pi nggak nyerah sama MCP. Mereka bangun interpreter, dan MCP kebetulan masuk di dalamnya. Alasan itu jauh lebih masuk akal buat ngerilis sebuah protokol daripada sekadar suka sama protokolnya.

Ada satu hal yang sering kelewat waktu orang ngomongin MCP: yang diuji sebenernya bukan protokolnya, tapi disiplin harness-nya. Kalau harness lo bisa nunda tool loading dan nyusun panggilan di dalam sandbox, protokol apa pun bakal keliatan lumayan. Kalau nggak bisa, protokol terbaik di dunia pun cuma nambah beban ke context yang udah sesak.

Dan lucunya, posisi awalnya nggak salah. Mereka cuma salah nebak kapan batasnya bergeser.
