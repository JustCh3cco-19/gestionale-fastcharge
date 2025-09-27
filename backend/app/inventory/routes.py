import csv
from io import StringIO

from flask import (
    Blueprint,
    Response,
    g,
    jsonify,
    request,
)

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
