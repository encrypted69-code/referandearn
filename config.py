import os

MONGO_URI = os.getenv "mongodb+srv://encryptedyt077_db_user:4iG7om8ELQJmzvGm@earnify.spbk6jd.mongodb.net/?retryWrites=true&w=majority&appName=earnify"
BOT_TOKEN = os.getenv "8400875138:AAE2zrn4ovvwAj98NPbuXALsPm3rSiRtRIk"
ADMIN_IDS = [7119001414]  # Owner and admins (Telegram user IDs)
LOGGER_ID = 7119001414  # Telegram ID for logging messages
FSUB_IDS = [-1002661417456]  # Telegram channel/group IDs for forwarding/subscription

MIN_WITHDRAWAL_AMOUNT = 100  # Minimum points required to withdraw
DATABASE_URL = MONGO_URI  # Database connection (MongoDB URI)

