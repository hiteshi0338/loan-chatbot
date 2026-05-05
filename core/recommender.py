from config.settings import ELIGIBILITY_THRESHOLDS


# ── Interest rate map based on credit score ──
def get_interest_rate(credit: float, purpose: str) -> float:
    base_rates = {
        "home":      {"excellent": 8.5,  "good": 9.5,  "fair": 11.0, "poor": 13.5},
        "education": {"excellent": 8.0,  "good": 9.0,  "fair": 10.5, "poor": 12.0},
        "car":       {"excellent": 7.5,  "good": 8.5,  "fair": 10.0, "poor": 12.5},
        "business":  {"excellent": 10.0, "good": 12.0, "fair": 15.0, "poor": 18.0},
        "personal":  {"excellent": 10.5, "good": 13.0, "fair": 16.0, "poor": 20.0},
    }
    purpose = purpose.lower() if purpose else "personal"
    if purpose not in base_rates:
        purpose = "personal"

    if credit >= 750:
        tier = "excellent"
    elif credit >= 700:
        tier = "good"
    elif credit >= 650:
        tier = "fair"
    else:
        tier = "poor"

    return base_rates[purpose][tier]


# ── Tenure recommendation based on purpose ──
def get_recommended_tenure(purpose: str) -> int:
    tenure_map = {
        "home":      20,
        "education": 10,
        "car":        7,
        "business":   5,
        "personal":   3,
    }
    purpose = purpose.lower() if purpose else "personal"
    return tenure_map.get(purpose, 3)


# ── Risk tier based on income + credit ──
def get_risk_tier(income: float, credit: float, foir: float) -> str:
    if credit >= 750 and income >= 50000 and foir < 30:
        return "Low"
    elif credit >= 650 and income >= 25000 and foir < 50:
        return "Medium"
    else:
        return "High"


# ── Core recommendation engine ──
def recommend_loan(income: float, credit: float,
                   existing_emi: float = 0,
                   purpose: str = "personal") -> dict:
    """
    Returns optimal loan recommendation based on user profile.
    Uses FOIR (Fixed Obligation to Income Ratio) — RBI standard.
    Max safe EMI = 40% of income minus existing EMIs.
    """
    print("DEBUG: recommender called")
    # ── Safety checks ──
    if not income or income <= 0:
        return {"error": "Invalid income provided"}
    if not credit or credit < 300:
        return {"error": "Invalid credit score provided"}

    foir = round((existing_emi / income) * 100, 1) if income else 0

    if existing_emi >= income * 0.40:
        return {
            "error": "Existing EMIs exceed 40% of income (RBI safe limit)",
            "foir":  foir,
            "tip":   "Close or reduce existing loans before applying"
        }

    # ── Core calculations ──
    max_emi_capacity = (income * 0.40) - existing_emi
    rate             = get_interest_rate(credit, purpose)
    tenure           = get_recommended_tenure(purpose)
    risk             = get_risk_tier(income, credit, foir)

    # Back-calculate principal from affordable EMI
    r = rate / (12 * 100)
    n = tenure * 12
    max_principal = max_emi_capacity * ((1 + r)**n - 1) / (r * (1 + r)**n)

    # Conservative amount (80% for high risk, 90% medium, 100% low)
    risk_factor = {"Low": 1.0, "Medium": 0.90, "High": 0.80}
    safe_amount = max_principal * risk_factor[risk]

    # Total interest payable
    actual_emi     = (safe_amount * r * (1 + r)**n) / ((1 + r)**n - 1)
    total_payment  = actual_emi * n
    total_interest = total_payment - safe_amount

    return {
        "recommended_amount":   round(safe_amount,    -3),   # nearest 1000
        "recommended_tenure":   tenure,
        "recommended_rate":     rate,
        "recommended_emi":      round(actual_emi,       2),
        "max_emi_capacity":     round(max_emi_capacity, 2),
        "total_interest":       round(total_interest,  -2),
        "total_payment":        round(total_payment,   -2),
        "foir":                 foir,
        "risk_tier":            risk,
        "purpose":              purpose,
    }