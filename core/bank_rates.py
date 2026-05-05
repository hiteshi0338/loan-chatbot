# Hardcoded current Indian bank rates (update periodically)
BANK_RATES = {
    "home": [
        {"bank": "SBI",          "min": 8.50, "max": 9.85,  "processing": "0.35%"},
        {"bank": "HDFC Bank",    "min": 8.75, "max": 9.65,  "processing": "0.50%"},
        {"bank": "ICICI Bank",   "min": 8.75, "max": 9.80,  "processing": "0.50%"},
        {"bank": "Kotak Mahindra","min": 8.75, "max": 9.50, "processing": "0.50%"},
        {"bank": "Axis Bank",    "min": 8.75, "max": 9.65,  "processing": "1.00%"},
        {"bank": "PNB",          "min": 8.50, "max": 9.75,  "processing": "0.35%"},
    ],
    "personal": [
        {"bank": "SBI",          "min": 11.45, "max": 14.60, "processing": "1.00%"},           # checked from official website
        {"bank": "HDFC Bank",    "min": 10.50, "max": 24.00, "processing": "2.50%"},
        {"bank": "ICICI Bank",   "min": 10.65, "max": 16.00, "processing": "2.25%"},
        {"bank": "Kotak Mahindra","min": 10.99, "max": 24.00,"processing": "2.50%"},
        {"bank": "Axis Bank",    "min": 11.25, "max": 22.00, "processing": "2.00%"},
        {"bank": "Bajaj Finance","min": 11.00, "max": 26.00, "processing": "3.99%"},
    ],
    "car": [
        {"bank": "SBI",          "min": 8.65,  "max": 9.55,  "processing": "Rs.1000"},
        {"bank": "HDFC Bank",    "min": 8.80,  "max": 10.30, "processing": "0.50%"},
        {"bank": "ICICI Bank",   "min": 8.80,  "max": 10.75, "processing": "0.50%"},
        {"bank": "Kotak Mahindra","min": 7.99, "max": 22.00, "processing": "0.50%"},
        {"bank": "Axis Bank",    "min": 9.25,  "max": 13.50, "processing": "Rs.3500"},
    ],
    "education": [
        {"bank": "SBI",          "min": 8.15,  "max": 11.15, "processing": "Nil"},
        {"bank": "Bank of Baroda","min": 8.15, "max": 12.85, "processing": "1.00%"},
        {"bank": "HDFC Credila", "min": 9.55,  "max": 13.25, "processing": "1.00%"},
        {"bank": "Axis Bank",    "min": 13.70, "max": 15.20, "processing": "2.00%"},
        {"bank": "ICICI Bank",   "min": 10.25, "max": 14.25, "processing": "1.00%"},
    ],
    "business": [
        {"bank": "SBI",          "min": 11.15, "max": 14.55, "processing": "1.00%"},
        {"bank": "HDFC Bank",    "min": 10.75, "max": 22.50, "processing": "2.00%"},
        {"bank": "ICICI Bank",   "min": 10.65, "max": 16.50, "processing": "2.00%"},
        {"bank": "Bajaj Finance","min": 14.00, "max": 26.00, "processing": "3.54%"},
        {"bank": "Axis Bank",    "min": 14.95, "max": 19.20, "processing": "2.00%"},
    ],
}


def get_bank_rates(purpose: str, credit: float = 0) -> list:
    purpose = purpose.lower().replace(" loan", "").strip()

    if purpose not in BANK_RATES:
        return []

    rates = sorted(BANK_RATES[purpose], key=lambda x: x["min"])

    result = []
    for i, bank in enumerate(rates):
        recommended = False

        if credit >= 750 and i == 0:
            recommended = True

        result.append({**bank, "recommended": recommended})

    return result

