from flask import Flask, request, jsonify, render_template, session, redirect
from flask_cors import CORS
import os
import psycopg2
import psycopg2.extras
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.secret_key = "ositv_secret_2026"
ADMIN_PASS = "ositv2026"

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            joined TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            item TEXT NOT NULL,
            price BIGINT,
            time TEXT NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")
        return render_template("admin.html", error="Şifre yanlış!", logged_in=False)
    if not session.get("admin"):
        return render_template("admin.html", error=None, logged_in=False)
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users ORDER BY id DESC")
    users = cur.fetchall()
    cur.execute("SELECT * FROM purchases ORDER BY id DESC")
    purchases = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("admin.html", logged_in=True, data={"users": users, "purchases": purchases})

@app.route("/admin/delete_user", methods=["POST"])
def delete_user():
    if not session.get("admin"):
        return jsonify({"error": "unauthorized"}), 401
    username = request.json.get("username")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE name = %s", (username,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/admin/rename_user", methods=["POST"])
def rename_user():
    if not session.get("admin"):
        return jsonify({"error": "unauthorized"}), 401
    old_name = request.json.get("old_name")
    new_name = request.json.get("new_name", "").strip()
    if not new_name:
        return jsonify({"error": "no name"}), 400
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET name = %s WHERE name = %s", (new_name, old_name))
    cur.execute("UPDATE purchases SET username = %s WHERE username = %s", (new_name, old_name))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/admin/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin")

@app.route("/api/register", methods=["POST"])
def register():
    body = request.json
    username = body.get("username", "").strip()
    if not username:
        return jsonify({"error": "no username"}), 400
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE LOWER(name) = LOWER(%s)", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"exists": True})
    cur.execute("INSERT INTO users (name, joined) VALUES (%s, %s)",
                (username, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"exists": False})

@app.route("/api/purchase", methods=["POST"])
def purchase():
    body = request.json
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO purchases (username, item, price, time) VALUES (%s, %s, %s, %s)",
                (body.get("username"), body.get("item"), body.get("price"),
                 datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/stats")
def stats():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users ORDER BY id DESC")
    users = [dict(u) for u in cur.fetchall()]
    cur.execute("SELECT * FROM purchases ORDER BY id DESC")
    purchases = [dict(p) for p in cur.fetchall()]
    cur.close()
    conn.close()
    total_spent = sum(p["price"] for p in purchases if p.get("price"))
    return jsonify({
        "users": users,
        "purchases": purchases,
        "total_users": len(users),
        "total_purchases": len(purchases),
        "total_spent": total_spent
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
