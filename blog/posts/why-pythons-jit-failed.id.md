---
title: Kenapa JIT Python Gagal: Cara Nyata Optimasi Backend
slug: why-pythons-jit-failed
date: 2026-10-28
excerpt: CPython resmi membatalkan copy-and-patch JIT menjelang Python 3.16. Inilah alasan teknis kenapa compiler ini gagal dan cara tim backend mengoptimasi performa di dunia nyata.
tags: python, compilers, performance, backend, architecture
---

Pada 19 Oktober 2026, wacana compiler Just-In-Time (JIT) bawaan di CPython resmi terhenti. Savannah Ostrowski mengumumkan penarikan proposal Python Enhancement Proposal (PEP) 836 yang berjudul "JIT Go Brrr: The Path to a Supported JIT Compiler for CPython."

Keputusan ini bukan tanpa sebab. Python Steering Council sebelumnya ngasih sepuluh syarat operasional yang wajib dipenuhi dalam enam bulan:

- Paritas platform penuh untuk seluruh target Tier 1.
- Audit keamanan menyeluruh terhadap eksekusi memori runtime.
- Verifikasi kompatibilitas ketat pada ekosistem PyPI.

Nah, begitu proposalnya resmi ditarik, nasib kodenya langsung jelas. Para core committer memastikan copy-and-patch JIT eksperimental yang sempat mendarat di Python 3.13 bakal dicopot total dari branch utama sebelum Python 3.16.

Forum developer langsung heboh. Di Hacker News dan Lobsters, banyak orang kecewa dan menganggap keputusan ini kemunduran birokratis.

Gue punya pandangan lain.

Setelah tiga belas tahun megang backend Python di production, gue rasa keputusan Steering Council justru langkah paling masuk akal. Penarikan ini bukan kegagalan birokrasi, tapi pengingat tegas soal batas fisik arsitektur Python.

## Angka Benchmark Cuma Bagus di Kertas

Intinya, klaim performa yang ditawarkan nggak pernah sebanding sama repotnya.

Hasil pengujian resmi di PEP 836 pada platform Tier 1 di Python 3.15 cuma ngasih kenaikan tipis:

- Rata-rata geometric mean speedup cuma 4% sampai 12% di benchmark sintetis.
- Target peningkatan kecepatan 20% malah diundur ke Python 3.17.
- Penggunaan memori membengkak drastis pada proses backend yang jalan terus-menerus.

Masalahnya, tim operasional harus menanggung beban teknis mahal demi mengejar kenaikan sekitar 8% itu:

- Ketergantungan wajib pada infrastruktur compiler LLVM (Low Level Virtual Machine) saat build binary.
- Rusaknya fungsi profiling tool penting seperti `perf` dan `sys.settrace`, termasuk debugger standar `pdb`.
- Benturan izin memori Write XOR Execute (W^X) pada kernel Linux yang diproteksi ketat.
- Proses cross-compilation paket binary ke berbagai platform target jadi makin ribet.

Nukar kesederhanaan build dan keamanan sistem demi kenaikan benchmark satu digit itu keputusan rugi. Di dunia nyata, trade-off kayak gini hampir nggak pernah masuk akal.

## Kenapa Desain CPython Selalu Alergi Sama JIT

Banyak developer sering heran kenapa V8 di JavaScript atau LuaJIT bisa lari kencang, sedangkan CPython selalu kepentok.

Kuncinya ada pada desain arsitektur CPython selama tiga puluh lima tahun terakhir.

Engine modern seperti V8 atau LuaJIT dari awal dirancang untuk pipeline eksekusi yang serba rapi:

- Hidden class dan shape yang bikin susunan memory layout object selalu stabil.
- Inline cache monomorfik yang melompati proses pencarian method dinamis.
- Model memori sandbox yang ramping dan siap dikompilasi langsung ke native machine code.

CPython punya dunia yang jauh berbeda. Dia terikat erat ke Application Programming Interface (API) bahasa C:

- Semua nilai dibungkus sebagai pointer ke struct `PyObject` di memori heap.
- Setiap kalkulasi memicu kenaikan dan penurunan angka reference counting.
- Atribut object tersimpan di dictionary dinamis yang bisa diutak-atik runtime kapan saja.
- Ribuan extension C langsung membaca pointer mentah ke struktur memori internal runtime.

JIT copy-and-patch memang bisa menghasilkan instruksi mesin untuk dispatch bytecode. Tapi instruksi mesin itu tetap terbentur oleh rantai pointer indirection.

Untuk nambahin dua angka integer biasa saja, prosesnya panjang:

- Buka bungkus dua pointer object dari heap.
- Cek tipe data runtime keduanya.
- Update hitungan reference count.
- Bikin alokasi struct object baru di memori heap untuk menampung hasilnya.

Terus kode mesin native mau bantu apa kalau CPU tetap buang-buang waktu nunggu cache miss ke memori utama?

## Di Mana Waktu Request Backend Sebenarnya Habis?

Gini, request di backend web jarang banget nyangkut di kecepatan eksekusi bytecode Python.

Di Dagango.com, kita menjalankan platform e-commerce multi-tenant yang menggunakan FastAPI di atas Virtual Private Server (VPS) Linux dan server bare metal. Dari profiling harian yang kita jalankan, waktu respons request nyaris nggak pernah habis di interpreter loop Python.

Latency checkout biasanya habis di titik-titik ini:

- Menunggu balasan query PostgreSQL yang sedang melakukan index scan.
- Perjalanan jaringan keluar menuju payment gateway pihak ketiga.
- Proses serialisasi data berukuran besar ke disk atau socket jaringan.
- Antrean connection pool waktu traffic database tiba-tiba melonjak.

Anggap satu endpoint butuh waktu 60 milidetik buat selesai. Di situ pemrosesan bytecode Python paling cuma makan 4 milidetik. Memotong 8% dari 4 milidetik itu cuma menghemat 0,32 milidetik.

Ya udah, pengguna website lo nggak bakal pernah merasakan bedanya. Sementara lo dan tim infra udah keburu pusing ngurusin izin W^X dan toolchain LLVM di setiap server.

## Playbook Nyata Bikin Python Ngebut

Tim backend yang matang nggak bakal nungguin runtime compiler ajaib buat beresin bottleneck.

Kuncinya sederhana: pasang batas arsitektur yang jelas di sistem kita. Bagian yang butuh komputasi berat langsung kita lempar ke perkakas native:

- Penjadwalan Input/Output (I/O) berkecepatan tinggi memakai `uvloop` di dalam event loop `asyncio`.
- Validasi data dan parsing JSON diserahkan ke modul Rust lewat PyO3, seperti Pydantic v2 dan `orjson`.
- Komputasi intensif dipindah ke background worker queue seperti Celery atau microservice mandiri.

Pola kerja ini kelihatan jelas di endpoint FastAPI berikut:

```python
from fastapi import FastAPI, Depends
import orjson
from pydantic import BaseModel

app = FastAPI()

class OrderPayload(BaseModel):
    account_id: str
    item_ids: list[int]
    total_cents: int

@app.post("/v1/orders")
async def create_order(payload: OrderPayload):
    # Validasi berjalan di kode compiled Rust via Pydantic v2
    # Event loop menangani I/O database tanpa memblokir thread
    order_id = await db.insert_order(
        payload.account_id,
        payload.item_ids,
        payload.total_cents
    )
    return {"status": "created", "order_id": order_id}
```

Lihat pembagian tugasnya. Pydantic v2 memproses dan memvalidasi payload masuk lewat kode Rust terkompilasi. Driver database async menangani traffic jaringan lewat panggilan non-blocking epoll.

Python fokus mengurus alur bisnis dan koordinasi data aplikasi. Urusan komputasi berat langsung diselesaikan oleh layer native yang ada di belakangnya.

## Pilihan Waras Steering Council

Mencabut JIT mungkin terdengar mengecewakan buat yang suka eksperimen compiler. Tapi buat kita yang maintain sistem di production, ini keputusan tepat.

Steering Council memilih menyelamatkan hal-hal yang bikin Python tetap unggul:

- Portabilitas sempurna di berbagai sistem operasi dan arsitektur CPU.
- Proses build dan instalasi dependensi di PyPI yang tetap sederhana.
- Jaminan kompatibilitas penuh untuk ekosistem extension C yang sudah mapan.

Aplikasi yang butuh komputasi numerik tinggi jelas lebih pas memakai Rust atau Go.

Daya tarik utama Python nggak pernah terletak pada adu cepat benchmark sintetis.

Kekuatannya bertumpu pada hal-hal yang langsung terasa di lapangan:

- Kenyamanan menulis kode yang mempercepat delivery harian.
- Abstraksi glue yang bersih untuk library native.
- Kestabilan sistem yang teruji di lingkungan production.
