from __future__ import annotations

import os
import re
from typing import Dict, Optional, Tuple

from flask import current_app, request
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
        'foto': item.foto,
        'data_ingresso': item.data_ingresso
    }
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
