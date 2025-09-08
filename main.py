from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from bot.handlers import start, balance, withdraw, enter_referral, admin_stats, check_sub_callback
from config import BOT_TOKEN

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("referral", enter_referral))
    app.add_handler(CommandHandler("adminstats", admin_stats))
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="check_sub"))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
