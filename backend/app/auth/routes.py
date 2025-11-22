from flask import Blueprint, jsonify, request

from .decorators import token_required
from .service import (
    authenticate_user,
    create_user,
    is_username_taken,
    issue_token,
    normalize_username,
    purge_expired_tokens,
    revoke_token,
    reset_password,
    validate_password,
    validate_username,
)

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = normalize_username(data.get('username') or '')
    password = data.get('password') or ''
    confirm_password = data.get('confirm_password') or ''

    if not username or not password or not confirm_password:
        return jsonify({'message': 'Dati mancanti'}), 400
    if not validate_username(username):
        return jsonify({'message': 'Username non valido. Usa 3-64 caratteri alfanumerici, ".", "-" o "_".'}), 400
    if is_username_taken(username):
        return jsonify({'message': 'Username già esistente'}), 400
    if password != confirm_password:
        return jsonify({'message': 'Le password non coincidono'}), 400
    if not validate_password(password):
        return jsonify({'message': 'Password troppo debole. Usa almeno 8 caratteri con maiuscole, minuscole e numeri.'}), 400

    create_user(username, password)
    return jsonify({'message': 'Registrazione avvenuta con successo'}), 201


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Dati mancanti'}), 400

    user = authenticate_user(username, password)
    if not user:
        return jsonify({'message': 'Credenziali non valide'}), 401

    purge_expired_tokens()
    token_value = issue_token(user)
    return jsonify({'message': 'Login avvenuto con successo', 'token': token_value}), 200


@bp.route('/logout', methods=['POST'])
@token_required
def logout():
    from flask import g

    revoke_token(g.current_token)
    return jsonify({'message': 'Logout avvenuto con successo'}), 200


@bp.route('/username-available', methods=['GET'])
def username_available():
    username = normalize_username(request.args.get('username') or '')
    if not username:
        return jsonify({'available': False, 'message': 'Username mancante'}), 400
    if not validate_username(username):
        return jsonify({'available': False, 'message': 'Username non valido. Usa 3-64 caratteri alfanumerici, \".\", \"-\" o \"_\".'}), 400
    return jsonify({'available': not is_username_taken(username)}), 200


@bp.route('/reset-password', methods=['POST'])
def reset_password_route():
    data = request.get_json() or {}
    username = normalize_username(data.get('username') or '')
    new_password = data.get('new_password') or ''
    confirm_password = data.get('confirm_password') or ''

    if not username or not new_password or not confirm_password:
        return jsonify({'message': 'Dati mancanti'}), 400
    if new_password != confirm_password:
        return jsonify({'message': 'Le password non coincidono'}), 400
    if not validate_password(new_password):
        return jsonify({'message': 'Password troppo debole. Usa almeno 8 caratteri con maiuscole, minuscole e numeri.'}), 400

    if not reset_password(username, new_password):
        return jsonify({'message': 'Utente non trovato'}), 404

    return jsonify({'message': 'Password reimpostata. Effettua il login con le nuove credenziali.'}), 200
