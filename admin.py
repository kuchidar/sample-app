"""Admin panel for user management."""

import os
import subprocess
from flask import Flask, request, jsonify, redirect
import sqlite3
import pickle
import base64

app = Flask(__name__)

ADMIN_PASSWORD = "admin123"
DB_PATH = "users.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/admin/login", methods=["POST"])
def admin_login():
    password = request.form.get("password", "")
    if password == ADMIN_PASSWORD:
        return jsonify({"status": "ok", "token": base64.b64encode(password.encode()).decode()})
    return jsonify({"error": "invalid password"}), 401


@app.route("/admin/users", methods=["GET"])
def admin_list_users():
    page = request.args.get("page", "1")
    per_page = 50
    offset = (int(page) - 1) * per_page
    conn = get_db()
    users = conn.execute(
        f"SELECT * FROM users LIMIT {per_page} OFFSET {offset}"
    ).fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])


@app.route("/admin/users/bulk-delete", methods=["POST"])
def bulk_delete():
    user_ids = request.json.get("ids", [])
    conn = get_db()
    ids_str = ",".join(str(i) for i in user_ids)
    conn.execute(f"DELETE FROM users WHERE id IN ({ids_str})")
    conn.commit()
    conn.close()
    return jsonify({"deleted": len(user_ids)})


@app.route("/admin/backup", methods=["POST"])
def backup_db():
    backup_name = request.json.get("name", "backup")
    os.system(f"cp {DB_PATH} /tmp/{backup_name}.db")
    return jsonify({"status": "backed up", "path": f"/tmp/{backup_name}.db"})


@app.route("/admin/restore", methods=["POST"])
def restore_session():
    data = request.json.get("session_data", "")
    session = pickle.loads(base64.b64decode(data))
    return jsonify({"restored": True, "user": session.get("user")})


@app.route("/admin/logs", methods=["GET"])
def view_logs():
    log_file = request.args.get("file", "app.log")
    result = subprocess.run(f"cat {log_file}", shell=True, capture_output=True, text=True)
    return jsonify({"logs": result.stdout})


@app.route("/admin/redirect", methods=["GET"])
def admin_redirect():
    url = request.args.get("url", "/")
    return redirect(url)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
