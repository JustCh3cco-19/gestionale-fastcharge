import os
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import secrets

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'chiave_segreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurazione upload file
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

# In-memory token store (solo a scopo dimostrativo)
tokens = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Modello per gli utenti
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Modello per gli articoli dell'inventario
class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codice_articolo = db.Column(db.String(50), nullable=False)
    descrizione = db.Column(db.String(200))
    unita_misura = db.Column(db.String(20))
    # La quantità totale è calcolata come carico cumulativo - scarico cumulativo
    quantita = db.Column(db.Float, default=0)
    locazione = db.Column(db.String(100))
    foto = db.Column(db.String(200))  # Salviamo il nome del file
    data_ingresso = db.Column(db.String(50))
    carico = db.Column(db.Float, default=0)
    scarico = db.Column(db.Float, default=0)

@app.before_first_request
def create_tables():
    db.create_all()

# Decoratore per endpoint protetti tramite token
def token_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'message': 'Token mancante'}), 401
        token = auth.split(" ")[1]
        if token not in tokens:
            return jsonify({'message': 'Token non valido'}), 401
        return f(*args, **kwargs)
    return decorated

# Registrazione
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Dati mancanti'}), 400
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username già esistente'}), 400
    hashed_password = generate_password_hash(data['password'])
    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registrazione avvenuta con successo'}), 201

# Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Dati mancanti'}), 400
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Credenziali non valide'}), 401
    token = secrets.token_hex(16)
    tokens[token] = user.username
    return jsonify({'message': 'Login avvenuto con successo', 'token': token}), 200

# Recupera l'elenco degli articoli con filtraggio
@app.route('/api/inventory', methods=['GET'])
@token_required
def get_inventory():
    query = Inventory.query
    codice = request.args.get("codice_articolo")
    descrizione = request.args.get("descrizione")
    locazione = request.args.get("locazione")
    if codice:
        query = query.filter(Inventory.codice_articolo.ilike(f"%{codice}%"))
    if descrizione:
        query = query.filter(Inventory.descrizione.ilike(f"%{descrizione}%"))
    if locazione:
        query = query.filter(Inventory.locazione.ilike(f"%{locazione}%"))
    
    items = query.all()
    output = []
    for item in items:
        item_data = {
            'id': item.id,
            'codice_articolo': item.codice_articolo,
            'descrizione': item.descrizione,
            'unita_misura': item.unita_misura,
            'quantita': item.quantita,
            'locazione': item.locazione,
            'foto': item.foto,
            'data_ingresso': item.data_ingresso
        }
        output.append(item_data)
    return jsonify(output), 200

# Recupera un singolo articolo (per la modifica)
@app.route('/api/inventory/<int:item_id>', methods=['GET'])
@token_required
def get_inventory_item(item_id):
    item = Inventory.query.get(item_id)
    if not item:
        return jsonify({'message': 'Articolo non trovato'}), 404
    item_data = {
        'id': item.id,
        'codice_articolo': item.codice_articolo,
        'descrizione': item.descrizione,
        'unita_misura': item.unita_misura,
        'quantita': item.quantita,
        'locazione': item.locazione,
        'foto': item.foto,
        'data_ingresso': item.data_ingresso
    }
    return jsonify(item_data), 200

# Inserisce un nuovo articolo: la quantità viene calcolata come (carico - scarico)
@app.route('/api/inventory', methods=['POST'])
@token_required
def add_inventory():
    if 'codice_articolo' not in request.form:
        return jsonify({'message': 'Dati mancanti'}), 400
    codice_articolo = request.form.get('codice_articolo')
    descrizione = request.form.get('descrizione')
    unita_misura = request.form.get('unita_misura')
    locazione = request.form.get('locazione')
    data_ingresso = request.form.get('data_ingresso')
    # Se il campo è vuoto, usa 0 (utilizzando "or 0")
    carico = float(request.form.get('carico') or 0)
    scarico = float(request.form.get('scarico') or 0)
    quantita = carico - scarico

    foto_filename = None
    if 'foto' in request.files:
        file = request.files['foto']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            foto_filename = filename
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    
    new_item = Inventory(
        codice_articolo=codice_articolo,
        descrizione=descrizione,
        unita_misura=unita_misura,
        quantita=quantita,
        locazione=locazione,
        foto=foto_filename,
        data_ingresso=data_ingresso,
        carico=carico,
        scarico=scarico
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'message': 'Articolo aggiunto con successo'}), 201

# Modifica un articolo esistente: i nuovi valori di carico e scarico vengono sommati a quelli esistenti
# e la quantità viene ricalcolata automaticamente
@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
@token_required
def update_inventory(item_id):
    item = Inventory.query.get(item_id)
    if not item:
        return jsonify({'message': 'Articolo non trovato'}), 404

    if request.content_type.startswith('multipart/form-data'):
        codice_articolo = request.form.get('codice_articolo')
        if codice_articolo:
            item.codice_articolo = codice_articolo
        descrizione = request.form.get('descrizione')
        if descrizione:
            item.descrizione = descrizione
        unita_misura = request.form.get('unita_misura')
        if unita_misura:
            item.unita_misura = unita_misura
        locazione = request.form.get('locazione')
        if locazione:
            item.locazione = locazione
        data_ingresso = request.form.get('data_ingresso')
        if data_ingresso:
            item.data_ingresso = data_ingresso
        
        nuovo_carico = float(request.form.get('carico') or 0)
        nuovo_scarico = float(request.form.get('scarico') or 0)
        # Somma i nuovi movimenti a quelli esistenti
        item.carico += nuovo_carico
        item.scarico += nuovo_scarico
        # Ricalcola la quantità finale
        item.quantita = item.carico - item.scarico
        
        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                item.foto = filename
    else:
        data = request.get_json()
        if data.get('codice_articolo'):
            item.codice_articolo = data.get('codice_articolo')
        if data.get('descrizione'):
            item.descrizione = data.get('descrizione')
        if data.get('unita_misura'):
            item.unita_misura = data.get('unita_misura')
        if data.get('locazione'):
            item.locazione = data.get('locazione')
        if data.get('data_ingresso'):
            item.data_ingresso = data.get('data_ingresso')
        nuovo_carico = float(data.get('carico') or 0)
        nuovo_scarico = float(data.get('scarico') or 0)
        item.carico += nuovo_carico
        item.scarico += nuovo_scarico
        item.quantita = item.carico - item.scarico
        if data.get('foto'):
            item.foto = data.get('foto')
    db.session.commit()
    return jsonify({'message': 'Articolo aggiornato con successo'}), 200

# Elimina un articolo esistente
@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
@token_required
def delete_inventory(item_id):
    item = Inventory.query.get(item_id)
    if not item:
        return jsonify({'message': 'Articolo non trovato'}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Articolo eliminato con successo'}), 200


# Serve i file caricati (foto)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
