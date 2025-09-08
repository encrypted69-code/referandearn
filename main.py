from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ConversationHandler
)
from config import BOT_TOKEN
from bot.handlers import (
    start, balance, enter_referral, admin_stats, menu_handler,
    refer_and_earn, info, wallet, set_upi_start, set_upi_received,
    change_upi_callback, withdraw_start, withdraw_amount_received,
    check_in, check_sub_callback,
    SET_UPI, WITHDRAW_AMOUNT
)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("referral", enter_referral))
    app.add_handler(CommandHandler("adminstats", admin_stats))

    # Force subscribe verification via callback
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="check_sub"))

    # Callback query handler for changing UPI
    app.add_handler(CallbackQueryHandler(change_upi_callback, pattern="change_upi"))

    # Conversation handler for setting UPI
    conv_set_upi = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(💳 Set UPI)$"), set_upi_start)],
        states={SET_UPI: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_upi_received)]},
        fallbacks=[]
    )
    app.add_handler(conv_set_upi)

    # Conversation handler for withdraw amount input
    conv_withdraw = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(💸 Withdraw)$"), withdraw_start)],
        states={WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount_received)]},
        fallbacks=[]
    )
    app.add_handler(conv_withdraw)

    # Menu text handler for other commands
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
