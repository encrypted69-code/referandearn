import asyncio
import random
import string
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)
db = client.referral_bot  # Database name

referral_bonus = 50  # points

def generate_referral_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def get_or_create_user(telegram_id, username):
    user = await db.users.find_one({"telegram_id": telegram_id})
    if user:
        return user
    referral_code = generate_referral_code()
    # Ensure unique referral code
    while await db.users.find_one({"referral_code": referral_code}):
        referral_code = generate_referral_code()
    new_user = {
        "telegram_id": telegram_id,
        "username": username,
        "referral_code": referral_code,
        "registered_at": datetime.utcnow()
    }
    await db.users.insert_one(new_user)
    return new_user

async def add_referral(referee_telegram_id, referrer_code):
    referee = await db.users.find_one({"telegram_id": referee_telegram_id})
    if not referee:
        return "You must start the bot first using /start."

    if referee.get("referral_code") == referrer_code:
        return "You cannot refer yourself."

    referrer = await db.users.find_one({"referral_code": referrer_code})
    if not referrer:
        return "Invalid referral code."

    existing_referral = await db.referrals.find_one({"referee_id": referee['_id']})
    if existing_referral:
        return "You have already used a referral code."

    await db.referrals.insert_one({
        "referrer_id": referrer['_id'],
        "referee_id": referee['_id'],
        "created_at": datetime.utcnow()
    })

    # Credit points
    await db.transactions.insert_many([
        {
            "user_id": referrer['_id'],
            "amount": referral_bonus,
            "type": "credit",
            "description": f"Referral bonus for referring user {referee.get('username')}",
            "created_at": datetime.utcnow()
        },
        {
            "user_id": referee['_id'],
            "amount": referral_bonus,
            "type": "credit",
            "description": f"Referral bonus for being referred by {referrer.get('username')}",
            "created_at": datetime.utcnow()
        }
    ])

    return "Referral successfully registered! Both you and your referrer have been credited."

async def get_balance(telegram_id):
    user = await db.users.find_one({"telegram_id": telegram_id})
    if not user:
        return 0
    pipeline = [
        {"$match": {"user_id": user['_id']}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    result = await db.transactions.aggregate(pipeline).to_list(length=1)
    return result[0]['total'] if result else 0

async def request_withdrawal(telegram_id, method, address, min_withdrawal_amount):
    user = await db.users.find_one({"telegram_id": telegram_id})
    if not user:
        return "User not found."

    balance = await get_balance(telegram_id)
    if balance < min_withdrawal_amount:
        return f"Minimum withdrawal amount is {min_withdrawal_amount} points. Your balance is {balance}."

    # Debit transactions
    await db.transactions.insert_one({
        "user_id": user['_id'],
        "amount": -balance,
        "type": "debit",
        "description": f"Withdrawal request via {method} to {address}",
        "created_at": datetime.utcnow()
    })

    await db.withdrawals.insert_one({
        "user_id": user['_id'],
        "amount": balance,
        "method": method,
        "address": address,
        "status": "pending",
        "requested_at": datetime.utcnow()
    })

    return f"Withdrawal request of {balance} points received. Processing soon."

async def is_admin(telegram_id, admin_ids):
    return telegram_id in admin_ids

async def get_admin_stats():
    total_users = await db.users.count_documents({})
    total_referrals = await db.referrals.count_documents({})
    total_withdrawals = await db.withdrawals.count_documents({})

    return (f"System Stats:\n"
            f"Total Users: {total_users}\n"
            f"Total Referrals: {total_referrals}\n"
            f"Total Withdrawals: {total_withdrawals}")
