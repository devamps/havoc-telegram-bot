import os
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue, CallbackQueryHandler
from dotenv import load_dotenv
import uuid

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

def generate_unique_task_id(existing_tasks):
    while True:
        task_id = uuid.uuid4().hex[:8]
        if not any(t["id"] == task_id for t in existing_tasks):
            return task_id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = (
        "👋🧑🏻‍💻 Welcome to Havoc Bot!\n\n"
        "📝 Task Commands:\n\n"
        "/add <task> - Add a new task\n"
        "/list - Show all your tasks\n"
        "/done <task_number> - Mark task as done\n"
        "/remove <task_number> - Remove a task\n"
        "/edit <task_number> <new_task> - Edit a task\n"
        "/clear - Delete all your tasks\n\n"

        "⏰ Reminder Commands:\n\n"
        "/reminder <task_number> <HH:MM> <days_number> - Set daily reminder\n"
        "/listreminders - List all your reminders\n"
        "/removereminder <reminder_number> - Remove a reminder\n"
        "/clearreminders - Clear all your reminders\n\n"

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
    task_id = generate_unique_task_id(tasks_data[user_id]["tasks"])
    tasks_data[user_id]["tasks"].append({"id": task_id, "task": task_text, "done": False})

    save_tasks(tasks_data)
    await update.message.reply_text(f"✅🧑🏻‍💻 Task added: {task_text} (ID: {task_id})")

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks_data = load_tasks()

    if user_id not in tasks_data or "tasks" not in tasks_data[user_id] or not tasks_data[user_id]["tasks"]:
        await update.message.reply_text("📭🧑🏻‍💻 You have no tasks yet! Use /add to create one.")
        return

    tasks = tasks_data[user_id]["tasks"]
    message = "🕓🧑🏻‍💻 Your Tasks:\n\n"
    for idx, task in enumerate(tasks, 1):
        status = "✅" if task["done"] else "🕓"
        message += f"{idx}. {status} {task['task']}\n"

    # Add inline button
    keyboard = [[InlineKeyboardButton("🗑️ clear all tasks", callback_data="clear_all_tasks")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message, reply_markup=reply_markup)

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

    await update.message.reply_text(f"✅🧑🏻‍💻 Task {task_num + 1} marked as done!")

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
    task_id = removed_task["id"]

    # Remove associated reminders and cancel their jobs
    reminders_removed = 0
    if "reminders" in tasks_data[user_id]:
        # Find reminders to remove
        reminders_to_remove = [
            r for r in tasks_data[user_id]["reminders"]
            if r["task_id"] == task_id
        ]
        reminders_removed = len(reminders_to_remove)

        # Remove from list
        tasks_data[user_id]["reminders"] = [
            r for r in tasks_data[user_id]["reminders"]
            if r["task_id"] != task_id
        ]

        # Cancel scheduled jobs
        for rem in reminders_to_remove:
            job_name = f"{user_id}_{task_id}_{rem['time'].replace(':', '')}"
            for job in context.job_queue.jobs():
                if job.name == job_name:
                    job.schedule_removal()

    save_tasks(tasks_data)

    response = f"🗑️🧑🏻‍💻 Removed task: {removed_task['task']}"
    if reminders_removed > 0:
        response += f"\n(Also removed {reminders_removed} associated reminder(s))"

    await update.message.reply_text(response)

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

    await update.message.reply_text(f"✏️🧑🏻‍💻 Task {task_num + 1} updated:\n'{old_task}' ➝ '{new_task_text}'")

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

    # Also clear all reminders since all tasks are being removed
    reminders_count = len(tasks_data[user_id].get("reminders", []))
    if reminders_count > 0:
        # Cancel all scheduled jobs
        for rem in tasks_data[user_id]["reminders"]:
            job_name = f"{user_id}_{rem['task_id']}_{rem['time'].replace(':', '')}"
            for job in context.job_queue.jobs():
                if job.name == job_name:
                    job.schedule_removal()

        tasks_data[user_id]["reminders"] = []

    save_tasks(tasks_data)

    response = f"🗑️🧑🏻‍💻 Cleared {task_count} task(s)!"
    if reminders_count > 0:
        response += f"\n(Also cleared {reminders_count} reminder(s))"

    await update.message.reply_text(response)

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
        name=f"{user_id}_{task_id}_{time_str.replace(':', '')}"
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
            data={"user_id": user_id, "task_id": task_id, "task_text": task_text, "days_left": days_left - 1,
                  "time": time_str},
            name=job.name
        )

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks_data = load_tasks()

    if user_id not in tasks_data or not tasks_data[user_id].get("reminders"):
        await update.message.reply_text("📭🧑🏻‍💻 You have no reminders set!")
        return

    reminders = tasks_data[user_id]["reminders"]
    message = "⏰🧑🏻‍💻 Your reminders:\n\n"

    for idx, rem in enumerate(reminders, 1):
        task = next((t for t in tasks_data[user_id]["tasks"] if t["id"] == rem["task_id"]), None)
        task_text = task["task"] if task else "(deleted task)"
        message += f"{idx}. {task_text} at {rem['time']} ({rem['days_left']} day(s) left)\n"

    # Add inline button
    keyboard = [[InlineKeyboardButton("🗑️ clear all reminders", callback_data="clear_all_reminders")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message, reply_markup=reply_markup)

async def remove_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks_data = load_tasks()

    if user_id not in tasks_data or not tasks_data[user_id].get("reminders"):
        await update.message.reply_text("📭🧑🏻‍💻 You have no reminders to remove!")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌🧑🏻‍💻 Usage: /removereminder <reminder_number>")
        return

    rem_index = int(context.args[0]) - 1
    reminders = tasks_data[user_id]["reminders"]

    if rem_index < 0 or rem_index >= len(reminders):
        await update.message.reply_text("❌🧑🏻‍💻 Invalid reminder number!")
        return

    removed = reminders.pop(rem_index)
    save_tasks(tasks_data)

    # Cancel scheduled job
    job_name = f"{user_id}_{removed['task_id']}_{removed['time'].replace(':', '')}"
    for job in context.job_queue.jobs():
        if job.name == job_name:
            job.schedule_removal()

    task = next((t for t in tasks_data[user_id]["tasks"] if t["id"] == removed["task_id"]), None)
    task_text = task["task"] if task else "(deleted task)"

    await update.message.reply_text(f"🗑️🧑🏻‍💻 Removed reminder for '{task_text}' at {removed['time']}")

async def clear_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks_data = load_tasks()

    if user_id not in tasks_data or not tasks_data[user_id].get("reminders"):
        await update.message.reply_text("📭🧑🏻‍💻 You have no reminders to clear!")
        return

    # Cancel all scheduled jobs for this user
    for rem in tasks_data[user_id]["reminders"]:
        job_name = f"{user_id}_{rem['task_id']}_{rem['time'].replace(':', '')}"
        for job in context.job_queue.jobs():
            if job.name == job_name:
                job.schedule_removal()

    count = len(tasks_data[user_id]["reminders"])
    tasks_data[user_id]["reminders"] = []
    save_tasks(tasks_data)

    await update.message.reply_text(f"🗑️🧑🏻‍💻 Cleared {count} reminder(s)!")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    tasks_data = load_tasks()

    if query.data == "clear_all_tasks":
        if user_id not in tasks_data or "tasks" not in tasks_data[user_id] or not tasks_data[user_id]["tasks"]:
            await query.edit_message_text("📭🧑🏻‍💻 You have no tasks to clear!")
            return

        task_count = len(tasks_data[user_id]["tasks"])
        tasks_data[user_id]["tasks"] = []

        # Also clear all reminders since all tasks are being removed
        reminders_count = len(tasks_data[user_id].get("reminders", []))
        if reminders_count > 0:
            # Cancel all scheduled jobs
            for rem in tasks_data[user_id]["reminders"]:
                job_name = f"{user_id}_{rem['task_id']}_{rem['time'].replace(':', '')}"
                for job in context.job_queue.jobs():
                    if job.name == job_name:
                        job.schedule_removal()

            tasks_data[user_id]["reminders"] = []

        save_tasks(tasks_data)

        response = f"🗑️🧑🏻‍💻 Cleared {task_count} task(s)!"
        if reminders_count > 0:
            response += f"\n(Also cleared {reminders_count} reminder(s))"

        await query.edit_message_text(response)

    elif query.data == "clear_all_reminders":
        if user_id not in tasks_data or not tasks_data[user_id].get("reminders"):
            await query.edit_message_text("📭🧑🏻‍💻 You have no reminders to clear!")
            return

        # Cancel all scheduled jobs
        for rem in tasks_data[user_id]["reminders"]:
            job_name = f"{user_id}_{rem['task_id']}_{rem['time'].replace(':', '')}"
            for job in context.job_queue.jobs():
                if job.name == job_name:
                    job.schedule_removal()

        count = len(tasks_data[user_id]["reminders"])
        tasks_data[user_id]["reminders"] = []
        save_tasks(tasks_data)
        await query.edit_message_text(f"🗑️🧑🏻‍💻 Cleared {count} reminder(s)!")

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
    application.add_handler(CommandHandler("listreminders", list_reminders))
    application.add_handler(CommandHandler("removereminder", remove_reminder))
    application.add_handler(CommandHandler("clearreminders", clear_reminders))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Reschedule reminders before run_polling
    tasks_data = load_tasks()
    total_users = len(tasks_data)
    total_reminders = 0
    total_tasks = 0

    for user_id, data in tasks_data.items():
        total_tasks += len(data.get("tasks", []))
        for rem in data.get("reminders", []):
            task = next((t for t in data.get("tasks", []) if t["id"] == rem["task_id"]), None)
            if task:
                total_reminders += 1
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

    # Start bot with enhanced logging
    print(f"🧑🏻‍💻 Bot is running...")
    print(f"📊 Loaded: {total_users} user(s), {total_tasks} task(s), {total_reminders} reminder(s)")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()