from flask_login import UserMixin
from core.database import get_connection

class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email


def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM auth_users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    return row


def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM auth_users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return User(row[0], row[1])
    return None
