from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import registry, relationship
import datetime

mapper_registry = registry()
metadata = mapper_registry.metadata

users = Table(
    'users', metadata,
    Column('id', Integer, primary_key=True),
    Column('telegram_id', Integer, unique=True, nullable=False),
    Column('username', String),
    Column('referral_code', String, unique=True, nullable=False),
    Column('registered_at', DateTime, default=datetime.datetime.utcnow)
)

referrals = Table(
    'referrals', metadata,
    Column('id', Integer, primary_key=True),
    Column('referrer_id', Integer, ForeignKey('users.id')),
    Column('referee_id', Integer, ForeignKey('users.id')),
    Column('created_at', DateTime, default=datetime.datetime.utcnow)
)

transactions = Table(
    'transactions', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('amount', Float, nullable=False),
    Column('type', String),  # 'credit' or 'debit'
    Column('description', String),
    Column('created_at', DateTime, default=datetime.datetime.utcnow)
)

withdrawals = Table(
    'withdrawals', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('amount', Float, nullable=False),
    Column('method', String),
    Column('address', String),
    Column('status', String, default='pending'),  # pending/processed/rejected
    Column('requested_at', DateTime, default=datetime.datetime.utcnow),
    Column('processed_at', DateTime, nullable=True)
)
