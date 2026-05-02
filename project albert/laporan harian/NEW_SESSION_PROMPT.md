# Prompt untuk Memulai Sesi Claude Baru

Salin semua teks di bawah ini, lalu paste ke Claude (Code atau Web) di awal sesi.
Ganti bagian [dalam kurung] sesuai situasi.

---

## TEMPLATE PROMPT — BUG FIX

```
Aku punya bot Telegram laporan keuangan harian yang sudah jalan di Google Cloud VM.
Berikut konteks lengkap projectnya:

[PASTE ISI FILE PROJECT_SUMMARY.md DI SINI]

---

MASALAH SEKARANG:
[Jelaskan bug/errornya]

ERROR LOG (dari VM):
[Paste output dari: sudo journalctl -u bot-laporan -n 50]

FILE YANG RELEVAN:
[Sebutkan file mana yang mungkin bermasalah, misal: sheets_service.py]
```

---

## TEMPLATE PROMPT — TAMBAH FITUR

```
Aku punya bot Telegram laporan keuangan harian yang sudah jalan di Google Cloud VM.
Berikut konteks lengkap projectnya:

[PASTE ISI FILE PROJECT_SUMMARY.md DI SINI]

---

FITUR YANG MAU DITAMBAHKAN:
[Jelaskan fitur baru yang diinginkan]

CATATAN TAMBAHAN:
[Kalau ada preferensi format, batasan, dll]
```

---

## CARA DAPAT ERROR LOG

SSH ke VM dulu (Google Cloud Console → VM Instances → SSH), lalu:

```bash
# 50 log terakhir
sudo journalctl -u bot-laporan -n 50 --no-pager

# Log real-time (tekan Ctrl+C untuk stop)
sudo journalctl -u bot-laporan -f
```

---

## CARA UPDATE CODE SETELAH FIX

Setelah Claude kasih fix di laptop:
```bash
# Di laptop — push ke GitHub
cd "D:\CODE\GITHUB\darmstater.github.io"
git add "project albert/laporan harian/"
git commit -m "fix: [deskripsi]"
git push
```

Di VM (SSH):
```bash
cd "/home/darmstater12/darmstater.github.io/project albert/laporan harian"
git pull
sudo systemctl restart bot-laporan
sudo systemctl status bot-laporan
```
