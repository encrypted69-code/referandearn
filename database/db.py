
from sqlalchemy import create_engine, select, insert, update
from sqlalchemy.orm import Session
from database.schema import metadata, users, referrals, transactions, withdrawals
import string, random
import datetime
from config import DATABASE_URL, MIN_WITHDRAWAL_AMOUNT

engine = create_engine(DATABASE_URL, echo=False, future=True)
metadata.create_all(engine)

def generate_referral_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def get_or_create_user(telegram_id, username):
    with Session(engine) as session:
        stmt = select(users).where(users.c.telegram_id == telegram_id)
        user = session.execute(stmt).first()
        if user:
            return dict(user._mapping)
        # create new user
        referral_code = generate_referral_code()
        # ensure unique code
        while session.execute(select(users).where(users.c.referral_code == referral_code)).first():
            referral_code = generate_referral_code()
        new_user = {
            "telegram_id": telegram_id,
            "username": username,
            "referral_code": referral_code,
            "registered_at": datetime.datetime.utcnow()
        }
        session.execute(insert(users).values(**new_user))
        session.commit()
        return new_user

def add_referral(referee_telegram_id, referrer_code):
    with Session(engine) as session:
        # Get referee user record
        referee_stmt = select(users).where(users.c.telegram_id == referee_telegram_id)
        referee = session.execute(referee_stmt).first()
        if not referee:
            return "You must start the bot first using /start."

        referee = dict(referee._mapping)
        if referee['referral_code'] == referrer_code:
            return "You cannot refer yourself."

        # Find referrer by referral code
        referrer_stmt = select(users).where(users.c.referral_code == referrer_code)
        referrer = session.execute(referrer_stmt).first()
        if not referrer:
            return "Invalid referral code."

        referrer = dict(referrer._mapping)

        # Check if referral already exists
        exists_stmt = select(referrals).where(
            referrals.c.referee_id == referee['id']
        )
        if session.execute(exists_stmt).first():
            return "You have already used a referral code."

        # Insert referral entry
        session.execute(insert(referrals).values(
            referrer_id=referrer['id'],
            referee_id=referee['id'],
            created_at=datetime.datetime.utcnow()
        ))
        # credit points to both users
        referral_bonus = 50  # points
        session.execute(insert(transactions).values(
            user_id=referrer['id'],
            amount=referral_bonus,
            type='credit',
            description=f"Referral bonus for referring user {referee['username']}",
            created_at=datetime.datetime.utcnow()
        ))
        session.execute(insert(transactions).values(
            user_id=referee['id'],
            amount=referral_bonus,
            type='credit',
            description=f"Referral bonus for being referred by {referrer['username']}",
            created_at=datetime.datetime.utcnow()
        ))
        session.commit()
        return "Referral successfully registered! Both you and your referrer have been credited."

def get_balance(telegram_id):
    with Session(engine) as session:
        user_stmt = select(users).where(users.c.telegram_id == telegram_id)
        user = session.execute(user_stmt).first()
        if not user:
            return 0
        user = dict(user._mapping)
        sum_stmt = select(transactions.c.amount).where(transactions.c.user_id == user['id'])
        amounts = session.execute(sum_stmt).scalars().all()
        return sum(amounts) if amounts else 0

def request_withdrawal(telegram_id, method, address):
    with Session(engine) as session:
        user_stmt = select(users).where(users.c.telegram_id == telegram_id)
        user = session.execute(user_stmt).first()
        if not user:
            return "User not found."

        user = dict(user._mapping)
        balance = get_balance(telegram_id)
        if balance < MIN_WITHDRAWAL_AMOUNT:
            return f"Minimum withdrawal amount is {MIN_WITHDRAWAL_AMOUNT} points. Your balance is {balance}."

        # Debit balance by creating a 'debit' transaction
        session.execute(insert(transactions).values(
            user_id=user['id'],
            amount=-balance,
            type='debit',
            description=f"Withdrawal request via {method} to {address}",
            created_at=datetime.datetime.utcnow()
        ))

        # Create withdrawal request
        session.execute(insert(withdrawals).values(
            user_id=user['id'],
            amount=balance,
            method=method,
            address=address,
            status='pending',
            requested_at=datetime.datetime.utcnow()
        ))
        session.commit()
        return f"Withdrawal request of {balance} points received. Processing soon."

def is_admin(telegram_id):
    from config import ADMIN_IDS
    return telegram_id in ADMIN_IDS

def get_admin_stats():
    with Session(engine) as session:
        total_users = session.execute(select(users.c.id)).all()
        total_referrals = session.execute(select(referrals.c.id)).all()
        total_withdrawals = session.execute(select(withdrawals.c.id)).all()
        return (
            f"System Stats:\n"
            f"Total Users: {len(total_users)}\n"
            f"Total Referrals: {len(total_referrals)}\n"
            f"Total Withdrawals: {len(total_withdrawals)}"
        )
