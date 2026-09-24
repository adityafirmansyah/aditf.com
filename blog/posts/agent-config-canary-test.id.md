---
title: Config Agent Lo Gagal Diam-Diam? Ini Cara Ngeceknya
slug: agent-config-canary-test
date: 2026-09-24
excerpt: Claude Code sempat ngeload AGENTS.md cuma kalau telemetry nyala, gara-gara digantung ke remote flag. Ini tes lima detik yang bisa nangkep bug sejenis di setup agent apapun.
tags: ai-agents, claude-code, developer-tooling, debugging, llm-workflows
---

Bayangin ada file markdown di repo lo, tapi agent coding lo jalan lewat gitu aja. Nggak ada error. Nggak ada warning juga. Output-nya cuma jadi lebih bodoh dari yang seharusnya, tanpa lo sadar kenapa.

Ini yang kejadian ke sebagian user Claude Code begitu mereka matiin telemetry. Bug ini nongol di Hacker News tanggal 23 September dan dalam sehari udah tembus 466 poin dan 267 komentar. Penyebabnya? Konyol banget kalau dipikir: baca file lokal doang, tapi digantung ke remote flag yang user telemetry-off nggak bakal pernah bisa akses.

## Yang Sebenarnya Rusak

Claude Code versi 2.1.277 ngeluarin dukungan AGENTS.md lewat built-in plugin. Plugin ini defaultnya mati (`isOnByDefault = false`), dan buat nyalain dia harus cek dulu satu remote flag namanya `tengu_agents_md_mod`. Kalau flag itu gagal diambil, fallback-nya ke `false`.

Padahal baca file markdown dari folder kerja itu nggak butuh internet sama sekali. Tapi izin buat baca file-nya malah digantung ke sesuatu yang butuh internet.

Kalau telemetry mati, request buat ambil flag itu nggak pernah jalan, fallback-nya nyala, dan AGENTS.md nggak pernah kebaca. Diam-diam. Di setiap sesi.

Bagian paling nyebelinnya, cara-cara yang keliatan logis buat benerin ini malah nggak ngefek:

- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` bikin flag-nya gagal diambil.
- `DISABLE_TELEMETRY=1` juga sama, bikin gagal.
- Nyetel salah satu variabel itu ke `0` **nggak nolong**, soalnya cara Claude Code baca env-var itu nganggep asal ada nilai berarti "aktif", nggak peduli isinya `true` atau `false`.
- Nambahin config di `.claude/settings.json` buat clear dua variabel itu juga nggak ngefek apa-apa. Nggak ada opsi opt-in per-repo.

Satu-satunya yang beneran jalan itu override level-session lewat `claude --settings '{"env":{...}}'`, dan itu pun baru ngefek mulai sesi kedua, karena sesi pertama itu yang justru ngambil flag-nya. Third-party gateway kayak Bedrock sama Vertex juga kena masalah yang sama, karena remote flag-nya tetap nggak bisa resolve jadi `true` lewat jalur manapun.

## Ngakunya Cepet, Fix-nya Juga Cepet

Yang menarik, kecepatan orang ngaku salah di sini justru ngalahin kecepatan bug-nya nyebar. Issue di GitHub-nya baru dibuat tiga hari sebelum post HN ini muncul, lengkap sama data pengukuran dari penulisnya sendiri. Terus ada engineer Anthropic, `mpoteat`, langsung nongol di thread dan ngaku: "ini murni kesalahan manusia dari pihak gue."

Ternyata mekanismenya itu kill-switch buat rollout darurat, yang harusnya bisa dimatiin dari jarak jauh kalau ada masalah. Masalahnya, user yang telemetry-nya mati justru nggak akan pernah bisa nerima sinyal itu.

Fix-nya keluar di versi 2.1.281, di hari yang sama. Ngaku salah secara terbuka, pakai nama, dan langsung fix di hari yang sama itu bagian dari cerita ini yang sama pentingnya sama bug-nya sendiri.

## Tes Canary yang Bisa Lo Coba Sekarang

Hal paling berguna dari kejadian ini bukan bug-nya, tapi cara si penulis buktiinnya. Caranya: taruh satu kata unik di file instruksi lo, terus suruh agent-nya nyebutin kata itu, sambil dilarang keras baca file buat nyari jawabannya.

```
echo 'The canary word is PERIWINKLE.' > AGENTS.md
```

Abis itu, di sesi baru, tanya ke agent lo: "Kata canary-nya apa? Jawab NONE kalau nggak ada." Lakuin dua kali. Soalnya sesi pertama biasanya yang justru ngambil flag atau nge-refresh cache, jadi tes yang beneran valid itu di sesi kedua.

Pola ini bisa lo pake ke mana-mana, bukan cuma buat AGENTS.md. Tiap permukaan instruksi di setup multi-agent lo layak dicek pake cara yang sama:

- Hermes skill yang bisa aja ke-prune dari context.
- File CLAUDE.md atau AGENTS.md yang diam-diam gagal keload.
- System prompt yang bisa aja kepotong atau ketuker.
- Config MCP yang nunjuk ke server yang sebenarnya nggak pernah nyambung.

Intinya, "file-nya ada" itu bukan bukti kalau "agent-nya nerima file itu." Dua klaim itu beda, dan jarak antara keduanya itu persis tempat bug ini ngumpet, entah berapa sesi lamanya sampai ketahuan.

## Solusi Kalau Lo Gabungin Beberapa Tool Sekaligus

Kalau lo pakai Claude Code sama Codex di repo yang sama, import pakai `@path` itu nggak kena gate yang sama, jadi ini jalan pintasnya:

```
echo '@AGENTS.md' > CLAUDE.md
```

Konsekuensinya, lo balik lagi butuh file per-tool, padahal AGENTS.md tadinya justru dibikin buat nyingkirin itu. Tapi setidaknya cara ini beneran jalan, di saat plugin bawaannya nggak.

Masalah serupa juga ada di shared skills. Codex baca folder `.agents/skills` secara native, tapi Claude Code versi 2.1.280 cuma ngenalin path itu lewat perintah `/import`, yang justru nge-copy file-nya, bukan nge-link. Begitu ada perubahan di salah satu sisi, copy-nya langsung ketinggalan zaman.

Solusi dari penulisnya: bikin symlink, `.claude/skills` diarahin ke `../.agents/skills`, biar dua tool itu baca file yang sama persis di disk, nggak perlu maintain dua versi yang lama-lama beda sendiri. Ada komentator HN, `vorticalbox`, yang ngelaporin masalah duplikasi yang sama persis antara Cursor sama Claude, jadi ini bukan masalah satu tool doang.

## Kalau Lo Jalanin Fleet, Bukan Cuma Satu CLI

Ada dua komentar HN yang ngerangkum pelajaran desainnya lebih jelas dari yang bisa gue jelasin sendiri:

- `mgaldys4` bilang, baca file lokal itu seharusnya nggak pernah tergantung ke remote flag, dan diam-diam skip tanpa warning itu jauh lebih parah.
- `nfRfqX5n` nambahin observasi yang lebih tajam: orang aja sampe nggak bisa mastiin ini bug atau emang disengaja.

Ketidakjelasan kayak gitu justru jadi masalah tersendiri, karena sistem yang didesain dengan baik nggak seharusnya ninggalin pertanyaan kayak gitu menggantung.

Kalau lo lagi bangun atau ngejalanin harness agent apapun, aturan mainnya sebenarnya simpel:

1. Gate hal yang sifatnya remote di remote. Gate hal yang sifatnya lokal di lokal. Jangan dicampur.
2. Kalau terpaksa skip loading sesuatu, kasih warning. Skip diam-diam itu penyebab bug ini bisa lolos beberapa rilis tanpa ketahuan.
3. Version-pin harness lo. Perubahan behavior yang diam-diam pas upgrade itu jauh lebih bahaya dibanding gagal keras pas install.

Gue sendiri jalanin fleet Hermes multi-agent buat coding, QA, sama PR review lewat provider custom. Kejadian ini jadi pengingat langsung buat gue: cek ulang delivery instruksi di CI, jangan cuma asumsi kalau file config-nya udah ke-commit berarti udah kebaca beneran.

"Agent-nya kelakuannya aneh" itu pertanyaan soal delivery config duluan, baru soal model. Coba jalanin tes canary ini di setup lo minggu ini. Waktunya lebih singkat dibanding baca tulisan ini sampai selesai.
