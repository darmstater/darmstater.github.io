# Deploy Bot untuk User Baru
> Panduan ini untuk menambahkan teman ke bot laporan harian yang sudah jalan.
> Tidak perlu setup Google Cloud / VM baru — semua reuse yang sudah ada.

---

## Yang Teman Kamu Siapkan (mereka kerjakan sendiri)

### 1. Buat Telegram Bot
1. Buka Telegram → cari **@BotFather**
2. Ketik `/newbot` → ikuti instruksi → kasih nama bot
3. Salin **TOKEN** yang diberikan BotFather → kirim ke kamu

### 2. Dapat Chat ID
1. Buka bot mereka di Telegram → klik **Start**
2. Buka browser, akses URL ini (ganti TOKEN):
   ```
   https://api.telegram.org/bot[TOKEN]/getUpdates
   ```
3. Cari nilai `"id"` di dalam `"chat"` → itu **CHAT_ID** mereka → kirim ke kamu

### 3. Siapkan Google Spreadsheet
1. Buat spreadsheet baru di Google Sheets (boleh kosong)
2. Klik **Share** → paste email ini → set **Editor** → klik Send:
   ```
   bot-laporan@laporan-harian-495106.iam.gserviceaccount.com
   ```
3. Copy **Spreadsheet ID** dari URL:
   ```
   https://docs.google.com/spreadsheets/d/[INI_YANG_DICOPY]/edit
   ```
4. Kirim Spreadsheet ID ke kamu

---

## Checklist Info yang Harus Diterima

Sebelum mulai setup di VM, pastikan sudah punya:
```
[ ] TELEGRAM_TOKEN   = ...
[ ] TELEGRAM_CHAT_ID = ...
[ ] SPREADSHEET_ID   = ...
[ ] Nama teman       = ... (untuk penamaan folder & service)
```

---

## Setup di VM (kamu yang kerjakan)

### Akses VM
Buka **console.cloud.google.com** → VM Instances → klik **SSH** di baris `bot-laporan`

### Jalankan perintah berikut (ganti `[nama]` dengan nama teman, tanpa spasi)

**Step 1 — Copy folder bot**
```bash
cp -r ~/bot-laporan ~/bot-laporan-[nama]
```

**Step 2 — Edit .env**
```bash
nano ~/bot-laporan-[nama]/.env
```
Ganti 3 baris ini dengan data teman:
```
TELEGRAM_TOKEN=[token_mereka]
TELEGRAM_CHAT_ID=[chatid_mereka]
SPREADSHEET_ID=[spreadsheetid_mereka]
```
Simpan: **Ctrl+X → Y → Enter**

**Step 3 — Buat script runner**
```bash
nano ~/run-bot-[nama].sh
```
Isi:
```bash
#!/bin/bash
cd /home/darmstater12/bot-laporan-[nama]
source venv/bin/activate
exec python3 bot.py
```
Simpan: **Ctrl+X → Y → Enter**

```bash
chmod +x ~/run-bot-[nama].sh
```

**Step 4 — Buat systemd service**
```bash
sudo nano /etc/systemd/system/bot-[nama].service
```
Isi:
```ini
[Unit]
Description=Bot Laporan Harian - [nama]
After=network.target

[Service]
Type=simple
User=darmstater12
ExecStart=/bin/bash /home/darmstater12/run-bot-[nama].sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
Simpan: **Ctrl+X → Y → Enter**

**Step 5 — Aktifkan & jalankan**
```bash
sudo systemctl daemon-reload
sudo systemctl enable bot-[nama]
sudo systemctl start bot-[nama]
sudo systemctl status bot-[nama]
```

Kalau statusnya **`active (running)`** → selesai!

---

## Verifikasi

Minta teman kirim `/start` ke bot mereka. Kalau bot reply → sukses.

Cek log kalau ada error:
```bash
sudo journalctl -u bot-[nama] -n 50
```

---

## Manage Bot Teman

```bash
# Cek status
sudo systemctl status bot-[nama]

# Restart
sudo systemctl restart bot-[nama]

# Stop permanen
sudo systemctl stop bot-[nama]
sudo systemctl disable bot-[nama]

# Lihat semua bot yang jalan
sudo systemctl list-units --type=service | grep bot-
```

---

## Catatan Penting

- **Satu VM bisa handle banyak bot** — tidak perlu VM baru
- **Service account Google sama** — cukup share spreadsheet baru ke email yang sama
- **Database masing-masing terpisah** — data tidak tercampur antar user
- **Kalau teman berhenti pakai** → stop & disable service-nya, hapus foldernya

---

## Contoh Nyata (misal nama teman: budi)

```bash
cp -r ~/bot-laporan ~/bot-laporan-budi
nano ~/bot-laporan-budi/.env          # isi token/chatid/spreadsheet budi
nano ~/run-bot-budi.sh                # buat script runner
chmod +x ~/run-bot-budi.sh
sudo nano /etc/systemd/system/bot-budi.service
sudo systemctl daemon-reload
sudo systemctl enable bot-budi
sudo systemctl start bot-budi
sudo systemctl status bot-budi
```
