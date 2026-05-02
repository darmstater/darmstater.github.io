# Project Summary — Bot Laporan Harian
> Dokumen ini dibuat sebagai konteks lengkap untuk melanjutkan development di sesi Claude lain.
> Dibuat: 2 Mei 2026
> Diupdate: 2 Mei 2026 (Sesi 2)

---

## Ide Awal

Pengguna ingin membuat bot untuk **mencatat keuangan harian** (pemasukan & pengeluaran) lewat chat,
dengan fitur:
- Input transaksi harian via chat
- Summary otomatis tiap malam
- Export mingguan ke spreadsheet
- Review bulanan

---

## Decision Making

### Platform Chat
- **Opsi**: Telegram vs WhatsApp
- **Dipilih**: Telegram
- **Alasan**: API resmi gratis, lebih mudah dibuat bot, tidak butuh WhatsApp Business

### Format Input
- **Dipilih**: Terstruktur (command-based)
- **Alasan**: Lebih mudah di-parse, mengurangi error
- **Format akhir**:
  ```
  /out [kategori] [qty] [harga_satuan] [keterangan]
  /in [kategori] [nominal] [keterangan]
  ```

### Output / Storage
- **Dipilih**: Google Sheets (spreadsheet pribadi user)
- **Alasan**: User sudah punya, mudah diakses, bisa review visual

### Struktur Sheet (hasil diskusi panjang)
- **1 sheet per bulan** (nama: `Mei 2026`, `Juni 2026`, dst)
- **Kolom**: NO | HARI | TANGGAL | KATEGORI | JUMLAH | HARGA SATUAN | HARGA TOTAL | KETERANGAN | TOTAL HARIAN
- **TOTAL HARIAN**: di-merge vertikal per hari, isi: MASUK / KELUAR / NET
- **Baris Weekly Summary**: setelah tiap minggu selesai, di dalam sheet bulanan
- **Sheet SUMMARY terpisah**: akumulasi semua minggu & bulan untuk review bulanan
- **Warna**: IN = hijau muda, OUT = merah muda, Weekly = biru muda, Header = navy

### Jadwal Otomatis
- **23:59 setiap hari** → kirim summary harian via Telegram
- **23:59 setiap Minggu** → kirim summary mingguan + rebuild Google Sheets lengkap

### Hosting
- **Opsi pertama**: Railway → ditolak (free trial $5 / 30 hari saja)
- **Opsi kedua**: Render, Koyeb, Fly.io → dipertimbangkan
- **Dipilih**: Google Cloud VM (e2-micro)
- **Alasan**: User sudah punya akun GCP, e2-micro masuk always-free tier (gratis selamanya, bukan dari kredit $300)

---

## Tech Stack

| Komponen | Pilihan | Alasan |
|---|---|---|
| Bahasa | Python 3 | Paling umum untuk Telegram bot |
| Bot library | python-telegram-bot v20.7 | Async, well-maintained |
| Google Sheets | gspread 6.0.2 | Wrapper paling simpel untuk Sheets API |
| Scheduler | APScheduler 3.10.4 | Mudah setup cron-like jobs |
| Database lokal | SQLite | Zero-config, cukup untuk 1 user |
| Hosting | Google Cloud VM e2-micro | Gratis selamanya, always-free tier |
| Service manager | systemd | Bawaan Linux, auto-restart |

---

## Arsitektur

```
User Telegram
     │
     ▼
bot.py (command handlers)
     │
     ├──► database.py (SQLite — simpan semua transaksi)
     │
     ├──► sheets_service.py (Google Sheets API)
     │         ├── append_transaction_row() — realtime saat transaksi masuk
     │         ├── rebuild_month_sheet()    — rebuild penuh tiap Minggu 23:59
     │         └── update_summary_sheet()  — update sheet SUMMARY
     │
     └──► scheduler_service.py (APScheduler)
               ├── send_daily_summary()           — tiap hari 23:59
               └── send_weekly_summary_and_sync() — tiap Minggu 23:59
```

---

## File Structure

```
project albert/laporan harian/
├── bot.py               ← main: semua command handler + scheduler setup
├── config.py            ← env vars + mapping kategori (OUT & IN)
├── database.py          ← SQLite: CRUD transaksi
├── sheets_service.py    ← Google Sheets: write + format + merge + rebuild
├── scheduler_service.py ← format summary harian & mingguan, kirim via bot
├── requirements.txt
├── Procfile
├── railway.toml
├── .env.example
├── .gitignore
└── MAINTENANCE.md
```

---

## Kategori yang Tersedia

**Pengeluaran (/out):**
`makan` `makanan` `minum` `kopi` `snack` → Makan & Minum
`transport` `grab` `gojek` `ojek` `bensin` `parkir` `tol` → Transport
`belanja` `shopping` `baju` `sepatu` → Belanja
`tagihan` `listrik` `air` `wifi` `internet` `pulsa` `sewa` `kos` → Tagihan
`hiburan` `nonton` `game` `spotify` `netflix` → Hiburan
`kesehatan` `obat` `dokter` `vitamin` `gym` → Kesehatan
`lain` `other` `dll` → Lain-lain

**Pemasukan (/in):**
`gaji` `salary` → Gaji
`freelance` `proyek` `project` → Freelance
`transfer` → Transfer
`bisnis` → Bisnis
`investasi` → Investasi
`lain` `other` → Lain-lain

---

## Setup yang Sudah Selesai

- [x] Telegram Bot dibuat via @BotFather
- [x] Google Cloud project `laporan-harian-495106` dibuat
- [x] Google Sheets API & Drive API diaktifkan
- [x] Service account `bot-laporan@laporan-harian-495106.iam.gserviceaccount.com` dibuat
- [x] Spreadsheet `CATATAN FINANCE` di-share ke service account (Editor)
- [x] Code di-push ke GitHub: `darmstater/darmstater.github.io` → `project albert/laporan harian/`
- [x] VM e2-micro di-deploy di GCP us-central1-f
- [x] Python 3.11.2 + pip + venv + git terinstall di VM
- [x] Dependencies terinstall di VM
- [x] `.env` dikonfigurasi di VM
- [x] systemd service `bot-laporan` aktif & running
- [x] Bot sudah test jalan & reply di Telegram

### Yang Sedang Dikerjakan (Sesi 2 — 2 Mei 2026)
- [ ] Clone repo dari GitHub ke VM
- [ ] Setup venv & install requirements di folder yang benar
- [ ] Konfigurasi `.env` di VM
- [ ] Jalankan bot via systemd

---

## Info Credentials (untuk referensi, jangan share publik)

| Key | Value |
|---|---|
| TELEGRAM_CHAT_ID | 1237353264 |
| SPREADSHEET_ID | 17lpwNA6pR4DMb_eqm2xamfZzU_VvXrGi1ha3LWoBLeU |
| GCP Project ID | laporan-harian-495106 |
| Service Account | bot-laporan@laporan-harian-495106.iam.gserviceaccount.com |
| VM Name | bot-laporan |
| VM Region | us-central1-f (bukan us-central1-a, Google auto-assign) |
| VM User | darmstater12 |
| VM External IP | 136.116.131.170 |
| Bot path di VM | `/home/darmstater12/darmstater.github.io/project albert/laporan harian` |
| Symlink | `/home/darmstater12/bot-laporan` |

---

## Kendala yang Sudah Diselesaikan

1. **Path dengan spasi** (`project albert/laporan harian`) → systemd error 203/EXEC
   - Solusi: buat shell script `run-bot.sh` sebagai wrapper, ExecStart pakai `/bin/bash run-bot.sh`

2. **Google Sheets tidak bisa diakses via WebFetch** → tidak bisa lihat format spreadsheet user
   - Solusi: user kirim screenshot, format dirancang ulang berdasarkan screenshot

3. **Railway hanya free trial** → diganti Google Cloud VM e2-micro (gratis selamanya)

4. **python-dotenv warning** di line 12 → GOOGLE_CREDENTIALS_JSON terlalu panjang
   - Non-critical, bot tetap jalan normal

5. **Telegram getUpdates result kosong `[]`** (Sesi 2)
   - Penyebab: bot belum pernah dikirimi pesan, bukan salah token
   - Solusi: buka bot di Telegram → klik START atau kirim pesan dulu → baru refresh getUpdates
   - Token benar ditandai dengan response `"ok": true`

6. **Google Cloud 2-Step Verification wajib** sejak 13 Mei 2025 (Sesi 2)
   - Semua akun Google Cloud wajib aktifkan 2SV/MFA
   - Solusi: aktifkan di myaccount.google.com/security → pakai nomor HP
   - Setelah aktif tunggu ~60 detik lalu refresh console.cloud.google.com

7. **Bingung Select Project / New Project** di Google Cloud Console (Sesi 2)
   - Tombol dropdown ada di pojok kiri atas: `[Select a project]` di sebelah logo Google Cloud
   - Klik tombol itu → popup muncul → ada tombol "New Project" di pojok kanan atas popup

8. **Compute Engine API minta billing** padahal mau pakai yang gratis (Sesi 2)
   - Ini normal — billing account wajib diaktifkan meski mau pakai free tier
   - Billing account ≠ langsung dicharge
   - Solusi: klik "Enable billing" → isi data kartu (hanya verifikasi identitas)
   - e2-micro di us-central1 tetap $0 karena masuk always-free tier

9. **Bingung memilih machine type e2-micro** di halaman Create Instance (Sesi 2)
   - Tampilan baru GCP menampilkan daftar Series (C4, N4, E2, N2, dst)
   - Harus klik **E2** di kolom Series terlebih dahulu
   - Setelah itu muncul dropdown Machine type → pilih **e2-micro**
   - Jangan salah pilih e2-small atau e2-medium (berbayar!)

10. **Estimasi harga masih $7-9 padahal pakai e2-micro** (Sesi 2)
    - Google tidak otomatis tampilkan free tier discount di estimasi
    - Tagihan asli = $0 untuk e2-micro di us-central1
    - Disk 30GB dari $300 kredit (bukan from pocket)
    - Kredit penuh IDR 5,172,751 — belum terpakai sama sekali per 2 Mei 2026

11. **Boot disk tidak ditemukan saat scroll** di halaman Create Instance (Sesi 2)
    - Tampilan baru GCP: Boot disk ada di menu sidebar kiri → **"OS and storage"**
    - Bukan di scroll bawah seperti tampilan lama

12. **Firewall (Allow HTTP/HTTPS) letaknya** (Sesi 2)
    - Ada di menu sidebar kiri → **"Networking"**
    - Centang: Allow HTTP traffic ✅ dan Allow HTTPS traffic ✅

---

## Catatan Penting Soal Billing GCP

> Untuk Claude di sesi berikutnya: user sempat panik soal billing. Jelaskan dengan tenang:
- **e2-micro di us-central1** = always-free, tidak perlu kredit $300
- **$300 kredit** = backup untuk resource lain (disk, network, dsb)
- **Billing account wajib ada** tapi tidak berarti langsung bayar
- **Kredit user masih penuh** IDR 5,172,751, berlaku sampai Agustus 2026
- VM bisa dihapus kapan saja → billing otomatis berhenti

---

## Yang Bisa Dikembangkan Selanjutnya

- [ ] **Tambah kategori** sesuai kebutuhan di `config.py`
- [ ] **Edit transaksi** — saat ini hanya bisa hapus (`/hapus`), belum bisa edit
- [ ] **Laporan per kategori bulanan** yang lebih detail
- [ ] **Grafik/chart** di Google Sheets (bar chart pengeluaran per kategori)
- [ ] **Budget limit** per kategori — notifikasi kalau sudah melebihi batas
- [ ] **Export PDF** summary bulanan
- [ ] **Multi-user** — saat ini hanya 1 chat ID yang bisa pakai
- [ ] **Inline keyboard** untuk pilih kategori (biar tidak perlu hafal kata kunci)

---

## Cara Lanjut Development

### Update code dari laptop → live di VM:
```bash
# 1. Edit code di laptop (D:\CODE\GITHUB\LAPORAN HARIAN\)
# 2. Push ke GitHub
git add .
git commit -m "deskripsi perubahan"
git push

# 3. Di VM (SSH), pull dan restart
cd "/home/darmstater12/darmstater.github.io/project albert/laporan harian"
git pull
sudo systemctl restart bot-laporan
```

### Cek log bot di VM:
```bash
sudo journalctl -u bot-laporan -f
```

### Akses SSH ke VM:
- Buka console.cloud.google.com → VM Instances → klik tombol **SSH** di baris bot-laporan
- Terminal langsung muncul di browser, tidak perlu software tambahan

### Hapus VM (kalau mau stop semua):
- VM Instances → centang bot-laporan → klik Delete
- Billing otomatis berhenti