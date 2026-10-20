---
title: Compiler Jadi CA: Kenapa Go Hardcode Delapan Sertifikat
slug: go-distrusts-eight-intermediate-cas
date: 2026-10-20
excerpt: Delapan intermediate eMudhra dicabut karena private key bocor. Sehari kemudian Go rilis patch yang jadi satu-satunya penegakan yang bakal diterima backend kita.
tags: golang, security, pki, tls, devops
---

Tanggal 18 Oktober 2026, log revocation CCADB nambah delapan intermediate eMudhra dengan alasan `cACompromise`.

Enam di antaranya rantainya nyambung ke emSign Root TLS CA - G3. Dua sisanya ke emSign Root CS CA - G3. Cakupannya termasuk penerbit DV sampai EV.

Sehari setelah catatan itu nongol, bentuk mitigasi yang realistis kita terima keluar sebagai literal di standard library. Go rilis go1.27.3 dan go1.26.10 lewat CVE-2026-111943.

Di dalam `crypto/x509` sekarang ada map isi delapan hash SHA-256 SPKI. Ada juga filter yang membuang rantai sertifikat begitu salah satu isinya cocok sama hash itu.

Commit-nya ditulis Roland Shoemaker, dilacak di issue 82345, di-review sebagai CL 851047. Backport-nya lewat CL 851145 buat Go 1.26 dan CL 851165 buat Go 1.27. Totalnya 42 baris nambah, nol baris hapus. Isinya nyebar di tiga file.

Gue penasaran apakah daftar itu benar-benar cocok sama catatan CCADB. Jadi gue ambil delapan nilai dari `verify.go`, terus hitung ulang SPKI SHA-256 dari sertifikat yang dicabut.

Hasilnya delapan dari delapan cocok.

Nggak ada tebak-tebakan issuer di sini. Yang di-pin itu sertifikat spesifiknya, lewat public key.

## Diff-nya cuma satu map dan satu filter

```go
// src/crypto/x509/verify.go
var distrustedSPKIHashes = map[string]struct{}{
	"ebed6475c2c2d80fcb199f3fe8dd6e6b3ce60b77eb15d4e42c3dec0c6f5b5105": {},
	"49dd353dc2b919a3770645117d0e60c16115e7d1bc259eefe734b00ea434fe5f": {},
	// ... enam entri lagi, dipotong di sini
}

func containsDistrustedSPKIHash(chain []*Certificate) bool {
	for _, c := range chain {
		h := sha256.Sum256(c.RawSubjectPublicKeyInfo)
		if _, ok := distrustedSPKIHashes[hex.EncodeToString(h[:])]; ok {
			return true
		}
	}
	return false
}
```

Dua detail yang bikin patch ini benar-benar kerja. Penolakannya berdasarkan hash SPKI, jadi sertifikat yang di-reissue dengan serial baru tetap kena selama key pair-nya sama. Lalu loop-nya jalan di seluruh rantai, termasuk leaf-nya.

Call site-nya lebih menarik daripada map-nya. `root_darwin.go` ngecek `containsDistrustedSPKIHash(chain[0])`. `root_windows.go` pakai `slices.DeleteFunc(chains, containsDistrustedSPKIHash)`.

Dua-duanya jalan di atas rantai yang sudah dibangun OS lewat `SecTrustCopyCertificateChain` dan `CertGetCertificateChain`. Platform bilang rantai itu valid. Go tetap membuangnya.

## Revocation di backend praktis nggak jalan

Semua tim yang jalanin API ngadepin hitungan availability yang sama soal OCSP. Hasilnya selalu mendarat di titik yang sama:

- **OCSP hard-fail** mengubah responder yang lambat jadi outage, jadi hampir nggak ada yang berani masang di depan traffic produksi.
- **OCSP soft-fail** jawab "good" tiap kali pengecekannya error. Penyerang yang pegang jalur jaringan tinggal drop traffic ke IP responder.
- **CRL** datang sesuai jadwal publish CA, ukurannya berat buat di-fetch per koneksi, dan jarang ada yang ngambil tiap request.
- **`x509.Verify` di Go** nggak melakukan network lookup sama sekali. Certificate-nya cuma bawa field `OCSPServer` plus parser response. Sisanya lo yang putusin.

Trade-off-nya masuk akal secara engineering. Efek strukturalnya tetap ada: intermediate yang sudah dicabut terus bisa nandatanganin leaf yang valid sampai ada sesuatu di luar proses lo yang bilang berhenti.

Kalau nggak ada yang bilang berhenti, komprominya nggak kelihatan dari sisi client. Semua client yang masih percaya root induknya jalan seperti biasa.

## Bundle CA di Linux nggak pernah jadi blocklist

Gue cek di mesin yang gue pakai nulis ini. `/etc/ssl/certs/ca-certificates.crt` isinya 121 sertifikat, total 178 KB.

Semuanya root trust anchor.

Dan root justru lapisan yang nggak kena masalah di kasus ini. Delapan sertifikat tadi itu intermediate, ditandatangani root emSign yang statusnya masih dipercaya.

Bundle root yang baru di-download nggak bisa nyatakan satu kalimat pun soal "intermediate ini jelek". Di situ nggak ada kosakata buat intermediate.

Windows sama macOS emang nyimpen data revocation intermediate di store masing-masing. Itu bagian yang di server Linux memang nggak ada.

Makanya diff yang nyentuh `root_darwin.go` dan `root_windows.go` itu bagian paling menarik. Di dua OS itu pun Go tetap harus buang rantainya sendiri.

Store platform itu bakal nangkep kedelapannya atau nggak, nggak ada yang sempat cek. Go buang rantainya duluan.

## Rebuild binary-nya, jangan cuma restart

Di binary yang statically linked, validasi rantai ya kode `crypto/x509` yang lo compile.

Update paket `ca-certificates` di host cuma ngaruh ke root mana yang di-load saat runtime. Sampai situ doang.

Paket itu nggak bisa mencabut intermediate. Dan sama sekali nggak bisa nyentuh daftar hash yang sudah ke-compile di binary lo.

```bash
# toolchain apa yang build binary yang benar-benar jalan?
go version -m ./service | grep goversion

# pertanyaan yang sama buat semua binary di dalam image
for b in /app/bin/*; do go version -m "$b" | head -2; done
```

Apa pun yang dibuild pakai go1.27.2, go1.26.9, atau versi lebih lama harus di-rebuild dan di-redeploy. Tanpa itu, filter-nya belum ada di proses yang jalan.

Bukan restart. Rebuild, terus redeploy semua image yang bawa binary Go dan bikin koneksi TLS keluar.

## Yang gue lakuin minggu ini

- Cek `go version -m` di artefak yang benar-benar jalan, jangan cuma `go.mod` di repo.
- Subscribe golang-announce dan perlakukan patch release toolchain sebagai channel keamanan. Karena memang itu fungsinya.
- Inventaris koneksi TLS keluar. Service mana yang nyambung ke endpoint pihak ketiga yang rantainya bisa mengandung intermediate yang baru dicabut?
- Buat service yang nggak bisa cepat di-rebuild, terminasi TLS-nya di proxy yang bisa lo ubah tanpa nyentuh binary.
- Pantau log revocation publik CCADB langsung. Sumber itu sudah melaporkannya 18 Oktober, sebelum ada release note apa pun.

Otomasi sertifikat nggak ngasih isolasi sebesar yang dipercaya tim platform. Rotasi ACME mengganti leaf milik kita sendiri, dan buat itu dia memang jalan baik.

`cpach` di thread Hacker News nunjuk ke ACME plus ARI (RFC 9773) sebagai jawaban dari sisi client. Di situ CA yang kasih tahu client kalau sertifikatnya perlu diganti.

Tapi nggak ada satu pun dari itu yang mencabut intermediate bocor di rantai orang lain.

Thread itu juga ngasih lelucon terbaik minggu ini. `accountrequired` bilang ini momen `"Sir, this is a Wendy's" where my compiler thought it was a root certificate authority`.

`TheDong` mengoreksi framing-nya: sertifikatnya nempel di paket TLS standard library, bukan di compiler, dan Go ngirim keduanya dalam satu rilis.

Oke, dan hasil operasionalnya tetap sama. Upgrade toolchain artinya ganti kebijakan sertifikat.

Yang bikin nggak nyaman bukan soal Go hardcode delapan hash. Yang bikin nggak nyaman: toolchain bahasa jadi tempat terakhir di mana hal ini bisa ditegakkan sama sekali.

Trust root sebuah service Go bukan file yang lo atur. Bentuknya commit yang sudah nempel di setiap binary yang lo kirim, dan dia cuma diperbarui kalau lo rebuild.

Dulu itu cuma poin filosofis soal supply chain. Sekarang jadi satu baris di `verify.go` yang isinya hash.
