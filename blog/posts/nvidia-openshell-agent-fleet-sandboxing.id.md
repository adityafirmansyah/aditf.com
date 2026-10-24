---
title: NVIDIA OpenShell: Kenapa Fleet Agent Butuh Prover SMT dan Proxy Kredensial
slug: nvidia-openshell-agent-fleet-sandboxing
date: 2026-10-24
excerpt: OpenShell nggak pernah kasih kredensial asli ke agent, dan tiap perubahan policy dicek dulu pakai solver Z3. Bagian sandbox-nya gampang ditiru. Model per-sandbox-nya yang bikin repot.
tags: ai-agents, sandboxing, rust, security, devops
---

OpenShell mendarat di Hacker News 22 Oktober 2026 dengan 490 poin dan 211 komentar.

Versinya sekarang 0.1.5, sudah lima patch lewat dari tag 0.1.0 di akhir September. Lisensinya Apache 2.0. Sebagian besar isi thread-nya perang soal telemetry. Yang gue baca ulang justru arsitektur di bawahnya.

Sampai beberapa waktu lalu, cara gue jalanin coding agent cuma satu container plus `-e OPENAI_API_KEY`.

Itu bukan isolasi. Itu bungkus praktis buat nyerahin tagihan cloud gue ke proses yang nurut sama teks apa pun yang kebetulan dia baca.

Container cuma jawab satu pertanyaan: apakah dua proses ini bisa lihat memori satu sama lain. Pertanyaan yang nggak dijawab: apakah proses ini bisa lihat secret.

Begitu key-nya nangkring di environment, semua mekanisme yang bikin agent berguna berubah jadi jalur keluar.

- Dependency jahat di lockfile.
- Build script yang kena poisoning.
- `curl` yang tiba-tiba muncul jam dua pagi karena modelnya ngarang.

DNS tunneling aja udah cukup. Beberapa ratus lookup nggak akan ada yang sadar.

## Kredensial berhenti di proxy, nggak pernah masuk sandbox

Yang OpenShell ubah itu strukturnya. Agent-nya nggak pegang kredensial sama sekali. Yang bikin ini jalan bukan panjangnya daftar fitur, tapi di mana kredensialnya disimpan.

Kredensial baru nempel waktu request-nya benar-benar keluar, dan cuma buat endpoint yang sudah di-approve. Yang nempelin supervisor, yang rumahnya di luar sandbox.

Sisi sandbox-nya justru bagian yang paling murah ditiru:

- `Landlock` membatasi file mana yang bisa dibuka workload.
- `seccomp` user notification menahan operasi jaringan sebelum dieksekusi.
- Workload-nya jalan sebagai satu identitas non-root, tanpa capability Linux apa pun.

Yang bikin semua itu jadi satu kesatuan justru koneksi antara dua sisi itu. Supervisor dan sandbox ngobrol lewat satu kanal HTTP/2 yang saling terautentikasi, dan kanal itu nampung banyak stream independen.

Transport-nya dipilih compute driver:

- Unix socket buat Docker dan Podman,
- TCP buat Kubernetes,
- vsock buat MicroVM.

Tiap koneksi TCP dapet stream sendiri, lengkap dengan backpressure sendiri. Download paket yang lambat nggak bisa nyumbat resolusi DNS atau exec.

Siapa pun yang pernah jalanin agent lewat proxy single-thread pasti tahu betapa nyebelinnya waktu satu request nyangkut dan sisanya ikut mati.

## Solver-nya cuma jawab empat pertanyaan

Policy expansion itu titik di mana sandboxing agent biasanya mulai rusak.

Agent nabrak tembok, ngusulin satu rule, rule-nya di-approve. Setahun kemudian file policy-nya jadi tumpukan pengecualian yang nggak ada yang berani cabut.

Jawaban NVIDIA: `openshell-prover`.

Krate Rust ini nyusun tiga input jadi satu model Z3 SMT, yaitu policy-nya, set kredensial yang nempel di sandbox, dan registry kemampuan tiap binary.

Habis itu dia jalanin reachability query di empat kategori:

- `link_local_reach`: policy-nya nembus host di `169.254.0.0/16` atau `fe80::/10`? Itu alamat metadata cloud.
- `l7_bypass_credentialed`: ada binary pakai protokol non-HTTP yang bisa nyampe host yang kredensialnya masuk scope?
- `credential_reach_expansion`: ada binary nyampe pasangan host dan port baru, padahal kredensialnya masuk scope?
- `capability_expansion`: di endpoint yang udah dicapai binary itu, perubahannya nambah HTTP method?

Dua yang pertama unconditional. Dua sisanya sifat delta: gateway buktiin policy baseline dan policy gabungan, terus cuma nampilin jalur yang baru muncul.

Ada temuan? Auto-approval diblokir. Delta yang kosong baru boleh lewat kalau reviewer sudah opt-in lewat `proposal_approval_mode` di scope gateway atau sandbox.

Yang sering ketuker: boundary check dan proposal risk check jawab pertanyaan beda. Lolos yang satu sama sekali nggak bilang apa-apa soal yang lain.

CLI-nya buat boundary check, dipakai agent yang perlu mastiin policy subagent tetap di dalam policy induknya. Advisor jalanin proposal risk check tiap agent ngusulin rule baru.

## Satu sandbox aman, fleet-nya belum tentu

Kalimat ini yang gue tempel di dokumen desain internal: model-nya per sandbox.

README krate-nya sendiri nyebut dia nggak nalar soal intent lintas sandbox atau lintas binary. Dua sandbox yang berbagi kredensial lewat policy eksternal dianalisis sendiri-sendiri.

Itu confused deputy, dan nggak perlu penyerang canggih buat manfaatinnya.

Agent yang koneksinya dibatasi, tapi boleh ngirim task ke deployment agent yang bebas lewat message bus, punya jalur keluar yang nggak dijelasin policy mana pun. Sandbox-nya masih utuh. Yang bocor fleet kita.

Formal verification nggak bikin ini lebih buruk. Dia bikin ini kelihatan, karena batas modelnya ditulis terbuka di README.

Kalau lo nyambungin delegasi antar agent, graf-nya yang harus diverifikasi. Siapa boleh ngirim ke siapa, dan kredensial siapa yang nempel di ujung rantai.

Buktiin satu node doang itu syarat minimum, bukan kontrak lengkapnya.

## Telemetry nyala dari awal, ada tiga jalan keluar

Telemetry dibawa sebagai Cargo feature, dan default-nya nyala. Cakupannya sempit menurut dokumentasi: sandbox lifecycle outcomes, provider profile buckets, policy decision counts, plus agregat kategori penolakan jaringan.

Nggak ada nama sandbox. Nggak ada hostname atau file path. Prompt dan kredensial juga nggak ikut.

Di thread, `overflowy` nempel policy itu plus flag opt-out-nya. Debatnya ngalir dari situ.

`lcampbell` nyorot pilihan katanya: kategori yang dikumpulkan dibuka dengan "such as" dan bukan daftar lengkap. Tapi dia juga bilang disable yang didokumentasikan itu sudah cukup.

`Lammy` beda arah. Buat dia nggak ada koneksi yang anonim, karena koneksinya sendiri udah bocorin IP dan jam kerja lo.

`dangoodmanUT` paling jelas nyebut tradeoff-nya: default telemetry itu default yang buruk, sementara kontrol yang disediain "almost too pedantic".

Gue setuju dua-duanya. Justru karena bagian kedua itu, bagian pertama masih bisa dimaafkan.

Jalan keluarnya tiga, dan nggak setara:

- `OPENSHELL_TELEMETRY_ENABLED=false` di deployment gateway.
- `server.telemetryEnabled=false` buat instalasi Helm.
- Build ulang dengan `--no-default-features --features defaults-without-telemetry`, yang bikin binary-nya nggak punya endpoint maupun kode pengirim.

Dua yang pertama itu konfigurasi. Yang ketiga satu-satunya yang gue percaya di box yang megang kredensial produksi, karena flag bisa dicabut sama orang berikutnya yang buka values file.

## Yang gue bawa pulang

Runtime-nya bukan pelajarannya. Pelajarannya ada di pemisahan antara apa yang bisa dilakukan agent dan apa yang dia tahu.

Mediated channel-nya OpenShell jawab pertanyaan kedua dengan benar. Harness buatan sendiri biasanya nggak kepikiran nanya.

Yang kedua: verifier dengan batas yang ditulis lebih berguna, bukan heuristik dengan landing page bagus. Model per sandbox itu keterbatasan nyata.

Bedanya, keterbatasan itu ditulis di README. Jadi gue bisa desain di sekitarnya sebelum ketemu langsung waktu incident.

Kalau gue mulai fleet besok, urutannya membosankan:

- Kredensial cuma lewat proxy dulu.
- Batas filesystem dan syscall kedua.
- Prover SMT paling akhir, setelah dua itu ada.

Solver yang nge-review policy yang udah ngasih API key mentah cuma ngitung rapi di masalah yang salah.

Dan itu bukan salah OpenShell. Itu urutan kerja gue sendiri yang kebalik. 😅
