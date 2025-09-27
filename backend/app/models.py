from datetime import datetime

from .extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codice_articolo = db.Column(db.String(50), nullable=False)
    descrizione = db.Column(db.String(200))
    unita_misura = db.Column(db.String(20))
    quantita = db.Column(db.Integer, default=0)
    locazione = db.Column(db.String(100))
    foto = db.Column(db.String(200))
    data_ingresso = db.Column(db.String(50))
    carico = db.Column(db.Integer, default=0)
    scarico = db.Column(db.Integer, default=0)
    created_by = db.Column(db.String(80))
    modified_by = db.Column(db.String(80))


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('tokens', lazy='dynamic'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= datetime.utcnow()
