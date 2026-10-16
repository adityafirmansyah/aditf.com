---
title: Kenapa Gue Bikin mycv.ai.id: Cara Tool Resume AI Diam-diam Menghapus Kedalaman Teknis dan Halusinasi Tanggal
slug: why-i-built-mycv-ai-id
date: 2026-10-16
excerpt: Tool resume AI biasa diam-diam ngabur-in tech stack konkret jadi omong kosong korporat, terus nganggep tahun 2026 tanggal masa depan. Ini cara gue ngerancang mycv.ai.id buat ngatasin itu.
tags: ai-engineering, resume-optimization, ats-parser, python, fastapi, anti-slop, self-hosting
---

## Jebakan bikin CV pakai prompt AI biasa

Sekarang hampir semua software engineer disuruh poles resume pakai AI sebelum berani apply ke mana pun.

Katanya bakal otomatis lolos screening ATS. Janjinya manis banget.

Tapi pas gue tes pakai resume gue sendiri dengan tiga belas tahun pengalaman bangun software, hasilnya bikin geleng-geleng kepala.

Semua detail arsitektur yang konkret disikat habis.

Kalimat asli gue soal arsitektur Next.js App Router dan FastAPI monorepo dengan isolasi database PostgreSQL diubah jadi kalimat klise: "memprakarsai arsitektur aplikasi untuk mendorong pertumbuhan bisnis."

Bukan cuma itu. Sistemnya juga nganggep masa kerja gue di tahun 2026 sebagai halusinasi masa depan.

Gara-gara training cut-off model mentok di akhir 2024 atau awal 2025, masa kerja kayak "Agustus 2024 – Juli 2026" langsung dicap nggak valid. Nilai audit CV gue dipotong cuma gara-gara modelnya nggak paham kalender nyata.

Makanya minggu ini gue ngebangun mycv.ai.id.

Mesin resume ini gue host sendiri di VPS Linux pakai FastAPI dan React 19. Prinsipnya sederhana: kalau lo nggak pasang pagar deterministik di sekitar LLM, hasil kerjanya bakal ngancurin sinyal teknis lo.

## Kenapa LLM demen banget hapus tech stack

Waktu lo minta LLM biasa buat optimasi CV ke format ATS, bias bawaan dari proses RLHF-nya langsung aktif. Model bakal ngira kalau tulisan profesional itu harus pakai gaya bahasa HR korporat.

Efek sampingnya fatal buat engineer:

- Framework spesifik kayak Next.js, FastAPI, Medusa, atau React 19 digeneralisir jadi "teknologi web modern."
- Pola arsitektur kayak monorepo, Kubernetes, service gRPC, dan isolasi tenant diringkas jadi "sistem yang scalable."
- Disiplin engineering kayak TDD dan automated quality gate di CI cuma disebut "menjaga kualitas kode."

Di commit `4490e8b`, gue pasang aturan anti-slop yang ketat di `backend/app/services/optimizer.py`. Gue bikin daftar hitam kata kerja korporat dan jargon kosong yang haram dipakai sama sekali:

```python
# From backend/app/services/optimizer.py (commit 4490e8b)
SYSTEM_CV_EXPERT = """
STRICT ZERO-AI-SLOP RULES (Non-Negotiable):

1. ABSOLUTE BAN ON AI RESUME SLOP & EMPTY CORPORATE CLICHÉS:
   - FORBIDDEN ACTION VERBS: NEVER use "Spearhead", "Spearheaded", "Spearheading",
     "Pioneered", "Orchestrated", "Fostered", "Leveraged", "Championed", "Catalyzed".
   - FORBIDDEN BUZZWORDS: NEVER use "robust", "seamless", "cutting-edge", "game-changer",
     "revolutionary", "holistic", "synergistic", "dynamic environment".
"""
```

Prompt sistemnya gue paksa cuma boleh pakai kata kerja praktisi. Tiap poin harus buka kalimat pakai kata kerja konkret kayak Built, Architected, Engineered, atau Deployed.

Tiap bullet point juga wajib lolos tiga syarat teknis:

- Sistem nyata apa yang lo bangun atau refactor.
- Tool dan framework spesifik apa yang lo pakai.
- Hasil teknis apa yang berhasil lo capai dan bisa diukur.

Kalau di input asli lo nyebut Kubernetes dan gRPC, kata itu pantang dihilangin. Model nggak boleh sok pintar ngerangkum istilah teknis jadi kata-kata abstrak.

## Bug tanggal 2026 yang dianggap fiktif

Masalah kedua ini jauh lebih ngeselin kalau lo nggak teliti merhatiin log.

Waktu ngetes sistem audit ATS, nilai kepatuhan kandidat sering anjlok dari skor 96 ke 88. Penyebabnya konyol: halusinasi waktu.

Waktu model ngeliat masa kerja "Agustus 2024 – Juli 2026", dia mikir bulan Juli 2026 itu belum pernah kejadian di dunia nyata. Pengetahuan model berhenti di pertengahan 2025, jadi dia nuduh kandidat ngarang riwayat kerja.

Di commit `4b90aba`, gue beresin ini lewat injeksi kalender dinamis dari sisi server:

```python
# From backend/app/services/optimizer.py (commit 4b90aba)
from datetime import datetime

def get_current_date_context() -> str:
    now = datetime.now()
    return f"{now.strftime('%B %Y')} (Year {now.year})"

# Injected directly into the system prompt and audit evaluator:
"""
REAL-WORLD DATE CONTEXT:
- The current calendar date is October 2026 (Year 2026).
- All employment dates through October 2026 are valid, normal historical dates.
- NEVER flag dates occurring in or before October 2026 as 'the future'.
"""
```

Begitu model dikasih konteks tanggal nyata pas runtime, halusinasi itu langsung hilang.

Dia bakal ngerti kalau tahun 2026 itu masa lalu yang valid, bukan fiksi ilmiah.

## PDF vektor langsung vs kanvas HTML yang sering bikin error

Banyak tool resume online jualan template visual cantik yang dirancang pakai Figma atau kanvas HTML. Tampilannya kelihatan keren di layar browser, tapi langsung berantakan waktu masuk ke parser ATS kayak Workday, Greenhouse, atau Taleo:

- Layout dua kolom bikin alur teks kepotong, sampai nama skill nyampur ke dalam judul pekerjaan.
- Fitur print bawaan browser ngasilin margin yang nggak konsisten dan font yang nggak kebaca mesin.
- Elemen grafis dekoratif kayak progress bar skill cuma kebaca sebagai artefak binary yang bikin parsing gagal.

Gue milih pakai ReportLab di Python buat ngehasilin PDF vektor satu kolom yang bersih. Semua font gue daftarin lewat `pdfmetrics` pakai file TrueType resmi: Inter buat sans modern, Merriweather buat serif, dan IBM Plex Mono buat profil teknis.

Di commit `7678422`, gue beresin dua masalah render yang sempat bikin layout bergeser:

```python
# From backend/app/services/pdf_generator.py (commit 7678422)
# Frame content box is [margin+6 .. PAGE_WIDTH-margin-6], i.e. doc.width - 12.
usable_width = doc.width - 12

# Dynamic glyph advance calculation for hanging indents:
bullet_glyph = "\u2022"
bullet_gap = "\u00a0\u00a0"
bullet_indent = (
    pdfmetrics.stringWidth(bullet_glyph, cfg["font_body"], cfg["body_size"])
    + pdfmetrics.stringWidth(bullet_gap, cfg["font_body"], cfg["body_size"])
)
```

Komponen `SimpleDocTemplate` bawaan ReportLab nambahin padding 6pt di dalam Frame internalnya.

Kalau lo pakai lebar halaman mentah, tabel riwayat kerja bakal tumpah 6pt ke margin kiri dan kelihatan mencong.

Rumus `usable_width = doc.width - 12` bikin posisi tabel pas rata sama tepi teks.

Menghitung hanging indent dari lebar glif font juga bikin baris teks kedua sejajar rapi di bawah huruf pertama, bukan nyangkut di bawah simbol bullet.

## Bayar lokal pakai QRIS dinamis tanpa ribet langganan

Platform resume luar negeri biasanya maksa lo langganan kartu kredit bulanan. Buat engineer dan pencari kerja di Indonesia, langganan auto-debit dolar kayak gitu jelas bikin males.

Makanya di commit `90c4584`, gue bikin integrasi QRIS dinamis berbasis spesifikasi resmi EMVCo Bank Indonesia:

- Backend ngebaca string payload QRIS statis berbasis Tag-Length-Value (TLV).
- Tag 01 diubah dari statis (`11`) jadi dinamis (`12`).
- Tag 54 disuntik langsung dengan nominal transaksi persis plus tiga digit kode unik verifikasi.
- Checksum CRC-16/CCITT-FALSE di Tag 63 dihitung ulang biar QR code valid pas discan.

User tinggal scan QR pakai GoPay, OVO, BCA, atau mobile banking apa pun. Pembayaran terverifikasi otomatis di VPS Linux milik kita sendiri, tanpa perlu nitipin nomor kartu ke layanan pihak ketiga.

## Pelajaran penting soal batasan sistem AI

Nilai utama dari aplikasi berbasis AI itu bukan sekadar manggil API model bahasa. Nilai aslinya ada pada pagar deterministik yang kita pasang di sekeliling model itu.

Kalau dibiarin jalan tanpa kendali, LLM bakal milih jalan gampang:

- Nelen detail teknis penting dan ngegantinya pakai jargon manajemen yang hambar.
- Nuduh riwayat kerja bermasalah cuma gara-gara modelnya nggak tahu hari ini tanggal berapa.
- Ngasilin format visual cantik yang justru nggak bisa dibaca sama mesin parser.

Begitu kita kurung modelnya pakai aturan prompt yang keras, konteks tanggal real-time, dan render PDF vektor yang presisi, hasilnya baru bisa diandalkan. AI nggak lagi bersikap kayak intern sotoy, tapi jadi mesin kompilasi yang beneran nolong karier lo.
