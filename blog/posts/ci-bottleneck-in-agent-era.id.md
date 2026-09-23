---
title: Antrean PR Dibanjiri AI Agent, CI Kita Hampir Kolaps
slug: ci-bottleneck-in-agent-era
date: 2026-09-22
excerpt: Coding agent bikin nulis PR jadi nyaris gratis, artinya pipeline CI-mu sekarang jadi bottleneck baru. Ini yang bisa dicontek dari rework CI-nya Linear buat skala tim kecil.
tags: ci-cd, ai-agents, developer-productivity, testing, github-actions
---

Empat belas PR nangkring di antrean pas Selasa pagi, semuanya dari agent, nggak ada satupun dari manusia yang ngetik satu baris kode. Ini fleet Hermes yang gue jalanin buat dagango.com dan beberapa repo klien di minggu biasa. Coding agent sama QA agent nggak tidur, nggak capek nulis test, dan nggak merasa bersalah buka PR #15 pas PR #12 masih running CI. Yang pertama kali jebol bukan codebase-nya. Yang jebol duluan itu pipeline yang harusnya nge-validate itu semua.

Linear nulis soal masalah persis ini tanggal 21 September ("AI coding has made CI a bottleneck, so we reworked ours to keep up"), dan dalam sehari udah tembus 230-an poin dan 250-an komentar di Hacker News. Kayaknya semua tim yang jalanin agent di skala besar mentok di titik yang sama, di waktu yang hampir bareng. Data produk Linear sendiri cerita gambaran yang lebih luas: tim yang pakai coding agent naik hampir tiga kali lipat PR mingguan dalam dua tahun, dari 21 jadi 65, sementara AI bergerak dari kurang dari satu issue per seribu jadi hampir separuh dari semua issue yang dibuat di Linear. Khusus di post CI-nya, mereka bilang test suite internal hampir empat kali lipat sejak Januari. Ini bukan masalah khusus Linear. Ini yang bakal terjadi ke pipeline manapun yang dibangun buat manusia, begitu "junior developer" kamu ternyata agent yang jalan paralel 24 jam.

## Bottleneck-nya pindah dari nulis kode ke verifikasi kode

Bertahun-tahun, kendala di software delivery itu di authoring: nulis kode, nulis test, nulis deskripsi PR yang nggak ada yang baca. Agent bikin biaya itu turun mendekati nol. Kapasitas CI nggak ikut turun, karena CI itu ukurannya buat kecepatan manusia bikin PR, dan agent bikin PR di kecepatan yang sama sekali beda. Linear berhasil jagain waktu tunggu PR di 5-6 menit walaupun test suite-nya meledak, tapi cuma karena mereka aktif motong runner time per test kira-kira setengahnya. Kapasitas verifikasi sekarang jadi hal yang harus kamu desain, sama kayak kamu desain buat load database atau rate limit API.

Gue ngerasain ini langsung waktu gue lepasin tiga coding agent bareng-bareng ke repo dagango.com. Menit GitHub Actions di plan kita habis sembilan hari, padahal biasanya cukup buat sebulan. Masalahnya bukan kualitas kode. Masalahnya pipeline-nya keselek jumlah job.

## Kemenangan termurah: benerin infra dulu sebelum ngoprek logic pipeline

Lever pertama Linear itu nggak butuh ubah pipeline sama sekali: pindah dari GitHub Actions ke runner pihak ketiga yang lebih cepat bikin job rata-rata 34% lebih ngebut, sementara `tsc` type-check turun 52%. File workflow-nya sendiri nggak berubah sama sekali.

Buat tim kecil atau budget UMKM, di volume job era-agent, runner hosted premium cepat jadi mahal, karena billing per-menit langsung numpuk begitu jumlah job meledak naik. Self-hosted runner di hardware biasa ngubah hitungannya. Punya gue jalan di homelab yang malu-maluin kalau disebut di forum hardware, dan tetep menang dari sisi waktu sampai hasil pertama muncul. Alasannya simpel: nggak ada antrean dan nggak ada meter yang jalan buat tiap job.

## Hitung berapa kali runner start, bukan berapa detik

Pelajaran kedua Linear: benerin critical path dulu sebelum micro-optimize apapun di dalemnya. Batasin fetch depth git aja bikin gate job paling lambat mereka turun dari 94 detik ke 20 detik. Batching tujuh check kecil jadi dua job hemat sekitar 87.000 runner-minute per bulan, 11,8% dari total spending CI mereka. Dua-duanya nggak nyentuh logic test sama sekali. Dua-duanya datang dari ngitung berapa job yang jalan, terlepas dari berapa lama tiap job jalan.

```yaml
# Sebelum: 7 job terpisah = 7x cold-start tax
jobs:
  lint: {...}
  typecheck: {...}
  unit-fast: {...}
  unit-slow: {...}
  format-check: {...}
  license-check: {...}
  deps-audit: {...}

# Sesudah: 2 job, check sama, runner start jauh lebih sedikit
jobs:
  static-checks: # lint + typecheck + format + license + deps-audit
    run: pnpm lint && pnpm typecheck && pnpm format:check && pnpm license:check && pnpm audit
  tests:
    run: pnpm test:unit
```

Setiap job start punya overhead tetap (checkout, restore dependency, setup environment) sebelum dia jalanin satu assertion pun. Kalikan itu sama volume PR hasil agent, dan itu berhenti jadi angka kecil yang bisa diabaikan. Di pipeline kita bentuknya beda, lima job alih-alih tujuh kayak punya Linear, tapi fix-nya sama persis: gabungin jadi dua job motong rata-rata waktu gate PR hampir sepertiga tanpa nyentuh satu test pun.

## Isolasi test sekarang jadi cost center, dan agent bikin risikonya naik

Isolasi per-file default-nya Vitest itu rebuild module graph di setiap file test. Aman, tapi mahal di skala besar. Opt-in `isolate: false` punya Linear itu penghematan terbesar mereka, sekitar 17% dari spending bulanan CI, nurunin runtime API shard dari 32,8 ke 22 menit. Ini juga perubahan paling berisiko di daftar itu: matiin isolasi berarti test bisa bocor state satu ke yang lain kalau nggak ditulis hati-hati.

Agent kamu sekarang nulis sebagian besar test kamu, dan mereka nggak reliable buat tahu kapan sebuah test butuh isolasi. Manusia yang pernah kena getahnya shared mutable state nulis test defensif karena udah pernah kapok. Agent yang cuma dioptimasi buat "bikin CI hijau" bakal santai nulis test yang lolos pas isolated dan malah ngerusak fixture test berikutnya pas isolasi dimatiin. Linear ngegate ini pakai comment opt-in eksplisit dan requirement teardown per file: tandain test yang aman isolasi satu-satu, dan review penandaan itu kayak review diff sensitif keamanan. Di proyek Next.js kita, itu artinya cuma unit test pure-function dengan nol shared module state. Apapun yang nyentuh fixture database atau mocked API client tetap pakai isolasi penuh, titik.

## Jangan cache hal yang lebih murah dibangun ulang

Cache `node_modules` punya Linear makan waktu sekitar 28 detik buat di-restore. `pnpm install` yang difilter cuma 7,5 detik. Mereka hapus cache-nya. Caching kerasa kayak kemenangan gratis karena itu saran default di mana-mana, tapi caching punya biaya restore yang jarang ada yang benchmark lawan alternatifnya. Pelajarannya lebih luas dari sekadar node_modules: cache itu taruhan bahwa waktu restore lebih cepat dari waktu rebuild, dan taruhan itu nggak selalu menang.

## CI di era agent harusnya gate di apa?

Thread HN di bawah post Linear kebagi jadi dua kubu. Satu komentator, yieldcrv, bilang unit test secara umum udah jadi kosmetik yang nggembungin angka coverage, dan bikin poin yang layak direnungin: dia nggak lihat agent make test beda dari developer junior atau mid-level, karena manusia juga sebenarnya nggak rigorous-rigorous amat soal itu. Komentator lain, sz4kerto, bikin poin praktisi yang lebih tajam: review diam-diam bergeser dari review kode ke review test, karena di situlah sekarang letak klaim beneran soal correctness dari agent. Solomon Hykes, founder Docker, bilang build dan test harus dijadwalin sebagai satu sistem yang jalan bareng, bukan dua proses terpisah.

Setelah jalanin fleet ini tiap hari, gue akhirnya punya satu prinsip sederhana:

Gate ketat itu cuma perlu dipasang di flow yang benar-benar berhubungan langsung sama duit masuk, atau flow kecil yang kalau gagal bisa bikin bisnis berantakan. Sisanya? Bikin semurah dan secepat mungkin.

Satu hal yang cukup cepat gue pelajari: test yang hijau dari agent bukan berarti apa yang dites itu otomatis benar di dunia nyata.

Agent bakal terus bikin PR dengan speed mereka sendiri. Pipeline kita mau siap atau nggak, mereka tetap jalan.

Dan ternyata pipeline kita nggak siap. 😅

Kita baru sadar ketika jatah GitHub Actions untuk sebulan habis cuma dalam sembilan hari.

Fix-nya ternyata bukan sekadar nambah check sampai semuanya hijau. Yang lebih penting adalah dari awal memperlakukan runner startup dan isolation policy sebagai bagian dari engineering design.

Bukan sesuatu yang baru ditempel belakangan karena kita butuh lebih banyak checkmark hijau.

Menurut gue, ini salah satu perbedaan penting ketika mulai menjalankan AI agent dalam skala fleet: masalahnya bukan cuma "apakah agent bisa menghasilkan code yang benar?", tapi juga "apakah sistem kita siap menghadapi seberapa cepat mereka bisa menghasilkan code?"
