import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
TIMEZONE = "Asia/Jakarta"

MONTH_NAMES_ID = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

DAY_NAMES_ID = {
    "Monday": "SENIN", "Tuesday": "SELASA", "Wednesday": "RABU",
    "Thursday": "KAMIS", "Friday": "JUMAT", "Saturday": "SABTU", "Sunday": "MINGGU"
}

CATEGORIES_OUT = {
    "makan": "Makan & Minum",
    "makanan": "Makan & Minum",
    "minum": "Makan & Minum",
    "food": "Makan & Minum",
    "kopi": "Makan & Minum",
    "snack": "Makan & Minum",
    "transport": "Transport",
    "transportasi": "Transport",
    "grab": "Transport",
    "gojek": "Transport",
    "ojek": "Transport",
    "bensin": "Transport",
    "parkir": "Transport",
    "tol": "Transport",
    "belanja": "Belanja",
    "shopping": "Belanja",
    "baju": "Belanja",
    "sepatu": "Belanja",
    "tagihan": "Tagihan",
    "listrik": "Tagihan",
    "air": "Tagihan",
    "wifi": "Tagihan",
    "internet": "Tagihan",
    "pulsa": "Tagihan",
    "sewa": "Tagihan",
    "kos": "Tagihan",
    "hiburan": "Hiburan",
    "entertainment": "Hiburan",
    "nonton": "Hiburan",
    "game": "Hiburan",
    "spotify": "Hiburan",
    "netflix": "Hiburan",
    "kesehatan": "Kesehatan",
    "obat": "Kesehatan",
    "dokter": "Kesehatan",
    "vitamin": "Kesehatan",
    "gym": "Kesehatan",
    "lain": "Lain-lain",
    "other": "Lain-lain",
    "dll": "Lain-lain",
}

CATEGORIES_IN = {
    "gaji": "Gaji",
    "salary": "Gaji",
    "freelance": "Freelance",
    "proyek": "Freelance",
    "project": "Freelance",
    "transfer": "Transfer",
    "bisnis": "Bisnis",
    "investasi": "Investasi",
    "lain": "Lain-lain",
    "other": "Lain-lain",
}
