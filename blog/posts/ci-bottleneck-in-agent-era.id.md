---
title: Antrean PR Dibanjiri AI Agent, CI Kita Hampir Kolaps
slug: ci-bottleneck-in-agent-era
date: 2026-09-22
excerpt: Coding agent bikin nulis PR jadi nyaris gratis, artinya pipeline CI-mu sekarang jadi bottleneck baru. Ini yang bisa dicontek dari rework CI-nya Linear buat skala tim kecil.
tags: ci-cd, ai-agents, developer-productivity, testing, github-actions
---

Empat belas PR nangkring di antrean pas Selasa pagi. Semuanya dari agent, nggak ada satu pun dari manusia yang ngetik satu baris kode.

Itu fleet Hermes yang gue jalanin buat dagango.com dan beberapa repo klien, dan itu cuma minggu biasa.

Coding agent sama QA agent nggak tidur dan nggak capek nulis test. Buka PR #15 pas PR #12 masih running CI pun mereka nggak merasa bersalah.

Yang jebol duluan bukan codebase-nya, tapi pipeline yang nge-validate kodenya.

Tanggal 21 September, Linear nulis soal masalah yang persis sama: "AI coding has made CI a bottleneck, so we reworked ours to keep up".

Sehari kemudian di Hacker News, tulisan itu udah lewat 230 poin dan 250-an komentar.

Kayaknya bukan cuma Linear yang mentok. Semua tim yang jalanin agent di skala gede nabrak dinding yang sama, dan waktunya berdekatan.

Angka dari Linear sendiri nunjukin bentuknya:

- PR mingguan dari tim yang pakai coding agent naik hampir tiga kali lipat dalam dua tahun, dari 21 jadi 65.
- Issue bikinan AI naik dari kurang dari satu per seribu jadi hampir separuh dari semua issue yang dibuat di Linear.
- Test suite internal mereka hampir empat kali lipat sejak Januari, kata post CI mereka sendiri.

Nggak ada satu pun angka itu yang khusus Linear.

Itu yang bakal kejadian ke pipeline mana pun yang dibangun buat manusia, begitu "junior developer" lo isinya agent yang jalan paralel 24 jam.

## Bottleneck-nya geser dari nulis kode ke verifikasi

Bertahun-tahun, yang jadi kendala di software delivery itu authoring.

Nulis kode, nulis test, sampai deskripsi PR yang nggak ada yang baca.

Agent bikin biaya itu nyaris nol. Tapi kapasitas CI nggak ikut turun, karena CI itu ukurannya buat kecepatan manusia bikin PR, dan agent bikin PR di kecepatan yang beda sama sekali.

Linear jagain waktu tunggu PR mereka di 5-6 menit walaupun test suite-nya meledak. Caranya cuma satu: runner time per test mereka potong kira-kira setengahnya.

Kapasitas verifikasi sekarang jadi hal yang harus lo desain, sama kayak lo desain buat load database atau rate limit API.

Gue ngerasain ini langsung pas ngelepas tiga coding agent ke repo dagango.com.

Dalam sembilan hari, jatah menit GitHub Actions kita untuk sebulan habis.

Yang bermasalah bukan kualitas kodenya, tapi pipeline yang nggak sanggup nampung jumlah job.

## Kemenangan termurah: benerin infra dulu sebelum ngoprek logic pipeline

Lever pertama Linear nggak butuh ubah pipeline sama sekali.

Ganti GitHub Actions ke runner pihak ketiga yang lebih cepat bikin job rata-rata 34% lebih ngebut. `tsc` type-check-nya turun 52%, dan file workflow-nya sendiri nggak disentuh.

Buat tim kecil atau budget UMKM, runner hosted premium jadi mahal cepat begitu jumlah job meledak naik. Sebab billing per-menit itu numpuk persis di volume yang diciptain agent.

Self-hosted runner di hardware biasa ngubah hitungannya.

Punya gue jalan di homelab yang malu-maluin kalau disebut di forum hardware. Tapi tetap menang dari sisi wall-clock time sampai hasil pertama muncul.

Alasannya simpel: nggak ada antrean, dan nggak ada meter yang jalan di tiap job.

## Hitung runner start, bukan detik

Pelajaran kedua dari Linear: benerin critical path dulu sebelum micro-optimize apa pun di dalemnya.

Batasin fetch depth git aja bikin gate job paling lambat mereka turun dari 94 detik ke 20 detik. Batching tujuh check kecil jadi dua job hemat sekitar 87.000 runner-minute per bulan, atau 11,8% dari total spending CI mereka.

Dua-duanya nggak nyentuh logic test sama sekali. Hitungannya pindah dari durasi tiap job ke jumlah job yang jalan.

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

Setiap job start bawa overhead tetap sebelum jalanin satu assertion pun.

Checkout, restore dependency, setup environment. Itu semua jalan dulu sebelum test-nya mulai.

Kalikan overhead itu sama volume PR yang dibikin agent, dan angkanya berhenti jadi pembulatan kecil yang bisa diabaikan.

Di pipeline kita bentuknya beda: lima job, sementara punya Linear tujuh.

Tapi fix-nya sama persis. Gabungin jadi dua job motong rata-rata waktu gate PR kita hampir sepertiga, tanpa nyentuh satu test pun.

## Isolasi test sekarang jadi cost center, dan agent bikin risikonya naik

Isolasi per-file default Vitest itu rebuild module graph di setiap file test. Aman, tapi mahal begitu skalanya gede.

Opt-in `isolate: false` jadi penghematan terbesar Linear, sekitar 17% dari spending CI bulanan mereka. Runtime API shard mereka turun dari 32,8 ke 22 menit.

Itu juga perubahan paling berisiko di daftar mereka. Matiin isolasi berarti test bisa bocor state satu ke yang lain kalau nggak ditulis hati-hati.

Sekarang test lo sebagian besar ditulis agent, dan mereka nggak reliable buat tahu kapan sebuah test butuh isolasi.

Manusia yang pernah kena shared mutable state nulis test defensif karena udah pernah kapok.

Agent yang cuma dioptimasi buat "bikin CI hijau" bakal santai nulis test yang lolos pas isolated, dan malah ngerusak fixture test berikutnya begitu isolasi dimatiin.

Linear ngegate ini pakai comment opt-in eksplisit plus requirement teardown per file.

Test ditandain aman-isolasi satu per satu, dan penandaan itu direview kayak diff yang sensitif keamanan.

Di proyek Next.js kita, itu artinya cuma unit test pure-function tanpa shared module state. Apa pun yang nyentuh fixture database atau mocked API client tetap pakai isolasi penuh, titik.

## Jangan cache hal yang lebih murah dibangun ulang

Cache `node_modules` punya Linear butuh sekitar 28 detik buat restore. `pnpm install` yang difilter cuma 7,5 detik. Cache-nya mereka hapus.

Caching kerasa kayak kemenangan gratis karena itu saran default di mana-mana.

Padahal caching bawa biaya restore yang hampir nggak ada yang benchmark lawan alternatifnya. Pelajarannya lebih luas dari node_modules.

Cache itu taruhan bahwa waktu restore lebih cepat dari waktu rebuild. Dan taruhan itu nggak selalu menang.

## CI di era agent harusnya gate di apa?

Thread HN di bawah post Linear pecah jadi dua kubu.

yieldcrv bilang unit test secara umum udah jadi kosmetik yang cuma bikin angka coverage naik.

Dia juga bikin poin yang layak direnungin: dia nggak lihat agent pakai test beda dari developer junior atau mid-level. Manusia sendiri juga nggak ketat-ketat amat soal itu.

sz4kerto bikin poin praktisi yang lebih tajam. Review diam-diam bergeser dari review kode ke review test, karena di situlah letak klaim beneran soal correctness dari agent.

Solomon Hykes, founder Docker, bilang build dan test harusnya dijadwalin sebagai satu sistem. Bukan dua proses yang jalan sendiri-sendiri.

Tiga komentator, tiga sudut pandang. Pertanyaan yang sebenarnya masih terbuka: apa yang pantas dijadikan gate di era agent?

<!-- owner-prose:start -->
Setelah jalanin fleet ini tiap hari, gue akhirnya punya satu prinsip sederhana:

Gate ketat itu cuma perlu dipasang di flow yang benar-benar berhubungan langsung sama duit masuk, atau flow kecil yang kalau gagal bisa bikin bisnis berantakan. Sisanya? Bikin semurah dan secepat mungkin.

Satu hal yang cukup cepat gue pelajari: test yang hijau dari agent bukan berarti apa yang dites itu otomatis benar di dunia nyata.

Agent bakal terus bikin PR dengan speed mereka sendiri. Pipeline kita mau siap atau nggak, mereka tetap jalan.

Dan ternyata pipeline kita nggak siap. 😅

Kita baru sadar ketika jatah GitHub Actions untuk sebulan habis cuma dalam sembilan hari.

Fix-nya ternyata bukan sekadar nambah check sampai semuanya hijau. Yang lebih penting adalah dari awal memperlakukan runner startup dan isolation policy sebagai bagian dari engineering design.

Bukan sesuatu yang baru ditempel belakangan karena kita butuh lebih banyak checkmark hijau.

Menurut gue, ini salah satu perbedaan penting ketika mulai menjalankan AI agent dalam skala fleet: masalahnya bukan cuma "apakah agent bisa menghasilkan code yang benar?", tapi juga "apakah sistem kita siap menghadapi seberapa cepat mereka bisa menghasilkan code?"
<!-- owner-prose:end -->
