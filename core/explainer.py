def explain_eligibility(income: float, credit: float,
                        existing_emi: float, eligibility: str) -> dict:
    """
    Returns a structured explanation of why the user got their eligibility level.
    Covers: credit score, income, FOIR, and improvement tips.
    """
    print("DEBUG: explainer called")
    foir      = round((existing_emi / income) * 100, 1) if income else 0
    sections  = []
    score     = 0   # internal score to build summary line

    # ── Credit Score Analysis ──
    if credit >= 750:
        credit_status = "Excellent"
        credit_icon   = "✅"
        credit_msg    = f"Your credit score of {credit} is excellent. You qualify for the best interest rates."
        score        += 3
    elif credit >= 700:
        credit_status = "Good"
        credit_icon   = "✅"
        credit_msg    = f"Your credit score of {credit} is good. Most lenders will approve your application."
        score        += 2
    elif credit >= 650:
        credit_status = "Fair"
        credit_icon   = "⚠️"
        credit_msg    = f"Your credit score of {credit} is fair. You may face higher interest rates."
        score        += 1
    else:
        credit_status = "Poor"
        credit_icon   = "❌"
        credit_msg    = f"Your credit score of {credit} is poor. Limited lenders will consider your application."
        score        += 0

    sections.append({
        "label":  f"{credit_icon} Credit Score — {credit_status}",
        "detail": credit_msg
    })

    # ── Income Analysis ──
    if income >= 60000:
        income_status = "Strong"
        income_icon   = "✅"
        income_msg    = f"Monthly income of ₹{income:,.0f} is strong. Eligible for high loan amounts."
        score        += 3
    elif income >= 40000:
        income_status = "Good"
        income_icon   = "✅"
        income_msg    = f"Monthly income of ₹{income:,.0f} meets high eligibility threshold."
        score        += 2
    elif income >= 25000:
        income_status = "Moderate"
        income_icon   = "⚠️"
        income_msg    = f"Monthly income of ₹{income:,.0f} meets medium eligibility threshold."
        score        += 1
    else:
        income_status = "Low"
        income_icon   = "❌"
        income_msg    = f"Monthly income of ₹{income:,.0f} is below minimum threshold for most lenders."
        score        += 0

    sections.append({
        "label":  f"{income_icon} Monthly Income — {income_status}",
        "detail": income_msg
    })

    # ── FOIR Analysis ──
    if foir == 0:
        foir_icon   = "✅"
        foir_status = "No existing debt"
        foir_msg    = "You have no existing EMIs — full income available for new loan."
        score      += 3
    elif foir < 30:
        foir_icon   = "✅"
        foir_status = f"{foir}% — Healthy"
        foir_msg    = f"Debt ratio of {foir}% is well within the safe limit of 40%."
        score      += 2
    elif foir < 40:
        foir_icon   = "⚠️"
        foir_status = f"{foir}% — Moderate"
        foir_msg    = f"Debt ratio of {foir}% is approaching the 40% RBI safe limit."
        score      += 1
    elif foir < 50:
        foir_icon   = "⚠️"
        foir_status = f"{foir}% — High"
        foir_msg    = f"Debt ratio of {foir}% exceeds safe limit. Lenders may reduce approved amount."
        score      += 0
    else:
        foir_icon   = "❌"
        foir_status = f"{foir}% — Critical"
        foir_msg    = f"Debt ratio of {foir}% is critically high. New loan approval is unlikely."
        score      -= 1

    sections.append({
        "label":  f"{foir_icon} Debt Ratio (FOIR) — {foir_status}",
        "detail": foir_msg
    })

    # ── Eligibility Summary ──
    if eligibility == "High":
        summary = "🟢 Strong profile — you qualify for the best loan products and rates."
    elif eligibility == "Medium":
        summary = "🟡 Decent profile — you qualify for standard loans with moderate rates."
    elif eligibility == "Low":
        summary = "🔴 Weak profile — limited options availablble. See tips below to improve."
    else:
        summary = "⚪ Profile incomplete — please provide income and credit score."

    # ── Improvement Tips (only if not High) ──
    tips = []
    if eligibility != "High":
        if credit < 750:
            tips.append("💳 Pay all credit card bills and EMIs on time to boost credit score.")
        if credit < 650:
            tips.append("🔄 Clear any outstanding dues or defaults immediately.")
        if foir >= 40:
            tips.append("📉 Close or prepay existing loans to reduce your debt ratio.")
        if income < 40000:
            tips.append("👥 Add a co-applicant (spouse/parent) to strengthen income profile.")
        if credit < 700:
            tips.append("💰 Maintain a credit utilisation ratio below 30% on credit cards.")
        tips.append("⏳ A stable employment history of 2+ years improves lender confidence.")

    return {
        "summary":     summary,
        "sections":    sections,
        "tips":        tips,
        "foir":        foir,
        "score":       score,        # internal 0–9 score
        "eligibility": eligibility
    }