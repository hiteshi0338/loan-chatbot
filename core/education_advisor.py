import os
import json
import time
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types
from config.settings import GEMINI_MODEL, MAX_RETRIES

load_dotenv()

# ─── Gemini client ────────────────────────────────────────────────────────────

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        _client = genai.Client(api_key=api_key)
    return _client


# ─── Intent Detection ─────────────────────────────────────────────────────────

EDUCATION_TRIGGERS = [
    "education loan", "course", "college", "degree", "study",
    "university", "admission", "fees", "tuition", "scholarship",
    "skill course", "certification", "diploma", "mba", "engineering",
    "medical college", "btech", "mtech", "which course", "what course",
    "course suggestion", "higher education", "abroad study",
    "career course", "best course", "career advice"
]

def is_education_query(message: str) -> bool:
    msg = message.lower()
    return any(trigger in msg for trigger in EDUCATION_TRIGGERS)


# ─── Prompt Builder ───────────────────────────────────────────────────────────

def build_education_prompt(user_message: str, preferences: dict) -> str:
    budget   = preferences.get("budget",   "not specified")
    field    = preferences.get("field",    "any field")
    goal     = preferences.get("goal",     "career growth")

    return f"""You are an Education Loan Advisor specializing in Indian students and courses.

A student wants course/college recommendations to support their education loan application.

Student details:
- Loan budget: {budget}
- Field of interest: {field}
- Career goal: {goal}
- Their query: {user_message}

Return ONLY a valid JSON object. No markdown, no explanation, no preamble, no backticks.

The JSON must follow this exact structure:
{{
  "courses": [
    {{
      "id": 1,
      "course_name": "Course Name",
      "institution": "College/Platform name",
      "tagline": "Max 6 words",
      "why_worth_it": "One sentence on ROI and job market.",
      "duration": "X years or X months",
      "total_fees": "₹X – ₹Y",
      "loan_amount_needed": "₹X – ₹Y",
      "avg_starting_salary": "₹X LPA",
      "difficulty_level": "Easy",
      "loan_approval_reason": "One sentence only.",
      "top_recruiters": ["Company 1", "Company 2"],
      "ideal_for": "One sentence only."
    }}
  ],
  "summary": {{
    "best_roi": "Course name only",
    "fastest_career": "Course name only",
    "easiest_loan_approval": "Course name only"
  }},
  "advisor_note": "Two sentences max of honest advice."
}}

Rules:
- Generate exactly 3 courses or colleges
- difficulty_level must be exactly one of: Easy, Medium, Hard
- Mix degree courses and skill-based certifications
- Focus on Indian market job prospects and salaries
- Keep all string fields SHORT — max 15 words each
- No newlines inside string values
- Return pure JSON only, nothing else

Important: why_worth_it max 1 sentence. loan_approval_reason max 1 sentence. advisor_note max 2 sentences. top_recruiters max 2 items. ideal_for max 1 sentence. tagline max 6 words."""


# ─── API Call ─────────────────────────────────────────────────────────────────

def get_education_ideas(user_message: str, preferences: dict) -> dict:
    """
    Calls Gemini API and returns parsed education recommendations dict.
    Returns {"error": "..."} on failure.
    """
    prompt = build_education_prompt(user_message, preferences)

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
                    temperature=0.4,
                    max_output_tokens=8100,
                    response_mime_type="application/json",
                )
            )

            raw = response.text.strip()
            print("RAW EDUCATION RESPONSE:", repr(raw[:200]))

            # Strip markdown fences if present
            if "```json" in raw:
                raw = raw.split("```json")[1]
            if "```" in raw:
                raw = raw.split("```")[0]
            raw = raw.strip()

            data = json.loads(raw)
            return data

        except json.JSONDecodeError as e:
            return {"error": f"Could not parse response as JSON: {str(e)}"}

        except Exception as e:
            error_str = str(e)
            print(f"[Education Advisor error attempt {attempt+1}] {error_str}")
            if "429" in error_str or "503" in error_str:
                wait = 60 + random.uniform(0, 5)
                print(f"Rate limited — waiting {wait:.0f}s...")
                time.sleep(wait)
                continue
            return {"error": f"Education advisor API error: {error_str}"}

    return {"error": "Education advisor failed after all retries"}