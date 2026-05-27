import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN           = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDENTIALS_JSON  = os.getenv("GOOGLE_CREDENTIALS_JSON")
TIMEZONE                 = "Asia/Jakarta"

MONTH_NAMES_ID = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

DAY_NAMES_ID = {
    "Monday": "SENIN", "Tuesday": "SELASA", "Wednesday": "RABU",
    "Thursday": "KAMIS", "Friday": "JUMAT", "Saturday": "SABTU", "Sunday": "MINGGU"
}

# keyword → nama produk resmi
PRODUCTS = {
    "gas":      "Gas LPG 3kg",
    "lpg":      "Gas LPG 3kg",
    "elpiji":   "Gas LPG 3kg",
    "tabung":   "Gas LPG 3kg",
    "sunlight": "Sunlight",
    "sl":       "Sunlight",
    "sabun":    "Sunlight",
    "cuci":     "Sunlight",
}

# keyword → kategori non-produk (untuk /out lain-lain)
EXPENSE_OTHERS = {
    "lain":       "Lain-lain",
    "other":      "Lain-lain",
    "dll":        "Lain-lain",
    "operasional": "Operasional",
    "ops":        "Operasional",
    "transport":  "Operasional",
    "bensin":     "Operasional",
    "ongkir":     "Operasional",
    "parkir":     "Operasional",
}
