from flask import Flask, render_template_string, request, redirect, url_for, session, flash, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import csv, io, base64, json
from PIL import Image
from calendar import monthrange

app = Flask(__name__)
app.secret_key = "cantina-2026"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://neondb_owner:npg_VS5JzKpOFQ3e@ep-wild-cloud-b4vl2kuk-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ==================== MODELS ====================
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), default="funcionario")
    foto = db.Column(db.Text, default="")
    perm_historico = db.Column(db.Boolean, default=False)
    perm_relatorio = db.Column(db.Boolean, default=False)
    perm_lucro = db.Column(db.Boolean, default=False)
    perm_produtos = db.Column(db.Boolean, default=False)
    perm_stock = db.Column(db.Boolean, default=False)
    perm_caixa = db.Column(db.Boolean, default=False)
    perm_hoje = db.Column(db.Boolean, default=False)
    perm_compras = db.Column(db.Boolean, default=False)
    perm_restos = db.Column(db.Boolean, default=False)
    perm_categorias = db.Column(db.Boolean, default=False)
    perm_mensagens = db.Column(db.Boolean, default=True)
    perm_resumo = db.Column(db.Boolean, default=True)

class Alerta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    mensagem = db.Column(db.Text)
    tipo = db.Column(db.String(50))
    data = db.Column(db.DateTime, default=datetime.utcnow)
    fechado = db.Column(db.Boolean, default=False)
    data_fechado = db.Column(db.DateTime)
    usuario = db.relationship("Usuario")

class Mensagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    de_user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    para_user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    texto = db.Column(db.Text)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    lida = db.Column(db.Boolean, default=False)
    de_user = db.relationship("Usuario", foreign_keys=[de_user_id])
    para_user = db.relationship("Usuario", foreign_keys=[para_user_id])

class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    preco_compra = db.Column(db.Float, default=0)
    unidades_caixa = db.Column(db.Integer, default=1)
    quantidade = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=5)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"))
    categoria = db.relationship("Categoria")

class HistoricoPreco(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"))
    preco_antigo = db.Column(db.Float)
    preco_novo = db.Column(db.Float)
    preco_compra_antigo = db.Column(db.Float)
    preco_compra_novo = db.Column(db.Float)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    produto = db.relationship("Produto")

class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    quantidade = db.Column(db.Integer)
    valor_total = db.Column(db.Float)
    lucro = db.Column(db.Float, default=0)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    produto = db.relationship("Produto")
    usuario = db.relationship("Usuario")

class FechamentoDia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    data = db.Column(db.Date)
    total_bruto = db.Column(db.Float)
    total_liquido = db.Column(db.Float)
    total_lucro = db.Column(db.Float, default=0)
    caixa = db.Column(db.Float)
    qtd_vendas = db.Column(db.Integer)
    meta_atingida = db.Column(db.Boolean, default=False)
    meta_lucro_atingida = db.Column(db.Boolean, default=False)
    nota = db.Column(db.Text)
    data_fechamento = db.Column(db.DateTime, default=datetime.utcnow)

class Caixa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Float, default=0)

class Compra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float)
    data = db.Column(db.DateTime, default=datetime.utcnow)

class Resto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float)
    data = db.Column(db.DateTime, default=datetime.utcnow)

META_VENDA = 48000
META_LUCRO = 15000

# ==================== TEMPLATE ====================
T = r"""<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cantina FC Pira</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
:root{--blue:#1565c0;--blue2:#1976d2;--blue-light:#e3f2fd;--green:#2e7d32;--orange:#ef6c00;--red:#c62828;--purple:#6a1b9a;--bg:#f0f4f8;--card:#fff;--text:#1e293b;--muted:#64748b;--sidebar:#0d47a1;--sidebar-w:240px}
body{background:var(--bg);color:var(--text);min-height:100vh}
body.dark{--bg:#0f172a;--card:#1e293b;--text:#e2e8f0;--muted:#94a3b8;--blue-light:#1e3a5f}
a{color:inherit}

/* LAYOUT */
.app{display:flex;min-height:100vh}
.sidebar{display:none;width:var(--sidebar-w);background:linear-gradient(180deg,#0d47a1,#1565c0);color:#fff;flex-shrink:0;flex-direction:column;padding:16px 12px;position:fixed;top:0;left:0;bottom:0;z-index:100;overflow-y:auto}
.sidebar .brand{font-size:1.15rem;font-weight:700;padding:8px 12px 20px;letter-spacing:.3px}
.sidebar .nav-item{display:block;padding:10px 14px;border-radius:10px;text-decoration:none;color:rgba(255,255,255,.9);font-size:.85rem;font-weight:500;margin-bottom:4px;transition:background .15s}
.sidebar .nav-item:hover,.sidebar .nav-item.active{background:rgba(255,255,255,.18)}
.sidebar .nav-section{font-size:.7rem;text-transform:uppercase;opacity:.6;padding:14px 14px 6px;letter-spacing:.5px}
.main{flex:1;min-width:0}
.topbar{background:linear-gradient(135deg,#0d47a1,#1976d2);color:#fff;padding:12px 16px;position:sticky;top:0;z-index:50}
.topbar h1{font-size:1.1rem;font-weight:700}
.topbar .user{font-size:.75rem;opacity:.9;margin-top:2px}
.top-nav{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}
.top-nav a{background:rgba(255,255,255,.15);color:#fff;padding:6px 12px;border-radius:16px;text-decoration:none;font-size:.72rem;font-weight:500;border:1px solid rgba(255,255,255,.2)}
.content{max-width:1100px;margin:0 auto;padding:16px}

@media(min-width:900px){
  .sidebar{display:flex}
  .main{margin-left:var(--sidebar-w)}
  .topbar .top-nav{display:none}
  .topbar{background:var(--card);color:var(--text);border-bottom:1px solid #e2e8f0;box-shadow:0 1px 3px rgba(0,0,0,.06)}
  body.dark .topbar{background:var(--card);border-color:#334155}
  .topbar h1{color:var(--blue)}
  body.dark .topbar h1{color:#90caf9}
  .topbar .user{color:var(--muted)}
}

/* CARDS & UI */
.card{background:var(--card);border-radius:14px;padding:18px;margin-bottom:14px;box-shadow:0 2px 12px rgba(15,23,42,.06);border:1px solid rgba(0,0,0,.04)}
.card h2{font-size:1rem;margin-bottom:12px;color:var(--blue);font-weight:700}
body.dark .card{border-color:rgba(255,255,255,.06)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px}
.grid-2{display:grid;grid-template-columns:1fr;gap:14px}
@media(min-width:700px){.grid-2{grid-template-columns:1fr 1fr}}
.stat{background:var(--card);border-radius:14px;padding:16px;box-shadow:0 2px 10px rgba(15,23,42,.06);border-top:3px solid var(--blue);position:relative}
.stat .label{font-size:.75rem;color:var(--muted);font-weight:500}
.stat b{display:block;font-size:1.45rem;margin-top:6px;font-weight:800;color:var(--text)}
.stat .sub{font-size:.7rem;color:var(--muted);margin-top:4px}
.stat.venda{border-top-color:#1565c0}.stat.venda b{color:#1565c0}
.stat.lucro{border-top-color:#2e7d32}.stat.lucro b{color:#2e7d32}
.stat.caixa{border-top-color:#ef6c00}.stat.caixa b{color:#ef6c00}
.stat.nvendas{border-top-color:#6a1b9a}.stat.nvendas b{color:#6a1b9a}
.stat.compras{border-top-color:#00838f}.stat.compras b{color:#00838f}
.stat.restos{border-top-color:#d84315}.stat.restos b{color:#d84315}
.stat.stock{border-top-color:#c62828}.stat.stock b{color:#c62828}
.stat.meta{border-top-color:#00897b}.stat.meta b{color:#00897b}
.stat.mes{border-top-color:#5c6bc0}.stat.mes b{color:#5c6bc0}
.up{color:#2e7d32;font-weight:600}.down{color:#c62828;font-weight:600}
.progress{height:8px;background:#e2e8f0;border-radius:8px;margin-top:8px;overflow:hidden}
.progress-bar{height:100%;border-radius:8px;background:linear-gradient(90deg,#1565c0,#42a5f5)}
.progress-bar.green{background:linear-gradient(90deg,#2e7d32,#66bb6a)}
.progress-bar.orange{background:linear-gradient(90deg,#ef6c00,#ffb74d)}

input,select,textarea,button{width:100%;padding:10px 12px;margin:4px 0;border-radius:10px;border:1px solid #cbd5e1;font-size:14px}
body.dark input,body.dark select,body.dark textarea{background:#0f172a;color:#e2e8f0;border-color:#334155}
button{background:linear-gradient(135deg,#1565c0,#1976d2);color:#fff;border:none;font-weight:600;cursor:pointer}
button:hover{opacity:.92}
.g{background:linear-gradient(135deg,#2e7d32,#43a047)!important}
.o{background:linear-gradient(135deg,#ef6c00,#fb8c00)!important}
.r{background:linear-gradient(135deg,#c62828,#e53935)!important}
.s{width:auto;padding:6px 10px;font-size:12px;margin:2px}
.btn{display:inline-block;padding:7px 12px;border-radius:10px;text-decoration:none;font-size:12px;font-weight:600;margin:2px;color:#fff;background:linear-gradient(135deg,#1565c0,#1976d2)}
.btn-green{background:linear-gradient(135deg,#2e7d32,#43a047)}.btn-orange{background:linear-gradient(135deg,#ef6c00,#fb8c00)}
.btn-red{background:linear-gradient(135deg,#c62828,#e53935)}.btn-purple{background:linear-gradient(135deg,#6a1b9a,#8e24aa)}
.btn-blue{background:linear-gradient(135deg,#1565c0,#1976d2)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:var(--blue-light);padding:9px;text-align:left;font-weight:600}
td{padding:8px;border-bottom:1px solid #e2e8f0}
body.dark th{background:#1e3a5f} body.dark td{border-color:#334155}
.flash{background:#e8f5e9;padding:10px 14px;border-radius:10px;margin-bottom:12px;font-size:.85rem}
.alerta{background:#ffebee;color:#c62828;padding:10px 14px;border-radius:10px;margin-bottom:12px;font-size:.85rem}
.parabens{background:linear-gradient(135deg,#2e7d32,#66bb6a);color:#fff;padding:20px;border-radius:14px;text-align:center;margin-bottom:14px}
.box{background:var(--card);border:1px solid #e2e8f0;border-radius:12px;padding:12px;text-align:center}
.box.destaque{border:2px solid #ff9800;background:#fff8e1}
.box b{display:block;color:var(--blue);margin-bottom:3px}
.box div{font-size:.75rem;color:var(--muted);margin:2px 0}
.grid-prod{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px}
.qty{width:56px!important;padding:6px;text-align:center;display:inline-block;margin:0 2px}
.lucro{color:#2e7d32;font-weight:700}.lucro-baixo{color:#c62828;font-weight:700}
.bemvindo{background:linear-gradient(135deg,#1565c0,#42a5f5);color:#fff;padding:16px;border-radius:14px;margin-bottom:14px}
.bemvindo.alerta-msg{background:linear-gradient(135deg,#ef6c00,#ff9800)}
.bemvindo h3{margin-bottom:6px}.bemvindo ul{margin:8px 0 0 18px;font-size:.9rem}
.bemvindo button{width:auto;margin-top:8px;background:#fff;color:#1565c0}
.avatar{width:34px;height:34px;border-radius:50%;object-fit:cover;background:#1565c0;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:.85rem}
.calc-float{position:fixed;top:70px;right:16px;width:270px;background:var(--card);border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,.2);z-index:1000;display:none;padding:12px}
.calc-float.show{display:block}
.calc-display{background:#1e293b;color:#fff;font-size:1.3rem;text-align:right;padding:12px;border-radius:10px;margin-bottom:8px;min-height:44px}
.calc-buttons{display:grid;grid-template-columns:repeat(4,1fr);gap:5px}
.calc-buttons button{font-size:.9rem;padding:10px;border-radius:8px}
.calc-buttons .op{background:linear-gradient(135deg,#ef6c00,#fb8c00)!important}
.calc-buttons .eq{background:linear-gradient(135deg,#2e7d32,#43a047)!important}
.calc-buttons .clear{background:linear-gradient(135deg,#c62828,#e53935)!important}
.calc-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.calc-header span{font-weight:700;color:var(--blue)}
.calc-close{background:none;border:none;font-size:1.2rem;cursor:pointer;color:var(--muted);width:auto;padding:0}
.filtro{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.filtro a{padding:6px 12px;background:var(--blue-light);border-radius:16px;text-decoration:none;color:var(--blue);font-size:.8rem}
.filtro a.ativo{background:var(--blue);color:#fff}
.chart-wrap{position:relative;height:200px;margin-top:8px}
.msg{padding:10px 12px;border-radius:12px;margin:6px 0;max-width:80%}
.msg.mine{background:#e3f2fd;margin-left:auto}.msg.other{background:#f1f5f9}
.resumo-item{padding:10px 0;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between}
.alerta-item{display:flex;gap:12px;align-items:flex-start;padding:12px;border-bottom:1px solid #e2e8f0}
.welcome-banner{background:linear-gradient(135deg,#0d47a1,#1976d2);color:#fff;border-radius:16px;padding:20px;margin-bottom:16px}
.welcome-banner h2{font-size:1.25rem;margin-bottom:4px}
.welcome-banner p{opacity:.9;font-size:.9rem}
</style>
</head>
<body id="body">
{% if session.get('user_id') %}
<div class="app">
  <aside class="sidebar">
    <div class="brand">Cantina FC Pira</div>
    <a class="nav-item" href="/">Vender</a>
    <a class="nav-item" href="/dashboard">Dashboard</a>
    {% if session.get('perm_resumo') or session.get('tipo')=='admin' %}<a class="nav-item" href="/resumo">Resumo do Dia</a>{% endif %}
    {% if session.get('perm_mensagens') or session.get('tipo')=='admin' %}<a class="nav-item" href="/mensagens">Mensagens</a>{% endif %}
    <a class="nav-item" href="/alertas">Alertas</a>
    <div class="nav-section">Gestão</div>
    {% if session.get('tipo')=='admin' or session.get('perm_hoje') %}<a class="nav-item" href="/hoje">Hoje</a>{% endif %}
    {% if session.get('tipo')=='admin' or session.get('perm_historico') %}<a class="nav-item" href="/historico">Histórico</a>{% endif %}
    {% if session.get('tipo')=='admin' or session.get('perm_relatorio') %}<a class="nav-item" href="/relatorio">Relatório</a>{% endif %}
    {% if session.get('tipo')=='admin' or session.get('perm_lucro') %}<a class="nav-item" href="/lucro">Lucro</a>{% endif %}
    {% if session.get('tipo')=='admin' or session.get('perm_caixa') %}<a class="nav-item" href="/caixa">Caixa</a>{% endif %}
    {% if session.get('tipo')=='admin' or session.get('perm_produtos') %}<a class="nav-item" href="/produtos">Produtos</a>{% endif %}
    {% if session.get('tipo')=='admin' or session.get('perm_stock') %}<a class="nav-item" href="/stock">Stock</a>{% endif %}
    {% if session.get('tipo')=='admin' or session.get('perm_compras') %}<a class="nav-item" href="/compras">Compras</a>{% endif %}
    {% if session.get('tipo')=='admin' or session.get('perm_restos') %}<a class="nav-item" href="/restos">Restos</a>{% endif %}
    {% if session.get('tipo')=='admin' or session.get('perm_categorias') %}<a class="nav-item" href="/categorias">Categorias</a>{% endif %}
    {% if session.get('tipo')=='admin' %}
    <div class="nav-section">Admin</div>
    <a class="nav-item" href="/utilizadores">Utilizadores</a>
    <a class="nav-item" href="/mensal">Mensal</a>
    <a class="nav-item" href="/ranking">Ranking</a>
    <a class="nav-item" href="/horas">Horas de Pico</a>
    <a class="nav-item" href="/valor-stock">Valor em Stock</a>
    <a class="nav-item" href="/exportar">Exportar</a>
    {% endif %}
    <div class="nav-section">Outros</div>
    <a class="nav-item" href="#" onclick="toggleCalc();return false;">Calculadora</a>
    <a class="nav-item" href="#" onclick="toggleDark();return false;">Modo claro/escuro</a>
    <a class="nav-item" href="/logout">Sair</a>
  </aside>
  <div class="main">
    <div class="topbar">
      <h1>Cantina FC Pira</h1>
      <div class="user">{{ session.get('nome','') }}</div>
      <div class="top-nav">
        <a href="/">Vender</a><a href="/dashboard">Dashboard</a>
        {% if session.get('perm_resumo') or session.get('tipo')=='admin' %}<a href="/resumo">Resumo</a>{% endif %}
        {% if session.get('perm_mensagens') or session.get('tipo')=='admin' %}<a href="/mensagens">Mensagens</a>{% endif %}
        <a href="/alertas">Alertas</a>
        {% if session.get('tipo')=='admin' %}
        <a href="/hoje">Hoje</a><a href="/historico">Histórico</a><a href="/relatorio">Relatório</a><a href="/lucro">Lucro</a>
        <a href="/caixa">Caixa</a><a href="/produtos">Produtos</a><a href="/stock">Stock</a><a href="/compras">Compras</a>
        <a href="/restos">Restos</a><a href="/categorias">Categorias</a><a href="/utilizadores">Utilizadores</a>
        <a href="/mensal">Mensal</a><a href="/ranking">Ranking</a><a href="/horas">Horas</a><a href="/valor-stock">Valor Stock</a><a href="/exportar">Exportar</a>
        {% else %}
        {% if session.get('perm_hoje') %}<a href="/hoje">Hoje</a>{% endif %}
        {% if session.get('perm_historico') %}<a href="/historico">Histórico</a>{% endif %}
        {% if session.get('perm_relatorio') %}<a href="/relatorio">Relatório</a>{% endif %}
        {% if session.get('perm_lucro') %}<a href="/lucro">Lucro</a>{% endif %}
        {% if session.get('perm_caixa') %}<a href="/caixa">Caixa</a>{% endif %}
        {% if session.get('perm_produtos') %}<a href="/produtos">Produtos</a>{% endif %}
        {% if session.get('perm_stock') %}<a href="/stock">Stock</a>{% endif %}
        {% if session.get('perm_compras') %}<a href="/compras">Compras</a>{% endif %}
        {% if session.get('perm_restos') %}<a href="/restos">Restos</a>{% endif %}
        {% if session.get('perm_categorias') %}<a href="/categorias">Categorias</a>{% endif %}
        {% endif %}
        <a href="#" onclick="toggleCalc();return false;">Calc</a>
        <a href="#" onclick="toggleDark();return false;">Modo</a>
        <a href="/logout">Sair</a>
      </div>
    </div>
    <div class="content">
{% endif %}
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}{% for cat, msg in messages %}<div class="flash">{{ msg }}</div>{% endfor %}{% endif %}
{% endwith %}
{{ content|safe }}
{% if session.get('user_id') %}
    </div>
  </div>
</div>
{% endif %}
<div class="calc-float" id="calcFloat">
  <div class="calc-header"><span>Calculadora</span><button class="calc-close" onclick="toggleCalc()">×</button></div>
  <div class="calc-display" id="display">0</div>
  <div class="calc-buttons">
    <button onclick="clearD()" class="clear">C</button><button onclick="back()">&lt;-</button>
    <button onclick="add('/')" class="op">/</button><button onclick="add('*')" class="op">×</button>
    <button onclick="add(7)">7</button><button onclick="add(8)">8</button><button onclick="add(9)">9</button><button onclick="add('-')" class="op">-</button>
    <button onclick="add(4)">4</button><button onclick="add(5)">5</button><button onclick="add(6)">6</button><button onclick="add('+')" class="op">+</button>
    <button onclick="add(1)">1</button><button onclick="add(2)">2</button><button onclick="add(3)">3</button><button onclick="calc()" class="eq">=</button>
    <button onclick="add(0)" style="grid-column:span 2">0</button><button onclick="add('.')">.</button>
  </div>
</div>
<script>
function toggleDark(){document.getElementById('body').classList.toggle('dark');localStorage.setItem('dark',document.getElementById('body').classList.contains('dark'))}
if(localStorage.getItem('dark')==='true')document.getElementById('body').classList.add('dark')
function toggleCalc(){document.getElementById('calcFloat').classList.toggle('show')}
function add(v){var d=document.getElementById('display');if(d.innerText==='0'&&v!=='.')d.innerText=v;else d.innerText+=v}
function clearD(){document.getElementById('display').innerText='0'}
function back(){var d=document.getElementById('display');d.innerText=d.innerText.slice(0,-1)||'0'}
function calc(){try{document.getElementById('display').innerText=eval(document.getElementById('display').innerText)}catch(e){document.getElementById('display').innerText='Erro'}}
</script>
</body></html>
"""

# ==================== HELPERS ====================
def is_admin():
    return session.get("tipo") == "admin"

def tem_perm(perm):
    if is_admin(): return True
    return session.get(perm, False)

def dia_fechado(uid):
    return FechamentoDia.query.filter_by(user_id=uid, data=date.today()).first() is not None

def calcular_lucro_unidade(preco, preco_compra, unidades_caixa):
    if preco_compra and unidades_caixa and unidades_caixa > 0:
        return preco - (preco_compra / unidades_caixa)
    return 0

def calcular_custo_unidade(preco_compra, unidades_caixa):
    if preco_compra and unidades_caixa and unidades_caixa > 0:
        return preco_compra / unidades_caixa
    return 0

def get_caixa():
    c = Caixa.query.first()
    if not c:
        c = Caixa(valor=0)
        db.session.add(c)
        db.session.commit()
    return c

def foto_html(user):
    if user and user.foto:
        return f'<img src="data:image/jpeg;base64,{user.foto}" class="avatar" alt="">'
    inicial = user.nome[0].upper() if user else "?"
    return f'<div class="avatar">{inicial}</div>'

def processar_foto(ficheiro):
    try:
        img = Image.open(ficheiro.stream)
        img.thumbnail((300, 300))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=70)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        print("Erro foto:", e)
        return ""

def limpar_mensagens_antigas():
    limite = datetime.utcnow() - timedelta(days=7)
    Mensagem.query.filter(Mensagem.data < limite).delete()
    db.session.commit()

def vendas_do_dia(uid=None, dia=None):
    if dia is None:
        dia = date.today()
    q = Venda.query.filter(db.func.date(Venda.data) == dia)
    if uid is not None:
        q = q.filter(Venda.user_id == uid)
    return q.all()

def vendas_periodo(uid, inicio, fim):
    q = Venda.query.filter(Venda.data >= datetime.combine(inicio, datetime.min.time()),
                           Venda.data <= datetime.combine(fim, datetime.max.time()))
    if uid is not None:
        q = q.filter(Venda.user_id == uid)
    return q.all()

def pct_change(atual, anterior):
    if not anterior:
        return 0
    return round((atual - anterior) / anterior * 100, 1)

def gerar_alertas(uid):
    if is_admin(): return ""
    user = Usuario.query.get(uid)
    if not user: return ""
    hoje = date.today()
    hora = datetime.now().hour
    baixos = Produto.query.filter(Produto.quantidade <= Produto.stock_minimo).count()
    fechado = dia_fechado(uid)
    alertas, tipo = [], "info"
    if baixos > 0:
        alertas.append(f"Atenção: tens {baixos} produto(s) com stock baixo.")
        tipo = "alerta"
    if hora >= 16 and not fechado:
        alertas.append("Lembra-te: no final do dia vai a Hoje e clica em Finalizar Dia.")
    if not alertas: return ""
    for msg in alertas:
        existe = Alerta.query.filter_by(user_id=uid, mensagem=msg).filter(db.func.date(Alerta.data)==hoje).first()
        if not existe:
            db.session.add(Alerta(user_id=uid, mensagem=msg, tipo=tipo))
    db.session.commit()
    abertos = Alerta.query.filter_by(user_id=uid, fechado=False).filter(db.func.date(Alerta.data)==hoje).all()
    if not abertos: return ""
    classe = "bemvindo alerta-msg" if tipo == "alerta" else "bemvindo"
    lista = "".join(f"<li>{a.mensagem}</li>" for a in abertos)
    ids = ",".join(str(a.id) for a in abertos)
    return f'<div class="{classe}" id="bemvindo"><h3>Olá {user.nome}!</h3><ul>{lista}</ul><form method="POST" action="/fechar-alertas"><input type="hidden" name="ids" value="{ids}"><button type="submit">Entendi</button></form></div>'

# ==================== ROUTES (core) ====================
@app.route("/fechar-alertas", methods=["POST"])
def fechar_alertas():
    if "user_id" not in session: return redirect("/login")
    for i in request.form.get("ids", "").split(","):
        if i.strip():
            a = Alerta.query.get(int(i))
            if a and a.user_id == session["user_id"]:
                a.fechado = True
                a.data_fechado = datetime.utcnow()
    db.session.commit()
    return redirect(request.referrer or "/")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = Usuario.query.filter_by(email=request.form["email"]).first()
        if u and check_password_hash(u.senha, request.form["senha"]):
            session["user_id"] = u.id
            session["nome"] = u.nome
            session["tipo"] = u.tipo or "funcionario"
            for p in ["perm_historico","perm_relatorio","perm_lucro","perm_produtos","perm_stock","perm_caixa","perm_hoje","perm_compras","perm_restos","perm_categorias","perm_mensagens","perm_resumo"]:
                session[p] = getattr(u, p) or False
            return redirect("/dashboard")
        flash("Email ou senha incorretos")
    return render_template_string(T, content='<div class="card" style="max-width:380px;margin:40px auto"><h2>Entrar – Cantina FC Pira</h2><form method="POST"><input type="email" name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button>Entrar</button></form></div>')

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/")
def index():
    if "user_id" not in session: return redirect(url_for("login"))
    uid = session["user_id"]
    if not is_admin() and dia_fechado(uid):
        return render_template_string(T, content='<div class="card">Dia finalizado<form method="POST" action="/reiniciar"><button class="o">Reiniciar turno</button></form></div>')
    busca = request.args.get("busca", "")
    cat_id = request.args.get("categoria", "")
    q = Produto.query
    if busca: q = q.filter(Produto.nome.ilike("%"+busca+"%"))
    if cat_id: q = q.filter(Produto.categoria_id == int(cat_id))
    inicio = date.today() - timedelta(days=7)
    top = db.session.query(Venda.produto_id, db.func.sum(Venda.quantidade).label("q")).filter(Venda.data >= inicio).group_by(Venda.produto_id).order_by(db.text("q desc")).limit(5).all()
    top_ids = [t[0] for t in top]
    boxes = ""
    for p in q.order_by(Produto.nome).all():
        cls = "box destaque" if p.id in top_ids else "box"
        lucro_un = calcular_lucro_unidade(p.preco, p.preco_compra or 0, p.unidades_caixa or 1)
        custo_un = calcular_custo_unidade(p.preco_compra or 0, p.unidades_caixa or 1)
        lucro_cls = "lucro" if lucro_un > 0 else "lucro-baixo"
        boxes += f'<div class="{cls}"><b>{p.nome}</b>'
        if p.categoria: boxes += f'<div style="color:#1976d2;font-size:.7rem">{p.categoria.nome}</div>'
        boxes += f'<div>Venda: Kz {int(p.preco)}</div><div>Custo/un: Kz {int(custo_un)}</div>'
        boxes += f'<div class="{lucro_cls}">Lucro: Kz {int(lucro_un)}</div><div>Stock: {p.quantidade}</div>'
        boxes += f'<form method="POST" action="/vender" style="margin-top:6px"><input type="hidden" name="produto_id" value="{p.id}">'
        boxes += f'<input type="number" name="quantidade" class="qty" value="1" min="1" max="{p.quantidade}"><button class="g s">Vender</button></form>'
        if is_admin():
            boxes += f'<form method="POST" action="/devolver/{p.id}"><button class="o s">Devolver</button></form>'
            boxes += f'<form method="POST" action="/eliminar/{p.id}"><button class="r s">Eliminar</button></form>'
        boxes += '</div>'
    cats = Categoria.query.all()
    sel = '<select name="categoria" onchange="this.form.submit()"><option value="">Todas</option>'
    for c in cats:
        sel += f'<option value="{c.id}"{" selected" if str(c.id)==cat_id else ""}>{c.nome}</option>'
    sel += '</select>'
    alertas = ""
    if is_admin():
        baixos = Produto.query.filter(Produto.quantidade <= Produto.stock_minimo).all()
        if baixos:
            alertas = '<div class="alerta">Stock baixo: '+", ".join(f"{p.nome} ({p.quantidade})" for p in baixos)+'</div>'
    return render_template_string(T, content=gerar_alertas(uid)+alertas+f'<div class="card"><h2>Vender</h2><form method="GET"><input name="busca" placeholder="Pesquisar..." value="{busca}">{sel}<button>Pesquisar</button></form><div class="grid-prod">{boxes}</div></div>')

@app.route("/vender", methods=["POST"])
def vender():
    if "user_id" not in session: return redirect("/login")
    uid = session["user_id"]
    if not is_admin() and dia_fechado(uid): return redirect("/")
    p = Produto.query.get(int(request.form["produto_id"]))
    qtd = int(request.form.get("quantidade", 1))
    if p and qtd > 0 and p.quantidade >= qtd:
        custo_un = calcular_custo_unidade(p.preco_compra or 0, p.unidades_caixa or 1)
        lucro_total = (p.preco - custo_un) * qtd
        db.session.add(Venda(produto_id=p.id, user_id=uid, quantidade=qtd, valor_total=p.preco*qtd, lucro=lucro_total))
        p.quantidade -= qtd
        db.session.commit()
        flash(f"Vendido {qtd}x {p.nome}")
    else:
        flash("Stock insuficiente")
    return redirect("/")

@app.route("/devolver/<int:id>", methods=["POST"])
def devolver(id):
    if not is_admin(): return redirect("/")
    p = Produto.query.get_or_404(id)
    v = Venda.query.filter_by(produto_id=id).order_by(Venda.data.desc()).first()
    if v:
        p.quantidade += v.quantidade
        db.session.delete(v)
        db.session.commit()
    return redirect("/")

@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    if not is_admin(): return redirect("/")
    db.session.delete(Produto.query.get_or_404(id))
    db.session.commit()
    return redirect("/")

@app.route("/reiniciar", methods=["POST"])
def reiniciar():
    if "user_id" not in session: return redirect("/login")
    FechamentoDia.query.filter_by(user_id=session["user_id"], data=date.today()).delete()
    db.session.commit()
    return redirect("/")

# ==================== DASHBOARD COM INDICADORES ====================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect("/login")
    uid_session = session["user_id"]
    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    inicio_mes = hoje.replace(day=1)
    if hoje.month == 1:
        inicio_mes_ant = date(hoje.year-1, 12, 1)
        fim_mes_ant = date(hoje.year-1, 12, 31)
    else:
        inicio_mes_ant = date(hoje.year, hoje.month-1, 1)
        fim_mes_ant = date(hoje.year, hoje.month-1, monthrange(hoje.year, hoje.month-1)[1])

    filtro = None if is_admin() else uid_session
    v_hoje = vendas_do_dia(filtro, hoje)
    v_ontem = vendas_do_dia(filtro, ontem)
    v_mes = vendas_periodo(filtro, inicio_mes, hoje)
    v_mes_ant = vendas_periodo(filtro, inicio_mes_ant, fim_mes_ant)

    bruto_hoje = sum(v.valor_total for v in v_hoje)
    lucro_hoje = sum(v.lucro or 0 for v in v_hoje)
    bruto_ontem = sum(v.valor_total for v in v_ontem)
    lucro_ontem = sum(v.lucro or 0 for v in v_ontem)
    bruto_mes = sum(v.valor_total for v in v_mes)
    lucro_mes = sum(v.lucro or 0 for v in v_mes)
    bruto_mes_ant = sum(v.valor_total for v in v_mes_ant)
    lucro_mes_ant = sum(v.lucro or 0 for v in v_mes_ant)

    cv = get_caixa().valor
    total_compras = sum(c.valor for c in Compra.query.all())
    total_restos = sum(r.valor for r in Resto.query.all())
    compras_mes = sum(c.valor for c in Compra.query.filter(Compra.data >= datetime.combine(inicio_mes, datetime.min.time())).all())
    baixos = Produto.query.filter(Produto.quantidade <= Produto.stock_minimo).count()
    valor_stock = sum(calcular_custo_unidade(p.preco_compra or 0, p.unidades_caixa or 1) * p.quantidade for p in Produto.query.all())

    pct_venda = pct_change(bruto_mes, bruto_mes_ant)
    pct_lucro = pct_change(lucro_mes, lucro_mes_ant)
    meta_pct = min(100, int(bruto_hoje / META_VENDA * 100)) if META_VENDA else 0
    meta_lucro_pct = min(100, int(lucro_hoje / META_LUCRO * 100)) if META_LUCRO else 0

    # Últimos 7 dias para gráfico de barras
    labels_7, data_7, data_lucro_7 = [], [], []
    for i in range(6, -1, -1):
        d = hoje - timedelta(days=i)
        vs = vendas_do_dia(filtro, d)
        labels_7.append(d.strftime("%d/%m"))
        data_7.append(round(sum(v.valor_total for v in vs), 0))
        data_lucro_7.append(round(sum(v.lucro or 0 for v in vs), 0))

    # Pizza: top produtos do mês
    por_prod = {}
    for v in v_mes:
        n = v.produto.nome if v.produto else "?"
        por_prod[n] = por_prod.get(n, 0) + v.valor_total
    top_prod = sorted(por_prod.items(), key=lambda x: x[1], reverse=True)[:6]
    pie_labels = [t[0][:18] for t in top_prod] or ["Sem dados"]
    pie_data = [round(t[1], 0) for t in top_prod] or [0]

    # Pizza composição: vendas vs lucro vs compras do mês (visão geral)
    comp_labels = ["Vendas mês", "Lucro mês", "Compras mês"]
    comp_data = [round(bruto_mes,0), round(lucro_mes,0), round(compras_mes,0)]

    meta_msg = ""
    if bruto_hoje >= META_VENDA:
        meta_msg += '<div class="parabens"><h3>Parabéns!</h3><p>Meta de vendas atingida!</p></div>'
    if lucro_hoje >= META_LUCRO:
        meta_msg += '<div class="parabens"><h3>Parabéns!</h3><p>Meta de lucro atingida!</p></div>'

    por_func = ""
    if is_admin():
        todas = vendas_do_dia(None, hoje)
        por_user = {}
        for v in todas:
            nome = v.usuario.nome if v.usuario else "—"
            if nome not in por_user:
                por_user[nome] = {"valor": 0, "qtd": 0, "lucro": 0}
            por_user[nome]["valor"] += v.valor_total
            por_user[nome]["qtd"] += 1
            por_user[nome]["lucro"] += v.lucro or 0
        if por_user:
            linhas = "".join(f"<tr><td>{n}</td><td>{d['qtd']}</td><td>Kz {int(d['valor'])}</td><td>Kz {int(d['lucro'])}</td></tr>" for n,d in por_user.items())
            por_func = f'<div class="card"><h2>Vendas por Funcionário (Hoje)</h2><table><tr><th>Funcionário</th><th>Nº</th><th>Total</th><th>Lucro</th></tr>{linhas}</table></div>'

    botao_r = ""
    if is_admin():
        botao_r = '<form method="POST" action="/reiniciar-dashboard" style="margin-top:12px"><button class="r">Reiniciar vendas de hoje</button></form>'

    nome = session.get("nome", "")
    titulo_v = "As minhas vendas" if not is_admin() else "Vendas hoje"
    cls_pv = "up" if pct_venda >= 0 else "down"
    cls_pl = "up" if pct_lucro >= 0 else "down"
    seta_v = "↑" if pct_venda >= 0 else "↓"
    seta_l = "↑" if pct_lucro >= 0 else "↓"

    html = gerar_alertas(uid_session) + meta_msg + f'''
    <div class="welcome-banner">
      <h2>Olá, {nome}</h2>
      <p>Visão geral da cantina · {hoje.strftime("%d/%m/%Y")}</p>
    </div>
    <div class="grid">
      <div class="stat venda"><div class="label">{titulo_v}</div><b>Kz {int(bruto_hoje)}</b><div class="sub">Ontem: Kz {int(bruto_ontem)}</div></div>
      <div class="stat lucro"><div class="label">Lucro hoje</div><b>Kz {int(lucro_hoje)}</b><div class="sub">Ontem: Kz {int(lucro_ontem)}</div></div>
      <div class="stat caixa"><div class="label">Caixa</div><b>Kz {int(cv)}</b></div>
      <div class="stat nvendas"><div class="label">Nº vendas</div><b>{len(v_hoje)}</b><div class="sub">Ontem: {len(v_ontem)}</div></div>
      <div class="stat mes"><div class="label">Vendas do mês</div><b>Kz {int(bruto_mes)}</b><div class="sub"><span class="{cls_pv}">{seta_v} {abs(pct_venda)}%</span> vs mês anterior</div></div>
      <div class="stat lucro"><div class="label">Lucro do mês</div><b>Kz {int(lucro_mes)}</b><div class="sub"><span class="{cls_pl}">{seta_l} {abs(pct_lucro)}%</span> vs mês anterior</div></div>
      <div class="stat compras"><div class="label">Total compras</div><b>Kz {int(total_compras)}</b><div class="sub">Este mês: Kz {int(compras_mes)}</div></div>
      <div class="stat restos"><div class="label">Total restos</div><b>Kz {int(total_restos)}</b></div>
      <div class="stat stock"><div class="label">Stock baixo</div><b>{baixos}</b></div>
      <div class="stat nvendas"><div class="label">Valor em stock</div><b>Kz {int(valor_stock)}</b></div>
      <div class="stat meta"><div class="label">Meta vendas ({META_VENDA} Kz)</div><b>{meta_pct}%</b>
        <div class="progress"><div class="progress-bar" style="width:{meta_pct}%"></div></div></div>
      <div class="stat meta"><div class="label">Meta lucro ({META_LUCRO} Kz)</div><b>{meta_lucro_pct}%</b>
        <div class="progress"><div class="progress-bar green" style="width:{meta_lucro_pct}%"></div></div></div>
    </div>

    <div class="grid-2" style="margin-top:14px">
      <div class="card">
        <h2>Vendas e lucro – últimos 7 dias</h2>
        <div class="chart-wrap"><canvas id="chart7"></canvas></div>
      </div>
      <div class="card">
        <h2>Top produtos do mês</h2>
        <div class="chart-wrap"><canvas id="chartPie"></canvas></div>
      </div>
    </div>
    <div class="grid-2">
      <div class="card">
        <h2>Composição do mês (vendas / lucro / compras)</h2>
        <div class="chart-wrap"><canvas id="chartComp"></canvas></div>
      </div>
      <div class="card">
        <h2>Resumo para análise</h2>
        <div class="resumo-item"><span>Vendas mês atual</span><b>Kz {int(bruto_mes)}</b></div>
        <div class="resumo-item"><span>Vendas mês anterior</span><b>Kz {int(bruto_mes_ant)}</b></div>
        <div class="resumo-item"><span>Lucro mês atual</span><b>Kz {int(lucro_mes)}</b></div>
        <div class="resumo-item"><span>Lucro mês anterior</span><b>Kz {int(lucro_mes_ant)}</b></div>
        <div class="resumo-item"><span>Compras este mês</span><b>Kz {int(compras_mes)}</b></div>
        <div class="resumo-item"><span>Resultado (vendas − compras mês)</span><b>Kz {int(bruto_mes - compras_mes)}</b></div>
      </div>
    </div>
    {por_func}
    {botao_r}
    <script>
    new Chart(document.getElementById('chart7'), {{
      type: 'bar',
      data: {{
        labels: {json.dumps(labels_7)},
        datasets: [
          {{ label: 'Vendas', data: {json.dumps(data_7)}, backgroundColor: '#1565c0' }},
          {{ label: 'Lucro', data: {json.dumps(data_lucro_7)}, backgroundColor: '#2e7d32' }}
        ]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
    }});
    new Chart(document.getElementById('chartPie'), {{
      type: 'doughnut',
      data: {{
        labels: {json.dumps(pie_labels)},
        datasets: [{{ data: {json.dumps(pie_data)}, backgroundColor: ['#1565c0','#2e7d32','#ef6c00','#6a1b9a','#00838f','#c62828'] }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
    }});
    new Chart(document.getElementById('chartComp'), {{
      type: 'pie',
      data: {{
        labels: {json.dumps(comp_labels)},
        datasets: [{{ data: {json.dumps(comp_data)}, backgroundColor: ['#1565c0','#2e7d32','#00838f'] }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
    }});
    </script>
    '''
    return render_template_string(T, content=html)

@app.route("/reiniciar-dashboard", methods=["POST"])
def reiniciar_dashboard():
    if not is_admin(): return redirect("/")
    Venda.query.filter(db.func.date(Venda.data)==date.today()).delete()
    db.session.commit()
    flash("Vendas de hoje apagadas do dashboard.")
    return redirect("/dashboard")

# ---- Restantes rotas (iguais à versão anterior, com filtro por funcionário) ----
@app.route("/hoje")
def hoje():
    if not tem_perm("perm_hoje"): return redirect("/")
    uid = None if is_admin() else session["user_id"]
    vendas = vendas_do_dia(uid)
    bruto = sum(v.valor_total for v in vendas)
    lucro = sum(v.lucro or 0 for v in vendas)
    extra_th = "<th>Funcionário</th>" if is_admin() else ""
    linhas = ""
    for v in vendas:
        vend = f"<td>{v.usuario.nome if v.usuario else '—'}</td>" if is_admin() else ""
        linhas += f"<tr><td>{v.produto.nome}</td><td>{v.quantidade}</td><td>Kz {int(v.valor_total)}</td><td>Kz {int(v.lucro or 0)}</td>{vend}</tr>"
    meta_msg = ""
    if bruto >= META_VENDA: meta_msg += '<div class="parabens"><h3>Parabéns!</h3><p>Meta de vendas!</p></div>'
    if lucro >= META_LUCRO: meta_msg += '<div class="parabens"><h3>Parabéns!</h3><p>Meta de lucro!</p></div>'
    titulo = "Hoje (todas)" if is_admin() else "As minhas vendas de hoje"
    return render_template_string(T, content=meta_msg+f'''
    <div class="card"><h2>{titulo}</h2>
    <p>Bruto: <b>Kz {int(bruto)}</b> · Lucro: <b>Kz {int(lucro)}</b> · Líquido: <b>Kz {int(max(0,bruto-5000))}</b></p>
    <form method="POST" action="/finalizar"><textarea name="nota" placeholder="Nota do dia"></textarea><button class="o">Finalizar Dia</button></form>
    <table><tr><th>Produto</th><th>Qtd</th><th>Valor</th><th>Lucro</th>{extra_th}</tr>{linhas}</table></div>''')

@app.route("/finalizar", methods=["POST"])
def finalizar():
    if not tem_perm("perm_hoje"): return redirect("/")
    uid = session["user_id"]
    vendas = vendas_do_dia(uid)
    bruto = sum(v.valor_total for v in vendas)
    lucro = sum(v.lucro or 0 for v in vendas)
    caixa = get_caixa()
    if bruto > 5000:
        caixa.valor += 5000
    db.session.add(FechamentoDia(user_id=uid, data=date.today(), total_bruto=bruto,
        total_liquido=max(0,bruto-5000) if bruto > 5000 else bruto, total_lucro=lucro,
        caixa=caixa.valor, qtd_vendas=len(vendas), meta_atingida=bruto>=META_VENDA,
        meta_lucro_atingida=lucro>=META_LUCRO, nota=request.form.get("nota","")))
    db.session.commit()
    if bruto >= META_VENDA: flash("Parabéns! Meta de vendas!")
    if lucro >= META_LUCRO: flash("Parabéns! Meta de lucro!")
    return redirect("/hoje")

@app.route("/historico")
def historico():
    if not tem_perm("perm_historico"): return redirect("/")
    data_f = request.args.get("data",""); prod_f = request.args.get("produto",""); user_f = request.args.get("user","")
    q = Venda.query
    if not is_admin(): q = q.filter(Venda.user_id == session["user_id"])
    elif user_f: q = q.filter(Venda.user_id == int(user_f))
    if data_f:
        try: q = q.filter(db.func.date(Venda.data)==datetime.strptime(data_f,"%Y-%m-%d").date())
        except: pass
    if prod_f: q = q.join(Produto).filter(Produto.nome.ilike("%"+prod_f+"%"))
    vendas = q.order_by(Venda.data.desc()).limit(200).all()
    extra_th = "<th>Funcionário</th>" if is_admin() else ""
    linhas = ""
    for v in vendas:
        vend = f"<td>{v.usuario.nome if v.usuario else '—'}</td>" if is_admin() else ""
        linhas += f"<tr><td>{v.data.strftime('%d/%m/%Y')}</td><td>{v.data.strftime('%H:%M')}</td><td>{v.produto.nome}</td><td>{v.quantidade}</td><td>Kz {int(v.valor_total)}</td>{vend}</tr>"
    filtro_user = ""
    if is_admin():
        opts = '<option value="">Todos</option>'+"".join(f'<option value="{u.id}"{" selected" if user_f==str(u.id) else ""}>{u.nome}</option>' for u in Usuario.query.filter(Usuario.tipo!="admin").all())
        filtro_user = f'<select name="user">{opts}</select>'
    reiniciar = '<form method="POST" action="/reiniciar-historico" style="margin-bottom:10px"><button class="r" onclick="return confirm(\'Apagar todo o histórico?\')">Reiniciar Histórico</button></form>' if is_admin() else ""
    return render_template_string(T, content=f'<div class="card"><h2>{"Histórico" if is_admin() else "O meu histórico"}</h2>{reiniciar}<form method="GET"><input type="date" name="data" value="{data_f}"><input name="produto" placeholder="Produto" value="{prod_f}">{filtro_user}<button>Pesquisar</button></form><table><tr><th>Data</th><th>Hora</th><th>Produto</th><th>Qtd</th><th>Valor</th>{extra_th}</tr>{linhas}</table></div>')

@app.route("/reiniciar-historico", methods=["POST"])
def reiniciar_historico():
    if not is_admin(): return redirect("/")
    Venda.query.delete(); db.session.commit(); flash("Histórico apagado.")
    return redirect("/historico")

@app.route("/lucro")
def lucro():
    if not tem_perm("perm_lucro"): return redirect("/")
    uid = None if is_admin() else session["user_id"]
    vendas = vendas_do_dia(uid)
    total_v = sum(v.valor_total for v in vendas); total_l = sum(v.lucro or 0 for v in vendas)
    por = {}
    for v in vendas:
        n = v.produto.nome
        if n not in por: por[n] = {"qtd":0,"venda":0,"lucro":0}
        por[n]["qtd"] += v.quantidade; por[n]["venda"] += v.valor_total; por[n]["lucro"] += v.lucro or 0
    linhas = "".join(f"<tr><td>{n}</td><td>{d['qtd']}</td><td>Kz {int(d['venda'])}</td><td>Kz {int(d['lucro'])}</td></tr>" for n,d in por.items())
    return render_template_string(T, content=f'<div class="card"><h2>{"Lucro de hoje" if is_admin() else "O meu lucro"}</h2><p>Vendas: <b>Kz {int(total_v)}</b> · Lucro: <b>Kz {int(total_l)}</b></p><table><tr><th>Produto</th><th>Qtd</th><th>Venda</th><th>Lucro</th></tr>{linhas}</table></div>')

@app.route("/resumo")
def resumo():
    if "user_id" not in session: return redirect("/login")
    if not is_admin() and not session.get("perm_resumo"): return redirect("/")
    uid = None if is_admin() else session["user_id"]
    vendas = vendas_do_dia(uid)
    bruto = sum(v.valor_total for v in vendas); lucro = sum(v.lucro or 0 for v in vendas)
    html = f'<div class="card"><h2>{"Resumo do dia" if is_admin() else "O meu resumo"}</h2><div class="resumo-item"><span>Total vendido</span><b>Kz {int(bruto)}</b></div><div class="resumo-item"><span>Lucro</span><b>Kz {int(lucro)}</b></div><div class="resumo-item"><span>Nº vendas</span><b>{len(vendas)}</b></div></div>'
    if is_admin():
        por_user = {}
        for v in vendas_do_dia(None):
            n = v.usuario.nome if v.usuario else "—"
            if n not in por_user: por_user[n] = {"valor":0,"qtd":0,"lucro":0}
            por_user[n]["valor"] += v.valor_total; por_user[n]["qtd"] += 1; por_user[n]["lucro"] += v.lucro or 0
        if por_user:
            linhas = "".join(f"<tr><td>{n}</td><td>{d['qtd']}</td><td>Kz {int(d['valor'])}</td><td>Kz {int(d['lucro'])}</td></tr>" for n,d in por_user.items())
            html += f'<div class="card"><h2>Por funcionário</h2><table><tr><th>Nome</th><th>Nº</th><th>Total</th><th>Lucro</th></tr>{linhas}</table></div>'
    return render_template_string(T, content=html)

@app.route("/caixa", methods=["GET","POST"])
def caixa():
    if not tem_perm("perm_caixa"): return redirect("/")
    c = get_caixa()
    if request.method == "POST" and is_admin():
        c.valor = float(request.form["valor"]); db.session.commit(); return redirect("/caixa")
    form = f'<form method="POST"><input type="number" name="valor" value="{c.valor}"><button>Alterar</button></form>' if is_admin() else ""
    return render_template_string(T, content=f'<div class="card"><h2>Caixa</h2><p style="font-size:1.4rem;font-weight:700">Kz {int(c.valor)}</p>{form}</div>')

@app.route("/produtos", methods=["GET","POST"])
def produtos():
    if not tem_perm("perm_produtos"): return redirect("/")
    busca = request.args.get("busca","")
    if request.method == "POST" and is_admin():
        db.session.add(Produto(nome=request.form["nome"], preco=float(request.form["preco"]),
            preco_compra=float(request.form.get("preco_compra",0)), unidades_caixa=int(request.form.get("unidades_caixa",1)),
            quantidade=int(request.form["quantidade"]), stock_minimo=int(request.form.get("stock_minimo",5)),
            categoria_id=int(request.form["categoria"]) if request.form.get("categoria") else None))
        db.session.commit(); return redirect("/produtos")
    q = Produto.query
    if busca: q = q.filter(Produto.nome.ilike("%"+busca+"%"))
    cats = Categoria.query.all()
    cat_opts = "".join(f'<option value="{c.id}">{c.nome}</option>' for c in cats)
    linhas = ""
    for p in q.order_by(Produto.nome).all():
        lu = calcular_lucro_unidade(p.preco, p.preco_compra or 0, p.unidades_caixa or 1)
        lc = "lucro" if lu > 0 else "lucro-baixo"
        ed = f'<td><a href="/editar/{p.id}" class="btn btn-blue">Editar</a></td>' if is_admin() else ""
        linhas += f'<tr><td>{p.nome}</td><td>{p.categoria.nome if p.categoria else "-"}</td><td>Kz {int(p.preco)}</td><td>Kz {int(p.preco_compra or 0)}</td><td>{p.unidades_caixa or 1}</td><td class="{lc}">Kz {int(lu)}</td><td>{p.quantidade}</td>{ed}</tr>'
    form = f'<form method="POST"><input name="nome" placeholder="Nome" required><select name="categoria"><option value="">Categoria</option>{cat_opts}</select><input type="number" name="preco" placeholder="Preço venda" required><input type="number" name="preco_compra" placeholder="Preço compra caixa"><input type="number" name="unidades_caixa" value="1" placeholder="Un/caixa"><input type="number" name="quantidade" placeholder="Stock" required><input type="number" name="stock_minimo" value="5"><button>Cadastrar</button></form>' if is_admin() else ""
    th = "<th></th>" if is_admin() else ""
    return render_template_string(T, content=f'<div class="card"><h2>Produtos</h2><form method="GET"><input name="busca" value="{busca}" placeholder="Pesquisar"><button>Pesquisar</button></form>{form}<table><tr><th>Nome</th><th>Cat.</th><th>Venda</th><th>Compra</th><th>Un</th><th>Lucro</th><th>Stock</th>{th}</tr>{linhas}</table></div>')

@app.route("/editar/<int:id>", methods=["GET","POST"])
def editar(id):
    if not is_admin(): return redirect("/")
    p = Produto.query.get_or_404(id)
    if request.method == "POST":
        pa, pca = p.preco, p.preco_compra or 0
        p.nome = request.form["nome"]; p.preco = float(request.form["preco"])
        p.preco_compra = float(request.form.get("preco_compra",0)); p.unidades_caixa = int(request.form.get("unidades_caixa",1))
        p.quantidade = int(request.form["quantidade"]); p.stock_minimo = int(request.form.get("stock_minimo",5))
        p.categoria_id = int(request.form["categoria"]) if request.form.get("categoria") else None
        if pa != p.preco or pca != p.preco_compra:
            db.session.add(HistoricoPreco(produto_id=p.id, preco_antigo=pa, preco_novo=p.preco, preco_compra_antigo=pca, preco_compra_novo=p.preco_compra))
        db.session.commit(); return redirect("/produtos")
    cats = Categoria.query.all()
    cat_opts = "".join(f'<option value="{c.id}"{" selected" if p.categoria_id==c.id else ""}>{c.nome}</option>' for c in cats)
    return render_template_string(T, content=f'<div class="card"><h2>Editar</h2><form method="POST"><input name="nome" value="{p.nome}"><select name="categoria"><option value="">Categoria</option>{cat_opts}</select><input type="number" name="preco" value="{p.preco}"><input type="number" name="preco_compra" value="{p.preco_compra or 0}"><input type="number" name="unidades_caixa" value="{p.unidades_caixa or 1}"><input type="number" name="quantidade" value="{p.quantidade}"><input type="number" name="stock_minimo" value="{p.stock_minimo or 5}"><button>Guardar</button></form></div>')

@app.route("/stock")
def stock():
    if not tem_perm("perm_stock"): return redirect("/")
    busca = request.args.get("busca","")
    q = Produto.query
    if busca: q = q.filter(Produto.nome.ilike("%"+busca+"%"))
    linhas = "".join(f'<tr><td>{p.nome}</td><td>{p.quantidade}</td><td>{p.stock_minimo or 5}</td><td>{"Baixo" if p.quantidade<=(p.stock_minimo or 5) else "OK"}</td><td><form method="POST" action="/ajustar/{p.id}" style="display:inline"><input type="hidden" name="acao" value="mais"><button class="g s">+</button></form> <form method="POST" action="/ajustar/{p.id}" style="display:inline"><input type="hidden" name="acao" value="menos"><button class="r s">-</button></form></td></tr>' for p in q.order_by(Produto.nome).all())
    return render_template_string(T, content=f'<div class="card"><h2>Stock</h2><form method="GET"><input name="busca" value="{busca}" placeholder="Pesquisar"><button>Pesquisar</button></form><table><tr><th>Produto</th><th>Qtd</th><th>Mín</th><th>Estado</th><th></th></tr>{linhas}</table></div>')

@app.route("/ajustar/<int:id>", methods=["POST"])
def ajustar(id):
    if not tem_perm("perm_stock"): return redirect("/")
    p = Produto.query.get_or_404(id)
    p.quantidade = p.quantidade+1 if request.form["acao"]=="mais" else max(0, p.quantidade-1)
    db.session.commit(); return redirect("/stock")

@app.route("/compras", methods=["GET","POST"])
def compras():
    if not tem_perm("perm_compras"): return redirect("/")
    if request.method == "POST":
        db.session.add(Compra(user_id=session["user_id"], descricao=request.form["descricao"], valor=float(request.form["valor"])))
        db.session.commit(); return redirect("/compras")
    items = Compra.query.order_by(Compra.data.desc()).all()
    total = sum(c.valor for c in items)
    linhas = "".join(f'<tr><td>{c.descricao}</td><td>Kz {int(c.valor)}</td><td>{c.data.strftime("%d/%m/%Y")}</td><td><a href="/editar-compra/{c.id}" class="btn btn-blue">Editar</a></td></tr>' for c in items)
    reiniciar = '<form method="POST" action="/reiniciar-compras" style="margin-bottom:10px"><button class="r" onclick="return confirm(\'Apagar todas as compras?\')">Reiniciar Compras</button></form>' if is_admin() else ""
    return render_template_string(T, content=f'<div class="card"><h2>Compras</h2><p>Total: <b>Kz {int(total)}</b></p>{reiniciar}<form method="POST"><input name="descricao" placeholder="Descrição" required><input type="number" name="valor" placeholder="Valor" required><button>Registar</button></form><table><tr><th>Descrição</th><th>Valor</th><th>Data</th><th></th></tr>{linhas}</table></div>')

@app.route("/reiniciar-compras", methods=["POST"])
def reiniciar_compras():
    if not is_admin(): return redirect("/")
    Compra.query.delete(); db.session.commit(); flash("Compras apagadas.")
    return redirect("/compras")

@app.route("/editar-compra/<int:id>", methods=["GET","POST"])
def editar_compra(id):
    if not is_admin() and not session.get("perm_compras"): return redirect("/")
    c = Compra.query.get_or_404(id)
    if request.method == "POST":
        c.descricao = request.form["descricao"]; c.valor = float(request.form["valor"]); db.session.commit()
        flash("Atualizado"); return redirect("/compras")
    return render_template_string(T, content=f'<div class="card"><h2>Editar compra</h2><form method="POST"><input name="descricao" value="{c.descricao}" required><input type="number" name="valor" value="{c.valor}" required><button>Guardar</button></form></div>')

@app.route("/restos", methods=["GET","POST"])
def restos():
    if not tem_perm("perm_restos"): return redirect("/")
    if request.method == "POST":
        db.session.add(Resto(user_id=session["user_id"], descricao=request.form["descricao"], valor=float(request.form["valor"])))
        db.session.commit(); return redirect("/restos")
    items = Resto.query.order_by(Resto.data.desc()).all()
    total = sum(r.valor for r in items)
    linhas = "".join(f'<tr><td>{r.descricao}</td><td>Kz {int(r.valor)}</td><td>{r.data.strftime("%d/%m/%Y")}</td><td><a href="/editar-resto/{r.id}" class="btn btn-blue">Editar</a></td></tr>' for r in items)
    reiniciar = '<form method="POST" action="/reiniciar-restos" style="margin-bottom:10px"><button class="r" onclick="return confirm(\'Apagar todos os restos?\')">Reiniciar Restos</button></form>' if is_admin() else ""
    return render_template_string(T, content=f'<div class="card"><h2>Restos</h2><p>Total: <b>Kz {int(total)}</b></p>{reiniciar}<form method="POST"><input name="descricao" placeholder="Descrição" required><input type="number" name="valor" placeholder="Valor" required><button>Registar</button></form><table><tr><th>Descrição</th><th>Valor</th><th>Data</th><th></th></tr>{linhas}</table></div>')

@app.route("/reiniciar-restos", methods=["POST"])
def reiniciar_restos():
    if not is_admin(): return redirect("/")
    Resto.query.delete(); db.session.commit(); flash("Restos apagados.")
    return redirect("/restos")

@app.route("/editar-resto/<int:id>", methods=["GET","POST"])
def editar_resto(id):
    if not is_admin() and not session.get("perm_restos"): return redirect("/")
    r = Resto.query.get_or_404(id)
    if request.method == "POST":
        r.descricao = request.form["descricao"]; r.valor = float(request.form["valor"]); db.session.commit()
        flash("Atualizado"); return redirect("/restos")
    return render_template_string(T, content=f'<div class="card"><h2>Editar resto</h2><form method="POST"><input name="descricao" value="{r.descricao}" required><input type="number" name="valor" value="{r.valor}" required><button>Guardar</button></form></div>')

@app.route("/categorias", methods=["GET","POST"])
def categorias():
    if not tem_perm("perm_categorias"): return redirect("/")
    if request.method == "POST" and is_admin():
        db.session.add(Categoria(nome=request.form["nome"])); db.session.commit(); return redirect("/categorias")
    linhas = "".join(f"<tr><td>{c.nome}</td></tr>" for c in Categoria.query.all())
    form = '<form method="POST"><input name="nome" placeholder="Nome" required><button>Adicionar</button></form>' if is_admin() else ""
    return render_template_string(T, content=f'<div class="card"><h2>Categorias</h2>{form}<table>{linhas}</table></div>')

@app.route("/relatorio")
def relatorio():
    if not tem_perm("perm_relatorio"): return redirect("/")
    fs = FechamentoDia.query.order_by(FechamentoDia.data_fechamento.desc()).all() if is_admin() else FechamentoDia.query.filter_by(user_id=session["user_id"]).order_by(FechamentoDia.data_fechamento.desc()).all()
    linhas = ""
    for f in fs:
        user = Usuario.query.get(f.user_id)
        extra = f"<td>{user.nome if user else '—'}</td>" if is_admin() else ""
        acoes = f'<td><a href="/editar-relatorio/{f.id}" class="btn btn-blue">Editar</a> <form method="POST" action="/eliminar-relatorio/{f.id}" style="display:inline"><button class="btn btn-red" onclick="return confirm(\'Eliminar?\')">Eliminar</button></form></td>' if is_admin() else ""
        linhas += f"<tr><td>{f.data.strftime('%d/%m/%Y')}</td>{extra}<td>Kz {int(f.total_bruto or 0)}</td><td>Kz {int(f.total_liquido or 0)}</td><td>Kz {int(f.total_lucro or 0)}</td><td>Kz {int(f.caixa or 0)}</td><td>{f.qtd_vendas or 0}</td>{acoes}</tr>"
    hu = "<th>Funcionário</th>" if is_admin() else ""; ha = "<th></th>" if is_admin() else ""
    add = '<p><a href="/adicionar-relatorio" class="btn btn-green">Adicionar relatório</a></p>' if is_admin() else ""
    rein = '<form method="POST" action="/reiniciar-relatorio"><button class="r" onclick="return confirm(\'Apagar todos?\')">Reiniciar relatório</button></form>' if is_admin() else ""
    return render_template_string(T, content=f'<div class="card"><h2>Relatório</h2>{add}{rein}<table><tr><th>Data</th>{hu}<th>Bruto</th><th>Líquido</th><th>Lucro</th><th>Caixa</th><th>Vendas</th>{ha}</tr>{linhas}</table></div>')

@app.route("/editar-relatorio/<int:id>", methods=["GET","POST"])
def editar_relatorio(id):
    if not is_admin(): return redirect("/")
    f = FechamentoDia.query.get_or_404(id)
    if request.method == "POST":
        f.data = datetime.strptime(request.form["data"],"%Y-%m-%d").date()
        f.total_bruto = float(request.form["bruto"]); f.total_liquido = float(request.form["liquido"])
        f.total_lucro = float(request.form["lucro"]); f.caixa = float(request.form["caixa"]); f.qtd_vendas = int(request.form["qtd"])
        f.nota = request.form.get("nota",""); db.session.commit(); flash("Atualizado"); return redirect("/relatorio")
    return render_template_string(T, content=f'<div class="card"><h2>Editar relatório</h2><form method="POST"><input type="date" name="data" value="{f.data.strftime("%Y-%m-%d")}" required><input type="number" step="0.01" name="bruto" value="{f.total_bruto or 0}" required><input type="number" step="0.01" name="liquido" value="{f.total_liquido or 0}" required><input type="number" step="0.01" name="lucro" value="{f.total_lucro or 0}" required><input type="number" step="0.01" name="caixa" value="{f.caixa or 0}" required><input type="number" name="qtd" value="{f.qtd_vendas or 0}" required><textarea name="nota">{f.nota or ""}</textarea><button>Guardar</button></form></div>')

@app.route("/reiniciar-relatorio", methods=["POST"])
def reiniciar_relatorio():
    if not is_admin(): return redirect("/")
    FechamentoDia.query.delete(); db.session.commit(); flash("Relatórios apagados.")
    return redirect("/relatorio")

@app.route("/adicionar-relatorio", methods=["GET","POST"])
def adicionar_relatorio():
    if not is_admin(): return redirect("/")
    if request.method == "POST":
        db.session.add(FechamentoDia(user_id=session["user_id"], data=datetime.strptime(request.form["data"],"%Y-%m-%d").date(),
            total_bruto=float(request.form["bruto"]), total_liquido=float(request.form["liquido"]), total_lucro=float(request.form["lucro"]),
            caixa=float(request.form["caixa"]), qtd_vendas=int(request.form["qtd"]), nota=request.form.get("nota","")))
        db.session.commit(); flash("Adicionado"); return redirect("/relatorio")
    return render_template_string(T, content='<div class="card"><h2>Adicionar relatório</h2><form method="POST"><input type="date" name="data" required><input type="number" step="0.01" name="bruto" placeholder="Bruto" required><input type="number" step="0.01" name="liquido" placeholder="Líquido" required><input type="number" step="0.01" name="lucro" placeholder="Lucro" required><input type="number" step="0.01" name="caixa" placeholder="Caixa" required><input type="number" name="qtd" placeholder="Nº vendas" required><textarea name="nota"></textarea><button>Adicionar</button></form></div>')

@app.route("/eliminar-relatorio/<int:id>", methods=["POST"])
def eliminar_relatorio(id):
    if not is_admin(): return redirect("/")
    db.session.delete(FechamentoDia.query.get_or_404(id)); db.session.commit(); flash("Eliminado")
    return redirect("/relatorio")

@app.route("/mensal")
def mensal():
    if not is_admin(): return redirect("/")
    hoje = date.today(); inicio = hoje.replace(day=1)
    fs = FechamentoDia.query.filter(FechamentoDia.data >= inicio).order_by(FechamentoDia.data).all()
    total = sum(f.total_liquido or 0 for f in fs); lucro = sum(f.total_lucro or 0 for f in fs)
    return render_template_string(T, content=f'<div class="card"><h2>Relatório mensal</h2><p>Líquido: <b>Kz {int(total)}</b> · Lucro: <b>Kz {int(lucro)}</b></p><p><a href="/exportar-mensal" class="btn btn-green">Exportar CSV</a></p></div>')

@app.route("/exportar-mensal")
def exportar_mensal():
    if not is_admin(): return redirect("/")
    hoje = date.today(); inicio = hoje.replace(day=1)
    fs = FechamentoDia.query.filter(FechamentoDia.data >= inicio).order_by(FechamentoDia.data).all()
    out = io.StringIO(); w = csv.writer(out)
    w.writerow(["Data","Bruto","Líquido","Lucro","Caixa","Vendas"])
    for f in fs: w.writerow([f.data.strftime("%d/%m/%Y"), f.total_bruto or 0, f.total_liquido or 0, f.total_lucro or 0, f.caixa or 0, f.qtd_vendas or 0])
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=mensal.csv"})

@app.route("/valor-stock")
def valor_stock():
    if not is_admin(): return redirect("/")
    total = 0; linhas = ""
    for p in Produto.query.all():
        cu = calcular_custo_unidade(p.preco_compra or 0, p.unidades_caixa or 1)
        val = cu * p.quantidade; total += val
        linhas += f"<tr><td>{p.nome}</td><td>{p.quantidade}</td><td>Kz {int(cu)}</td><td>Kz {int(val)}</td></tr>"
    return render_template_string(T, content=f'<div class="card"><h2>Valor em stock</h2><p style="font-size:1.3rem"><b>Kz {int(total)}</b></p><table><tr><th>Produto</th><th>Qtd</th><th>Custo/un</th><th>Total</th></tr>{linhas}</table></div>')

@app.route("/ranking")
def ranking():
    if not is_admin(): return redirect("/")
    periodo = request.args.get("periodo","hoje")
    if periodo == "ontem":
        d = date.today()-timedelta(days=1); vendas = Venda.query.filter(db.func.date(Venda.data)==d).all(); titulo = "Ranking ontem"
    elif periodo == "7dias":
        vendas = Venda.query.filter(Venda.data >= date.today()-timedelta(days=6)).all(); titulo = "Ranking 7 dias"
    elif periodo == "mes":
        vendas = Venda.query.filter(Venda.data >= date.today().replace(day=1)).all(); titulo = "Ranking do mês"
    else:
        vendas = Venda.query.filter(db.func.date(Venda.data)==date.today()).all(); titulo = "Ranking hoje"
    por = {}
    for v in vendas:
        n = v.produto.nome
        if n not in por: por[n] = {"qtd":0,"valor":0,"lucro":0}
        por[n]["qtd"] += v.quantidade; por[n]["valor"] += v.valor_total; por[n]["lucro"] += v.lucro or 0
    rank = sorted(por.items(), key=lambda x: x[1]["valor"], reverse=True)
    linhas = "".join(f"<tr><td>{i}</td><td>{n}</td><td>{d['qtd']}</td><td>Kz {int(d['valor'])}</td><td>Kz {int(d['lucro'])}</td></tr>" for i,(n,d) in enumerate(rank,1))
    filtros = "".join(f'<a href="/ranking?periodo={p}" class="{"ativo" if periodo==p else ""}">{l}</a>' for p,l in [("hoje","Hoje"),("ontem","Ontem"),("7dias","7 dias"),("mes","Mês")])
    return render_template_string(T, content=f'<div class="card"><h2>{titulo}</h2><div class="filtro">{filtros}</div><table><tr><th>#</th><th>Produto</th><th>Qtd</th><th>Valor</th><th>Lucro</th></tr>{linhas}</table></div>')

@app.route("/horas")
def horas():
    if not is_admin(): return redirect("/")
    vendas = Venda.query.filter(db.func.date(Venda.data)==date.today()).all()
    por_h = {}
    for v in vendas: por_h[v.data.hour] = por_h.get(v.data.hour, 0) + v.valor_total
    labels = [f"{h}h" for h in range(8,22)]
    data = [round(por_h.get(h,0),0) for h in range(8,22)]
    return render_template_string(T, content=f'''<div class="card"><h2>Vendas por hora (hoje)</h2><div class="chart-wrap"><canvas id="ch"></canvas></div></div>
    <script>new Chart(document.getElementById('ch'),{{type:'bar',data:{{labels:{json.dumps(labels)},datasets:[{{data:{json.dumps(data)},backgroundColor:'#1565c0'}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}}}}}});</script>''')

@app.route("/exportar")
def exportar():
    if not is_admin(): return redirect("/")
    return render_template_string(T, content='<div class="card"><h2>Exportar</h2><p><a href="/exportar-csv" class="btn btn-green">Vendas CSV</a></p><p style="margin-top:8px"><a href="/exportar-mensal" class="btn btn-blue">Mensal CSV</a></p></div>')

@app.route("/exportar-csv")
def exportar_csv():
    if not is_admin(): return redirect("/")
    out = io.StringIO(); w = csv.writer(out)
    w.writerow(["Data","Hora","Produto","Qtd","Valor","Lucro","Funcionário"])
    for v in Venda.query.order_by(Venda.data.desc()).all():
        w.writerow([v.data.strftime("%d/%m/%Y"), v.data.strftime("%H:%M"), v.produto.nome, v.quantidade, v.valor_total, v.lucro or 0, v.usuario.nome if v.usuario else ""])
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=vendas.csv"})

@app.route("/alertas")
def alertas():
    if "user_id" not in session: return redirect("/login")
    lista = Alerta.query.order_by(Alerta.data.desc()).limit(100).all() if is_admin() else Alerta.query.filter_by(user_id=session["user_id"]).order_by(Alerta.data.desc()).limit(50).all()
    linhas = ""
    for a in lista:
        linhas += f'<div class="alerta-item">{foto_html(a.usuario)}<div style="flex:1"><b>{a.usuario.nome if a.usuario else "—"}</b><div style="font-size:.85rem;margin:4px 0">{a.mensagem}</div><div style="font-size:.75rem;color:#666">{a.data.strftime("%d/%m/%Y %H:%M")}</div></div></div>'
    rein = '<form method="POST" action="/reiniciar-alertas" style="margin-bottom:10px"><button class="r" onclick="return confirm(\'Apagar alertas?\')">Reiniciar Alertas</button></form>' if is_admin() else ""
    return render_template_string(T, content=f'<div class="card"><h2>Alertas</h2>{rein}{linhas}</div>')

@app.route("/reiniciar-alertas", methods=["POST"])
def reiniciar_alertas():
    if not is_admin(): return redirect("/")
    Alerta.query.delete(); db.session.commit(); flash("Alertas apagados.")
    return redirect("/alertas")

@app.route("/mensagens", methods=["GET","POST"])
def mensagens():
    if "user_id" not in session: return redirect("/login")
    if not is_admin() and not session.get("perm_mensagens"): return redirect("/")
    limpar_mensagens_antigas()
    uid = session["user_id"]
    admin = Usuario.query.filter_by(tipo="admin").first()
    if not admin: return render_template_string(T, content='<div class="card">Sem administrador.</div>')
    outro = admin.id if not is_admin() else request.args.get("para", type=int)
    if is_admin() and not outro:
        links = "".join(f'<p><a href="/mensagens?para={u.id}" class="btn btn-blue">{u.nome}</a></p>' for u in Usuario.query.filter(Usuario.tipo!="admin").all())
        return render_template_string(T, content=f'<div class="card"><h2>Mensagens</h2>{links}</div>')
    hoje = date.today()
    enviadas = Mensagem.query.filter(Mensagem.de_user_id==uid, db.func.date(Mensagem.data)==hoje).count()
    if request.method == "POST":
        if enviadas >= 5: flash("Limite de 5 mensagens/dia."); return redirect(request.url)
        texto = request.form.get("texto","").strip()
        if texto:
            para = admin.id if not is_admin() else outro
            db.session.add(Mensagem(de_user_id=uid, para_user_id=para, texto=texto)); db.session.commit(); flash("Enviada")
        return redirect(request.url)
    if is_admin():
        msgs = Mensagem.query.filter(((Mensagem.de_user_id==uid)&(Mensagem.para_user_id==outro))|((Mensagem.de_user_id==outro)&(Mensagem.para_user_id==uid))).order_by(Mensagem.data).all()
    else:
        msgs = Mensagem.query.filter(((Mensagem.de_user_id==uid)&(Mensagem.para_user_id==admin.id))|((Mensagem.de_user_id==admin.id)&(Mensagem.para_user_id==uid))).order_by(Mensagem.data).all()
    chat = "".join(f'<div class="msg {"mine" if m.de_user_id==uid else "other"}"><div style="font-size:.75rem;color:#666">{m.de_user.nome} · {m.data.strftime("%d/%m %H:%M")}</div><div>{m.texto}</div></div>' for m in msgs)
    form = '<form method="POST"><textarea name="texto" required></textarea><button>Enviar</button></form>' if enviadas < 5 else '<p style="color:#c62828">Limite diário atingido.</p>'
    return render_template_string(T, content=f'<div class="card"><h2>Mensagens</h2>{chat}{form}</div>')

@app.route("/utilizadores")
def utilizadores():
    if not is_admin(): return redirect("/")
    linhas = ""
    for u in Usuario.query.all():
        av = foto_html(u)
        acoes = f'<a href="/permissoes/{u.id}" class="btn btn-blue">Permissões</a> <a href="/redefinir/{u.id}" class="btn btn-orange">Senha</a> <a href="/alterar-foto/{u.id}" class="btn btn-purple">Foto</a>'
        if u.tipo != "admin":
            acoes += f' <form method="POST" action="/eliminar-utilizador/{u.id}" style="display:inline"><button class="btn btn-red" onclick="return confirm(\'Eliminar?\')">Eliminar</button></form>'
        linhas += f'<tr><td>{av}</td><td>{u.nome}</td><td>{u.email}</td><td>{u.tipo or "funcionario"}</td><td>{acoes}</td></tr>'
    return render_template_string(T, content=f'<div class="card"><h2>Utilizadores</h2><p><a href="/criar-utilizador" class="btn btn-green">Criar utilizador</a></p><table><tr><th>Foto</th><th>Nome</th><th>Email</th><th>Tipo</th><th></th></tr>{linhas}</table></div>')

@app.route("/criar-utilizador", methods=["GET","POST"])
def criar_utilizador():
    if not is_admin(): return redirect("/")
    if request.method == "POST":
        if not Usuario.query.filter_by(email=request.form["email"]).first():
            foto = ""
            f = request.files.get("foto")
            if f and f.filename: foto = processar_foto(f)
            db.session.add(Usuario(nome=request.form["nome"], email=request.form["email"], senha=generate_password_hash(request.form["senha"]), tipo="funcionario", foto=foto))
            db.session.commit(); flash("Criado"); return redirect("/utilizadores")
        flash("Email já existe")
    return render_template_string(T, content='<div class="card"><h2>Criar utilizador</h2><form method="POST" enctype="multipart/form-data"><input name="nome" required placeholder="Nome"><input type="email" name="email" required placeholder="Email"><input type="password" name="senha" required placeholder="Senha"><input type="file" name="foto" accept="image/*"><button>Criar</button></form></div>')

@app.route("/permissoes/<int:id>", methods=["GET","POST"])
def permissoes(id):
    if not is_admin(): return redirect("/")
    u = Usuario.query.get_or_404(id)
    if u.tipo == "admin": return render_template_string(T, content='<div class="card"><p>Admin tem acesso total.</p><a href="/utilizadores" class="btn btn-blue">Voltar</a></div>')
    if request.method == "POST":
        for p in ["perm_hoje","perm_historico","perm_relatorio","perm_lucro","perm_produtos","perm_stock","perm_caixa","perm_compras","perm_restos","perm_categorias","perm_mensagens","perm_resumo"]:
            setattr(u, p, p in request.form)
        db.session.commit(); flash("Permissões atualizadas"); return redirect("/utilizadores")
    checks = ""
    for p, label in [("perm_hoje","Hoje"),("perm_historico","Histórico"),("perm_relatorio","Relatório"),("perm_lucro","Lucro"),("perm_produtos","Produtos"),("perm_stock","Stock"),("perm_caixa","Caixa"),("perm_compras","Compras"),("perm_restos","Restos"),("perm_categorias","Categorias"),("perm_mensagens","Mensagens"),("perm_resumo","Resumo")]:
        checks += f'<label style="display:block;margin:8px 0"><input type="checkbox" name="{p}"{" checked" if getattr(u,p) else ""}> {label}</label>'
    return render_template_string(T, content=f'<div class="card"><h2>Permissões – {u.nome}</h2><form method="POST">{checks}<button>Guardar</button></form></div>')

@app.route("/redefinir/<int:id>", methods=["GET","POST"])
def redefinir(id):
    if not is_admin(): return redirect("/")
    u = Usuario.query.get_or_404(id)
    if request.method == "POST":
        u.senha = generate_password_hash(request.form["senha"]); db.session.commit(); flash("Senha alterada"); return redirect("/utilizadores")
    return render_template_string(T, content=f'<div class="card"><h2>Senha – {u.nome}</h2><form method="POST"><input type="password" name="senha" required placeholder="Nova senha"><button>Guardar</button></form></div>')

@app.route("/alterar-foto/<int:id>", methods=["GET","POST"])
def alterar_foto(id):
    if not is_admin(): return redirect("/")
    u = Usuario.query.get_or_404(id)
    if request.method == "POST":
        f = request.files.get("foto")
        if f and f.filename:
            b64 = processar_foto(f)
            if b64: u.foto = b64; db.session.commit(); flash("Foto atualizada")
        return redirect("/utilizadores")
    return render_template_string(T, content=f'<div class="card"><h2>Foto – {u.nome}</h2><form method="POST" enctype="multipart/form-data"><input type="file" name="foto" accept="image/*" required><button>Guardar</button></form></div>')

@app.route("/eliminar-utilizador/<int:id>", methods=["POST"])
def eliminar_utilizador(id):
    if not is_admin(): return redirect("/")
    u = Usuario.query.get_or_404(id)
    if u.tipo == "admin": flash("Não podes eliminar o admin"); return redirect("/utilizadores")
    db.session.delete(u); db.session.commit(); flash("Eliminado")
    return redirect("/utilizadores")

@app.route("/tornar-admin/<email>")
def tornar_admin(email):
    u = Usuario.query.filter_by(email=email).first()
    if u: u.tipo = "admin"; db.session.commit(); return "Admin: "+email
    return "Não encontrado"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        try:
            for sql in [
                "ALTER TABLE usuario ALTER COLUMN foto TYPE TEXT",
                "ALTER TABLE produto ADD COLUMN IF NOT EXISTS preco_compra FLOAT DEFAULT 0",
                "ALTER TABLE produto ADD COLUMN IF NOT EXISTS unidades_caixa INTEGER DEFAULT 1",
                "ALTER TABLE produto ADD COLUMN IF NOT EXISTS stock_minimo INTEGER DEFAULT 5",
                "ALTER TABLE produto ADD COLUMN IF NOT EXISTS categoria_id INTEGER",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS tipo VARCHAR(20) DEFAULT 'funcionario'",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS foto TEXT DEFAULT ''",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_historico BOOLEAN DEFAULT FALSE",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_relatorio BOOLEAN DEFAULT FALSE",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_lucro BOOLEAN DEFAULT FALSE",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_produtos BOOLEAN DEFAULT FALSE",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_stock BOOLEAN DEFAULT FALSE",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_caixa BOOLEAN DEFAULT FALSE",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_hoje BOOLEAN DEFAULT FALSE",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_compras BOOLEAN DEFAULT FALSE",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_restos BOOLEAN DEFAULT FALSE",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_categorias BOOLEAN DEFAULT FALSE",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_mensagens BOOLEAN DEFAULT TRUE",
                "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_resumo BOOLEAN DEFAULT TRUE",
                "ALTER TABLE venda ADD COLUMN IF NOT EXISTS lucro FLOAT DEFAULT 0",
                "ALTER TABLE fechamento_dia ADD COLUMN IF NOT EXISTS total_lucro FLOAT DEFAULT 0",
                "ALTER TABLE fechamento_dia ADD COLUMN IF NOT EXISTS meta_atingida BOOLEAN DEFAULT FALSE",
                "ALTER TABLE fechamento_dia ADD COLUMN IF NOT EXISTS meta_lucro_atingida BOOLEAN DEFAULT FALSE",
                "ALTER TABLE fechamento_dia ADD COLUMN IF NOT EXISTS nota TEXT",
                "ALTER TABLE historico_preco ADD COLUMN IF NOT EXISTS preco_compra_antigo FLOAT",
                "ALTER TABLE historico_preco ADD COLUMN IF NOT EXISTS preco_compra_novo FLOAT",
            ]:
                db.session.execute(db.text(sql))
            db.session.commit()
        except Exception as e:
            print(e); db.session.rollback()
    app.run(host="0.0.0.0", port=5001, debug=True)