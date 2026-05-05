from core.emi import calculate_emi


def simulate_scenarios(
    income:       float,
    credit:       float,
    base_amount:  float,
    base_rate:    float,
    base_tenure:  float
) -> list:
    """
    Generates 9 what-if scenarios by varying
    loan amount (±20%) and tenure (±2 years).
    """
    scenarios = []

    for amount_mult in [0.8, 1.0, 1.2]:
        for tenure_delta in [-2, 0, 2]:
            amount  = round(base_amount * amount_mult, -3)
            tenure  = max(1, base_tenure + tenure_delta)
            emi_val = calculate_emi(amount, base_rate, tenure)
            burden  = round((emi_val / income) * 100, 1) if income else 0

            if burden < 30:
                verdict     = "✅ Safe"
                verdict_color = "#4caf50"
            elif burden < 40:
                verdict     = "⚠️ Moderate"
                verdict_color = "#ffc107"
            elif burden < 55:
                verdict     = "⚠️ Risky"
                verdict_color = "#ff9800"
            else:
                verdict     = "❌ Avoid"
                verdict_color = "#f44336"

            scenarios.append({
                "amount":        amount,
                "tenure":        tenure,
                "rate":          base_rate,
                "emi":           emi_val,
                "burden":        burden,
                "verdict":       verdict,
                "verdict_color": verdict_color,
                "is_base":       amount_mult == 1.0 and tenure_delta == 0
            })

    return scenarios