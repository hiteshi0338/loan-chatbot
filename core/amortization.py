def generate_amortization(P: float, r: float, years: float, months: int = 12) -> list:
    if P is None or r is None or years is None or years <= 0:
        return []

    monthly_rate = r / (12 * 100)
    total_months = int(years * 12)
    months = min(months, total_months)

    # Handle zero interest case
    if monthly_rate == 0:
        emi = P / total_months
    else:
        emi = (P * monthly_rate * (1 + monthly_rate) ** total_months) / \
              ((1 + monthly_rate) ** total_months - 1)

    schedule = []
    balance = P

    for month in range(1, months + 1):
        interest = balance * monthly_rate
        principal = emi - interest
        balance -= principal

        schedule.append({
            "month": month,
            "emi": round(emi, 2),
            "principal": round(principal, 2),
            "interest": round(interest, 2),
            "balance": round(max(balance, 0), 2)
        })

    return schedule