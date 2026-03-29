
# MAIN PART 


from google import genai
from google.genai import types
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session, render_template
import re
import os
import time

load_dotenv()

app = Flask(__name__)
app.secret_key = "loan_chatbot_secret_0338"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# System prompt
SYSTEM_PROMPT = """
You are an expert Loan Eligibility Advisor for Indian users.
Your job is to analyze the user's financial details and suggest 
suitable loan options.

You must:
- Only answer questions related to loans, finance, and eligibility
- Ask for details like salary, age, credit score if not provided
- Suggest loan types like Home Loan, Personal Loan, Car Loan, Education Loan
- Give clear eligibility verdicts based on the information given
- Be professional, helpful, and easy to understand
- Keep responses concise and under 750 words
- Use simple bullet points only when necessary
- Do not use markdown headers like ### or ---
- Do not use ** for bold, write plainly

If the user asks anything unrelated to loans or finance, politely 
refuse and bring the conversation back to loan advisory.
"""

@app.route('/')
def home():
    print("Home hits")
    return render_template('index.html')

def check_eligibility(income, credit):
    try:
        if not income or not credit:
            return "Unknown"
        try:
            income = float(income)
            credit = float(credit)
        except:
            return "Invalid"

        if credit >= 750 and income >= 40000:
            return "High"
        elif credit >= 650 and income >= 25000:
            return "Medium"
        else:
            return "Low"
    except:
        return "Unknown"
    

def is_loan_related(query):
    keywords = ["loan", "emi", "interest", "credit", "cibil", "mortgage"]
    query = query.lower()
    return any(word in query for word in keywords)

def calculate_emi(P, r, n):
    r = r / (12 * 100)  # monthly interest
    n = n * 12          # years → months

    emi = (P * r * (1 + r)**n) / ((1 + r)**n - 1)
    return round(emi, 2)
    

def safe_generate(contents):
    for i in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    top_p=0.8,
                    max_output_tokens=1800
                )
            )
            return response.text
        except Exception as e:
            if "429" in str(e):
                time.sleep(5 ** i)
            else:
                return "Error: " + str(e)
    return "⚠️ API limit reached. Try again later."


@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    session.pop('history', None)
    return jsonify({"status": "cleared"})


@app.route('/chat', methods=['POST'])

def chat():
    try:
        
        
        data = request.get_json()
        user_message = data.get('message')

        income = data.get("income", 0)
        credit = data.get("credit", 0)

        # user_message = request.json.get('message')
        if not is_loan_related(user_message):
            return jsonify({"reply": "⚠️ I only assist with loan-related queries."})
    
    
        eligibility = check_eligibility(income, credit)
    # Initialize history in session
        MAX_HISTORY = 10
        if 'history' in session:
            session['history'] = session['history'][-MAX_HISTORY:]
        else:
            session['history'] = []



        

    # Build history for Gemini
     # Build history for Gemini
        contents = []

# Only add system prompt if history is empty
        if len(session['history']) == 0:
            contents.append(types.Content(
            role="user",
            parts=[types.Part(text=f"System Instruction:\n{SYSTEM_PROMPT}")]
        ))
            contents.append(types.Content(
            role="model",
            parts=[types.Part(text="Understood. I am your Loan Eligibility Advisor.")]
        ))

    # Add previous history
        for msg in session['history']:
            contents.append(types.Content(
                role=msg['role'],
                parts=[types.Part(text=msg['text'])]
            ))

    # Add current user message
    # Add current user message WITH eligibility context
        enhanced_message = f"""
            User Query: {user_message}

        User Financial Context:
        - Monthly Income: {income}
        - Credit Score: {credit}
        - Eligibility Level: {eligibility}
        Reply in maximum 150 words. Be direct and concise. Complete your answer fully.
        Please give loan advice accordingly.
        """

        contents.append(types.Content(
        role="user",
        parts=[types.Part(text=enhanced_message)]
        ))
    
  

# Detect EMI query
        numbers = re.findall(r'\d+\.?\d*', user_message)

        if re.search(r'\bcalculate\s+emi\b|\bemi\s+calculator\b|\bcompute\s+emi\b', user_message.lower()):
            if len(numbers) >= 3:
                try:
                    P = float(numbers[0])
                    r = float(numbers[1])
                    n = float(numbers[2])
                    emi = calculate_emi(P, r, n)
                    return jsonify({
                        "reply": f"📊 Estimated EMI: ₹{emi} per month\n\nLoan: ₹{P}, Rate: {r}%, Tenure: {n} years"
                    })
                except:
                    return jsonify({
                        "reply": "⚠️ Couldn't calculate EMI. Please enter like: 500000 10 5"
                })

    # Call Gemini API
    # response = client.models.generate_content(
    #     model="gemini-2.0-flash",
    #     contents=contents,
    #     config=types.GenerateContentConfig(
    #         temperature=0.2,
    #         top_p=0.8,
    #         max_output_tokens=1000
    #     )
    # )

    # bot_reply = response.text

        # bot_reply = f"(TEST MODE)\nEligibility: {eligibility}\nYour query: {user_message}"
        bot_reply = safe_generate(contents)
        
    # Save history
        session['history'].append({'role': 'user', 'text': user_message})
        session['history'].append({'role': 'model', 'text': bot_reply})
        session.modified = True

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({
            "reply": "⚠️ Server error occurred. Please try again."
        })

if __name__ == '__main__':
    app.run(debug=True)

   