import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

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
        "👋 Welcome to Havoc Bot!\n\n"
        "Available commands 🧑🏻‍💻:\n\n"
        "/add <task> - Add a new task\n"
        "/list - Show all your tasks\n"
        "/clear - Delete all your tasks\n"
        "/start - Show this message"
    )
    await update.message.reply_text(welcome_message)

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)  # use string keys for JSON
    tasks = load_tasks()  # always load fresh

    # Get the task text from the command arguments
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a task! 🧑🏻‍💻\n"
            "Usage: /add <task description>"
        )
        return

    task = " ".join(context.args)

    # Initialize user's task list if it doesn't exist
    if user_id not in tasks:
        tasks[user_id] = []

    tasks[user_id].append(task)
    save_tasks(tasks)

    await update.message.reply_text(
        f"✅ Task added! 🧑🏻‍💻\n\n"
        f"📝 {task}\n\n"
        f"Total tasks: {len(tasks[user_id])}"
    )

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks = load_tasks()  # always load fresh

    # Check if user has any tasks
    if user_id not in tasks or not tasks[user_id]:
        await update.message.reply_text(
            "📭 You have no tasks yet! 🧑🏻‍💻\nUse /add to create one."
        )
        return

    # Build the task list message
    message = "🧑🏻‍💻 Your Tasks:\n\n"
    for idx, task in enumerate(tasks[user_id], 1):
        message += f"{idx}. {task}\n"

    message += f"\nTotal: {len(tasks[user_id])} task(s)"
    await update.message.reply_text(message)

async def clear_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks = load_tasks()  # always load fresh

    # Check if user has any tasks
    if user_id not in tasks or not tasks[user_id]:
        await update.message.reply_text("📭 You have no tasks to clear!")
        return

    # Clear the tasks
    task_count = len(tasks[user_id])
    tasks[user_id] = []
    save_tasks(tasks)

    await update.message.reply_text(
        f"🗑️ Cleared {task_count} task(s)!\n"
        f"Your task list is now empty. 🧑🏻‍💻"
    )

def main() -> None:
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("No TELEGRAM_TOKEN found in .env file!")

    # Create the Application
    application = Application.builder().token(token).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_task))
    application.add_handler(CommandHandler("list", list_tasks))
    application.add_handler(CommandHandler("clear", clear_tasks))

    # Start bot
    print("🧑🏻‍💻 Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
