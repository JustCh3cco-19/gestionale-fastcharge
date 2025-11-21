from pathlib import Path

from flask import Blueprint, current_app, jsonify, send_from_directory

from ..auth.decorators import token_required
from ..utils import resolve_file_token

bp = Blueprint('files', __name__)


@bp.get('/<string:file_token>')
@token_required
def serve_uploaded_file(file_token: str):
    """Restituisce un file caricato partendo da un token firmato."""
    try:
        filename = resolve_file_token(file_token)
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400

    uploads_dir = Path(current_app.config['UPLOAD_FOLDER'])
    file_path = uploads_dir / filename
    if not file_path.exists():
        return jsonify({'message': 'File non trovato'}), 404

    return send_from_directory(uploads_dir, filename, as_attachment=False)
