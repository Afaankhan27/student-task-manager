from pathlib import Path
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-development-key-change-before-deploy")
DATABASE = Path(os.environ.get("DATABASE_PATH", Path(__file__).with_name("tasks.db")))

@app.context_processor
def inject_today():
    return {'today_label': date.today().strftime('%d %B %Y')}

CATEGORIES = ["Study", "Personal", "Research", "Coding", "Other"]

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def initialize_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Other',
                due_date TEXT,
                is_done INTEGER NOT NULL DEFAULT 0,
                is_deleted INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

# Gunicorn imports this module without running the __main__ block.
initialize_database()

@app.route("/", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "Other")
        due_date = request.form.get("due_date", "").strip() or None

        if not title or len(title) > 120:
            flash("Please enter a task title (1–120 characters).", "error")
        elif category not in CATEGORIES:
            flash("Please choose a valid category.", "error")
        else:
            with get_db() as db:
                db.execute(
                    "INSERT INTO tasks (title, category, due_date) VALUES (?, ?, ?)",
                    (title, category, due_date)
                )
            flash("Task added successfully!", "success")
        return redirect(url_for("dashboard"))

    with get_db() as db:
        total = db.execute("SELECT COUNT(*) FROM tasks WHERE is_deleted=0").fetchone()[0]
        completed = db.execute("SELECT COUNT(*) FROM tasks WHERE is_done=1 AND is_deleted=0").fetchone()[0]
        pending = total - completed
        deleted = db.execute("SELECT COUNT(*) FROM tasks WHERE is_deleted=1").fetchone()[0]
        tasks = db.execute(
            "SELECT * FROM tasks WHERE is_deleted=0 ORDER BY is_done ASC, "
            "CASE WHEN due_date IS NULL OR due_date='' THEN 1 ELSE 0 END, due_date, id DESC"
        ).fetchall()
    return render_template("index.html", tasks=tasks, categories=CATEGORIES,
                           total=total, completed=completed, pending=pending, deleted=deleted,
                           active_page="dashboard")

@app.post("/task/<int:task_id>/toggle")
def toggle_task(task_id):
    with get_db() as db:
        db.execute("""
            UPDATE tasks SET is_done = CASE WHEN is_done=1 THEN 0 ELSE 1 END
            WHERE id=? AND is_deleted=0
        """, (task_id,))
    flash("Task status updated.", "success")
    return redirect(request.referrer or url_for("dashboard"))

@app.post("/task/<int:task_id>/delete")
def delete_task(task_id):
    with get_db() as db:
        db.execute("UPDATE tasks SET is_deleted=1 WHERE id=?", (task_id,))
    flash("Task moved to Deleted Tasks.", "success")
    return redirect(request.referrer or url_for("dashboard"))

@app.route("/completed")
def completed_tasks():
    with get_db() as db:
        tasks = db.execute(
            "SELECT * FROM tasks WHERE is_done=1 AND is_deleted=0 ORDER BY id DESC"
        ).fetchall()
    return render_template("tasks.html", tasks=tasks, page_title="Completed Tasks",
                           subtitle="Great work! Keep building your progress.",
                           active_page="completed", empty_message="No completed tasks yet.")

@app.route("/deleted")
def deleted_tasks():
    with get_db() as db:
        tasks = db.execute(
            "SELECT * FROM tasks WHERE is_deleted=1 ORDER BY id DESC"
        ).fetchall()
    return render_template("tasks.html", tasks=tasks, page_title="Deleted Tasks",
                           subtitle="Tasks you have moved to the deleted list.",
                           active_page="deleted", empty_message="Your deleted list is empty.")

@app.post("/task/<int:task_id>/restore")
def restore_task(task_id):
    with get_db() as db:
        db.execute("UPDATE tasks SET is_deleted=0 WHERE id=?", (task_id,))
    flash("Task restored.", "success")
    return redirect(url_for("deleted_tasks"))

@app.post("/task/<int:task_id>/permanent-delete")
def permanent_delete(task_id):
    with get_db() as db:
        db.execute("DELETE FROM tasks WHERE id=? AND is_deleted=1", (task_id,))
    flash("Task permanently deleted.", "success")
    return redirect(url_for("deleted_tasks"))

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
