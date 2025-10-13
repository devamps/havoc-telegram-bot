import sqlite3
from datetime import datetime

DB_FILE = "tasks.db"

def init_db(): # Create tables if they don't exist
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        task TEXT NOT NULL,
        done INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        time TEXT NOT NULL,
        days_left INTEGER NOT NULL,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
    )''')

    conn.commit()
    conn.close()


def get_user_tasks(user_id): # Get all tasks for a user
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("SELECT id, task, done FROM tasks WHERE user_id = ? ORDER BY created_at", (user_id,))
    tasks = [{"id": row[0], "task": row[1], "done": bool(row[2])} for row in c.fetchall()]
    conn.close()
    return tasks

def add_task(user_id, task_id, task_text): # Add a new task
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("INSERT INTO tasks (id, user_id, task) VALUES (?, ?, ?)", (task_id, user_id, task_text))
    conn.commit()
    conn.close()

def update_task_status(user_id, task_id, done=True): # Mark task as done/undone
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("UPDATE tasks SET done = ? WHERE user_id = ? AND id = ?", (int(done), user_id, task_id))
    conn.commit()
    conn.close()

def update_task_text(user_id, task_id, new_text): # Update task text
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("UPDATE tasks SET task = ? WHERE user_id = ? AND id = ?", (new_text, user_id, task_id))
    conn.commit()
    conn.close()

def delete_task(user_id, task_id): # Delete a task (cascades to reminders)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE user_id = ? AND id = ?", (user_id, task_id))
    conn.commit()
    conn.close()

def clear_all_tasks(user_id): # Delete all tasks for a user
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_user_reminders(user_id): # Get all reminders for a user
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("SELECT task_id, time, days_left FROM reminders WHERE user_id = ?", (user_id,))
    reminders = [{"task_id": row[0], "time": row[1], "days_left": row[2]} for row in c.fetchall()]
    conn.close()
    return reminders

def add_reminder(user_id, task_id, time_str, days): # Add a reminder
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("INSERT INTO reminders (user_id, task_id, time, days_left) VALUES (?, ?, ?, ?)",
              (user_id, task_id, time_str, days))
    conn.commit()
    conn.close()

def update_reminder_days(user_id, task_id, time_str, new_days): # Update reminder days left"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("UPDATE reminders SET days_left = ? WHERE user_id = ? AND task_id = ? AND time = ?",
              (new_days, user_id, task_id, time_str))
    conn.commit()
    conn.close()

def delete_reminder(user_id, task_id, time_str): # Delete a specific reminder
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE user_id = ? AND task_id = ? AND time = ?",
              (user_id, task_id, time_str))
    conn.commit()
    conn.close()

def clear_all_reminders(user_id): # Delete all reminders for a user
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_all_reminders(): # Get all reminders (for rescheduling on startup)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("""SELECT r.user_id, r.task_id, r.time, r.days_left, t.task 
                 FROM reminders r 
                 JOIN tasks t ON r.task_id = t.id""")
    reminders = [{"user_id": row[0], "task_id": row[1], "time": row[2],
                  "days_left": row[3], "task_text": row[4]} for row in c.fetchall()]
    conn.close()
    return reminders

def get_stats(): # stats for startup logging
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("SELECT COUNT(DISTINCT user_id) FROM tasks")
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks")
    tasks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM reminders")
    reminders = c.fetchone()[0]
    conn.close()
    return users, tasks, reminders