from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ConversationHandler
)
from config import BOT_TOKEN
from bot.handlers import (
    start, balance, withdraw_start, withdraw_amount_received,
    enter_referral, admin_stats, check_sub_callback,
    menu_handler, set_upi_start, set_upi_received,
    change_upi_callback, check_in,
    SET_UPI, WITHDRAW_AMOUNT
)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("referral", enter_referral))
    app.add_handler(CommandHandler("adminstats", admin_stats))
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="check_sub"))
    app.add_handler(CallbackQueryHandler(change_upi_callback, pattern="change_upi"))

    conv_set_upi = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(💳 Set UPI)$"), set_upi_start)],
        states={SET_UPI: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_upi_received)]},
        fallbacks=[]
    )
    app.add_handler(conv_set_upi)

    conv_withdraw = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(💸 Withdraw)$"), withdraw_start)],
        states={WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount_received)]},
        fallbacks=[]
    )
    app.add_handler(conv_withdraw)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

    print("Bot is running…")
    app.run_polling()

if __name__ == "__main__":
    main()
