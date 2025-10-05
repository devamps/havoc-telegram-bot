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
        "👋🧑🏻‍💻 Welcome to Havoc Bot!\n\n"
        "Available commands:\n\n"
        "/add <task> - Add a new task\n"
        "/list - Show all your tasks\n"
        "/done <task_number> - Mark task as done\n"
        "/remove <task_number> - Remove a task\n"
        "/edit <task_number> <new_task> - Edit a task\n"
        "/clear - Delete all your tasks\n"
        "/start - Show this message"
    )
    await update.message.reply_text(welcome_message)

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id) # use string keys for JSON
    tasks = load_tasks() # always load fresh

    # Get the task text from the command arguments
    if not context.args:
        await update.message.reply_text("❌🧑🏻‍💻 Please provide a task! Usage: /add <task>")
        return

    task_text = " ".join(context.args)

    # Initialize user's task list if it doesn't exist
    if user_id not in tasks:
        tasks[user_id] = []

    # Store as dict with status
    tasks[user_id].append({"task": task_text, "done": False})
    save_tasks(tasks)

    await update.message.reply_text(f"✅🧑🏻‍💻 Task added: {task_text}")

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks = load_tasks()  # always load fresh

    # Check if user has any tasks
    if user_id not in tasks or not tasks[user_id]:
        await update.message.reply_text("📭🧑🏻‍💻 You have no tasks yet! Use /add to create one.")
        return

    # Build the task list message
    message = "🧑🏻‍💻 Your Tasks:\n\n"
    for idx, task in enumerate(tasks[user_id], 1):
        status = "✅" if task["done"] else "⏳"
        message += f"{idx}. {status} {task['task']}\n"

    await update.message.reply_text(message)

async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks = load_tasks()

    # Check if user has any tasks
    if user_id not in tasks or not tasks[user_id]:
        await update.message.reply_text("📭🧑🏻‍💻 You have no tasks to mark as done!")
        return

    # Validate that a number was provided
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌🧑🏻‍💻 Usage: /done <task_number>")
        return

    task_num = int(context.args[0]) - 1

    # Check if number is within range
    if task_num < 0 or task_num >= len(tasks[user_id]):
        await update.message.reply_text("❌🧑🏻‍💻 Invalid task number!")
        return

    # Mark task as done
    tasks[user_id][task_num]["done"] = True
    save_tasks(tasks)

    await update.message.reply_text(f"✅🧑🏻‍💻 Task {task_num+1} marked as done!")

async def remove_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks = load_tasks()

    # Check if user has any tasks
    if user_id not in tasks or not tasks[user_id]:
        await update.message.reply_text("📭🧑🏻‍💻 You have no tasks to remove!")
        return

    # Validate that a number was provided
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌🧑🏻‍💻 Usage: /remove <task_number>")
        return

    task_num = int(context.args[0]) - 1

    # Check if number is within range
    if task_num < 0 or task_num >= len(tasks[user_id]):
        await update.message.reply_text("❌🧑🏻‍💻 Invalid task number!")
        return

    # Remove task from list
    removed = tasks[user_id].pop(task_num)
    save_tasks(tasks)

    await update.message.reply_text(f"🗑️🧑🏻‍💻 Removed task: {removed['task']}")

async def edit_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks = load_tasks()

    # Check if user has any tasks
    if user_id not in tasks or not tasks[user_id]:
        await update.message.reply_text("📭🧑🏻‍💻 You have no tasks to edit!")
        return

    # Validate that number + new text were provided
    if len(context.args) < 2 or not context.args[0].isdigit():
        await update.message.reply_text("❌🧑🏻‍💻 Usage: /edit <task_number> <new_task>")
        return

    task_num = int(context.args[0]) - 1
    new_task_text = " ".join(context.args[1:])

    # Check if number is within range
    if task_num < 0 or task_num >= len(tasks[user_id]):
        await update.message.reply_text("❌🧑🏻‍💻 Invalid task number!")
        return

    # Replace old text with new one
    old_task = tasks[user_id][task_num]["task"]
    tasks[user_id][task_num]["task"] = new_task_text
    save_tasks(tasks)

    await update.message.reply_text(f"✏️🧑🏻‍💻 Task {task_num+1} updated:\n'{old_task}' ➝ '{new_task_text}'")

async def clear_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    tasks = load_tasks()

    # Check if user has any tasks
    if user_id not in tasks or not tasks[user_id]:
        await update.message.reply_text("📭🧑🏻‍💻 You have no tasks to clear!")
        return

    # Clear the tasks
    task_count = len(tasks[user_id])
    tasks[user_id] = []
    save_tasks(tasks)

    await update.message.reply_text(f"🗑️🧑🏻‍💻 Cleared {task_count} task(s)!")

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
    application.add_handler(CommandHandler("done", done_task))
    application.add_handler(CommandHandler("remove", remove_task))
    application.add_handler(CommandHandler("edit", edit_task))
    application.add_handler(CommandHandler("clear", clear_tasks))

    # Start bot
    print("🧑🏻‍💻 Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
