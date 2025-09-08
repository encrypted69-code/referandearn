from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import FSUB_IDS, ADMIN_IDS, MIN_WITHDRAWAL_AMOUNT
from database.db import (
    get_or_create_user, get_balance, add_referral,
    request_withdrawal, is_admin, get_admin_stats
)

FSUB_CHANNEL_ID = FSUB_IDS[0]  # e.g. -1002661417456
FSUB_CHANNEL_LINK = "https://t.me/+qXNXNu_LytJiMzU0"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Send force-subscription message with buttons
    keyboard = [
        [InlineKeyboardButton("Join Now", url=FSUB_CHANNEL_LINK)],
        [InlineKeyboardButton("Joined", callback_data="check_sub")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text="To access this bot, please join our channel first.",
        reply_markup=reply_markup
    )

async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    try:
        member = await context.bot.get_chat_member(FSUB_CHANNEL_ID, user_id)
        status = member.status
        if status in ["member", "creator", "administrator"]:
            await query.answer("Welcome! You have access to the bot now.")

            # Proceed with normal start flow, e.g. create/get user data
            user_record = await get_or_create_user(user_id, query.from_user.username)
            text = (
                f"Thanks for joining! You now have access to the bot.\n"
                f"Your referral code is: {user_record['referral_code']}\n"
                "Invite others using your code!"
            )
            await query.edit_message_text(text)
        else:
            await query.answer("Please join the channel first to access the bot.", show_alert=True)
    except Exception:
        await query.answer("Please join the channel first to access the bot.", show_alert=True)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    balance = await get_balance(user.id)
    await update.message.reply_text(f"Your current balance is: {balance} points.")

async def enter_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Please provide a referral code: /referral <code>")
        return
    referral_code = context.args[0]
    result = await add_referral(user.id, referral_code)
    await update.message.reply_text(result)

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /withdraw <method> <address>")
        return
    method = context.args[0]
    address = " ".join(context.args[1:])
    result = await request_withdrawal(user.id, method, address, MIN_WITHDRAWAL_AMOUNT)
    await update.message.reply_text(result)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(user.id, ADMIN_IDS):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    stats_msg = await get_admin_stats()
    await update.message.reply_text(stats_msg)
