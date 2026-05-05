import os
import uuid
import json
import bcrypt


from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from core.auth import User, get_user_by_email, get_user_by_id

from flask import Flask, request, jsonify, session, render_template, send_file, Response, stream_with_context,redirect
from dotenv import load_dotenv

from config.settings import MAX_HISTORY
from core.validators  import is_loan_related, validate_financial_input
from core.eligibility import check_eligibility, suggest_govt_schemes
from core.emi         import calculate_emi, parse_emi_intent
from core.chat_engine import build_context, safe_generate, safe_generate_stream
from core.pdf_report  import generate_loan_report
from core.recommender import recommend_loan, get_interest_rate
from core.explainer   import explain_eligibility
from core.simulator   import simulate_scenarios
from core.memory      import save_user, get_user,get_profile_delta
from core.amortization import generate_amortization
from core.bank_rates  import get_bank_rates
from core.database import create_table,get_connection
from core.business_advisor import is_business_query, get_business_ideas
from core.education_advisor import is_education_query, get_education_ideas

create_table()

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
os.environ['PYTHONUNBUFFERED'] = '1'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

@app.route("/register", methods=["POST"])
def register():
    email = request.form.get("email")
    password = request.form.get("password")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO auth_users (email, password) VALUES (?, ?)",
            (email, hashed)
        )
        conn.commit()
    except:
        return "User already exists"

    conn.close()
    return redirect("/login")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    user = get_user_by_email(email)

    if user and bcrypt.checkpw(password.encode(), user[2]):
        user_obj = User(user[0], user[1])
        login_user(user_obj)
        return redirect("/")   # go to chatbot

    return "Invalid credentials"



# def get_uid():
#     if "uid" not in session:
#         session["uid"] = str(uuid.uuid4())
#     return session["uid"]


def make_stream_response(generator_func):
    """Helper — wraps any generator into a proper SSE Response."""
    return Response(
        stream_with_context(generator_func()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        }
    )


@app.route("/")
@login_required
def home():
    return render_template("index.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    session.pop("history", None)
    return jsonify({"status": "cleared"})


@app.route("/simulate", methods=["POST"])
def simulate():
    try:
        data   = request.get_json()
        income = float(data.get("income") or 0)
        credit = float(data.get("credit") or 0)
        amount = float(data.get("amount") or 0)
        rate   = float(data.get("rate")   or 0)
        tenure = float(data.get("tenure") or 0)

        if not all([income, credit, amount, rate, tenure]):
            return jsonify({"error": "All fields required"}), 400

        scenarios = simulate_scenarios(income, credit, amount, rate, tenure)
        return jsonify({"scenarios": scenarios})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Simulation error"}), 500


@app.route("/download_report", methods=["POST"])
def download_report():
    try:
        data        = request.get_json()
        income      = data.get("income",      0)
        credit      = data.get("credit",      0)
        eligibility = data.get("eligibility", "Unknown")
        schemes     = data.get("schemes",     [])
        summary     = data.get("summary",     "")
        emi_data    = data.get("emi_data",    None)

        recommendation = session.get("last_recommendation", None)
        explanation    = session.get("last_explanation",    None)
        dashboard      = session.get("last_dashboard",      None)

        # ✅ Bug 2 fixed — use 'years' not 'n' (matching amortization.py signature)
        amortization = None
        if recommendation and not recommendation.get("error"):
            amortization = generate_amortization(
                P      = recommendation["recommended_amount"],
                r      = recommendation["recommended_rate"],
                years  = recommendation["recommended_tenure"],  # ✅ fixed
                months = 12
            )

        filepath = generate_loan_report(
            income=income,
            credit=credit,
            eligibility=eligibility,
            schemes=schemes,
            chat_summary=summary,
            emi_data=emi_data,
            recommendation=recommendation,
            explanation=explanation,
            dashboard=dashboard,
            amortization=amortization
        )

        return send_file(
            filepath,
            as_attachment=True,
            download_name="Loan_Eligibility_Report.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Could not generate report"}), 500


@app.route("/dashboard_data", methods=["POST"])
def dashboard_data():
    try:
        data         = request.get_json()
        income       = float(data.get("income") or 0)
        credit       = float(data.get("credit") or 0)
        existing_emi = float(data.get("emi")    or 0)
        purpose      = data.get("purpose", "personal")

        if not income or not credit:
            return jsonify({"error": "Income and credit required"}), 400

        safe_emi_limit = round(income * 0.40, 2)
        remaining      = round(safe_emi_limit - existing_emi, 2)
        foir           = round((existing_emi / income) * 100, 1)
        rate           = get_interest_rate(credit, purpose)

        affordability = (
            "Excellent" if existing_emi == 0 else
            "Good"      if foir < 30          else
            "Moderate"  if foir < 40          else
            "Stretched" if foir < 50          else
            "Critical"
        )
        credit_health = (
            "Excellent" if credit >= 750 else
            "Good"      if credit >= 700 else
            "Fair"      if credit >= 650 else
            "Poor"
        )

        recommendation = recommend_loan(income, credit, existing_emi, purpose)
        new_emi = recommendation.get("recommended_emi", 0) \
                  if not recommendation.get("error") else 0

        session["last_dashboard"] = {
            "income":          income,
            "existing_emi":    existing_emi,
            "safe_emi_limit":  safe_emi_limit,
            "remaining":       remaining,
            "foir":            foir,
            "after_loan_foir": round(((existing_emi + new_emi) / income) * 100, 1),
            "affordability":   affordability,
            "credit_health":   credit_health,
            "rate":            rate
        }
        session.modified = True

        return jsonify({
            "income":          income,
            "existing_emi":    existing_emi,
            "safe_emi_limit":  safe_emi_limit,
            "remaining":       remaining,
            "foir":            foir,
            "affordability":   affordability,
            "credit_health":   credit_health,
            "credit":          credit,
            "rate":            rate,
            "new_emi":         round(new_emi, 2),
            "after_loan_foir": round(((existing_emi + new_emi) / income) * 100, 1)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Dashboard error"}), 500


@app.route("/bank_rates", methods=["POST"])
def bank_rates():
    try:
        data    = request.get_json()
        purpose = data.get("purpose", "personal")
        credit  = float(data.get("credit") or 0)
        rates   = get_bank_rates(purpose, credit)
        return jsonify({"rates": rates})
    except Exception as e:
        return jsonify({"error": "Could not fetch rates"}), 500

# ── ADD THIS ENTIRE ROUTE after your /bank_rates route ──────────────────────

@app.route("/business_advice", methods=["POST"])
@login_required
def business_advice():
    try:
        data        = request.get_json()
        message     = data.get("message", "")
        preferences = data.get("preferences", {})   # budget, city, risk, experience

        result = get_business_ideas(message, preferences)
        print("BUSINESS RESULT:", result) 
        if "error" in result:
            return jsonify({"error": result["error"]}), 500

        # Store in session so follow-up questions work
        session["last_business_context"] = {
            "businesses":   result.get("businesses", []),
            "preferences":  preferences,
            "user_message": message
        }
        session.modified = True

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Business advisor error"}), 500


@app.route("/education_advice", methods=["POST"])
@login_required
def education_advice():
    try:
        data        = request.get_json()
        message     = data.get("message", "")
        preferences = data.get("preferences", {})

        result = get_education_ideas(message, preferences)
        print("EDUCATION RESULT:", result)

        if "error" in result:
            return jsonify({"error": result["error"]}), 500

        session["last_education_context"] = {
            "courses":      result.get("courses", []),
            "preferences":  preferences,
            "user_message": message
        }
        session.modified = True

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Education advisor error"}), 500




@app.route("/chat", methods=["POST"])
@login_required
def chat():
    try:
        data         = request.get_json()
        message      = data.get("message", "")
        income       = float(data.get("income")  or 0)
        credit       = float(data.get("credit")  or 0)
        existing_emi = float(data.get("emi")      or 0)
        purpose      = data.get("purpose", "general")

        errors = validate_financial_input(income, credit)
        if errors and income > 0:
            return jsonify({"reply": "⚠️ " + " | ".join(errors)})

        if not is_loan_related(message):
            return jsonify({"reply": "I only assist with loan-related queries."})

        eligibility    = check_eligibility(income, credit)
        schemes        = suggest_govt_schemes(income, credit, purpose)
        recommendation = recommend_loan(income, credit, existing_emi, purpose)
        explanation    = explain_eligibility(income, credit, existing_emi, eligibility)

        session["last_recommendation"] = recommendation
        session["last_explanation"]    = explanation

        # uid = get_uid()
        uid = str(current_user.id)
  
        delta = get_profile_delta(uid)
        print("DELTA:", delta)
              
        save_user(uid, {
            "income":      income,
            "credit":      credit,
            "eligibility": eligibility,
            "purpose":     purpose
        })
        print("USER DATA FROM DB:", get_user(uid))

        if delta :
            credit_status = (
            "improved 📈" if delta["credit_delta"] > 0 else
            "declined 📉" if delta["credit_delta"] < 0 else
            "unchanged"
        )

            message += (
                f"\nReturning user detected.\n"
                f"Credit score: {delta['previous_credit']} → {credit} ({credit_status})\n"
                f"Income: ₹{delta['previous_income']} → ₹{income}\n"
                f"Previous eligibility: {delta['previous_eligibility']}\n"
            )

        session.setdefault("history", [])
        session["history"] = session["history"][-MAX_HISTORY:]

        contents  = build_context(session["history"], message, income, credit, eligibility)
        bot_reply = safe_generate(contents)

        if bot_reply is None:
            bot_reply = (
                f"Loan Eligibility: {eligibility}\n"
                f"Income: Rs. {income} | Credit: {credit}\n"
                f"AI server is busy — showing fallback response."
            )
            if schemes:
                bot_reply += "\nGovernment Schemes:\n" + \
                             "\n".join(f"- {s}" for s in schemes)

        session["history"].append({"role": "user",  "text": message})
        session["history"].append({"role": "model", "text": bot_reply})
        session.modified = True

        return jsonify({
            "reply":          bot_reply,
            "eligibility":    eligibility,
            "explanation":    explanation,
            "schemes":        schemes,
            "recommendation": recommendation,
            "delta":          delta
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"reply": "Server error. Please try again."})


@app.route("/chat_stream", methods=["POST"])
@login_required
def chat_stream():
    try:
        data         = request.get_json()
        message      = data.get("message", "")
        income       = float(data.get("income")  or 0)
        credit       = float(data.get("credit")  or 0)
        existing_emi = float(data.get("emi")      or 0)
        purpose      = data.get("purpose", "general")

        # ✅ Bug 1 fixed — use correct function name not_related, not generate()
        if not is_loan_related(message):
            def not_related():
                yield f"data: {json.dumps({'text': 'I only assist with loan-related queries.'})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            return make_stream_response(not_related)   # ✅

        emi_params = parse_emi_intent(message)
        if emi_params:
            emi   = calculate_emi(**emi_params)
            reply = (
                f"Estimated EMI: Rs.{emi}/month\n"
                f"Loan: Rs.{emi_params['P']} | "
                f"Rate: {emi_params['r']}% | "
                f"Tenure: {emi_params['n']} yrs"
            )
            def emi_stream():
                yield f"data: {json.dumps({'text': reply})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            return make_stream_response(emi_stream)    # ✅

        # ── Core processing ──
        eligibility    = check_eligibility(income, credit)
        schemes        = suggest_govt_schemes(income, credit, purpose)
        recommendation = recommend_loan(income, credit, existing_emi, purpose)
        explanation    = explain_eligibility(income, credit, existing_emi, eligibility)

        session["last_recommendation"] = recommendation
        session["last_explanation"]    = explanation

        # uid = get_uid()
        uid = str(current_user.id)
        print("CURRENT USER:", current_user.id)
        delta = get_profile_delta(uid)
        print("DELTA:", delta)
        save_user(uid, {
            "income":      income,
            "credit":      credit,
            "eligibility": eligibility,
            "purpose":     purpose
        })
        print("USER DATA FROM DB:", get_user(uid))
       

        if delta:
            message += (
                f"\nReturning user — visit #{delta['visits']}.\n"
                f"Previous credit: {delta['previous_credit']} → Current: {credit}.\n"
                f"Previous eligibility: {delta['previous_eligibility']}.\n"
            )

        session.setdefault("history", [])
        session["history"] = session["history"][-MAX_HISTORY:]

        contents     = build_context(session["history"], message, income, credit, eligibility)
        history_user = {"role": "user", "text": message}

        def stream_response():
            full_reply  = ""
            chunk_count = 0

            try:
                for chunk in safe_generate_stream(contents):
                    if chunk is None:
                        continue
                    full_reply  += chunk
                    chunk_count += 1
                    yield f"data: {json.dumps({'text': chunk})}\n\n"

                if chunk_count == 0:
                    fallback = (
                        f"Loan Eligibility: {eligibility}\n"
                        f"Income: Rs. {income} | Credit: {credit}\n"
                        f"AI server is busy — showing fallback response."
                    )
                    if schemes:
                        fallback += "\nGovernment Schemes:\n" + \
                                    "\n".join(f"- {s}" for s in schemes)
                    full_reply = fallback
                    yield f"data: {json.dumps({'text': fallback})}\n\n"

                yield f"data: {json.dumps({'done': True, 'eligibility': eligibility, 'schemes': schemes, 'recommendation': recommendation, 'explanation': explanation, 'delta': delta})}\n\n"
                # yield f"data: {json.dumps({'done': True, 'eligibility': eligibility, 'schemes': schemes, 'recommendation': recommendation, 'explanation': explanation})}\n\n"


            except Exception as ex:
                print(f"[stream error] {ex}")
                fallback = (
                    f"Loan Eligibility: {eligibility}\n"
                    f"Income: Rs. {income} | Credit: {credit}\n"
                    f"AI server is busy — showing fallback response."
                )
                yield f"data: {json.dumps({'text': fallback, 'done': True, 'eligibility': eligibility, 'schemes': schemes})}\n\n"
                full_reply = fallback

            session["history"].append(history_user)
            session["history"].append({"role": "model", "text": full_reply})
            session.modified = True

        return make_stream_response(stream_response)   # ✅

    except Exception as e:
        import traceback
        traceback.print_exc()
        # ✅ Bug 3 fixed — was calling generate() which doesn't exist here
        def error_stream():
            yield f"data: {json.dumps({'text': 'Server error. Please try again.', 'done': True})}\n\n"
        return make_stream_response(error_stream)      # ✅


if __name__ == "__main__":
    app.run(debug=True, threaded=True)

