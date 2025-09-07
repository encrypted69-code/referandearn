from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS, MIN_WITHDRAWAL_AMOUNT
from database.db import get_or_create_user, get_balance, add_referral, request_withdrawal, is_admin, get_admin_stats

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_record = await get_or_create_user(user.id, user.username)
    await update.message.reply_text(f"Welcome {user.first_name}! Your referral code is: {user_record['referral_code']}.\nInvite others with your code!")

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
    await update.message.reply_text(f"Your current balance is: {balance} points.")

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
