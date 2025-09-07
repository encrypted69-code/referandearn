
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_or_create_user, get_balance, add_referral, request_withdrawal, is_admin, get_admin_stats

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_record = get_or_create_user(user.id, user.username)
    await update.message.reply_text(f"Welcome {user.first_name}! Your referral code is: {user_record['referral_code']}.\nInvite others with your code!")

async def enter_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Please provide a referral code: /referral <code>")
        return
    referral_code = context.args[0]
    result = add_referral(user.id, referral_code)
    await update.message.reply_text(result)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    balance = get_balance(user.id)
    await update.message.reply_text(f"Your current balance is: {balance} points.")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Please specify withdrawal method and address: /withdraw <method> <address>")
        return
    method = context.args[0]
    address = " ".join(context.args[1:])
    result = request_withdrawal(user.id, method, address)
    await update.message.reply_text(result)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    stats_msg = get_admin_stats()
    await update.message.reply_text(stats_msg)
