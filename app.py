from flask import Flask, render_template_string, request, redirect, url_for, session, flash, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import io
import base64
from PIL import Image

app = Flask(__name__)
app.secret_key = "cantina-2026"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://neondb_owner:npg_VS5JzKpOFQ3e@ep-wild-cloud-b4vl2kuk-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

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

class Alerta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    mensagem = db.Column(db.Text)
    tipo = db.Column(db.String(50))
    data = db.Column(db.DateTime, default=datetime.utcnow)
    fechado = db.Column(db.Boolean, default=False)
    data_fechado = db.Column(db.DateTime)
    usuario = db.relationship("Usuario")

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
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
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

T = """<!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cantina FC Pira</title><style>
*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif}
body{background:#f4f6f8;color:#222}
body.dark{background:#121212;color:#e0e0e0}
body.dark .card,body.dark .box,body.dark .stat{background:#1e1e1e;color:#e0e0e0}
body.dark .top{background:#0a1929}
body.dark th{background:#1a3a5c;color:#fff}
body.dark input,body.dark select,body.dark textarea{background:#2a2a2a;color:#fff;border-color:#444}
.top{background:#0d47a1;color:#fff;padding:12px 16px;position:sticky;top:0;z-index:50}
.top h1{font-size:1.1rem}
.top .user{font-size:.75rem;opacity:.85;margin-top:2px}
.nav{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}
.nav a{background:rgba(255,255,255,.15);color:#fff;padding:5px 11px;border-radius:16px;text-decoration:none;font-size:.75rem}
.c{max-width:920px;margin:0 auto;padding:12px}
.card{background:#fff;border-radius:10px;padding:14px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.card h2{font-size:1rem;margin-bottom:10px;color:#0d47a1}
body.dark .card h2{color:#64b5f6}
input,button,select,textarea{width:100%;padding:10px;margin:4px 0;border-radius:7px;border:1px solid #ddd;font-size:14px}
button{background:#1565c0;color:#fff;border:none;font-weight:500;cursor:pointer}
.g{background:#2e7d32}.o{background:#e65100}.r{background:#c62828}
.s{width:auto;padding:6px 10px;font-size:12px;margin:2px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}
.box{background:#fff;border:1px solid #e3f2fd;border-radius:10px;padding:10px;text-align:center}
.box.destaque{border:2px solid #ff9800;background:#fff8e1}
.box b{display:block;color:#0d47a1;margin-bottom:3px}
.box div{font-size:.75rem;color:#555;margin:2px 0}
.stat{background:#fff;border-radius:12px;padding:16px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,.08);border-top:4px solid #1565c0}
.stat b{display:block;font-size:1.5rem;margin-top:6px;font-weight:700}
.stat.venda{border-top-color:#1565c0}.stat.venda b{color:#1565c0}
.stat.lucro{border-top-color:#2e7d32}.stat.lucro b{color:#2e7d32}
.stat.caixa{border-top-color:#f57c00}.stat.caixa b{color:#f57c00}
.stat.nvendas{border-top-color:#6a1b9a}.stat.nvendas b{color:#6a1b9a}
.stat.compras{border-top-color:#00838f}.stat.compras b{color:#00838f}
.stat.restos{border-top-color:#d84315}.stat.restos b{color:#d84315}
.stat.stock{border-top-color:#c62828}.stat.stock b{color:#c62828}
.stat.valor-stock{border-top-color:#6a1b9a}.stat.valor-stock b{color:#6a1b9a}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#e3f2fd;padding:7px;text-align:left}
td{padding:7px;border-bottom:1px solid #eee}
.alerta{background:#ffebee;color:#c62828;padding:8px;border-radius:6px;margin-bottom:10px;font-size:.85rem}
.flash{background:#e8f5e9;padding:8px 12px;border-radius:6px;margin-bottom:10px;font-size:.85rem}
.btn{display:inline-block;padding:6px 12px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:500;margin:2px}
.btn-blue{background:#1565c0;color:#fff}
.btn-green{background:#2e7d32;color:#fff}
.btn-orange{background:#e65100;color:#fff}
.btn-red{background:#c62828;color:#fff}
.btn-purple{background:#6a1b9a;color:#fff}
.btn:hover{opacity:.9}
.parabens{background:linear-gradient(135deg,#4caf50,#8bc34a);color:#fff;padding:20px;border-radius:10px;text-align:center;margin-bottom:12px;font-size:1.1rem}
.parabens h3{margin-bottom:8px;font-size:1.3rem}
.lucro{color:#2e7d32;font-weight:600}
.lucro-baixo{color:#c62828;font-weight:600}
.qty{width:60px !important;padding:6px;text-align:center;display:inline-block;margin:0 2px}
.bar-container{display:flex;align-items:flex-end;height:120px;gap:4px;overflow-x:auto;padding-bottom:8px}
.bar{display:flex;flex-direction:column;align-items:center;min-width:32px}
.bar-fill{background:linear-gradient(to top,#1565c0,#42a5f5);border-radius:4px 4px 0 0;width:28px}
.bar-label{font-size:.65rem;margin-top:4px;color:#555}
.filtro{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.filtro a{padding:6px 12px;background:#e3f2fd;border-radius:16px;text-decoration:none;color:#0d47a1;font-size:.8rem}
.filtro a.ativo{background:#1565c0;color:#fff}
.calc-float{position:fixed;top:80px;right:20px;width:280px;background:#fff;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.2);z-index:1000;display:none;padding:12px}
.calc-float.show{display:block}
.calc-display{background:#1e1e1e;color:#fff;font-size:1.4rem;text-align:right;padding:12px;border-radius:8px;margin-bottom:8px;min-height:48px}
.calc-buttons{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
.calc-buttons button{font-size:.95rem;padding:10px;border-radius:6px;font-weight:500}
.calc-buttons .op{background:#e65100}
.calc-buttons .eq{background:#2e7d32}
.calc-buttons .clear{background:#c62828}
.calc-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.calc-header span{font-weight:600;color:#0d47a1}
.calc-close{background:none;border:none;font-size:1.3rem;cursor:pointer;color:#666;width:auto;padding:0}
.bemvindo{background:linear-gradient(135deg,#1565c0,#42a5f5);color:#fff;padding:16px;border-radius:10px;margin-bottom:12px}
.bemvindo.alerta-msg{background:linear-gradient(135deg,#e65100,#ff9800)}
.bemvindo.sucesso{background:linear-gradient(135deg,#2e7d32,#66bb6a)}
.bemvindo h3{margin-bottom:6px}
.bemvindo ul{margin:8px 0 0 18px;font-size:.9rem}
.bemvindo button{width:auto;margin-top:8px;background:#fff;color:#1565c0}
.avatar{width:36px;height:36px;border-radius:50%;object-fit:cover;background:#1565c0;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-weight:600;font-size:.9rem}
.alerta-item{display:flex;gap:12px;align-items:flex-start;padding:12px;border-bottom:1px solid #eee}
</style></head><body id="body">{% if session.get('user_id') %}<div class="top"><h1>Cantina FC Pira</h1><div class="user">{{ session.get('nome','') }}</div><div class="nav"><a href="/">Vender</a><a href="/dashboard">Dashboard</a><a href="/alertas">Alertas</a>{% if session.get('tipo')=='admin' %}<a href="/hoje">Hoje</a><a href="/historico">Historico</a><a href="/relatorio">Relatorio</a><a href="/lucro">Lucro</a><a href="/caixa">Caixa</a><a href="/produtos">Produtos</a><a href="/stock">Stock</a><a href="/compras">Compras</a><a href="/restos">Restos</a><a href="/categorias">Categorias</a><a href="/exportar">Exportar</a><a href="/utilizadores">Utilizadores</a><a href="/mensal">Mensal</a><a href="/ranking">Ranking</a><a href="/horas">Horas de Pico</a><a href="/valor-stock">Valor em Stock</a>{% else %}{% if session.get('perm_hoje') %}<a href="/hoje">Hoje</a>{% endif %}{% if session.get('perm_historico') %}<a href="/historico">Historico</a>{% endif %}{% if session.get('perm_relatorio') %}<a href="/relatorio">Relatorio</a>{% endif %}{% if session.get('perm_lucro') %}<a href="/lucro">Lucro</a>{% endif %}{% if session.get('perm_caixa') %}<a href="/caixa">Caixa</a>{% endif %}{% if session.get('perm_produtos') %}<a href="/produtos">Produtos</a>{% endif %}{% if session.get('perm_stock') %}<a href="/stock">Stock</a>{% endif %}{% endif %}<a href="#" onclick="toggleCalc();return false;">Calculadora</a><a href="#" onclick="toggleDark();return false;">Modo</a><a href="/logout">Sair</a></div></div>{% endif %}<div class="c">{% with messages = get_flashed_messages(with_categories=true) %}{% if messages %}{% for cat, msg in messages %}<div class="flash">{{ msg }}</div>{% endfor %}{% endif %}{% endwith %}{{ content|safe }}</div>
<div class="calc-float" id="calcFloat">
  <div class="calc-header"><span>Calculadora</span><button class="calc-close" onclick="toggleCalc()">×</button></div>
  <div class="calc-display" id="display">0</div>
  <div class="calc-buttons">
    <button onclick="clearD()" class="clear">C</button>
    <button onclick="back()">&lt;-</button>
    <button onclick="add('/')" class="op">/</button>
    <button onclick="add('*')" class="op">×</button>
    <button onclick="add(7)">7</button>
    <button onclick="add(8)">8</button>
    <button onclick="add(9)">9</button>
    <button onclick="add('-')" class="op">-</button>
    <button onclick="add(4)">4</button>
    <button onclick="add(5)">5</button>
    <button onclick="add(6)">6</button>
    <button onclick="add('+')" class="op">+</button>
    <button onclick="add(1)">1</button>
    <button onclick="add(2)">2</button>
    <button onclick="add(3)">3</button>
    <button onclick="calc()" class="eq">=</button>
    <button onclick="add(0)" style="grid-column:span 2">0</button>
    <button onclick="add('.')">.</button>
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
function fecharBemvindo(){document.getElementById('bemvindo').style.display='none'}
</script>
</body></html>"""

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
        print("Erro ao processar foto:", e)
        return ""

def gerar_alertas(uid):
    if is_admin(): return ""
    user = Usuario.query.get(uid)
    if not user: return ""
    nome = user.nome
    hoje = date.today()
    hora = datetime.now().hour

    baixos = Produto.query.filter(Produto.quantidade <= Produto.stock_minimo).count()
    fechado = dia_fechado(uid)

    alertas = []
    tipo = "info"

    # Só alertas realmente importantes
    if baixos > 0:
        alertas.append(f"Atenção: tens {baixos} produto(s) com stock baixo. Verifica e reabastece se for necessário.")
        tipo = "alerta"

    if hora >= 16 and not fechado:
        alertas.append("Lembra-te: no final do dia vai a Hoje e clica em Finalizar Dia para guardar o relatório.")

    if not alertas:
        return ""

    # Evitar criar o mesmo alerta várias vezes no mesmo dia
    for msg in alertas:
        existe = Alerta.query.filter_by(user_id=uid, mensagem=msg).filter(db.func.date(Alerta.data)==hoje).first()
        if not existe:
            db.session.add(Alerta(user_id=uid, mensagem=msg, tipo=tipo))
    db.session.commit()

    # Só mostrar se ainda não foi fechado hoje
    abertos = Alerta.query.filter_by(user_id=uid, fechado=False).filter(db.func.date(Alerta.data)==hoje).all()
    if not abertos: return ""

    classe = "bemvindo alerta-msg" if tipo == "alerta" else "bemvindo"

    lista = "".join(f"<li>{a.mensagem}</li>" for a in abertos)
    ids = ",".join(str(a.id) for a in abertos)

    return f'''
    <div class="{classe}" id="bemvindo">
        <h3>Olá {nome}!</h3>
        <ul>{lista}</ul>
        <form method="POST" action="/fechar-alertas" style="margin-top:8px">
            <input type="hidden" name="ids" value="{ids}">
            <button type="submit">Entendi</button>
        </form>
    </div>
    '''

@app.route("/fechar-alertas", methods=["POST"])
def fechar_alertas():
    if "user_id" not in session: return redirect("/login")
    ids = request.form.get("ids", "").split(",")
    for i in ids:
        if i.strip():
            a = Alerta.query.get(int(i))
            if a and a.user_id == session["user_id"]:
                a.fechado = True
                a.data_fechado = datetime.utcnow()
    db.session.commit()
    return redirect(request.referrer or "/")

@app.route("/alertas")
def alertas():
    if "user_id" not in session: return redirect("/login")
    if is_admin():
        alertas_list = Alerta.query.order_by(Alerta.data.desc()).limit(100).all()
    else:
        alertas_list = Alerta.query.filter_by(user_id=session["user_id"]).order_by(Alerta.data.desc()).limit(50).all()
    
    linhas = ""
    for a in alertas_list:
        avatar = foto_html(a.usuario)
        estado = "Lida" if a.fechado else "Não lida"
        estado_cor = "#2e7d32" if a.fechado else "#c62828"
        linhas += f'''
        <div class="alerta-item">
            {avatar}
            <div style="flex:1">
                <b>{a.usuario.nome if a.usuario else "—"}</b>
                <div style="font-size:.85rem;margin:4px 0">{a.mensagem}</div>
                <div style="font-size:.75rem;color:#666">{a.data.strftime("%d/%m/%Y %H:%M")} · <span style="color:{estado_cor}">{estado}</span></div>
            </div>
        </div>
        '''
    return render_template_string(T, content='<div class="card"><h2>Alertas</h2>'+linhas+'</div>')

@app.route("/")
def index():
    if "user_id" not in session: return redirect(url_for("login"))
    uid = session["user_id"]
    if not is_admin() and dia_fechado(uid):
        return render_template_string(T, content='<div class="card">Dia finalizado<form method="POST" action="/reiniciar"><button class="o">Reiniciar</button></form></div>')
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
        boxes += '<div class="'+cls+'"><b>'+p.nome+'</b>'
        if p.categoria: boxes += '<div style="font-size:.7rem;color:#1976d2">'+p.categoria.nome+'</div>'
        boxes += '<div>Venda: Kz '+str(int(p.preco))+'</div>'
        boxes += '<div>Custo/un: Kz '+str(int(custo_un))+'</div>'
        boxes += '<div class="'+lucro_cls+'">Lucro: Kz '+str(int(lucro_un))+'</div>'
        boxes += '<div>Stock: '+str(p.quantidade)+'</div>'
        boxes += '<form method="POST" action="/vender" style="margin-top:6px">'
        boxes += '<input type="hidden" name="produto_id" value="'+str(p.id)+'">'
        boxes += '<input type="number" name="quantidade" class="qty" value="1" min="1" max="'+str(p.quantidade)+'">'
        boxes += '<button class="g s">Vender</button></form>'
        if is_admin():
            boxes += '<form method="POST" action="/devolver/'+str(p.id)+'"><button class="o s">Devolver</button></form>'
            boxes += '<form method="POST" action="/eliminar/'+str(p.id)+'"><button class="r s">Eliminar</button></form>'
        boxes += '</div>'
    cats = Categoria.query.all()
    sel = '<select name="categoria" onchange="this.form.submit()"><option value="">Todas</option>'
    for c in cats:
        sel += '<option value="'+str(c.id)+'"'+(' selected' if str(c.id)==cat_id else '')+'>'+c.nome+'</option>'
    sel += '</select>'
    alertas = ""
    if is_admin():
        baixos = Produto.query.filter(Produto.quantidade <= Produto.stock_minimo).all()
        if baixos:
            alertas = '<div class="alerta">Stock baixo: '+", ".join(p.nome+" ("+str(p.quantidade)+")" for p in baixos)+'</div>'
    bemvindo = gerar_alertas(uid)
    return render_template_string(T, content=bemvindo+alertas+'<div class="card"><h2>Vender</h2><form method="GET"><input name="busca" placeholder="Pesquisar..." value="'+busca+'">'+sel+'<button>Pesquisar</button></form><div class="grid">'+boxes+'</div></div>')

@app.route("/vender", methods=["POST"])
def vender():
    if "user_id" not in session: return redirect("/login")
    uid = session["user_id"]
    if not is_admin() and dia_fechado(uid): return redirect("/")
    p = Produto.query.get(int(request.form["produto_id"]))
    qtd = int(request.form.get("quantidade", 1))
    if p and qtd > 0 and p.quantidade >= qtd:
        custo_un = calcular_custo_unidade(p.preco_compra or 0, p.unidades_caixa or 1)
        lucro_un = p.preco - custo_un
        lucro_total = lucro_un * qtd
        valor_total = p.preco * qtd
        db.session.add(Venda(produto_id=p.id, user_id=uid, quantidade=qtd, valor_total=valor_total, lucro=lucro_total))
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

@app.route("/hoje")
def hoje():
    if not tem_perm("perm_hoje"): return redirect("/")
    vendas = Venda.query.filter(db.func.date(Venda.data)==date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    lucro = sum(v.lucro or 0 for v in vendas)
    linhas = "".join("<tr><td>"+v.produto.nome+"</td><td>"+str(v.quantidade)+"</td><td>Kz "+str(int(v.valor_total))+"</td><td>Kz "+str(int(v.lucro or 0))+"</td></tr>" for v in vendas)
    meta_msg = ""
    if bruto >= META_VENDA:
        meta_msg += '<div class="parabens"><h3>Parabéns!</h3><p>Atingiste a meta de vendas (48.000 Kz)!</p></div>'
    if lucro >= META_LUCRO:
        meta_msg += '<div class="parabens"><h3>Parabéns!</h3><p>Atingiste a meta de lucro (15.000 Kz)!</p></div>'
    return render_template_string(T, content=meta_msg+'<div class="card"><h2>Hoje</h2><p>Bruto: <b>Kz '+str(int(bruto))+'</b></p><p>Lucro: <b>Kz '+str(int(lucro))+'</b></p><p>Líquido: <b>Kz '+str(int(max(0,bruto-5000)))+'</b></p><form method="POST" action="/finalizar"><textarea name="nota" placeholder="Nota do dia (opcional)"></textarea><button class="o">Finalizar Dia</button></form><table><tr><th>Produto</th><th>Qtd</th><th>Valor</th><th>Lucro</th></tr>'+linhas+'</table></div>')

@app.route("/finalizar", methods=["POST"])
def finalizar():
    if not tem_perm("perm_hoje"): return redirect("/")
    uid = session["user_id"]
    vendas = Venda.query.filter(db.func.date(Venda.data)==date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    lucro = sum(v.lucro or 0 for v in vendas)
    caixa = Caixa.query.filter_by(user_id=uid).first()
    if not caixa:
        caixa = Caixa(user_id=uid, valor=0)
        db.session.add(caixa)
    meta_atingida = bruto >= META_VENDA
    meta_lucro = lucro >= META_LUCRO
    if bruto > 5000:
        caixa.valor += 5000
    nota = request.form.get("nota", "")
    db.session.add(FechamentoDia(user_id=uid, data=date.today(), total_bruto=bruto, total_liquido=max(0,bruto-5000) if bruto > 5000 else bruto, total_lucro=lucro, caixa=caixa.valor, qtd_vendas=len(vendas), meta_atingida=meta_atingida, meta_lucro_atingida=meta_lucro, nota=nota))
    db.session.commit()
    if meta_atingida:
        flash("Parabéns! Atingiste a meta de vendas!")
    if meta_lucro:
        flash("Parabéns! Atingiste a meta de lucro!")
    return redirect("/hoje")

@app.route("/historico")
def historico():
    if not tem_perm("perm_historico"): return redirect("/")
    data_filtro = request.args.get("data", "")
    produto_filtro = request.args.get("produto", "")
    query = Venda.query
    if data_filtro:
        try:
            d = datetime.strptime(data_filtro, "%Y-%m-%d").date()
            query = query.filter(db.func.date(Venda.data) == d)
        except: pass
    if produto_filtro:
        query = query.join(Produto).filter(Produto.nome.ilike("%"+produto_filtro+"%"))
    vendas = query.order_by(Venda.data.desc()).limit(200).all()
    linhas = "".join("<tr><td>"+v.data.strftime("%d/%m/%Y")+"</td><td>"+v.data.strftime("%H:%M")+"</td><td>"+v.produto.nome+"</td><td>"+str(v.quantidade)+"</td><td>Kz "+str(int(v.valor_total))+"</td></tr>" for v in vendas)
    return render_template_string(T, content='<div class="card"><h2>Histórico</h2><form method="GET"><input type="date" name="data" value="'+data_filtro+'"><input name="produto" placeholder="Produto" value="'+produto_filtro+'"><button>Pesquisar</button></form><table><tr><th>Data</th><th>Hora</th><th>Produto</th><th>Qtd</th><th>Valor</th></tr>'+linhas+'</table></div>')

@app.route("/lucro")
def lucro():
    if not tem_perm("perm_lucro"): return redirect("/")
    hoje = date.today()
    vendas = Venda.query.filter(db.func.date(Venda.data)==hoje).all()
    total_venda = sum(v.valor_total for v in vendas)
    total_lucro = sum(v.lucro or 0 for v in vendas)
    por_produto = {}
    for v in vendas:
        if v.produto.nome not in por_produto:
            por_produto[v.produto.nome] = {"qtd":0,"venda":0,"lucro":0}
        por_produto[v.produto.nome]["qtd"] += v.quantidade
        por_produto[v.produto.nome]["venda"] += v.valor_total
        por_produto[v.produto.nome]["lucro"] += v.lucro or 0
    linhas = "".join("<tr><td>"+n+"</td><td>"+str(d["qtd"])+"</td><td>Kz "+str(int(d["venda"]))+"</td><td>Kz "+str(int(d["lucro"]))+"</td></tr>" for n,d in por_produto.items())
    meta_status = "Atingida" if total_lucro >= META_LUCRO else "Em progresso"
    return render_template_string(T, content='<div class="card"><h2>Lucro de Hoje</h2><p>Total vendas: <b>Kz '+str(int(total_venda))+'</b></p><p>Lucro: <b>Kz '+str(int(total_lucro))+'</b></p><p>Meta lucro: Kz '+str(META_LUCRO)+' ('+meta_status+')</p><table><tr><th>Produto</th><th>Qtd</th><th>Venda</th><th>Lucro</th></tr>'+linhas+'</table></div>')

@app.route("/mensal")
def mensal():
    if not is_admin(): return redirect("/")
    hoje = date.today()
    inicio = hoje.replace(day=1)
    fs = FechamentoDia.query.filter(FechamentoDia.data >= inicio).order_by(FechamentoDia.data).all()
    total_mes = sum(f.total_liquido for f in fs)
    total_lucro = sum(f.total_lucro or 0 for f in fs)
    dias = []
    for i in range(1, hoje.day+1):
        d = date(hoje.year, hoje.month, i)
        f = next((x for x in fs if x.data == d), None)
        dias.append((d.strftime("%d"), int(f.total_liquido) if f else 0))
    max_v = max([d[1] for d in dias] or [1]) or 1
    barras = ""
    for d in dias:
        h = max(8, int(100 * d[1] / max_v))
        barras += '<div class="bar"><div class="bar-fill" style="height:'+str(h)+'px"></div><div class="bar-label">'+d[0]+'</div></div>'
    return render_template_string(T, content='<div class="card"><h2>Relatório Mensal</h2><p>Total líquido: <b>Kz '+str(int(total_mes))+'</b></p><p>Lucro: <b>Kz '+str(int(total_lucro))+'</b></p><p><a href="/exportar-mensal" class="btn btn-green">Exportar CSV do Mês</a></p><div class="bar-container">'+barras+'</div></div>')

@app.route("/exportar-mensal")
def exportar_mensal():
    if not is_admin(): return redirect("/")
    hoje = date.today()
    inicio = hoje.replace(day=1)
    fs = FechamentoDia.query.filter(FechamentoDia.data >= inicio).order_by(FechamentoDia.data).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Data", "Valor Bruto", "Valor Líquido", "Lucro", "Caixa", "Vendas", "Meta Venda", "Meta Lucro"])
    for f in fs:
        writer.writerow([f.data.strftime("%d/%m/%Y"), f.total_bruto or 0, f.total_liquido or 0, f.total_lucro or 0, f.caixa or 0, f.qtd_vendas or 0, "Sim" if f.meta_atingida else "Não", "Sim" if f.meta_lucro_atingida else "Não"])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=relatorio_mensal.csv"})

@app.route("/valor-stock")
def valor_stock():
    if not is_admin(): return redirect("/")
    produtos = Produto.query.all()
    total = 0
    linhas = ""
    for p in produtos:
        custo_un = calcular_custo_unidade(p.preco_compra or 0, p.unidades_caixa or 1)
        valor = custo_un * p.quantidade
        total += valor
        linhas += "<tr><td>"+p.nome+"</td><td>"+str(p.quantidade)+"</td><td>Kz "+str(int(custo_un))+"</td><td>Kz "+str(int(valor))+"</td></tr>"
    return render_template_string(T, content='<div class="card"><h2>Valor em Stock</h2><p style="font-size:1.3rem;font-weight:600">Total parado: <b>Kz '+str(int(total))+'</b></p><table><tr><th>Produto</th><th>Quantidade</th><th>Custo/Un</th><th>Valor Total</th></tr>'+linhas+'</table></div>')

@app.route("/ranking")
def ranking():
    if not is_admin(): return redirect("/")
    periodo = request.args.get("periodo", "hoje")
    cat_id = request.args.get("categoria", "")
    if periodo == "ontem":
        d = date.today() - timedelta(days=1)
        vendas = Venda.query.filter(db.func.date(Venda.data)==d)
        titulo = "Ranking de Ontem"
    elif periodo == "7dias":
        inicio = date.today() - timedelta(days=6)
        vendas = Venda.query.filter(Venda.data >= inicio)
        titulo = "Ranking dos Últimos 7 Dias"
    elif periodo == "30dias":
        inicio = date.today() - timedelta(days=29)
        vendas = Venda.query.filter(Venda.data >= inicio)
        titulo = "Ranking dos Últimos 30 Dias"
    elif periodo == "mes":
        inicio = date.today().replace(day=1)
        vendas = Venda.query.filter(Venda.data >= inicio)
        titulo = "Ranking do Mês"
    else:
        vendas = Venda.query.filter(db.func.date(Venda.data)==date.today())
        titulo = "Ranking de Hoje"
    
    if cat_id:
        vendas = vendas.join(Produto).filter(Produto.categoria_id == int(cat_id))
    
    vendas = vendas.all()
    por_produto = {}
    for v in vendas:
        nome = v.produto.nome
        if nome not in por_produto:
            por_produto[nome] = {"qtd": 0, "valor": 0, "lucro": 0}
        por_produto[nome]["qtd"] += v.quantidade
        por_produto[nome]["valor"] += v.valor_total
        por_produto[nome]["lucro"] += v.lucro or 0
    
    ranking = sorted(por_produto.items(), key=lambda x: x[1]["valor"], reverse=True)
    linhas = ""
    for i, (nome, dados) in enumerate(ranking, 1):
        linhas += "<tr><td>"+str(i)+"</td><td>"+nome+"</td><td>"+str(dados["qtd"])+"</td><td>Kz "+str(int(dados["valor"]))+"</td><td>Kz "+str(int(dados["lucro"]))+"</td></tr>"
    
    filtros = '<div class="filtro">'
    for p, label in [("hoje","Hoje"),("ontem","Ontem"),("7dias","7 Dias"),("30dias","30 Dias"),("mes","Mês")]:
        cls = " ativo" if periodo == p else ""
        filtros += '<a href="/ranking?periodo='+p+('&categoria='+cat_id if cat_id else '')+'" class="'+cls+'">'+label+'</a>'
    filtros += '</div>'
    
    cats = Categoria.query.all()
    cat_sel = '<select name="categoria" onchange="location.href=\'/ranking?periodo='+periodo+'&categoria=\'+this.value"><option value="">Todas as categorias</option>'
    for c in cats:
        cat_sel += '<option value="'+str(c.id)+'"'+(' selected' if str(c.id)==cat_id else '')+'>'+c.nome+'</option>'
    cat_sel += '</select>'
    
    return render_template_string(T, content='<div class="card"><h2>'+titulo+'</h2>'+filtros+cat_sel+'<table><tr><th>#</th><th>Produto</th><th>Quantidade</th><th>Valor Total</th><th>Lucro</th></tr>'+linhas+'</table></div>')

@app.route("/horas")
def horas():
    if not is_admin(): return redirect("/")
    vendas = Venda.query.filter(db.func.date(Venda.data)==date.today()).all()
    por_hora = {}
    for v in vendas:
        h = v.data.hour
        por_hora[h] = por_hora.get(h, 0) + v.valor_total
    max_v = max(por_hora.values() or [1]) or 1
    barras = ""
    for h in range(8, 22):
        valor = por_hora.get(h, 0)
        height = max(8, int(100 * valor / max_v))
        barras += '<div class="bar"><div class="bar-fill" style="height:'+str(height)+'px"></div><div class="bar-label">'+str(h)+'h</div></div>'
    return render_template_string(T, content='<div class="card"><h2>Vendas por Hora (Hoje)</h2><div class="bar-container">'+barras+'</div></div>')

@app.route("/relatorio")
def relatorio():
    if not tem_perm("perm_relatorio"): return redirect("/")
    fs = FechamentoDia.query.order_by(FechamentoDia.data_fechamento.desc()).all()
    linhas = ""
    for f in fs:
        linhas += "<tr><td>"+f.data.strftime("%d/%m/%Y")+"</td><td>Kz "+str(int(f.total_bruto or 0))+"</td><td>Kz "+str(int(f.total_liquido or 0))+"</td><td>Kz "+str(int(f.total_lucro or 0))+"</td><td>Kz "+str(int(f.caixa or 0))+"</td><td>"+str(f.qtd_vendas or 0)+"</td><td>"+("Sim" if f.meta_atingida else "Não")+"</td><td>"+("Sim" if f.meta_lucro_atingida else "Não")+"</td>"
        if is_admin():
            linhas += "<td><form method='POST' action='/eliminar-relatorio/"+str(f.id)+"' style='display:inline'><button class='btn btn-red' onclick=\"return confirm('Eliminar este relatório?')\">Eliminar</button></form></td>"
        linhas += "</tr>"
    header_extra = "<th></th>" if is_admin() else ""
    return render_template_string(T, content='<div class="card"><h2>Relatório</h2><table><tr><th>Data</th><th>Valor Bruto</th><th>Valor Líquido</th><th>Lucro</th><th>Caixa</th><th>Vendas</th><th>Meta Venda</th><th>Meta Lucro</th>'+header_extra+'</tr>'+linhas+'</table></div>')

@app.route("/eliminar-relatorio/<int:id>", methods=["POST"])
def eliminar_relatorio(id):
    if not is_admin(): return redirect("/")
    f = FechamentoDia.query.get_or_404(id)
    db.session.delete(f)
    db.session.commit()
    flash("Relatório eliminado")
    return redirect("/relatorio")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect("/login")
    uid = session["user_id"]
    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    
    vendas_hoje = Venda.query.filter(db.func.date(Venda.data)==hoje).all()
    vendas_ontem = Venda.query.filter(db.func.date(Venda.data)==ontem).all()
    
    bruto_hoje = sum(v.valor_total for v in vendas_hoje)
    lucro_hoje = sum(v.lucro or 0 for v in vendas_hoje)
    bruto_ontem = sum(v.valor_total for v in vendas_ontem)
    lucro_ontem = sum(v.lucro or 0 for v in vendas_ontem)
    
    caixa = Caixa.query.filter_by(user_id=uid).first()
    cv = caixa.valor if caixa else 0
    
    compras_hoje = Compra.query.filter(db.func.date(Compra.data)==hoje).all()
    restos_hoje = Resto.query.filter(db.func.date(Resto.data)==hoje).all()
    total_compras = sum(c.valor for c in compras_hoje)
    total_restos = sum(r.valor for r in restos_hoje)
    
    baixos = Produto.query.filter(Produto.quantidade <= Produto.stock_minimo).count()
    valor_stock = 0
    for p in Produto.query.all():
        custo_un = calcular_custo_unidade(p.preco_compra or 0, p.unidades_caixa or 1)
        valor_stock += custo_un * p.quantidade
    
    meta_msg = ""
    if bruto_hoje >= META_VENDA:
        meta_msg += '<div class="parabens"><h3>Parabéns!</h3><p>Meta de vendas atingida!</p></div>'
    if lucro_hoje >= META_LUCRO:
        meta_msg += '<div class="parabens"><h3>Parabéns!</h3><p>Meta de lucro atingida!</p></div>'
    
    botao_reiniciar = ""
    if is_admin():
        botao_reiniciar = '<form method="POST" action="/reiniciar-dashboard" style="margin-top:12px"><button class="r">Reiniciar Dashboard</button></form>'
    
    bemvindo = gerar_alertas(uid)
    
    return render_template_string(T, content=bemvindo+meta_msg+'''
    <h2>Dashboard</h2>
    <div class="grid">
        <div class="stat venda">Vendas Hoje<b>Kz '''+str(int(bruto_hoje))+'''</b><div style="font-size:.75rem;color:#666">Ontem: Kz '''+str(int(bruto_ontem))+'''</div></div>
        <div class="stat lucro">Lucro Hoje<b>Kz '''+str(int(lucro_hoje))+'''</b><div style="font-size:.75rem;color:#666">Ontem: Kz '''+str(int(lucro_ontem))+'''</div></div>
        <div class="stat caixa">Caixa<b>Kz '''+str(int(cv))+'''</b></div>
        <div class="stat nvendas">Nº Vendas<b>'''+str(len(vendas_hoje))+'''</b></div>
        <div class="stat compras">Compras<b>Kz '''+str(int(total_compras))+'''</b></div>
        <div class="stat restos">Restos<b>Kz '''+str(int(total_restos))+'''</b></div>
        <div class="stat stock">Stock Baixo<b>'''+str(baixos)+'''</b></div>
        <div class="stat valor-stock">Valor em Stock<b>Kz '''+str(int(valor_stock))+'''</b></div>
    </div>
    '''+botao_reiniciar)

@app.route("/reiniciar-dashboard", methods=["POST"])
def reiniciar_dashboard():
    if not is_admin(): return redirect("/")
    Venda.query.filter(db.func.date(Venda.data)==date.today()).delete()
    db.session.commit()
    flash("Dashboard reiniciado. Apenas as vendas e o lucro de hoje foram apagados.")
    return redirect("/dashboard")

@app.route("/caixa", methods=["GET","POST"])
def caixa():
    if not tem_perm("perm_caixa"): return redirect("/")
    uid = session["user_id"]
    c = Caixa.query.filter_by(user_id=uid).first()
    if not c:
        c = Caixa(user_id=uid, valor=0)
        db.session.add(c)
        db.session.commit()
    if request.method == "POST":
        c.valor = float(request.form["valor"])
        db.session.commit()
        return redirect("/caixa")
    return render_template_string(T, content='<div class="card"><h2>Caixa</h2><p style="font-size:1.3rem;font-weight:600">Kz '+str(int(c.valor))+'</p><form method="POST"><input type="number" name="valor" value="'+str(c.valor)+'"><button>Alterar</button></form></div>')

@app.route("/produtos", methods=["GET","POST"])
def produtos():
    if not tem_perm("perm_produtos"): return redirect("/")
    busca = request.args.get("busca", "")
    if request.method == "POST" and is_admin():
        db.session.add(Produto(nome=request.form["nome"], preco=float(request.form["preco"]), preco_compra=float(request.form.get("preco_compra",0)), unidades_caixa=int(request.form.get("unidades_caixa",1)), quantidade=int(request.form["quantidade"]), stock_minimo=int(request.form.get("stock_minimo",5)), categoria_id=int(request.form["categoria"]) if request.form.get("categoria") else None))
        db.session.commit()
        return redirect("/produtos")
    q = Produto.query
    if busca:
        q = q.filter(Produto.nome.ilike("%"+busca+"%"))
    ps = q.order_by(Produto.nome).all()
    cats = Categoria.query.all()
    cat_opts = "".join('<option value="'+str(c.id)+'">'+c.nome+'</option>' for c in cats)
    linhas = ""
    for p in ps:
        lucro_un = calcular_lucro_unidade(p.preco, p.preco_compra or 0, p.unidades_caixa or 1)
        lucro_cls = "lucro" if lucro_un > 0 else "lucro-baixo"
        linhas += "<tr><td>"+p.nome+"</td><td>"+(p.categoria.nome if p.categoria else "-")+"</td><td>Kz "+str(int(p.preco))+"</td><td>Kz "+str(int(p.preco_compra or 0))+"</td><td>"+str(p.unidades_caixa or 1)+"</td><td class='"+lucro_cls+"'>Kz "+str(int(lucro_un))+"</td><td>"+str(p.quantidade)+"</td>"+("<td><a href='/editar/"+str(p.id)+"' class='btn btn-blue'>Editar</a></td>" if is_admin() else "")+"</tr>"
    form = '<form method="POST"><input name="nome" placeholder="Nome" required><select name="categoria"><option value="">Categoria</option>'+cat_opts+'</select><input type="number" name="preco" placeholder="Preço venda (unidade)" required><input type="number" name="preco_compra" placeholder="Preço compra (caixa)"><input type="number" name="unidades_caixa" placeholder="Unidades por caixa" value="1"><input type="number" name="quantidade" placeholder="Qtd stock" required><input type="number" name="stock_minimo" placeholder="Stock mínimo" value="5"><button>Cadastrar</button></form>' if is_admin() else ""
    return render_template_string(T, content='<div class="card"><h2>Produtos</h2><form method="GET"><input name="busca" placeholder="Pesquisar produto..." value="'+busca+'"><button>Pesquisar</button></form>'+form+'<table><tr><th>Nome</th><th>Categoria</th><th>Venda</th><th>Compra</th><th>Un/Caixa</th><th>Lucro</th><th>Stock</th>'+("<th></th>" if is_admin() else "")+'</tr>'+linhas+'</table></div>')

@app.route("/editar/<int:id>", methods=["GET","POST"])
def editar(id):
    if not is_admin(): return redirect("/")
    p = Produto.query.get_or_404(id)
    if request.method == "POST":
        preco_antigo = p.preco
        preco_compra_antigo = p.preco_compra or 0
        p.nome = request.form["nome"]
        p.preco = float(request.form["preco"])
        p.preco_compra = float(request.form.get("preco_compra",0))
        p.unidades_caixa = int(request.form.get("unidades_caixa",1))
        p.quantidade = int(request.form["quantidade"])
        p.stock_minimo = int(request.form.get("stock_minimo",5))
        p.categoria_id = int(request.form["categoria"]) if request.form.get("categoria") else None
        if preco_antigo != p.preco or preco_compra_antigo != p.preco_compra:
            db.session.add(HistoricoPreco(produto_id=p.id, preco_antigo=preco_antigo, preco_novo=p.preco, preco_compra_antigo=preco_compra_antigo, preco_compra_novo=p.preco_compra))
        db.session.commit()
        return redirect("/produtos")
    cats = Categoria.query.all()
    cat_opts = "".join('<option value="'+str(c.id)+'"'+(' selected' if p.categoria_id==c.id else '')+'>'+c.nome+'</option>' for c in cats)
    lucro_un = calcular_lucro_unidade(p.preco, p.preco_compra or 0, p.unidades_caixa or 1)
    custo_un = calcular_custo_unidade(p.preco_compra or 0, p.unidades_caixa or 1)
    hist = HistoricoPreco.query.filter_by(produto_id=p.id).order_by(HistoricoPreco.data.desc()).limit(5).all()
    hist_linhas = "".join("<tr><td>"+h.data.strftime("%d/%m/%Y")+"</td><td>Kz "+str(int(h.preco_antigo))+"</td><td>Kz "+str(int(h.preco_novo))+"</td><td>Kz "+str(int(h.preco_compra_antigo or 0))+"</td><td>Kz "+str(int(h.preco_compra_novo or 0))+"</td></tr>" for h in hist)
    return render_template_string(T, content='<div class="card"><h2>Editar</h2><p>Custo por unidade: <b>Kz '+str(int(custo_un))+'</b></p><p>Lucro por unidade: <b>Kz '+str(int(lucro_un))+'</b></p><form method="POST"><input name="nome" value="'+p.nome+'"><select name="categoria"><option value="">Categoria</option>'+cat_opts+'</select><input type="number" name="preco" value="'+str(p.preco)+'" placeholder="Preço venda (unidade)"><input type="number" name="preco_compra" value="'+str(p.preco_compra or 0)+'" placeholder="Preço compra (caixa)"><input type="number" name="unidades_caixa" value="'+str(p.unidades_caixa or 1)+'" placeholder="Unidades por caixa"><input type="number" name="quantidade" value="'+str(p.quantidade)+'"><input type="number" name="stock_minimo" value="'+str(p.stock_minimo or 5)+'"><button>Guardar</button></form></div><div class="card"><h2>Histórico de Preços</h2><table><tr><th>Data</th><th>Venda Antiga</th><th>Venda Nova</th><th>Compra Antiga</th><th>Compra Nova</th></tr>'+hist_linhas+'</table></div>')

@app.route("/categorias", methods=["GET","POST"])
def categorias():
    if not is_admin(): return redirect("/")
    if request.method == "POST":
        db.session.add(Categoria(nome=request.form["nome"]))
        db.session.commit()
        return redirect("/categorias")
    cats = Categoria.query.all()
    linhas = "".join("<tr><td>"+c.nome+"</td></tr>" for c in cats)
    return render_template_string(T, content='<div class="card"><h2>Categorias</h2><form method="POST"><input name="nome" placeholder="Nome da categoria" required><button>Adicionar</button></form><table>'+linhas+'</table></div>')

@app.route("/stock")
def stock():
    if not tem_perm("perm_stock"): return redirect("/")
    busca = request.args.get("busca", "")
    q = Produto.query
    if busca:
        q = q.filter(Produto.nome.ilike("%"+busca+"%"))
    ps = q.order_by(Produto.nome).all()
    linhas = "".join("<tr><td>"+p.nome+"</td><td>"+str(p.quantidade)+"</td><td>"+str(p.stock_minimo or 5)+"</td><td>"+("Baixo" if p.quantidade <= (p.stock_minimo or 5) else "OK")+"</td><td><form method='POST' action='/ajustar/"+str(p.id)+"' style='display:inline'><input type='hidden' name='acao' value='mais'><button class='g s'>+</button></form> <form method='POST' action='/ajustar/"+str(p.id)+"' style='display:inline'><input type='hidden' name='acao' value='menos'><button class='r s'>-</button></form></td></tr>" for p in ps)
    return render_template_string(T, content='<div class="card"><h2>Stock</h2><form method="GET"><input name="busca" placeholder="Pesquisar produto..." value="'+busca+'"><button>Pesquisar</button></form><table><tr><th>Produto</th><th>Qtd</th><th>Mínimo</th><th>Estado</th><th>Ajustar</th></tr>'+linhas+'</table></div>')

@app.route("/ajustar/<int:id>", methods=["POST"])
def ajustar(id):
    if not tem_perm("perm_stock"): return redirect("/")
    p = Produto.query.get_or_404(id)
    p.quantidade = p.quantidade+1 if request.form["acao"]=="mais" else max(0, p.quantidade-1)
    db.session.commit()
    return redirect("/stock")

@app.route("/compras", methods=["GET","POST"])
def compras():
    if not is_admin(): return redirect("/")
    uid = session["user_id"]
    if request.method == "POST":
        db.session.add(Compra(user_id=uid, descricao=request.form["descricao"], valor=float(request.form["valor"])))
        db.session.commit()
        return redirect("/compras")
    items = Compra.query.filter_by(user_id=uid).order_by(Compra.data.desc()).all()
    linhas = ""
    for c in items:
        linhas += "<tr><td>"+c.descricao+"</td><td>Kz "+str(int(c.valor))+"</td><td>"+c.data.strftime("%d/%m/%Y")+"</td><td><a href='/editar-compra/"+str(c.id)+"' class='btn btn-blue'>Editar</a></td></tr>"
    return render_template_string(T, content='<div class="card"><h2>Compras</h2><form method="POST"><input name="descricao" placeholder="Descrição" required><input type="number" name="valor" placeholder="Valor" required><button>Registar</button></form><table><tr><th>Descrição</th><th>Valor</th><th>Data</th><th></th></tr>'+linhas+'</table></div>')

@app.route("/editar-compra/<int:id>", methods=["GET","POST"])
def editar_compra(id):
    if not is_admin(): return redirect("/")
    c = Compra.query.get_or_404(id)
    if request.method == "POST":
        c.descricao = request.form["descricao"]
        c.valor = float(request.form["valor"])
        db.session.commit()
        flash("Compra atualizada")
        return redirect("/compras")
    return render_template_string(T, content='<div class="card"><h2>Editar Compra</h2><form method="POST"><input name="descricao" value="'+c.descricao+'" required><input type="number" name="valor" value="'+str(c.valor)+'" required><button>Guardar</button></form><p style="margin-top:10px"><a href="/compras" class="btn btn-blue">Voltar</a></p></div>')

@app.route("/restos", methods=["GET","POST"])
def restos():
    if not is_admin(): return redirect("/")
    uid = session["user_id"]
    if request.method == "POST":
        db.session.add(Resto(user_id=uid, descricao=request.form["descricao"], valor=float(request.form["valor"])))
        db.session.commit()
        return redirect("/restos")
    items = Resto.query.filter_by(user_id=uid).order_by(Resto.data.desc()).all()
    linhas = ""
    for r in items:
        linhas += "<tr><td>"+r.descricao+"</td><td>Kz "+str(int(r.valor))+"</td><td>"+r.data.strftime("%d/%m/%Y")+"</td><td><a href='/editar-resto/"+str(r.id)+"' class='btn btn-blue'>Editar</a></td></tr>"
    return render_template_string(T, content='<div class="card"><h2>Restos</h2><form method="POST"><input name="descricao" placeholder="Descrição" required><input type="number" name="valor" placeholder="Valor" required><button>Registar</button></form><table><tr><th>Descrição</th><th>Valor</th><th>Data</th><th></th></tr>'+linhas+'</table></div>')

@app.route("/editar-resto/<int:id>", methods=["GET","POST"])
def editar_resto(id):
    if not is_admin(): return redirect("/")
    r = Resto.query.get_or_404(id)
    if request.method == "POST":
        r.descricao = request.form["descricao"]
        r.valor = float(request.form["valor"])
        db.session.commit()
        flash("Resto atualizado")
        return redirect("/restos")
    return render_template_string(T, content='<div class="card"><h2>Editar Resto</h2><form method="POST"><input name="descricao" value="'+r.descricao+'" required><input type="number" name="valor" value="'+str(r.valor)+'" required><button>Guardar</button></form><p style="margin-top:10px"><a href="/restos" class="btn btn-blue">Voltar</a></p></div>')

@app.route("/exportar")
def exportar():
    if not is_admin(): return redirect("/")
    return render_template_string(T, content='<div class="card"><h2>Exportar</h2><p><a href="/exportar-csv" class="btn btn-green">Descarregar Vendas (CSV)</a></p><p style="margin-top:8px"><a href="/exportar-mensal" class="btn btn-blue">Descarregar Relatório Mensal (CSV)</a></p></div>')

@app.route("/exportar-csv")
def exportar_csv():
    if not is_admin(): return redirect("/")
    vendas = Venda.query.order_by(Venda.data.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Data", "Hora", "Produto", "Quantidade", "Valor", "Lucro"])
    for v in vendas:
        writer.writerow([v.data.strftime("%d/%m/%Y"), v.data.strftime("%H:%M"), v.produto.nome, v.quantidade, v.valor_total, v.lucro or 0])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=vendas.csv"})

@app.route("/utilizadores")
def utilizadores():
    if not is_admin(): return redirect("/")
    users = Usuario.query.all()
    linhas = ""
    for u in users:
        avatar = foto_html(u)
        linhas += '<tr><td>'+avatar+'</td><td>'+u.nome+'</td><td>'+u.email+'</td><td>'+(u.tipo or "funcionario")+'</td><td><a href="/permissoes/'+str(u.id)+'" class="btn btn-blue">Permissões</a> <a href="/redefinir/'+str(u.id)+'" class="btn btn-orange">Senha</a> <a href="/alterar-foto/'+str(u.id)+'" class="btn btn-purple">Foto</a>'
        if u.tipo != "admin":
            linhas += ' <form method="POST" action="/eliminar-utilizador/'+str(u.id)+'" style="display:inline"><button class="btn btn-red" onclick="return confirm(\'Eliminar este utilizador?\')">Eliminar</button></form>'
        linhas += '</td></tr>'
    return render_template_string(T, content='<div class="card"><h2>Utilizadores</h2><p><a href="/criar-utilizador" class="btn btn-green">Criar Utilizador</a></p><table><tr><th>Foto</th><th>Nome</th><th>Email</th><th>Tipo</th><th>Ações</th></tr>'+linhas+'</table></div>')

@app.route("/alterar-foto/<int:id>", methods=["GET","POST"])
def alterar_foto(id):
    if not is_admin(): return redirect("/")
    u = Usuario.query.get_or_404(id)
    if request.method == "POST":
        ficheiro = request.files.get("foto")
        if ficheiro and ficheiro.filename:
            foto_b64 = processar_foto(ficheiro)
            if foto_b64:
                u.foto = foto_b64
                db.session.commit()
                flash("Foto atualizada para "+u.nome)
            else:
                flash("Não foi possível processar a foto. Tenta outra imagem.")
            return redirect("/utilizadores")
    return render_template_string(T, content='<div class="card"><h2>Alterar foto de '+u.nome+'</h2><form method="POST" enctype="multipart/form-data"><input type="file" name="foto" accept="image/*" required><button>Guardar Foto</button></form><p style="margin-top:10px"><a href="/utilizadores" class="btn btn-blue">Voltar</a></p></div>')

@app.route("/eliminar-utilizador/<int:id>", methods=["POST"])
def eliminar_utilizador(id):
    if not is_admin(): return redirect("/")
    u = Usuario.query.get_or_404(id)
    if u.tipo == "admin":
        flash("Não podes eliminar o administrador")
        return redirect("/utilizadores")
    db.session.delete(u)
    db.session.commit()
    flash("Utilizador eliminado")
    return redirect("/utilizadores")

@app.route("/criar-utilizador", methods=["GET","POST"])
def criar_utilizador():
    if not is_admin(): return redirect("/")
    if request.method == "POST":
        if not Usuario.query.filter_by(email=request.form["email"]).first():
            foto_b64 = ""
            ficheiro = request.files.get("foto")
            if ficheiro and ficheiro.filename:
                foto_b64 = processar_foto(ficheiro)
            db.session.add(Usuario(nome=request.form["nome"], email=request.form["email"], senha=generate_password_hash(request.form["senha"]), tipo="funcionario", foto=foto_b64))
            db.session.commit()
            flash("Utilizador criado")
            return redirect("/utilizadores")
        flash("Email já existe")
    return render_template_string(T, content='<div class="card"><h2>Criar Utilizador</h2><form method="POST" enctype="multipart/form-data"><input name="nome" placeholder="Nome" required><input type="email" name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><input type="file" name="foto" accept="image/*"><button>Criar</button></form><p style="margin-top:10px"><a href="/utilizadores" class="btn btn-blue">Voltar</a></p></div>')

@app.route("/dar-tudo/<int:id>")
def dar_tudo(id):
    if not is_admin(): return redirect("/")
    u = Usuario.query.get_or_404(id)
    if u.tipo != "admin":
        u.perm_historico = True
        u.perm_relatorio = True
        u.perm_lucro = True
        u.perm_produtos = True
        u.perm_stock = True
        u.perm_caixa = True
        u.perm_hoje = True
        db.session.commit()
        flash("Todas as permissões dadas a "+u.nome)
    return redirect("/utilizadores")

@app.route("/permissoes/<int:id>", methods=["GET","POST"])
def permissoes(id):
    if not is_admin(): return redirect("/")
    u = Usuario.query.get_or_404(id)
    if u.tipo == "admin":
        return render_template_string(T, content='<div class="card"><p>O administrador tem acesso total.</p><a href="/utilizadores" class="btn btn-blue">Voltar</a></div>')
    if request.method == "POST":
        u.perm_historico = "perm_historico" in request.form
        u.perm_relatorio = "perm_relatorio" in request.form
        u.perm_lucro = "perm_lucro" in request.form
        u.perm_produtos = "perm_produtos" in request.form
        u.perm_stock = "perm_stock" in request.form
        u.perm_caixa = "perm_caixa" in request.form
        u.perm_hoje = "perm_hoje" in request.form
        db.session.commit()
        flash("Permissões atualizadas para "+u.nome)
        return redirect("/utilizadores")
    checks = ""
    for p, label in [("perm_hoje","Hoje (finalizar dia)"),("perm_historico","Histórico"),("perm_relatorio","Relatório"),("perm_lucro","Lucro"),("perm_produtos","Produtos"),("perm_stock","Stock"),("perm_caixa","Caixa")]:
        checked = " checked" if getattr(u, p) else ""
        checks += '<label style="display:block;margin:8px 0"><input type="checkbox" name="'+p+'"'+checked+'> '+label+'</label>'
    return render_template_string(T, content='<div class="card"><h2>Permissões de '+u.nome+'</h2><form method="POST">'+checks+'<button>Guardar</button></form><p style="margin-top:10px"><a href="/utilizadores" class="btn btn-blue">Voltar</a></p></div>')

@app.route("/redefinir/<int:id>", methods=["GET","POST"])
def redefinir(id):
    if not is_admin(): return redirect("/")
    u = Usuario.query.get_or_404(id)
    if request.method == "POST":
        u.senha = generate_password_hash(request.form["senha"])
        db.session.commit()
        flash("Senha redefinida para "+u.nome)
        return redirect("/utilizadores")
    return render_template_string(T, content='<div class="card"><h2>Redefinir senha de '+u.nome+'</h2><form method="POST"><input type="password" name="senha" placeholder="Nova senha" required><button>Guardar</button></form><p style="margin-top:10px"><a href="/utilizadores" class="btn btn-blue">Voltar</a></p></div>')

@app.route("/tornar-admin/<email>")
def tornar_admin(email):
    u = Usuario.query.filter_by(email=email).first()
    if u:
        u.tipo = "admin"
        db.session.commit()
        return "Admin definido para " + email
    return "Utilizador não encontrado"

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = Usuario.query.filter_by(email=request.form["email"]).first()
        if u and check_password_hash(u.senha, request.form["senha"]):
            session["user_id"] = u.id
            session["nome"] = u.nome
            session["tipo"] = u.tipo or "funcionario"
            session["perm_historico"] = u.perm_historico or False
            session["perm_relatorio"] = u.perm_relatorio or False
            session["perm_lucro"] = u.perm_lucro or False
            session["perm_produtos"] = u.perm_produtos or False
            session["perm_stock"] = u.perm_stock or False
            session["perm_caixa"] = u.perm_caixa or False
            session["perm_hoje"] = u.perm_hoje or False
            return redirect("/dashboard")
        flash("Email ou senha incorretos")
    return render_template_string(T, content='<div class="card" style="max-width:360px;margin:30px auto"><h2>Entrar</h2><form method="POST"><input type="email" name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button>Entrar</button></form></div>')

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        try:
            db.session.execute(db.text("ALTER TABLE usuario ALTER COLUMN foto TYPE TEXT"))
            db.session.execute(db.text("ALTER TABLE produto ADD COLUMN IF NOT EXISTS preco_compra FLOAT DEFAULT 0"))
            db.session.execute(db.text("ALTER TABLE produto ADD COLUMN IF NOT EXISTS unidades_caixa INTEGER DEFAULT 1"))
            db.session.execute(db.text("ALTER TABLE produto ADD COLUMN IF NOT EXISTS stock_minimo INTEGER DEFAULT 5"))
            db.session.execute(db.text("ALTER TABLE produto ADD COLUMN IF NOT EXISTS categoria_id INTEGER"))
            db.session.execute(db.text("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS tipo VARCHAR(20) DEFAULT 'funcionario'"))
            db.session.execute(db.text("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS foto TEXT DEFAULT ''"))
            db.session.execute(db.text("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_historico BOOLEAN DEFAULT FALSE"))
            db.session.execute(db.text("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_relatorio BOOLEAN DEFAULT FALSE"))
            db.session.execute(db.text("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_lucro BOOLEAN DEFAULT FALSE"))
            db.session.execute(db.text("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_produtos BOOLEAN DEFAULT FALSE"))
            db.session.execute(db.text("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_stock BOOLEAN DEFAULT FALSE"))
            db.session.execute(db.text("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_caixa BOOLEAN DEFAULT FALSE"))
            db.session.execute(db.text("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS perm_hoje BOOLEAN DEFAULT FALSE"))
            db.session.execute(db.text("ALTER TABLE venda ADD COLUMN IF NOT EXISTS lucro FLOAT DEFAULT 0"))
            db.session.execute(db.text("ALTER TABLE fechamento_dia ADD COLUMN IF NOT EXISTS total_lucro FLOAT DEFAULT 0"))
            db.session.execute(db.text("ALTER TABLE fechamento_dia ADD COLUMN IF NOT EXISTS meta_atingida BOOLEAN DEFAULT FALSE"))
            db.session.execute(db.text("ALTER TABLE fechamento_dia ADD COLUMN IF NOT EXISTS meta_lucro_atingida BOOLEAN DEFAULT FALSE"))
            db.session.execute(db.text("ALTER TABLE fechamento_dia ADD COLUMN IF NOT EXISTS nota TEXT"))
            db.session.execute(db.text("ALTER TABLE historico_preco ADD COLUMN IF NOT EXISTS preco_compra_antigo FLOAT"))
            db.session.execute(db.text("ALTER TABLE historico_preco ADD COLUMN IF NOT EXISTS preco_compra_novo FLOAT"))
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
    app.run(host="0.0.0.0", port=5001, debug=True)