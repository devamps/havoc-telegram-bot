# **Havoc** - Telegram Bot 🤖 [![Telegram](https://img.shields.io/badge/Telegram-HavocHelperBot-blue?logo=telegram)](https://t.me/HavocHelperBot)

> “If you haven’t got **Havoc** in your everyday life, you’re not busy enough —  
> and if you have, you’re doing something **right**.”

Havoc is a Telegram bot designed to keep your daily chaos _organized_ — managing your tasks and reminders _effortlessly_.

It’s _fully deployed_ and running on Railway, powered by a simple SQLite database for _persistence_.

## ✨ Features
- 📝 **Task Management** — Add, edit, and track your daily tasks
- ⏰ **Smart Reminders** — Set recurring daily reminders with custom schedules
- 🔒 **Private & Persistent** — Your data stays yours, stored securely in SQLite
- ☁️ **Always Online** — Deployed on Railway for 24/7 availability

## 📖 Quick Start

**Add a task:**
```
/add Finish project documentation
```

**Set a reminder for task #1 at 9 AM for 7 days:**
```
/reminder 1 09:00 7
```

## 📋 Command List

### 📝 Task Commands

- `/add <task>` — Add a new task 
- `/list` — Show all your tasks  
- `/done <task_number>` — Mark a task as done  
- `/remove <task_number>` — Remove a task  
- `/edit <task_number> <new_task>` — Edit a selected task  
- `/clear` — Delete all your tasks  

### ⏰ Reminder Commands

- `/reminder <task_number> <HH:MM> <days_number>` — Set a daily reminder at specific time for chosen amount of days  
- `/listreminders` — List all your reminders  
- `/removereminder <reminder_number>` — Remove a reminder  
- `/clearreminders` — Clear all your reminders  

### 💬 General
- `/start` — Show this message

## 🛠️ Tech Stack
| Tool | Purpose |
|------|----------|
| **Python 3.11+** | Core language |
| **python-telegram-bot** | Telegram Bot API integration |
| **SQLite3** | Local database for storing tasks and reminders |
| **Railway** | Cloud hosting and deployment |
| **dotenv** | Secure environment variable management |

## 📁 Project Structure
```
havoc-telegram-bot/
├─ bot.py               # Main Telegram bot logic and command handling
├─ db.py                # Database operations for tasks and reminders
├─ requirements.txt     # Python dependencies
├─ Procfile             # Defines startup command for Railway deployment
├─ .env.example         # Example environment variable file
├─ .gitignore           # Git ignore rules
└─ README.md            # Project documentation
```
## 🚀 Deployment
Havoc runs on [Railway](https://railway.app) with automatic deploys from the main branch.

## 📄 License
Licensed under the `MIT` License.
