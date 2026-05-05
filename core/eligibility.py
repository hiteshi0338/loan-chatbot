from config.settings import (
    ELIGIBILITY_THRESHOLDS,
    GOVT_SCHEME_INCOME_LIMIT,
)


def check_eligibility(income, credit) -> str:
    try:
        if income is None or credit is None:
            return "Unknown"
        income = float(income)
        credit = float(credit)
        if income <= 0 or credit <= 0:
            return "Unknown"
        high   = ELIGIBILITY_THRESHOLDS["HIGH"]
        medium = ELIGIBILITY_THRESHOLDS["MEDIUM"]
        if credit >= high["credit"] and income >= high["income"]:
            return "High"
        elif credit >= medium["credit"] and income >= medium["income"]:
            return "Medium"
        return "Low"
    except (ValueError, TypeError):
        return "Invalid"


def suggest_govt_schemes(income, credit, purpose="general") -> list:
    schemes = []
    try:
        income = float(income)
        credit = float(credit)
    except (ValueError, TypeError):
        return schemes

    if income < GOVT_SCHEME_INCOME_LIMIT:
        schemes.append("PM Mudra Loan")
    if credit < 600:
        schemes.append("Credit Builder Loan (SIDBI)")
    if purpose == "home":
        schemes.append("PM Awas Yojana")
    if purpose == "education":
        schemes.append("Interest Subsidy Scheme")

    # ✅ Fallback for users with good profile
    if not schemes:
        schemes.append("Standard Bank Loan (SBI / HDFC / ICICI)")

    return schemes
