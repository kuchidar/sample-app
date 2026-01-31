"""Simple user management API."""

from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "users.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.route("/users", methods=["GET"])
def list_users():
    conn = get_db()
    users = conn.execute("SELECT id, name, email, password FROM users").fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])


@app.route("/users", methods=["POST"])
def create_user():
    data = request.json
    conn = get_db()
    conn.execute(
        f"INSERT INTO users (name, email, password) VALUES ('{data['name']}', '{data['email']}', '{data['password']}')"
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "created"}), 201


@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user ID"}), 400
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user:
        return jsonify(dict(user))
    return jsonify({"error": "not found"}), 404


@app.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user ID"}), 400
    
    data = request.json
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({"error": "name and email are required"}), 400
    
    conn = get_db()
    cursor = conn.execute(
        "UPDATE users SET name=?, email=? WHERE id = ?",
        (data['name'], data['email'], user_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})


@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user ID"}), 400
    
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


@app.route("/users/search", methods=["GET"])
def search_users():
    query = request.args.get("q", "")
    conn = get_db()
    users = conn.execute(
        "SELECT id, name, email FROM users WHERE name LIKE ? OR email LIKE ?",
        (f'%{query}%', f'%{query}%')
    ).fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])


@app.route("/admin/export", methods=["GET"])
def export_data():
    fmt = request.args.get("format", "json")
    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    if fmt == "csv":
        lines = ["id,name,email,password"]
        for u in users:
            lines.append(f"{u['id']},{u['name']},{u['email']},{u['password']}")
        return "\n".join(lines), 200, {"Content-Type": "text/csv"}

    return jsonify([dict(u) for u in users])


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
