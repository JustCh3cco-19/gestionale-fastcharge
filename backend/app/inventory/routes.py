import csv
import json
import zipfile
from datetime import datetime
from io import BytesIO, StringIO
from pathlib import Path

from flask import Blueprint, Response, current_app, g, jsonify, request, send_file

from ..auth.decorators import token_required
from ..extensions import db
from ..models import Inventory
from ..utils import extract_inventory_payload, inventory_to_dict, save_uploaded_file

bp = Blueprint('inventory', __name__)


@bp.route('/inventory', methods=['GET'])
@token_required
def list_inventory():
    query = Inventory.query
    codice = request.args.get('codice_articolo')
    descrizione = request.args.get('descrizione')
    locazione = request.args.get('locazione')

    if codice:
        query = query.filter(Inventory.codice_articolo.ilike(f"%{codice}%"))
    if descrizione:
        query = query.filter(Inventory.descrizione.ilike(f"%{descrizione}%"))
    if locazione:
        query = query.filter(Inventory.locazione.ilike(f"%{locazione}%"))

    items = query.all()
    return jsonify([inventory_to_dict(item, include_tracking=True) for item in items]), 200


@bp.route('/inventory/<int:item_id>', methods=['GET'])
@token_required
def get_inventory_item(item_id: int):
    item = Inventory.query.get(item_id)
    if not item:
        return jsonify({'message': 'Articolo non trovato'}), 404
    return jsonify(inventory_to_dict(item)), 200


@bp.route('/inventory', methods=['POST'])
@token_required
def add_inventory():
    try:
        payload, uploaded_file = extract_inventory_payload()
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400
    codice_articolo = payload.get('codice_articolo')

    if not codice_articolo:
        return jsonify({'message': 'Dati mancanti'}), 400
    if Inventory.query.filter_by(codice_articolo=codice_articolo).first():
        return jsonify({'message': 'Prodotto già esistente'}), 400
    if payload['carico'] < 0 or payload['scarico'] < 0:
        return jsonify({'message': 'Carico e scarico devono essere maggiori o uguali a zero'}), 400

    foto_filename = payload.get('foto')
    try:
        saved_filename = save_uploaded_file(uploaded_file)
        if saved_filename:
            foto_filename = saved_filename
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400

    quantita = payload['carico'] - payload['scarico']

    new_item = Inventory(
        codice_articolo=codice_articolo,
        descrizione=payload.get('descrizione'),
        unita_misura=payload.get('unita_misura'),
        quantita=quantita,
        locazione=payload.get('locazione'),
        foto=foto_filename,
        data_ingresso=payload.get('data_ingresso'),
        carico=payload['carico'],
        scarico=payload['scarico'],
        created_by=g.current_user.username,
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'message': 'Articolo aggiunto con successo'}), 201


@bp.route('/inventory/<int:item_id>', methods=['PUT'])
@token_required
def update_inventory(item_id: int):
    item = Inventory.query.get(item_id)
    if not item:
        return jsonify({'message': 'Articolo non trovato'}), 404

    try:
        payload, uploaded_file = extract_inventory_payload()
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400

    if payload['carico'] < 0 or payload['scarico'] < 0:
        return jsonify({'message': 'Carico e scarico devono essere maggiori o uguali a zero'}), 400

    if payload.get('codice_articolo'):
        item.codice_articolo = payload['codice_articolo']
    if payload.get('descrizione'):
        item.descrizione = payload['descrizione']
    if payload.get('unita_misura'):
        item.unita_misura = payload['unita_misura']
    if payload.get('locazione'):
        item.locazione = payload['locazione']
    if payload.get('data_ingresso'):
        item.data_ingresso = payload['data_ingresso']

    item.carico += payload['carico']
    item.scarico += payload['scarico']
    item.quantita = item.carico - item.scarico

    try:
        saved_filename = save_uploaded_file(uploaded_file)
        if saved_filename:
            item.foto = saved_filename
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400

    if payload.get('foto') and not uploaded_file:
        item.foto = payload['foto']

    item.modified_by = g.current_user.username

    db.session.commit()
    return jsonify({'message': 'Articolo aggiornato con successo'}), 200


@bp.route('/inventory/<int:item_id>', methods=['DELETE'])
@token_required
def delete_inventory(item_id: int):
    item = Inventory.query.get(item_id)
    if not item:
        return jsonify({'message': 'Articolo non trovato'}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Articolo eliminato con successo'}), 200


@bp.route('/inventory/export', methods=['GET'])
@token_required
def export_inventory():
    items = Inventory.query.all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Codice Articolo', 'Descrizione', 'Unità Misura', 'Quantità', 'Locazione', 'Data Ingresso'])
    for item in items:
        writer.writerow([
            item.codice_articolo,
            item.descrizione,
            item.unita_misura,
            item.quantita,
            item.locazione,
            item.data_ingresso,
        ])
    output = si.getvalue()
    si.close()

    response = Response(output, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=inventario.csv'
    return response


@bp.route('/inventory/export/bundle', methods=['GET'])
@token_required
def export_inventory_bundle():
    items = Inventory.query.all()
    bundle = _build_export_bundle(items)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f'inventario_bundle_{timestamp}.zip'
    return send_file(bundle, mimetype='application/zip', as_attachment=True, download_name=filename)


@bp.route('/inventory/import', methods=['POST'])
@token_required
def import_inventory_bundle():
    uploaded = request.files.get('file')
    if not uploaded or not uploaded.filename:
        return jsonify({'message': 'Carica un archivio .zip esportato dall\'inventario'}), 400
    if not uploaded.filename.lower().endswith('.zip'):
        return jsonify({'message': 'Il file deve essere un archivio .zip'}), 400

    try:
        payload = uploaded.read()
        zf = zipfile.ZipFile(BytesIO(payload))
    except zipfile.BadZipFile:
        return jsonify({'message': 'Archivio non valido o corrotto'}), 400

    if 'manifest.json' not in zf.namelist():
        return jsonify({'message': 'Manifest mancante nell\'archivio'}), 400
    try:
        manifest = json.loads(zf.read('manifest.json'))
    except Exception:
        return jsonify({'message': 'Manifest non leggibile'}), 400

    items = manifest.get('items')
    if not isinstance(items, list):
        return jsonify({'message': 'Manifest non valido: campo "items" mancante'}), 400

    uploads_dir = Path(current_app.config['UPLOAD_FOLDER'])
    uploads_dir.mkdir(parents=True, exist_ok=True)

    try:
        prepared_items = _prepare_items_for_import(items, zf)
        _replace_inventory(prepared_items, uploads_dir)
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'message': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Errore durante l'import dell'inventario")
        return jsonify({'message': 'Errore durante l\'importazione dell\'inventario'}), 500

    return jsonify({'message': 'Inventario importato con successo', 'items_imported': len(items)}), 200


def _serialise_item_for_bundle(item: Inventory) -> dict:
    return {
        'codice_articolo': item.codice_articolo,
        'descrizione': item.descrizione,
        'unita_misura': item.unita_misura,
        'quantita': item.quantita,
        'locazione': item.locazione,
        'data_ingresso': item.data_ingresso,
        'carico': item.carico,
        'scarico': item.scarico,
        'foto': item.foto,
        'created_by': item.created_by,
        'modified_by': item.modified_by,
    }


def _build_export_bundle(items) -> BytesIO:
    uploads_dir = Path(current_app.config['UPLOAD_FOLDER'])
    manifest = {
        'version': 1,
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'items': [_serialise_item_for_bundle(item) for item in items],
    }
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        for item in items:
            if not item.foto:
                continue
            file_path = uploads_dir / item.foto
            if file_path.exists():
                archive.write(file_path, arcname=f'uploads/{item.foto}')
    memory_file.seek(0)
    return memory_file


def _prepare_items_for_import(items, archive: zipfile.ZipFile):
    prepared = []
    for idx, raw in enumerate(items, start=1):
        code = (raw.get('codice_articolo') or '').strip()
        if not code:
            raise ValueError(f'Manifest non valido: codice_articolo mancante alla riga {idx}')
        carico = _safe_import_int(raw.get('carico'))
        scarico = _safe_import_int(raw.get('scarico'))
        foto_name = raw.get('foto')
        attachment_bytes = None
        if foto_name:
            zip_path = f'uploads/{foto_name}'
            if zip_path not in archive.namelist():
                raise ValueError(f'Manifest non valido: allegato "{foto_name}" non presente nell\'archivio')
            with archive.open(zip_path) as src:
                attachment_bytes = src.read()
        prepared.append({
            'codice_articolo': code,
            'descrizione': raw.get('descrizione'),
            'unita_misura': raw.get('unita_misura'),
            'locazione': raw.get('locazione'),
            'data_ingresso': raw.get('data_ingresso'),
            'carico': carico,
            'scarico': scarico,
            'created_by': raw.get('created_by'),
            'modified_by': raw.get('modified_by'),
            'foto': foto_name,
            'attachment_bytes': attachment_bytes,
        })
    return prepared


def _replace_inventory(prepared_items, uploads_dir: Path) -> None:
    _clear_uploads_dir(uploads_dir)
    db.session.query(Inventory).delete()
    db.session.flush()

    for item in prepared_items:
        record = Inventory(
            codice_articolo=item['codice_articolo'],
            descrizione=item.get('descrizione'),
            unita_misura=item.get('unita_misura'),
            locazione=item.get('locazione'),
            data_ingresso=item.get('data_ingresso'),
            carico=item['carico'],
            scarico=item['scarico'],
            created_by=item.get('created_by'),
            modified_by=item.get('modified_by'),
        )
        record.quantita = record.carico - record.scarico

        if item.get('foto') and item.get('attachment_bytes') is not None:
            destination = uploads_dir / item['foto']
            with open(destination, 'wb') as dst:
                dst.write(item['attachment_bytes'])
            record.foto = item['foto']

        db.session.add(record)

    db.session.commit()


def _clear_uploads_dir(uploads_dir: Path) -> None:
    for child in uploads_dir.iterdir():
        if child.is_file():
            child.unlink()


def _safe_import_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError('Manifest non valido: usa solo numeri interi per carico/scarico') from exc
