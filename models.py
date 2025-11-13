"""
SQLAlchemy models: User, Therapist, Record.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="staff")  # owner / staff
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_owner(self):
        return self.role == "owner"

class Therapist(db.Model):
    __tablename__ = "therapists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default="active")  # active / inactive
    commission_rate = db.Column(db.Float, default=0.0)  # reserved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Record(db.Model):
    __tablename__ = "records"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    datetime_created = db.Column(db.DateTime, default=datetime.utcnow)

    # financials
    card_amount = db.Column(db.Float, default=0.0)
    cash_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)

    # meta
    customer_count = db.Column(db.Integer, default=1)
    note = db.Column(db.Text, nullable=True)

    # service details
    service_type = db.Column(db.String(64), default="Full Body")  # Full Body / Foot / Combination / Chair
    duration = db.Column(db.String(32), default="60min")  # 20min/30min/40min/60min

    therapist_id = db.Column(db.Integer, db.ForeignKey('therapists.id'), nullable=True)
    therapist = db.relationship('Therapist', backref=db.backref('records', lazy='dynamic'))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
