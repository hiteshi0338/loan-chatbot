import os
import time
import random
from dotenv import load_dotenv   
from google import genai
from google.genai import types
from config.settings import (
    GEMINI_MODEL, MAX_TOKENS, TEMPERATURE, TOP_P, MAX_RETRIES
)

load_dotenv()  

client = None

def get_client():
    global client
    if client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        client = genai.Client(api_key=api_key)
    return client

SYSTEM_PROMPT = """
You are an expert Loan Eligibility Advisor for Indian users.
Your job is to analyze the user's financial details and suggest
suitable loan options, interest rates, and government schemes.
Always be concise, helpful, and specific to Indian banking context.
If eligibility is Low, suggest ways to improve credit score.
If eligibility is High or Medium, recommend suitable loan products.

CRITICAL RULES:
- Always complete your response fully. Never leave a sentence unfinished.
- If recommending multiple loan options, complete all of them.
- End with a clear closing sentence or next step for the user.
- Maximum 200 words. If you cannot finish in 200 words, summarize instead.
- Never end mid-sentence or mid-list.
"""


def build_context(history: list, message: str,
                  income, credit, eligibility: str) -> list:
    contents = []
    if not history:
        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=f"System Instruction:\n{SYSTEM_PROMPT}")]
        ))
        contents.append(types.Content(
            role="model",
            parts=[types.Part(text="Understood. I am your Loan Eligibility Advisor.")]
        ))
    for msg in history:
        contents.append(types.Content(
            role=msg["role"],
            parts=[types.Part(text=msg["text"])]
        ))
    enhanced = (
        f"User Query: {message}\n"
        f"Monthly Income: {income}\n"
        f"Credit Score: {credit}\n"
        f"Eligibility Level: {eligibility}\n"
        f"Reply in maximum 150 words. Be direct and complete."
        f"Do not cut off mid-sentence or mid-list. "
        f"Keep it under 200 words but always finish properly. "
        f"End with a clear next step or closing sentence."
    )
    contents.append(types.Content(
        role="user", parts=[types.Part(text=enhanced)]
    ))
    return contents


def safe_generate(contents: list) -> str | None:
    for attempt in range(MAX_RETRIES):
        try:
            response = get_client().models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    max_output_tokens=MAX_TOKENS,
                )
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            print(f"[Gemini error attempt {attempt+1}] {error_str}")
            if "429" in error_str or "503" in error_str:
                wait = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait)
            else:
                return None
    return None


def safe_generate_stream(contents: list):
    """
    Generator — yields text chunks as they stream from Gemini.
    Caller must handle empty generator as a failure signal.
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = get_client().models.generate_content_stream(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    max_output_tokens=MAX_TOKENS,
                )
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
            return  # ✅ clean exit after successful stream

        except Exception as e:
            error_str = str(e)
            print(f"[Gemini stream error attempt {attempt+1}] {error_str}")
            if "429" in error_str or "503" in error_str:
                wait = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait)
                continue  # ✅ retry on rate limit
            else:
                return  # ✅ non-retryable error — stop cleanly
    return  # ✅ all retries exhausted
