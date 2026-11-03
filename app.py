from flask import Flask, render_template_string, request, redirect, url_for, session, flash, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import io

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
    perm_historico = db.Column(db.Boolean, default=False)
    perm_relatorio = db.Column(db.Boolean, default=False)
    perm_lucro = db.Column(db.Boolean, default=False)
    perm_produtos = db.Column(db.Boolean, default=False)
    perm_stock = db.Column(db.Boolean, default=False)
    perm_caixa = db.Column(db.Boolean, default=False)
    perm_hoje = db.Column(db.Boolean, default=False)

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
</style></head><body id="body">{% if session.get('user_id') %}<div class="top"><h1>Cantina FC Pira</h1><div class="nav"><a href="/">Vender</a><a href="/dashboard">Dashboard</a>{% if session.get('tipo')=='admin' %}<a href="/hoje">Hoje</a><a href="/historico">Historico</a><a href="/relatorio">Relatorio</a><a href="/lucro">Lucro</a><a href="/caixa">Caixa</a><a href="/produtos">Produtos</a><a href="/stock">Stock</a><a href="/compras">Compras</a><a href="/restos">Restos</a><a href="/categorias">Categorias</a><a href="/exportar">Exportar</a><a href="/utilizadores">Utilizadores</a><a href="/mensal">Mensal</a><a href="/ranking">Ranking</a><a href="/horas">Horas de Pico</a><a href="/valor-stock">Valor em Stock</a>{% else %}{% if session.get('perm_hoje') %}<a href="/hoje">Hoje</a>{% endif %}{% if session.get('perm_historico') %}<a href="/historico">Historico</a>{% endif %}{% if session.get('perm_relatorio') %}<a href="/relatorio">Relatorio</a>{% endif %}{% if session.get('perm_lucro') %}<a href="/lucro">Lucro</a>{% endif %}{% if session.get('perm_caixa') %}<a href="/caixa">Caixa</a>{% endif %}{% if session.get('perm_produtos') %}<a href="/produtos">Produtos</a>{% endif %}{% if session.get('perm_stock') %}<a href="/stock">Stock</a>{% endif %}{% endif %}<a href="/calculadora">Calculadora</a><a href="#" onclick="toggleDark();return false;">Modo</a><a href="/logout">Sair</a></div></div>{% endif %}<div class="c">{% with messages = get_flashed_messages(with_categories=true) %}{% if messages %}{% for cat, msg in messages %}<div class="flash">{{ msg }}</div>{% endfor %}{% endif %}{% endwith %}{{ content|safe }}</div><script>function toggleDark(){document.getElementById('body').classList.toggle('dark');localStorage.setItem('dark',document.getElementById('body').classList.contains('dark'))}if(localStorage.getItem('dark')==='true')document.getElementById('body').classList.add('dark')</script></body></html>"""

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
    return render_template_string(T, content=alertas+'<div class="card"><h2>Vender</h2><form method="GET"><input name="busca" placeholder="Pesquisar..." value="'+busca+'">'+sel+'<button>Pesquisar</button></form><div class="grid">'+boxes+'</div></div>')

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

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect("/login")
    if not is_admin():
        return render_template_string(T, content='<div class="card"><h2>Bem-vindo</h2><p>Usa o menu para vender.</p></div>')
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
    
    # Valor em stock
    valor_stock = 0
    for p in Produto.query.all():
        custo_un = calcular_custo_unidade(p.preco_compra or 0, p.unidades_caixa or 1)
        valor_stock += custo_un * p.quantidade
    
    meta_msg = ""
    if bruto_hoje >= META_VENDA:
        meta_msg += '<div class="parabens"><h3>Parabéns!</h3><p>Meta de vendas atingida!</p></div>'
    if lucro_hoje >= META_LUCRO:
        meta_msg += '<div class="parabens"><h3>Parabéns!</h3><p>Meta de lucro atingida!</p></div>'
    
    return render_template_string(T, content=meta_msg+'''
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
    <form method="POST" action="/reiniciar-dashboard" style="margin-top:12px"><button class="r">Reiniciar Dashboard</button></form>
    ''')

# (As restantes rotas: /relatorio, /eliminar-relatorio, /mensal, /horas, /caixa, /produtos, /editar, /stock, /compras, /restos, /utilizadores, etc. ficam iguais ao código anterior)

# No final mantém o if __name__ == "__main__" com os ALTER TABLE, incluindo o novo campo nota:

# Adiciona esta linha no bloco try do if __name__:
# db.session.execute(db.text("ALTER TABLE fechamento_dia ADD COLUMN IF NOT EXISTS nota TEXT"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        try:
            db.session.execute(db.text("ALTER TABLE produto ADD COLUMN IF NOT EXISTS preco_compra FLOAT DEFAULT 0"))
            db.session.execute(db.text("ALTER TABLE produto ADD COLUMN IF NOT EXISTS unidades_caixa INTEGER DEFAULT 1"))
            db.session.execute(db.text("ALTER TABLE produto ADD COLUMN IF NOT EXISTS stock_minimo INTEGER DEFAULT 5"))
            db.session.execute(db.text("ALTER TABLE produto ADD COLUMN IF NOT EXISTS categoria_id INTEGER"))
            db.session.execute(db.text("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS tipo VARCHAR(20) DEFAULT 'funcionario'"))
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
        except:
            db.session.rollback()
    app.run(host="0.0.0.0", port=5001, debug=True)