import json
import os
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)
db = client.referral_bot

referral_bonus = 2  # INR per referral, adjust as needed

# USER FUNCTIONS

async def get_or_create_user(telegram_id, username):
    user = await db.users.find_one({"telegram_id": telegram_id})
    if user:
        return user
    # Create referral code
    import random, string
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    # Avoid duplicate referral code
    while await db.users.find_one({"referral_code": code}):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    user_doc = {
        "telegram_id": telegram_id,
        "username": username,
        "referral_code": code,
        "registered_at": datetime.utcnow(),
        "balance": 0,
        "upi_id": None,
        "last_checkin": None
    }
    await db.users.insert_one(user_doc)
    return user_doc

async def get_balance(telegram_id):
    user = await db.users.find_one({"telegram_id": telegram_id})
    if not user:
        return 0
    return user.get("balance", 0)

async def save_user_upi(telegram_id, upi_id):
    await db.users.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"upi_id": upi_id}}
    )

async def get_user_upi(telegram_id):
    user = await db.users.find_one({"telegram_id": telegram_id})
    if not user:
        return None
    return user.get("upi_id")

async def get_referred_count(telegram_id):
    user = await db.users.find_one({"telegram_id": telegram_id})
    if not user:
        return 0
    referral_code = user.get("referral_code")
    if not referral_code:
        return 0
    count = await db.users.count_documents({"referred_by": referral_code})
    return count

async def add_referral(referee_telegram_id, refl_code):
    referee = await db.users.find_one({"telegram_id": referee_telegram_id})
    if not referee:
        return "Start the bot first by sending /start"

    if referee.get("referred_by"):
        return "Referral already applied."

    if referee.get("referral_code") == refl_code:
        return "You cannot refer yourself."

    referrer = await db.users.find_one({"referral_code": refl_code})
    if not referrer:
        return "Invalid referral code."

    await db.users.update_one(
        {"telegram_id": referee_telegram_id},
        {"$set": {"referred_by": refl_code}}
    )

    # Credit referral bonus to both users
    await db.users.update_one(
        {"telegram_id": referee_telegram_id},
        {"$inc": {"balance": referral_bonus}}
    )
    await db.users.update_one(
        {"telegram_id": referrer["telegram_id"]},
        {"$inc": {"balance": referral_bonus}}
    )
    return "Referral added! You both earned ₹2."


# WITHDRAWALS

async def request_withdrawal(telegram_id, method, address, min_withdrawal_amount):
    user = await db.users.find_one({"telegram_id": telegram_id})
    if not user:
        return "User not found."

    balance = user.get("balance", 0)
    if balance < min_withdrawal_amount:
        return f"Minimum withdrawal is ₹{min_withdrawal_amount}. Your balance: ₹{balance}"

    # Deduct all balance for withdrawal
    await db.users.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"balance": 0}}
    )

    # Add withdrawal record
    withdrawal_doc = {
        "telegram_id": telegram_id,
        "amount": balance,
        "method": method,
        "address": address,
        "status": "pending",
        "requested_at": datetime.utcnow()
    }
    await db.withdrawals.insert_one(withdrawal_doc)

    return f"Withdrawal request for ₹{balance} received and is being processed."


# ADMIN CHECK

async def is_admin(telegram_id, admin_ids):
    return telegram_id in admin_ids

async def get_admin_stats():
    total_users = await db.users.count_documents({})
    total_withdrawals = await db.withdrawals.count_documents({})
    total_referrals = await db.users.count_documents({"referred_by": {"$exists": True}})
    text = (
        f"📊 Bot Stats:\n"
        f"Total Users: {total_users}\n"
        f"Total Referrals: {total_referrals}\n"
        f"Total Withdrawals: {total_withdrawals}\n"
    )
    return text

# DAILY CHECK-IN

async def process_daily_checkin(telegram_id):
    user = await db.users.find_one({"telegram_id": telegram_id})
    if not user:
        return "User not found."

    last_checkin = user.get("last_checkin")
    now = datetime.utcnow()

    if last_checkin:
        elapsed = now - last_checkin
        if elapsed < timedelta(hours=24):
            remaining = timedelta(hours=24) - elapsed
            hours = remaining.seconds // 3600
            return hours

    # Update last checkin and add bonus
    await db.users.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"last_checkin": now},
         "$inc": {"balance": 0.5}}
    )
    return "success"
