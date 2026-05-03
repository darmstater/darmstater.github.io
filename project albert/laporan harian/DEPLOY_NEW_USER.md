# Panduan untuk User Baru
> Bot sudah jalan — teman kamu cukup ikuti 3 langkah ini sendiri, tidak perlu bantuan teknis dari kamu.

---

## Langkah 1 — Buat Google Spreadsheet

1. Buka [Google Sheets](https://sheets.google.com) → buat spreadsheet baru (boleh kosong)
2. Klik tombol **Share** (pojok kanan atas)
3. Di kolom "Add people", paste email berikut lalu set akses **Editor**:
   ```
   bot-laporan@laporan-harian-495106.iam.gserviceaccount.com
   ```
4. Klik **Send**

---

## Langkah 2 — Ambil Spreadsheet ID

Lihat URL spreadsheet, ambil bagian yang di-highlight:

```
https://docs.google.com/spreadsheets/d/  >>>INI_SPREADSHEET_ID<<<  /edit
```

Contoh:
```
https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit
                                        ↑ salin bagian ini ↑
```

---

## Langkah 3 — Daftar ke Bot

Buka bot di Telegram, ketik:
```
/register [spreadsheet_id_kamu]
```

Contoh:
```
/register 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
```

Kalau muncul ✅ **Berhasil terdaftar!** → langsung bisa pakai.

---

## Cara Pakai Bot

**Catat pengeluaran:**
```
/out [kategori] [qty] [harga_satuan] [keterangan]
/out makan 2 25000 makan siang
/out transport 1 35000 grab ke kantor
```

**Catat pemasukan:**
```
/in [kategori] [nominal] [keterangan]
/in freelance 500000 transfer klien
```

**Input ke hari lain (kalau lupa mencatat):**
```
/out kemarin makan 2 25000 makan siang
/out 2hari transport 1 35000 ojek
/out 01/05 makan 1 50000 makan malam
```

Format tanggal yang bisa dipakai: `kemarin` `besok` `2hari` `15` `01/05`

**Lihat summary:**
```
/today   — ringkasan hari ini
/week    — ringkasan minggu ini
/list    — daftar transaksi hari ini
```

**Lainnya:**
```
/hapus [id]   — hapus transaksi (ada konfirmasi)
/sync         — sinkronkan ulang ke Google Sheets
/kategori     — daftar semua kategori
/start        — panduan lengkap
```

---

## Catatan

- Setiap transaksi akan minta konfirmasi dulu sebelum disimpan
- Data kamu tersimpan di spreadsheet Google Sheets milikmu sendiri, terpisah dari user lain
- Ringkasan harian dikirim otomatis tiap malam pukul 23:59
- Ringkasan mingguan + sync spreadsheet otomatis tiap Minggu 23:59
