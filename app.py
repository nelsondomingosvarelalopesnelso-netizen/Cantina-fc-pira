import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "cantina-fc-pira-2026"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://neondb_owner:npg_VS5JzKpOFQ3e@ep-wild-cloud-b4vl2kuk-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    preco_compra = db.Column(db.Float, default=0)
    quantidade = db.Column(db.Integer, default=0)

class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    produto = db.relationship("Produto")

class FechamentoDia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    data = db.Column(db.Date, nullable=False)
    total_bruto = db.Column(db.Float, nullable=False)
    total_liquido = db.Column(db.Float, nullable=False)
    caixa = db.Column(db.Float, nullable=False)
    qtd_vendas = db.Column(db.Integer, nullable=False)
    data_fechamento = db.Column(db.DateTime, default=datetime.utcnow)

class Caixa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    valor = db.Column(db.Float, default=0)

class Compra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)

class Resto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)

TEMPLATE = """<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Cantina FC Pira</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
        body { background: #f5f5f5; }
        .topbar { background: #1565c0; color: white; padding: 12px; }
        .nav { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
        .nav a { background: rgba(255,255,255,0.2); color: white; padding: 6px 10px; border-radius: 16px; text-decoration: none; font-size: 0.8rem; }
        .container { max-width: 900px; margin: 0 auto; padding: 12px; }
        .card { background: white; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
        input, button { width: 100%; padding: 10px; margin: 4px 0; border-radius: 8px; border: 1px solid #ccc; }
        button { background: #1565c0; color: white; border: none; }
        .btn-verde { background: #00c853; }
        .btn-laranja { background: #ff9800; }
        .btn-vermelho { background: #d32f2f; }
        .btn-pequeno { width: auto; padding: 6px 10px; font-size: 12px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 10px; }
        .produto-box { border: 2px solid #bbdefb; border-radius: 10px; padding: 10px; text-align: center; }
        .stat { background: white; border-radius: 10px; padding: 12px; text-align: center; border-top: 4px solid #1565c0; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; border-bottom: 1px solid #eee; text-align: left; }
    </style>
</head>
<body>
{% if session.get('user_id') %}
<div class="topbar">
    <h1>Cantina FC Pira</h1>
    <div class="nav">
        <a href="/">Vender</a>
        <a href="/dashboard">Dashboard</a>
        <a href="/hoje">Hoje</a>
        <a href="/relatorio">Relatório</a>
        <a href="/caixa">Caixa</a>
        <a href="/produtos">Produtos</a>
        <a href="/stock">Stock</a>
        <a href="/compras">Compras</a>
        <a href="/restos">Restos</a>
        <a href="/logout">Sair</a>
    </div>
</div>
{% endif %}
<div class="container">
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for cat, msg in messages %}
                <div class="card" style="background:#e8f5e9;">{{ msg }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    {{ content|safe }}
</div>
</body>
</html>"""

def dia_fechado(user_id):
    return FechamentoDia.query.filter_by(user_id=user_id, data=date.today()).first() is not None

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if dia_fechado(session["user_id"]):
        content = '<div class="card">Dia finalizado.<form method="POST" action="/reiniciar"><button class="btn-laranja">Reiniciar</button></form></div>'
        return render_template_string(TEMPLATE, content=content)
    busca =