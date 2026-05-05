import os
import json
import time
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types
from config.settings import GEMINI_MODEL, MAX_RETRIES

load_dotenv()

# ─── Gemini client (reuses same pattern as chat_engine.py) ───────────────────

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        _client = genai.Client(api_key=api_key)
    return _client


# ─── Intent Detection (English only) ─────────────────────────────────────────

BUSINESS_TRIGGERS = [
    "business idea", "business ideas", "small business", "profitable business",
    "start a business", "suggest business", "recommend business",
    "startup idea", "low investment business", "high profit business",
    "which business", "what business", "business to start",
]

def is_business_query(message: str) -> bool:
    msg = message.lower()
    return any(trigger in msg for trigger in BUSINESS_TRIGGERS)


# ─── Prompt Builder ───────────────────────────────────────────────────────────

def build_business_prompt(user_message: str, preferences: dict) -> str:
    budget    = preferences.get("budget",   "not specified")
    city      = preferences.get("city",     "India (general)")
    risk      = preferences.get("risk",     "moderate")

    return f"""You are a Business Consultant and Loan Advisor specializing in Indian markets.

A user wants business ideas to support their loan application.

User details:
- Budget: {budget}
- Location type: {city}
- Risk appetite: {risk}
- Their query: {user_message}

Return ONLY a valid JSON object. No markdown, no explanation, no preamble, no backticks.

The JSON must follow this exact structure:
{{
  "businesses": [
    {{
      "id": 1,
      "business_name": "Name of Business",
      "tagline": "One line catchy description",
      "why_profitable": "2-3 sentences explaining profitability in India",
      "investment_level": "Low",
      "investment_range": "X – Y",
      "monthly_profit_range": "X – Y/month",
      "risk_level": "Low",
      "time_to_profit": "2-3 months",
      "loan_approval_reason": "Why banks easily approve loan for this business",
      "govt_schemes": ["Scheme 1", "Scheme 2"],
      "ideal_for": "Who this suits best"
    }}
  ],
  "summary": {{
    "best_for_quick_profit": "Business name + reason in one line",
    "best_for_long_term":    "Business name + reason in one line",
    "safest_for_loan":       "Business name + reason in one line"
  }},
  "advisor_note": "One paragraph of honest advice for this user based on their profile"
}}

Rules:
- Generate exactly 3 businesses
- risk_level and investment_level must be exactly one of: Low, Medium, High
- Make businesses realistic, specific to Indian market, relevant to user budget and location
- Return pure JSON only, nothing else
- Important: Keep each field concise. why_profitable max 1 sentence. loan_approval_reason max 1 sentence. advisor_note max 2 sentences. govt_schemes max 1 item. tagline max 6 words. ideal_for max 1 sentence."""


# ─── API Call ─────────────────────────────────────────────────────────────────

def get_business_ideas(user_message: str, preferences: dict) -> dict:
    """
    Calls Gemini API and returns parsed business ideas dict.
    Returns {"error": "..."} on failure.
    """
    prompt = build_business_prompt(user_message, preferences)

    for attempt in range(MAX_RETRIES):
        try:
            response = get_client().models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=8100,
                )
            )
            raw = response.text.strip()
            print("RAW GEMINI RESPONSE:", repr(raw))

            # Strip markdown fences robustly
            if "```json" in raw:
                raw = raw.split("```json")[1]
            if "```" in raw:
                raw = raw.split("```")[0]
            raw = raw.strip()

            data = json.loads(raw)
            # raw = response.text.strip()
            # print("RAW GEMINI RESPONSE:", repr(raw))  # ← ADD THIS

            # # Strip accidental markdown fences if model adds them
            # if raw.startswith("```"):
            #     raw = raw.split("```")[1]
            #     if raw.startswith("json"):
            #         raw = raw[4:]
            # raw = raw.strip()

            data = json.loads(raw)
            return data

        except json.JSONDecodeError as e:
            return {"error": f"Could not parse response as JSON: {str(e)}"}

        except Exception as e:
            error_str = str(e)
            print(f"[Business Advisor error attempt {attempt+1}] {error_str}")
            if "429" in error_str or "503" in error_str:
                wait = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait)
                continue
            return {"error": f"Business advisor API error: {error_str}"}

    return {"error": "Business advisor failed after all retries"}