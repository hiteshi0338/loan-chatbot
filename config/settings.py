LOAN_KEYWORDS = [
    "loan", "emi", "interest",
    "credit", "cibil", "mortgage",
    "borrow", "eligibility", "mudra",
    "home", "education", "personal",
    "repay", "tenure", "bank", "finance",
    "lend", "sanction", "disburse",
    "government scheme", "govt scheme", "apply for loan", 
    "business loan", "documents needed", "loan process",
    "mudra", "pmegp", "startup",
    "education loan", "course", "scholarship", "college fees",
    "tuition", "certification", "documents needed", "apply for loan"
]

ELIGIBILITY_THRESHOLDS = {
    "HIGH":   {"credit": 750, "income": 40000},
    "MEDIUM": {"credit": 650, "income": 25000},
}

GOVT_SCHEME_INCOME_LIMIT = 30000
MAX_HISTORY = 20
MAX_RETRIES = 3

GEMINI_MODEL    = "gemini-2.5-flash"
MAX_TOKENS      = 4500
TEMPERATURE     = 0.2
TOP_P           = 0.8