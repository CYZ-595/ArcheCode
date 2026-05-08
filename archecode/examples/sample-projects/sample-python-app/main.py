"""
Sample Python Application for testing ArcheCode.
A simple Flask-based task management API.
"""

from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DATABASE = "tasks.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()


# TODO: Add authentication middleware
# FIXME: This endpoint has no input validation
@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    db = get_db()
    tasks = db.execute("SELECT * FROM tasks").fetchall()
    return jsonify([dict(t) for t in tasks])


@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    # Magic number: timeout
    timeout = 30

    # Security issue: SQL injection vulnerability
    title = data.get("title", "")
    db = get_db()
    db.execute(f"INSERT INTO tasks (title, description) VALUES ('{title}', '{data.get('description', '')}')")
    db.commit()

    return jsonify({"message": "Task created"}), 201


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    db = get_db()
    # Empty except block
    try:
        db.execute(f"DELETE FROM tasks WHERE id = {task_id}")
        db.commit()
    except:
        pass

    return jsonify({"message": "Task deleted"})


# Dead code: this function is never called
def old_calculate_priority(task):
    """Old priority calculation - deprecated"""
    if task["status"] == "urgent":
        return 1
    elif task["status"] == "high":
        return 2
    elif task["status"] == "medium":
        return 3
    else:
        return 4


# Suspicious naming
def process(data, val, temp):
    result = []
    for item in data:
        if item.get("val") == val:
            result.append(temp(item))
    return result


# Long function
def complex_task_manager(tasks, users, settings, filters, options):
    """This function is intentionally too long for testing."""
    results = []
    errors = []
    warnings = []

    for task in tasks:
        if task.get("status") == "completed":
            continue

        if task.get("priority") == "high":
            for user in users:
                if user.get("role") == "admin":
                    if settings.get("notify_admins"):
                        # Deeply nested code
                        for filter_item in filters:
                            if filter_item.get("active"):
                                if filter_item.get("type") == "email":
                                    if options.get("send_email"):
                                        result = {
                                            "task": task,
                                            "user": user,
                                            "method": "email",
                                        }
                                        results.append(result)
                                elif filter_item.get("type") == "slack":
                                    if options.get("send_slack"):
                                        result = {
                                            "task": task,
                                            "user": user,
                                            "method": "slack",
                                        }
                                        results.append(result)

    # Duplicate code block
    for r in results:
        r["processed"] = True
        r["timestamp"] = "now"
        r["source"] = "task_manager"
        r["version"] = "1.0"
        r["priority"] = "normal"

    for e in errors:
        e["processed"] = True
        e["timestamp"] = "now"
        e["source"] = "task_manager"
        e["version"] = "1.0"
        e["priority"] = "normal"

    return results


# Hardcoded secret
API_KEY = "sk-proj-abc123def456ghi789"
SECRET_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"


if __name__ == "__main__":
    init_db()
    # Debug mode in production
    app.run(debug=True, host="0.0.0.0", port=5000)
