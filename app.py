from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.secret_key = "ositv_secret_2026"

DATA_FILE  = "data.json"
ADMIN_PASS = "Eftal123"  # Bunu değiştir!

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "purchases": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

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
    data = load_data()
    return render_template("admin.html", logged_in=True, data=data)

@app.route("/admin/delete_user", methods=["POST"])
def delete_user():
    if not session.get("admin"):
        return jsonify({"error": "unauthorized"}), 401
    username = request.json.get("username")
    data = load_data()
    data["users"] = [u for u in data["users"] if u["name"] != username]
    save_data(data)
    return jsonify({"ok": True})

@app.route("/admin/rename_user", methods=["POST"])
def rename_user():
    if not session.get("admin"):
        return jsonify({"error": "unauthorized"}), 401
    old_name = request.json.get("old_name")
    new_name = request.json.get("new_name", "").strip()
    if not new_name:
        return jsonify({"error": "no name"}), 400
    data = load_data()
    for u in data["users"]:
        if u["name"] == old_name:
            u["name"] = new_name
    for p in data["purchases"]:
        if p["username"] == old_name:
            p["username"] = new_name
    save_data(data)
    return jsonify({"ok": True})

@app.route("/admin/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin")

@app.route("/api/register", methods=["POST"])
def register():
    data = load_data()
    body = request.json
    username = body.get("username", "").strip()
    if not username:
        return jsonify({"error": "no username"}), 400
    for u in data["users"]:
        if u["name"].lower() == username.lower():
            return jsonify({"exists": True})
    data["users"].append({
        "name": username,
        "joined": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data(data)
    return jsonify({"exists": False})

@app.route("/api/purchase", methods=["POST"])
def purchase():
    data = load_data()
    body = request.json
    data["purchases"].append({
        "username": body.get("username"),
        "item":     body.get("item"),
        "price":    body.get("price"),
        "time":     datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data(data)
    return jsonify({"ok": True})

@app.route("/api/stats")
def stats():
    data = load_data()
    return jsonify({
        "users":     data["users"],
        "purchases": data["purchases"],
        "total_users": len(data["users"]),
        "total_purchases": len(data["purchases"]),
        "total_spent": sum(p["price"] for p in data["purchases"] if p.get("price"))
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
