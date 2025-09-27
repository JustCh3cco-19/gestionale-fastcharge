from __future__ import annotations

import re
import secrets
from datetime import datetime, timedelta
from typing import Optional

from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import Token, User


USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_.-]{3,64}$')


def normalize_username(username: str) -> str:
    return username.strip()


def validate_username(username: str) -> bool:
    return bool(USERNAME_PATTERN.fullmatch(username))


def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def create_user(username: str, password: str) -> User:
    normalized_username = normalize_username(username)
    user = User(username=normalized_username, password=hash_password(password))
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(username: str, password: str) -> Optional[User]:
    user = User.query.filter_by(username=normalize_username(username)).first()
    if user and check_password_hash(user.password, password):
        return user
    return None


def is_username_taken(username: str) -> bool:
    return User.query.filter_by(username=normalize_username(username)).first() is not None


def issue_token(user: User) -> str:
    token_value = secrets.token_hex(32)
    ttl_seconds = current_app.config.get('TOKEN_TTL_SECONDS', 86400)
    expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    token = Token(token=token_value, user=user, expires_at=expires_at)
    db.session.add(token)
    db.session.commit()
    return token_value


def get_user_from_token(token_value: str) -> Optional[User]:
    if not token_value:
        return None
    token = Token.query.filter_by(token=token_value).first()
    if not token:
        return None
    if token.is_expired:
        db.session.delete(token)
        db.session.commit()
        return None
    return token.user


def revoke_token(token_value: str) -> None:
    token = Token.query.filter_by(token=token_value).first()
    if token:
        db.session.delete(token)
        db.session.commit()


def purge_expired_tokens() -> None:
    now = datetime.utcnow()
    expired_tokens = Token.query.filter(Token.expires_at <= now).all()
    if not expired_tokens:
        return
    for token in expired_tokens:
        db.session.delete(token)
    db.session.commit()
