from functools import wraps
from typing import Callable, TypeVar

from flask import g, jsonify, request

from .service import get_user_from_token

F = TypeVar('F', bound=Callable)


def token_required(func: F) -> F:
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'message': 'Token mancante'}), 401
        token_value = auth_header.split(' ', 1)[1].strip()
        user = get_user_from_token(token_value)
        if not user:
            return jsonify({'message': 'Token non valido'}), 401
        g.current_user = user
        g.current_token = token_value
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
