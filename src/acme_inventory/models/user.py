from datetime import datetime

import pyotp
from flask_login import UserMixin

from ..extensions import bcrypt, db


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    avatar_url = db.Column("pfp_url", db.String(255), default="/static/images/default-profile.svg")
    joined_at = db.Column("joindate", db.DateTime, nullable=False, default=datetime.now)
    is_2fa_enabled = db.Column(db.Boolean, nullable=False, default=False)
    token_2fa = db.Column(db.String, unique=True, default=pyotp.random_base32)

    def set_password(self, password):
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes.")
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        if len(password.encode("utf-8")) > 72:
            return False
        return bcrypt.check_password_hash(self.password, password)
