# Deploy Bot DaganganEny

---

## LANGKAH 1 — Buat Telegram Bot

1. Chat `@BotFather` di Telegram
2. Kirim `/newbot`
3. Nama: `DaganganEny` (atau bebas)
4. Username: `DaganganEny_bot` (harus unik, diakhiri `_bot`)
5. Simpan **TOKEN** yang diberikan

---

## LANGKAH 2 — Setup Google Cloud (Service Account)

> Ini digunakan agar bot bisa tulis/baca ke Google Sheets.

1. Buka [console.cloud.google.com](https://console.cloud.google.com)
2. Buat project baru (misal: `dagangan-eny`) atau pakai project yang sudah ada
3. Aktifkan **Google Sheets API**:
   - Klik menu ≡ → APIs & Services → Library
   - Cari "Google Sheets API" → Enable
4. Buat **Service Account**:
   - Menu ≡ → APIs & Services → Credentials
   - Klik "+ CREATE CREDENTIALS" → "Service Account"
   - Isi nama: `bot-dagangan`
   - Klik Create → Done
5. Klik service account yang baru dibuat → tab **Keys**
6. Klik "ADD KEY" → "Create new key" → JSON → Download
7. Buka file JSON tersebut — isinya akan dipakai sebagai `GOOGLE_CREDENTIALS_JSON`

---

## LANGKAH 3 — Buat Google Spreadsheet

1. Buka [sheets.google.com](https://sheets.google.com) → buat spreadsheet baru
2. Beri nama: **"Dagangan Eny 2026"**
3. Salin **Spreadsheet ID** dari URL:
   ```
   https://docs.google.com/spreadsheets/d/[INI_SPREADSHEET_ID]/edit
   ```
4. Share spreadsheet ke email service account:
   - Klik tombol **Share** (pojok kanan atas)
   - Masukkan email service account (ada di file JSON, field `client_email`)
     contoh: `bot-dagangan@dagangan-eny.iam.gserviceaccount.com`
   - Pilih role **Editor**
   - Klik Send

---

## LANGKAH 4 — Deploy ke Railway

> Railway adalah platform cloud gratis (dengan limit) untuk menjalankan bot 24/7.

1. Buka [railway.app](https://railway.app) → Login dengan GitHub
2. Klik **"New Project"** → **"Deploy from GitHub repo"**
3. Pilih repo yang berisi folder `bot-laporan-dagangan`
   - Atau bisa juga push folder ini ke repo GitHub baru dulu
4. Di Railway dashboard, klik proyek → tab **Variables**
5. Tambahkan environment variables:

   | Key | Value |
   |-----|-------|
   | `TELEGRAM_TOKEN` | token dari BotFather |
   | `GOOGLE_CREDENTIALS_JSON` | isi lengkap file JSON service account (1 baris) |

6. Railway akan otomatis build dan jalankan bot

> **Tips GOOGLE_CREDENTIALS_JSON:** Buka file JSON, pilih semua → copy → paste sebagai 1 baris di Railway Variables.

---

## LANGKAH 5 — Alternatif: Deploy ke Google Cloud (GCE via SSH)

Jika sudah punya VM di Google Compute Engine:

```bash
# SSH ke VM
gcloud compute ssh nama-vm-mu --zone=asia-southeast2-a

# Install Python & dependencies
sudo apt update && sudo apt install -y python3 python3-pip

# Clone / upload file bot ke VM
# (bisa pakai SCP atau git)

# Masuk ke folder bot
cd bot-laporan-dagangan

# Buat .env dari contoh
cp .env.example .env
nano .env  # isi TELEGRAM_TOKEN dan GOOGLE_CREDENTIALS_JSON

# Install dependencies
pip3 install -r requirements.txt

# Jalankan bot (background dengan screen)
screen -S dagangan
python3 bot.py
# Ctrl+A lalu D untuk detach dari screen

# Bot berjalan di background, cek dengan:
screen -r dagangan
```

---

## LANGKAH 6 — Setup Bot di Grup Telegram

1. Tambahkan bot ke grup: Tambah Anggota → cari `@DaganganEny_bot`
2. Salah satu admin grup kirim:
   ```
   /setup SPREADSHEET_ID_KAMU
   ```
   (ganti dengan ID dari langkah 3)
3. Bot akan konfirmasi ✅
4. Selesai! Semua anggota grup bisa langsung pakai bot.

---

## Perintah Bot

| Perintah | Keterangan |
|----------|------------|
| `/in Budi gas 1 20000` | Catat penjualan gas ke Budi |
| `/in SariBu sunlight 2 5000 bayar besok` | Catat penjualan sunlight |
| `/out gas 25 16000 kulakan pagi` | Catat restock gas |
| `/out sunlight 12 7000` | Catat restock sunlight |
| `/out lain 1 50000 bensin` | Catat pengeluaran lain |
| `/stok` | Lihat stok + saldo kas |
| `/today` | Ringkasan hari ini |
| `/week` | Ringkasan minggu ini |
| `/list` | Daftar transaksi hari ini |
| `/hapus 5` | Hapus transaksi #5 |
| `/edit 5 harga 21000` | Edit harga transaksi #5 |
| `/sync` | Sinkron manual ke Google Sheets |
| `/produk` | Daftar produk & kategori |

---

## Format Tanggal (Opsional di Awal Perintah)

| Format | Contoh |
|--------|--------|
| `kemarin` | `/in kemarin Budi gas 1 20000` |
| `besok` | `/out besok gas 25 16000` |
| `2hari` | 2 hari yang lalu |
| `15` | tanggal 15 bulan ini |
| `01/05` | 1 Mei |
