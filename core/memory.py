# from database import get_connection
from core.database import get_connection
from datetime import datetime
import json

def save_user(uid, profile):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE uid = ?", (uid,))
    user = cursor.fetchone()

    if user:
        # Update existing user
        cursor.execute("""
            UPDATE users
            SET income = ?, credit = ?, purpose = ?, visits = visits + 1, last_seen = ?
            WHERE uid = ?
        """, (
            profile.get("income"),
            profile.get("credit"),
            profile.get("purpose"),
            now,
            uid
        ))
    else:
        # Insert new user
        cursor.execute("""
            INSERT INTO users (uid, income, credit, purpose, visits, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            uid,
            profile.get("income"),
            profile.get("credit"),
            profile.get("purpose"),
            1,
            now,
            now
        ))
        cursor.execute("""
        INSERT INTO user_history (user_id, income, credit, eligibility, purpose, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            uid,  # using uid for now (we can later map to auth id)
            profile.get("income"),
            profile.get("credit"),
            profile.get("eligibility"),
            profile.get("purpose"),
            now
        ))

    conn.commit()
    conn.close()


def get_user(uid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE uid = ?", (uid,))
    user = cursor.fetchone()

    conn.close()

    if not user:
        return None

    return {
        "uid": user[0],
        "income": user[1],
        "credit": user[2],
        "purpose": user[3],
        "visits": user[4],
        "first_seen": user[5],
        "last_seen": user[6]
    }

def get_profile_delta(uid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT income, credit, eligibility
        FROM user_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 2
    """, (uid,))

    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 2:
        return None

    current = rows[0]
    previous = rows[1]

    income_delta = current[0] - previous[0]
    credit_delta = current[1] - previous[1]

    return {
        "income_delta": income_delta,
        "credit_delta": credit_delta,
        "previous_income": previous[0],
        "previous_credit": previous[1],
        "previous_eligibility": previous[2]
    }


# def get_profile_delta(uid: str) -> dict | None:
#     user = get_user(uid)
#     if not user:
#         return None

#     current  = user.get("last_profile")
#     previous = user.get("previous_profile")

#     if not current or not previous:
#         return None

#     credit_delta = round(
#         float(current.get("credit", 0)) -
#         float(previous.get("credit", 0)), 0
#     )
#     income_delta = round(
#         float(current.get("income", 0)) -
#         float(previous.get("income", 0)), 0
#     )

#     return {
#         "credit_delta": credit_delta,
#         "income_delta": income_delta,
#         "previous_credit": previous.get("credit"),
#         "previous_income": previous.get("income"),
#         "previous_eligibility": previous.get("eligibility"),
#         "visits": user.get("visits", 1)
#     }













# import json
# import os
# from datetime import datetime

# MEMORY_FILE = "data/users.json"


# def _load_all() -> dict:
#     if not os.path.exists(MEMORY_FILE):
#         return {}
#     with open(MEMORY_FILE, "r") as f:
#         return json.load(f)


# def _save_all(data: dict):
#     os.makedirs("data", exist_ok=True)
#     with open(MEMORY_FILE, "w") as f:
#         json.dump(data, f, indent=2)


# def save_user(uid: str, profile: dict):
#     """
#     Save or update user profile.
#     Keeps last_profile and previous_profile for comparison.
#     """
#     all_users = _load_all()

#     if uid not in all_users:
#         all_users[uid] = {
#             "visits":           0,
#             "first_seen":       datetime.now().isoformat(),
#             "last_profile":     None,
#             "previous_profile": None,
#             "last_seen":        None
#         }

#     user = all_users[uid]

#     # Shift current → previous before saving new
#     if user["last_profile"]:
#         user["previous_profile"] = user["last_profile"]

#     user["last_profile"] = {
#         **profile,
#         "saved_at": datetime.now().isoformat()
#     }
#     user["visits"]   += 1
#     user["last_seen"] = datetime.now().isoformat()

#     all_users[uid] = user
#     _save_all(all_users)


# def get_user(uid: str) -> dict | None:
#     """Returns full user memory object or None if not found."""
#     return _load_all().get(uid)


# def get_profile_delta(uid: str) -> dict | None:
#     """
#     Compares current vs previous profile.
#     Returns changes in income and credit score.
#     """
#     user = get_user(uid)
#     if not user:
#         return None

#     current  = user.get("last_profile")
#     previous = user.get("previous_profile")

#     if not current or not previous:
#         return None

#     credit_delta = round(
#         float(current.get("credit", 0)) -
#         float(previous.get("credit", 0)), 0
#     )
#     income_delta = round(
#         float(current.get("income", 0)) -
#         float(previous.get("income", 0)), 0
#     )

#     return {
#         "credit_delta":       credit_delta,
#         "income_delta":       income_delta,
#         "previous_credit":    previous.get("credit"),
#         "previous_income":    previous.get("income"),
#         "previous_eligibility": previous.get("eligibility"),
#         "visits":             user.get("visits", 1)
#     }