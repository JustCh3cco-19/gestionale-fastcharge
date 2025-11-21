from __future__ import annotations

import os
import re
from typing import Dict, Optional, Tuple

from flask import current_app, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def allowed_file(filename: str) -> bool:
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', set())
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def safe_int(value: object) -> int:
    if value in (None, ""):
        return 0
    if isinstance(value, bool):
        raise ValueError('Valore non valido per la quantità')
    if isinstance(value, (int,)):
        return int(value)
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError('Usa solo numeri interi per carico/scarico')
        return int(value)
    text = str(value).strip()
    if text == "":
        return 0
    if not re.fullmatch(r'-?\d+', text):
        raise ValueError('Usa solo numeri interi per carico/scarico')
    return int(text)


def inventory_to_dict(item: "Inventory", include_tracking: bool = False) -> Dict[str, object]:
    data = {
        'id': item.id,
        'codice_articolo': item.codice_articolo,
        'descrizione': item.descrizione,
        'unita_misura': item.unita_misura,
        'quantita': item.quantita,
        'locazione': item.locazione,
        'data_ingresso': item.data_ingresso
    }
    attachment_payload = _build_attachment_payload(item)
    if attachment_payload:
        data['attachment'] = attachment_payload
    if include_tracking:
        data['created_by'] = item.created_by
        data['modified_by'] = item.modified_by
    return data


def extract_inventory_payload() -> Tuple[Dict[str, object], Optional[FileStorage]]:
    is_form_data = (request.content_type or '').startswith('multipart/form-data')
    source = request.form if is_form_data else (request.get_json(silent=True) or {})

    try:
        carico = safe_int(source.get('carico'))
        scarico = safe_int(source.get('scarico'))
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    payload = {
        'codice_articolo': source.get('codice_articolo'),
        'descrizione': source.get('descrizione'),
        'unita_misura': source.get('unita_misura'),
        'locazione': source.get('locazione'),
        'data_ingresso': source.get('data_ingresso'),
        'carico': carico,
        'scarico': scarico,
        'foto': source.get('foto')
    }

    uploaded_file = request.files.get('foto') if is_form_data else None
    return payload, uploaded_file


def save_uploaded_file(file: Optional[FileStorage]) -> Optional[str]:
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError('Estensione file non consentita')
    filename = secure_filename(file.filename)
    destination = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(destination)
    return filename


def _get_file_serializer() -> URLSafeTimedSerializer:
    secret_key = current_app.config.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError('SECRET_KEY non configurata')
    return URLSafeTimedSerializer(secret_key=secret_key, salt='file-download')


def generate_file_token(filename: Optional[str]) -> Optional[str]:
    if not filename:
        return None
    serializer = _get_file_serializer()
    payload = {'filename': filename}
    return serializer.dumps(payload)


def resolve_file_token(token: str) -> str:
    serializer = _get_file_serializer()
    max_age = current_app.config.get('FILE_TOKEN_TTL_SECONDS')
    try:
        if max_age and max_age > 0:
            data = serializer.loads(token, max_age=max_age)
        else:
            data = serializer.loads(token)
    except SignatureExpired as exc:
        raise ValueError('Link scaduto, richiedi nuovamente il file') from exc
    except BadSignature as exc:
        raise ValueError('Token file non valido') from exc
    filename = data.get('filename')
    if not filename:
        raise ValueError('Token file non valido')
    return filename


def _build_attachment_payload(item: "Inventory") -> Optional[Dict[str, str]]:
    if not getattr(item, 'foto', None):
        return None
    token = generate_file_token(item.foto)
    if not token:
        return None

    _, extension = os.path.splitext(item.foto)
    extension = extension.lstrip('.').lower()
    if not extension:
        extension = 'bin'

    if extension == 'pdf':
        kind = 'pdf'
    elif extension in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
        kind = 'image'
    else:
        kind = 'file'

    base_code = item.codice_articolo or 'allegato'
    safe_base = re.sub(r'[^A-Za-z0-9_-]+', '-', base_code).strip('-') or 'allegato'
    suggested_filename = f"{safe_base}.{extension}"

    return {
        'token': token,
        'kind': kind,
        'extension': extension,
        'suggested_filename': suggested_filename
    }
