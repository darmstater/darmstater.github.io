# Maintenance Guide — Bot Laporan Harian

## Info Server
- **Platform**: Google Cloud VM (e2-micro) — FREE selamanya
- **Region**: us-central1
- **User**: darmstater12
- **Path bot**: `/home/darmstater12/darmstater.github.io/project albert/laporan harian`
- **Service name**: `bot-laporan`

---

## Perintah Harian

```bash
# Cek status bot (hidup/mati?)
sudo systemctl status bot-laporan

# Lihat log real-time
sudo journalctl -u bot-laporan -f

# Lihat 50 log terakhir
sudo journalctl -u bot-laporan -n 50
```

---

## Update Code (paling sering dipakai)

Kalau ada perubahan code di GitHub:

```bash
# 1. Masuk ke folder bot
cd "/home/darmstater12/darmstater.github.io/project albert/laporan harian"

# 2. Pull update terbaru dari GitHub
git pull

# 3. Restart bot
sudo systemctl restart bot-laporan

# 4. Cek statusnya
sudo systemctl status bot-laporan
```

---

## Start / Stop / Restart

```bash
sudo systemctl start bot-laporan      # Jalankan bot
sudo systemctl stop bot-laporan       # Matikan bot
sudo systemctl restart bot-laporan    # Restart bot
```

---

## Bot Mati / Error

```bash
# Lihat error detail
sudo journalctl -u bot-laporan -n 100 --no-pager

# Coba restart dulu
sudo systemctl restart bot-laporan
```

### Error umum & solusinya:

| Error | Penyebab | Solusi |
|---|---|---|
| `ConnectionError` | Internet VM putus | Tunggu sebentar, auto-restart |
| `Unauthorized` | Token Telegram salah | Cek `.env`, update token |
| `SpreadsheetNotFound` | Spreadsheet ID salah | Cek `.env`, update ID |
| `403 Forbidden` | Service account belum diberi akses | Share spreadsheet ke service account email |

---

## Update Credentials (.env)

Kalau perlu ganti token/credentials:

```bash
cd "/home/darmstater12/darmstater.github.io/project albert/laporan harian"
nano .env
# Edit nilainya → Ctrl+X → Y → Enter
sudo systemctl restart bot-laporan
```

---

## Tambah Kategori Baru

Edit `config.py` di laptop:
- Buka `D:\CODE\GITHUB\LAPORAN HARIAN\config.py`
- Tambahkan kata kunci di `CATEGORIES_OUT` atau `CATEGORIES_IN`
- Push ke GitHub
- Pull di VM → restart bot

---

## Sync Manual ke Google Sheets

Kirim perintah ini ke bot Telegram:
```
/sync
```

---

## Backup Database

Database SQLite ada di VM:
```bash
# Lihat ukuran database
ls -lh "/home/darmstater12/darmstater.github.io/project albert/laporan harian/laporan.db"

# Copy backup ke home folder
cp "/home/darmstater12/darmstater.github.io/project albert/laporan harian/laporan.db" \
   /home/darmstater12/laporan-backup-$(date +%Y%m%d).db
```

---

## VM Mati / Restart

VM bisa restart sendiri (jarang). Setelah restart:
- Bot **otomatis jalan lagi** (sudah di-enable di systemd)
- Tidak perlu manual start

Kalau mau cek VM nyala:
- Buka Google Cloud Console → VM Instances → cek status hijau ✅

---

## Akses SSH ke VM

Buka **console.cloud.google.com** → VM Instances → klik tombol **SSH**
