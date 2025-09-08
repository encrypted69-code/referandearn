from telegram.ext import ApplicationBuilder, CommandHandler
from bot.handlers import start, balance, withdraw, enter_referral, admin_stats
from config import BOT_TOKEN  # Import your actual bot token here

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()  # Use the token from config
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("referral", enter_referral))
    app.add_handler(CommandHandler("adminstats", admin_stats))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
