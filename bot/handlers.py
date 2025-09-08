from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
)
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
)
from config import FSUB_IDS, ADMIN_IDS, MIN_WITHDRAWAL_AMOUNT
from database.db import (
    get_or_create_user, get_balance, add_referral,
    request_withdrawal, is_admin, get_admin_stats,
    save_user_upi, get_user_upi,
    get_referred_count,
    process_daily_checkin
)

FSUB_CHANNEL_ID = FSUB_IDS[0]  # -1002661417456
FSUB_CHANNEL_LINK = "https://t.me/+qXNXNu_LytJiMzU0"

SET_UPI, WITHDRAW_AMOUNT = range(2)

menu_buttons = [
    ["📢 Refer and Earn", "ℹ️ Info"],
    ["👛 Wallet", "💳 Set UPI"],
    ["💸 Withdraw", "✅ Check In"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Optionally, add force-subscribe check here

    reply_markup = ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True)
    welcome_text = (
        f"👋 Hey {user.first_name}!\n\n"
        "Welcome to Refer & Earn Bot 💰\n\n"
        "Earn ₹2 per referral! Share your unique link and start earning instant UPI cashout! 🚀\n"
        "Please use the menu below to navigate."
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_text, reply_markup=reply_markup)

async def enter_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Please provide a referral code: /referral <code>")
        return
    referral_code = context.args[0]
    result = await add_referral(user.id, referral_code)
    await update.message.reply_text(result)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    balance = await get_balance(user.id)
    await update.message.reply_text(f"Your current balance is: ₹{balance}")

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "📢 Refer and Earn":
        await refer_and_earn(update, context)
    elif text == "ℹ️ Info":
        await info(update, context)
    elif text == "👛 Wallet":
        await wallet(update, context)
    elif text == "💳 Set UPI":
        await set_upi_start(update, context)
        return SET_UPI
    elif text == "💸 Withdraw":
        await withdraw_start(update, context)
        return WITHDRAW_AMOUNT
    elif text == "✅ Check In":
        await check_in(update, context)
    else:
        await update.message.reply_text("Please select an option from the menu.")

async def refer_and_earn(update, context):
    user = update.effective_user
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={user.id}"
    text = (
        f"📢 Share your referral link and earn ₹2 for every friend who joins and uses the bot!\n\n"
        f"Your referral link:\n{referral_link}\n\n"
        "Start sharing now to earn instant UPI cashouts! 💸"
    )
    await update.message.reply_text(text)

async def info(update, context):
    text = (
        "ℹ️ *Refer & Earn Bot Info*\n\n"
        "🔹 Earn ₹2 per referral\n"
        "🔹 Instant UPI cashouts available 💳\n"
        "🔹 Daily check-in bonus of ₹0.50\n"
        "🔹 No delays, instant credit on referrals\n\n"
        "Share this bot and start earning money today! 🚀"
    )
    await update.message.reply_markdown_v2(text)

async def wallet(update, context):
    user = update.effective_user
    balance = await get_balance(user.id)
    user_record = await get_or_create_user(user.id, user.username)
    referral_code = user_record["referral_code"]
    upi_id = await get_user_upi(user.id) or "Not set"
    referred_count = await get_referred_count(user.id)
    text = (
        f"👛 *Your Wallet*\n\n"
        f"Balance: ₹{balance}\n"
        f"Referral Code: {referral_code}\n"
        f"Referred Users: {referred_count}\n"
        f"UPI ID: {upi_id}"
    )
    await update.message.reply_markdown_v2(text)

async def set_upi_start(update, context):
    await update.message.reply_text("Please send your UPI ID (e.g. 7797382937@paytm):")
    return SET_UPI

async def set_upi_received(update, context):
    upi_id = update.message.text.strip()
    user_id = update.effective_user.id
    await save_user_upi(user_id, upi_id)
    keyboard = [[InlineKeyboardButton("Change UPI ID", callback_data="change_upi")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Your UPI ID has been set to: {upi_id}", reply_markup=reply_markup)
    return ConversationHandler.END

async def change_upi_callback(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please send your new UPI ID:")
    return SET_UPI

async def withdraw_start(update, context):
    user = update.effective_user
    balance = await get_balance(user.id)
    if balance < MIN_WITHDRAWAL_AMOUNT:
        await update.message.reply_text(f"Minimum withdrawal amount is ₹{MIN_WITHDRAWAL_AMOUNT}. Your balance: ₹{balance}")
        return ConversationHandler.END
    await update.message.reply_text(f"Your balance: ₹{balance}\nHow much would you like to withdraw?")
    return WITHDRAW_AMOUNT

async def withdraw_amount_received(update, context):
    user = update.effective_user
    amount_text = update.message.text.strip()
    if not amount_text.isdigit():
        await update.message.reply_text("Please enter a valid number amount.")
        return WITHDRAW_AMOUNT
    amount = int(amount_text)
    balance = await get_balance(user.id)
    if amount > balance:
        await update.message.reply_text(f"You cannot withdraw more than your balance ₹{balance}. Enter a valid amount.")
        return WITHDRAW_AMOUNT
    method = "UPI"
    upi_id = await get_user_upi(user.id)
    if not upi_id:
        await update.message.reply_text("You need to set your UPI ID first via 'Set UPI' menu.")
        return ConversationHandler.END
    result = await request_withdrawal(user.id, method, upi_id, MIN_WITHDRAWAL_AMOUNT)
    await update.message.reply_text(result)
    return ConversationHandler.END

async def check_in(update, context):
    user_id = update.effective_user.id
    result = await process_daily_checkin(user_id)
    if result == "success":
        await update.message.reply_text("✅ Daily check-in successful! You earned ₹0.50.")
    else:
        await update.message.reply_text(f"⏳ You can check in again after {result} hours.")
