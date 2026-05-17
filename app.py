from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = "data.json"

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
