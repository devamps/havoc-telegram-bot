import os
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue
from dotenv import load_dotenv
import random

load_dotenv()

TASKS_FILE = "tasks.json"

def load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = (
        "👋🧑🏻‍💻 Welcome to Havoc Bot!\n\n"
        "Available commands:\n\n"
        "/add <task> - Add a new task\n"
        "/list - Show all your tasks\n"
        "/done <task_number> - Mark task as done\n"
        "/remove <task_number> - Remove a task\n"
        "/edit <task_number> <new_task> - Edit a task\n"
        "/reminder <task_number> <HH:MM> <days> - Set daily reminder\n"
        "/clear - Delete all your tasks\n"
        "/start - Show this message"
    )
    await update.message.reply_text(welcome_message)

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks_data = load_tasks()

    if not context.args:
        await update.message.reply_text("❌🧑🏻‍💻 Please provide a task! Usage: /add <task>")
        return

    task_text = " ".join(context.args)

    if user_id not in tasks_data:
        tasks_data[user_id] = {"tasks": [], "reminders": []}

    # Generate unique task ID
    task_id = random.randint(100000, 999999)
    tasks_data[user_id]["tasks"].append({"id": task_id, "task": task_text, "done": False})

    save_tasks(tasks_data)
    await update.message.reply_text(f"✅🧑🏻‍💻 Task added: {task_text} (ID: {task_id})")



async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks_data = load_tasks()  # always load fresh

    # Check if user has any tasks
    if user_id not in tasks_data or "tasks" not in tasks_data[user_id] or not tasks_data[user_id]["tasks"]:
        await update.message.reply_text("📭🧑🏻‍💻 You have no tasks yet! Use /add to create one.")
        return

    tasks = tasks_data[user_id]["tasks"]

    # Build the task list message
    message = "🧑🏻‍💻 Your Tasks:\n\n"
    for idx, task in enumerate(tasks, 1):
        status = "✅" if task["done"] else "⏳"
        message += f"{idx}. {status} {task['task']}\n"

    await update.message.reply_text(message)

async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks_data = load_tasks()  # load fresh

    # Check if user exists and has any tasks
    if user_id not in tasks_data or "tasks" not in tasks_data[user_id] or not tasks_data[user_id]["tasks"]:
        await update.message.reply_text("📭🧑🏻‍💻 You have no tasks to mark as done!")
        return

    # Validate that a task number was provided
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌🧑🏻‍💻 Usage: /done <task_number>")
        return

    task_num = int(context.args[0]) - 1
    tasks_list = tasks_data[user_id]["tasks"]

    # Check if number is within range
    if task_num < 0 or task_num >= len(tasks_list):
        await update.message.reply_text("❌🧑🏻‍💻 Invalid task number!")
        return

    # Mark task as done
    tasks_list[task_num]["done"] = True
    save_tasks(tasks_data)

    await update.message.reply_text(f"✅🧑🏻‍💻 Task {task_num+1} marked as done!")

async def remove_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks_data = load_tasks()  # load fresh

    # Check if user exists and has any tasks
    if user_id not in tasks_data or "tasks" not in tasks_data[user_id] or not tasks_data[user_id]["tasks"]:
        await update.message.reply_text("📭🧑🏻‍💻 You have no tasks to remove!")
        return

    # Validate that a task number was provided
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌🧑🏻‍💻 Usage: /remove <task_number>")
        return

    task_num = int(context.args[0]) - 1
    tasks_list = tasks_data[user_id]["tasks"]

    # Check if number is within range
    if task_num < 0 or task_num >= len(tasks_list):
        await update.message.reply_text("❌🧑🏻‍💻 Invalid task number!")
        return

    # Remove the task
    removed_task = tasks_list.pop(task_num)
    save_tasks(tasks_data)

    await update.message.reply_text(f"🗑️🧑🏻‍💻 Removed task: {removed_task['task']}")

async def edit_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks_data = load_tasks()  # load fresh

    # Check if user exists and has any tasks
    if user_id not in tasks_data or "tasks" not in tasks_data[user_id] or not tasks_data[user_id]["tasks"]:
        await update.message.reply_text("📭🧑🏻‍💻 You have no tasks to edit!")
        return

    # Validate that task number + new text were provided
    if len(context.args) < 2 or not context.args[0].isdigit():
        await update.message.reply_text("❌🧑🏻‍💻 Usage: /edit <task_number> <new_task>")
        return

    task_num = int(context.args[0]) - 1
    new_task_text = " ".join(context.args[1:])
    tasks_list = tasks_data[user_id]["tasks"]

    # Check if number is within range
    if task_num < 0 or task_num >= len(tasks_list):
        await update.message.reply_text("❌🧑🏻‍💻 Invalid task number!")
        return

    # Replace old text with new one
    old_task = tasks_list[task_num]["task"]
    tasks_list[task_num]["task"] = new_task_text
    save_tasks(tasks_data)

    await update.message.reply_text(f"✏️🧑🏻‍💻 Task {task_num+1} updated:\n'{old_task}' ➝ '{new_task_text}'")

async def clear_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks_data = load_tasks()  # load fresh

    # Check if user exists and has any tasks
    if user_id not in tasks_data or "tasks" not in tasks_data[user_id] or not tasks_data[user_id]["tasks"]:
        await update.message.reply_text("📭🧑🏻‍💻 You have no tasks to clear!")
        return

    # Clear the tasks
    task_count = len(tasks_data[user_id]["tasks"])
    tasks_data[user_id]["tasks"] = []
    save_tasks(tasks_data)

    await update.message.reply_text(f"🗑️🧑🏻‍💻 Cleared {task_count} task(s)!")

from datetime import datetime, timedelta

async def reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks_data = load_tasks()

    if user_id not in tasks_data or not tasks_data[user_id]["tasks"]:
        await update.message.reply_text("📭🧑🏻‍💻 You have no tasks!")
        return

    if len(context.args) != 3 or not context.args[0].isdigit() or not context.args[2].isdigit():
        await update.message.reply_text("❌🧑🏻‍💻 Usage: /reminder <task_number> <HH:MM> <days>")
        return

    task_index = int(context.args[0]) - 1
    time_str = context.args[1]
    days = int(context.args[2])

    tasks = tasks_data[user_id]["tasks"]
    if task_index < 0 or task_index >= len(tasks):
        await update.message.reply_text("❌🧑🏻‍💻 Invalid task number!")
        return

    task = tasks[task_index]
    task_id = task["id"]

    try:
        reminder_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        await update.message.reply_text("❌🧑🏻‍💻 Invalid time format! Use HH:MM")
        return

    # Save reminder in JSON
    tasks_data[user_id]["reminders"].append({
        "task_id": task_id,
        "time": time_str,
        "days_left": days
    })
    save_tasks(tasks_data)

    # Schedule first reminder
    now = datetime.now()
    target = datetime.combine(now.date(), reminder_time)
    if target < now:
        target += timedelta(days=1)
    delay = (target - now).total_seconds()

    context.job_queue.run_once(
        send_reminder,
        when=delay,
        data={"user_id": user_id, "task_id": task_id, "task_text": task["task"], "days_left": days, "time": time_str},
        name=f"{user_id}_{task_id}_{time_str.replace(':','')}"
    )

    await update.message.reply_text(
        f"⏰🧑🏻‍💻 Reminder set for task '{task['task']}' at {time_str} for {days} day(s)!"
    )

async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    data = job.data
    user_id = data["user_id"]
    task_id = data["task_id"]
    task_text = data["task_text"]
    days_left = data["days_left"]
    time_str = data["time"]

    # Send the reminder
    await context.bot.send_message(
        chat_id=user_id,
        text=f"⏰🧑🏻‍💻 Reminder: {task_text}\n({days_left} day(s) remaining)!"
    )

    # Update JSON
    tasks_data = load_tasks()
    reminders = tasks_data.get(user_id, {}).get("reminders", [])
    for rem in reminders:
        if rem["task_id"] == task_id and rem["time"] == time_str:
            rem["days_left"] -= 1
            if rem["days_left"] <= 0:
                reminders.remove(rem)
            break
    save_tasks(tasks_data)

    # Schedule next reminder if needed
    if days_left > 1:
        next_time = datetime.now() + timedelta(days=1)
        reminder_dt = datetime.combine(next_time.date(), datetime.strptime(time_str, "%H:%M").time())
        delay = (reminder_dt - datetime.now()).total_seconds()
        context.job_queue.run_once(
            send_reminder,
            when=delay,
            data={"user_id": user_id, "task_id": task_id, "task_text": task_text, "days_left": days_left - 1, "time": time_str},
            name=job.name
        )

def main() -> None:
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("No TELEGRAM_TOKEN found in .env file!")

    # Create the Application
    application = Application.builder().token(token).build()
    job_queue = application.job_queue

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_task))
    application.add_handler(CommandHandler("list", list_tasks))
    application.add_handler(CommandHandler("done", done_task))
    application.add_handler(CommandHandler("remove", remove_task))
    application.add_handler(CommandHandler("edit", edit_task))
    application.add_handler(CommandHandler("clear", clear_tasks))
    application.add_handler(CommandHandler("reminder", reminder))

    # Reschedule reminders before run_polling
    tasks_data = load_tasks()
    for user_id, data in tasks_data.items():
        for rem in data.get("reminders", []):
            task = next((t for t in data.get("tasks", []) if t["id"] == rem["task_id"]), None)
            if task:
                now = datetime.now()
                rem_time = datetime.strptime(rem["time"], "%H:%M").time()
                target = datetime.combine(now.date(), rem_time)
                if target < now:
                    target += timedelta(days=1)
                delay = (target - now).total_seconds()
                application.job_queue.run_once(
                    send_reminder,
                    when=delay,
                    data={
                        "user_id": user_id,
                        "task_id": task["id"],
                        "task_text": task["task"],
                        "days_left": rem["days_left"],
                        "time": rem["time"]
                    },
                    name=f"{user_id}_{task['id']}_{rem['time'].replace(':', '')}"
                )

    # Start bot
    print("🧑🏻‍💻 Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()