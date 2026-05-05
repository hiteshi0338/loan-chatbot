import re


def calculate_emi(P: float, r: float, n: float) -> float:
    """
    P = principal amount
    r = annual interest rate (%)
    n = tenure in years
    """
    if r <= 0 or n <= 0 or P <= 0:
        return 0.0
    r = r / (12 * 100)   # monthly rate
    n = n * 12           # months
    emi = (P * r * (1 + r)**n) / ((1 + r)**n - 1)
    return round(emi, 2)


def extract_amount(message: str) -> float | None:
    """Handles '5 lakh', '1.5 crore', or plain numbers"""
    lakh  = re.search(r'(\d+\.?\d*)\s*lakh',  message.lower())
    crore = re.search(r'(\d+\.?\d*)\s*crore', message.lower())
    if crore:
        return float(crore.group(1)) * 10_000_000
    if lakh:
        return float(lakh.group(1)) * 100_000
    return None

def parse_emi_intent(message: str) -> dict | None:
    msg_lower = message.lower()

    # ✅ Must explicitly ask for EMI calculation
    # Profile analysis messages should NOT trigger this
    intent = re.search(
        r'\b(calculate|compute|find|what is|tell me|show me)\b.{0,20}\bemi\b'
        r'|\bemi\b.{0,20}\b(calculator|for|of|on)\b'
        r'|\bemi calculator\b',
        msg_lower
    )
    if not intent:
        return None

    # ✅ Also block if message looks like a profile analysis
    block_phrases = [
        "analyze my profile",
        "my name is",
        "monthly income",
        "credit score",
        "loan purpose",
        "eligibility is pre-calculated"
    ]
    if any(phrase in msg_lower for phrase in block_phrases):
        return None

    # Extract loan amount (lakh/crore aware)
    P = extract_amount(message)

    numbers = re.findall(r'\d+\.?\d*', message)

    if P is not None:
        plain_numbers = [float(n) for n in numbers
                         if float(n) not in [P / 100_000, P / 10_000_000]]
        if len(plain_numbers) >= 2:
            return {
                "P": P,
                "r": plain_numbers[0],
                "n": plain_numbers[1],
            }

    if len(numbers) >= 3:
        return {
            "P": float(numbers[0]),
            "r": float(numbers[1]),
            "n": float(numbers[2]),
        }

    return None

