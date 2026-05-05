from config.settings import LOAN_KEYWORDS



def is_loan_related(query: str) -> bool:
    return any(kw in query.lower() for kw in LOAN_KEYWORDS)


def validate_financial_input(income, credit) -> list:
    errors = []
    try:
        income = float(income)
        if income <= 0 or income >= 10_000_000:
            errors.append("Income must be a positive number")
    except (ValueError, TypeError):
        errors.append("Income must be a number")
    try:
        credit = float(credit)
        if not (300 <= credit <= 900):
            errors.append("Credit score must be between 300 and 900")
    except (ValueError, TypeError):
        errors.append("Credit score must be a number")
    return errors
