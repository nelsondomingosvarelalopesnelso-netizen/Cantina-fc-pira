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
    quantidade = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=5)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"))
    categoria = db.relationship("Categoria")

class HistoricoPreco(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"))
    preco_antigo = db.Column(db.Float)
    preco_novo = db.Column(db.Float)
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

T = """<!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cantina FC Pira</title><style>
*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif}
body{background:#f4f6f8;color:#222}
body.dark{background:#121212;color:#e0e0e0}
body.dark .card,body.dark .box,body.dark .stat{background:#1e1e1e;color:#e0e0e0}
body.dark .top{background:#0a1929}
body.dark th{background:#1a3a5c;color:#fff}
body.dark input,body.dark select{background:#2a2a2a;color:#fff;border-color:#444}
.top{background:#0d47a1;color:#fff;padding:12px 16px;position:sticky;top:0;z-index:50}
.top h1{font-size:1.1rem}
.nav{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}
.nav a{background:rgba(255,255,255,.15);color:#fff;padding:5px 11px;border-radius:16px;text-decoration:none;font-size:.75rem}
.c{max-width:920px;margin:0 auto;padding:12px}
.card{background:#fff;border-radius:10px;padding:14px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.card h2{font-size:1rem;margin-bottom:10px;color:#0d47a1}
body.dark .card h2{color:#64b5f6}
input,button,select{width:100%;padding:10px;margin:4px 0;border-radius:7px;border:1px solid #ddd;font-size:14px}
button{background:#1565c0;color:#fff;border:none;font-weight:500;cursor:pointer}
.g{background:#2e7d32}.o{background:#e65100}.r{background:#c62828}
.s{width:auto;padding:6px 10px;font-size:12px;margin:2px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(165px,1fr));gap:10px}
.box{background:#fff;border:1px solid #e3f2fd;border-radius:10px;padding:10px;text-align:center}
.box.destaque{border:2px solid #ff9800;background:#fff8e1}
.box b{display:block;color:#0d47a1;margin-bottom:3px}
.box div{font-size:.75rem;color:#555;margin:2px 0}
.stat{background:#fff;border-radius:10px;padding:12px;text-align:center;border-top:3px solid #1565c0}
.stat b{display:block;font-size:1.2rem;margin-top:3px;color:#0d47a1}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#e3f2fd;padding:7px;text-align:left}
td{padding:7px;border-bottom:1px solid #eee}
.alerta{background:#ffebee;color:#c62828;padding:8px;border-radius:6px;margin-bottom:10px;font-size:.85rem}
.flash{background:#e8f5e9;padding:8px 12px;border-radius:6px;margin-bottom:10px;font-size:.85rem}
</style></head><body id="body">{% if session.get('user_id') %}<div class="top"><h1>Cantina FC Pira</h1><div class="nav"><a href="/">Vender</a><a href="/dashboard">Dashboard</a>{% if session.get('tipo')=='admin' %}<a href="/hoje">Hoje</a><a href="/historico">Historico</a><a href="/relatorio">Relatorio</a><a href="/lucro">Lucro</a><a href="/caixa">Caixa</a><a href="/produtos">Produtos</a><a href="/stock">Stock</a><a href="/compras">Compras</a><a href="/restos">Restos</a><a href="/categorias">Categorias</a><a href="/exportar">Exportar</a><a href="/utilizadores">Utilizadores</a><a href="/mensal">Mensal</a>{% else %}{% if session.get('perm_hoje') %}<a href="/hoje">Hoje</a>{% endif %}{% if session.get('perm_historico') %}<a href="/historico">Historico</a>{% endif %}{% if session.get('perm_relatorio') %}<a href="/relatorio">Relatorio</a>{% endif %}{% if session.get('perm_lucro') %}<a href="/lucro">Lucro</a>{% endif %}{% if session.get('perm_caixa') %}<a href="/caixa">Caixa</a>{% endif %}{% if session.get('perm_produtos') %}<a href="/produtos">Produtos</a>{% endif %}{% if session.get('perm_stock') %}<a href="/stock">Stock</a>{% endif %}{% endif %}<a href="/calculadora">Calculadora</a><a href="#" onclick="toggleDark();return false;">Modo</a><a href="/logout">Sair</a></div></div>{% endif %}<div class="c">{% with messages = get_flashed_messages(with_categories=true) %}{% if messages %}{% for cat, msg in messages %}<div class="flash">{{ msg }}</div>{% endfor %}{% endif %}{% endwith %}{{ content|safe }}</div><script>function toggleDark(){document.getElementById('body').classList.toggle('dark');localStorage.setItem('dark',document.getElementById('body').classList.contains('dark'))}if(localStorage.getItem('dark')==='true')document.getElementById('body').classList.add('dark')</script></body></html>"""

def is_admin():
    return session.get("tipo") == "admin"

def tem_perm(perm):
    if is_admin(): return True
    return session.get(perm, False)

def dia_fechado(uid):
    return FechamentoDia.query.filter_by(user_id=uid, data=date.today()).first() is not None

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
        boxes += '<div class="'+cls+'"><b>'+p.nome+'</b>'
        if p.categoria: boxes += '<div style="font-size:.7rem;color:#1976d2">'+p.categoria.nome+'</div>'
        boxes += '<div>Venda: Kz '+str(int(p.preco))+'</div><div>Compra: Kz '+str(int(p.preco_compra or 0))+'</div><div>Stock: '+str(p.quantidade)+'</div>'
        boxes += '<form method="POST" action="/vender"><input type="hidden" name="produto_id" value="'+str(p.id)+'"><button class="g s">Vender</button></form>'
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
            alertas = '<div class="alerta">Stock baixo: '+", ".join(p.nome for p in baixos)+'</div>'
    return render_template_string(T, content=alertas+'<div class="card"><h2>Vender</h2><form method="GET"><input name="busca" placeholder="Pesquisar..." value="'+busca+'">'+sel+'<button>Pesquisar</button></form><div class="grid">'+boxes+'</div></div>')

@app.route("/vender", methods=["POST"])
def vender():
    if "user_id" not in session: return redirect("/login")
    uid = session["user_id"]
    if not is_admin() and dia_fechado(uid): return redirect("/")
    p = Produto.query.get(int(request.form["produto_id"]))
    if p and p.quantidade >= 1:
        lucro = p.preco - (p.preco_compra or 0)
        db.session.add(Venda(produto_id=p.id, user_id=uid, quantidade=1, valor_total=p.preco, lucro=lucro))
        p.quantidade -= 1
        db.session.commit()
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
    return render_template_string(T, content='<div class="card"><h2>Hoje</h2><p>Bruto: <b>Kz '+str(int(bruto))+'</b></p><p>Lucro: <b>Kz '+str(int(lucro))+'</b></p><p>Liquido: <b>Kz '+str(int(max(0,bruto-5000)))+'</b></p><form method="POST" action="/finalizar"><button class="o">Finalizar Dia</button></form><table><tr><th>Produto</th><th>Qtd</th><th>Valor</th><th>Lucro</th></tr>'+linhas+'</table></div>')

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
    caixa.valor += 5000
    db.session.add(FechamentoDia(user_id=uid, data=date.today(), total_bruto=bruto, total_liquido=max(0,bruto-5000), total_lucro=lucro, caixa=caixa.valor, qtd_vendas=len(vendas)))
    db.session.commit()
    return redirect("/hoje")

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
    return render_template_string(T, content='<div class="card"><h2>Lucro de Hoje</h2><p>Total vendas: <b>Kz '+str(int(total_venda))+'</b></p><p>Lucro: <b>Kz '+str(int(total_lucro))+'</b></p><table><tr><th>Produto</th><th>Qtd</th><th>Venda</th><th>Lucro</th></tr>'+linhas+'</table></div>')

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
    return render_template_string(T, content='<div class="card"><h2>Historico</h2><form method="GET"><input type="date" name="data" value="'+data_filtro+'"><input name="produto" placeholder="Produto" value="'+produto_filtro+'"><button>Pesquisar</button></form><table><tr><th>Data</th><th>Hora</th><th>Produto</th><th>Qtd</th><th>Valor</th></tr>'+linhas+'</table></div>')

@app.route("/calculadora")
def calculadora():
    if "user_id" not in session: return redirect("/login")
    content = '<div class="card"><h2>Calculadora</h2><input id="display" readonly style="text-align:right;font-size:1.4rem;margin-bottom:8px"><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px"><button onclick="add(7)">7</button><button onclick="add(8)">8</button><button onclick="add(9)">9</button><button onclick="add(\'+\')" class="o">+</button><button onclick="add(4)">4</button><button onclick="add(5)">5</button><button onclick="add(6)">6</button><button onclick="add(\'-\')" class="o">-</button><button onclick="add(1)">1</button><button onclick="add(2)">2</button><button onclick="add(3)">3</button><button onclick="add(\'*\')" class="o">x</button><button onclick="add(0)">0</button><button onclick="add(\'.\')">.</button><button onclick="calc()" class="g">=</button><button onclick="add(\'/\')" class="o">/</button><button onclick="clearD()" class="r" style="grid-column:span 2">C</button><button onclick="back()" style="grid-column:span 2">&lt;-</button></div><script>function add(v){document.getElementById("display").value+=v}function clearD(){document.getElementById("display").value=""}function back(){var d=document.getElementById("display");d.value=d.value.slice(0,-1)}function calc(){try{document.getElementById("display").value=eval(document.getElementById("display").value)}catch(e){document.getElementById("display").value="Erro"}}</script></div>'
    return render_template_string(T, content=content)

@app.route("/relatorio")
def relatorio():
    if not tem_perm("perm_relatorio"): return redirect("/")
    fs = FechamentoDia.query.order_by(FechamentoDia.data_fechamento.desc()).all()
    linhas = "".join("<tr><td>"+f.data.strftime("%d/%m/%Y")+"</td><td>Kz "+str(int(f.total_liquido))+"</td><td>Kz "+str(int(f.total_lucro or 0))+"</td><td>Kz "+str(int(f.caixa))+"</td><td>"+str(f.qtd_vendas)+"</td></tr>" for f in fs)
    return render_template_string(T, content='<div class="card"><h2>Relatorio</h2><table><tr><th>Data</th><th>Liquido</th><th>Lucro</th><th>Caixa</th><th>Vendas</th></tr>'+linhas+'</table></div>')

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
    barras = "".join('<div style="display:inline-block;width:28px;text-align:center;margin:0 2px"><div style="background:#1565c0;height:'+str(max(5,int(80*d[1]/max_v)))+'px;border-radius:3px"></div><div style="font-size:.65rem">'+d[0]+'</div></div>' for d in dias)
    return render_template_string(T, content='<div class="card"><h2>Relatorio Mensal</h2><p>Total liquido: <b>Kz '+str(int(total_mes))+'</b></p><p>Lucro: <b>Kz '+str(int(total_lucro))+'</b></p><div style="overflow-x:auto;margin-top:12px"><div style="display:flex;align-items:flex-end;height:100px">'+barras+'</div></div></div>')

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
    if request.method == "POST" and is_admin():
        db.session.add(Produto(nome=request.form["nome"], preco=float(request.form["preco"]), preco_compra=float(request.form.get("preco_compra",0)), quantidade=int(request.form["quantidade"]), stock_minimo=int(request.form.get("stock_minimo",5)), categoria_id=int(request.form["categoria"]) if request.form.get("categoria") else None))
        db.session.commit()
        return redirect("/produtos")
    ps = Produto.query.order_by(Produto.nome).all()
    cats = Categoria.query.all()
    cat_opts = "".join('<option value="'+str(c.id)+'">'+c.nome+'</option>' for c in cats)
    linhas = "".join("<tr><td>"+p.nome+"</td><td>"+(p.categoria.nome if p.categoria else "-")+"</td><td>Kz "+str(int(p.preco))+"</td><td>Kz "+str(int(p.preco_compra or 0))+"</td><td>"+str(p.quantidade)+"</td>"+("<td><a href='/editar/"+str(p.id)+"'>Editar</a></td>" if is_admin() else "")+"</tr>" for p in ps)
    form = '<form method="POST"><input name="nome" placeholder="Nome" required><select name="categoria"><option value="">Categoria</option>'+cat_opts+'</select><input type="number" name="preco" placeholder="Preco venda" required><input type="number" name="preco_compra" placeholder="Preco compra"><input type="number" name="quantidade" placeholder="Qtd" required><input type="number" name="stock_minimo" placeholder="Stock minimo" value="5"><button>Cadastrar</button></form>' if is_admin() else ""
    return render_template_string(T, content='<div class="card"><h2>Produtos</h2>'+form+'<table><tr><th>Nome</th><th>Categoria</th><th>Venda</th><th>Compra</th><th>Stock</th>'+("<th></th>" if is_admin() else "")+'</tr>'+linhas+'</table></div>')

@app.route("/editar/<int:id>", methods=["GET","POST"])
def editar(id):
    if not is_admin(): return redirect("/")
    p = Produto.query.get_or_404(id)
    if request.method == "POST":
        preco_antigo = p.preco
        p.nome = request.form["nome"]
        p.preco = float(request.form["preco"])
        p.preco_compra = float(request.form.get("preco_compra",0))
        p.quantidade = int(request.form["quantidade"])
        p.stock_minimo = int(request.form.get("stock_minimo",5))
        p.categoria_id = int(request.form["categoria"]) if request.form.get("categoria") else None
        if preco_antigo != p.preco:
            db.session.add(HistoricoPreco(produto_id=p.id, preco_antigo=preco_antigo, preco_novo=p.preco))
        db.session.commit()
        return redirect("/produtos")
    cats = Categoria.query.all()
    cat_opts = "".join('<option value="'+str(c.id)+'"'+(' selected' if p.categoria_id==c.id else '')+'>'+c.nome+'</option>' for c in cats)
    hist = HistoricoPreco.query.filter_by(produto_id=p.id).order_by(HistoricoPreco.data.desc()).limit(5).all()
    hist_linhas = "".join("<tr><td>"+h.data.strftime("%d/%m/%Y")+"</td><td>Kz "+str(int(h.preco_antigo))+"</td><td>Kz "+str(int(h.preco_novo))+"</td></tr>" for h in hist)
    return render_template_string(T, content='<div class="card"><h2>Editar</h2><form method="POST"><input name="nome" value="'+p.nome+'"><select name="categoria"><option value="">Categoria</option>'+cat_opts+'</select><input type="number" name="preco" value="'+str(p.preco)+'"><input type="number" name="preco_compra" value="'+str(p.preco_compra or 0)+'"><input type="number" name="quantidade" value="'+str(p.quantidade)+'"><input type="number" name="stock_minimo" value="'+str(p.stock_minimo or 5)+'"><button>Guardar</button></form></div><div class="card"><h2>Historico de Precos</h2><table><tr><th>Data</th><th>Antigo</th><th>Novo</th></tr>'+hist_linhas+'</table></div>')

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
    ps = Produto.query.order_by(Produto.nome).all()
    linhas = "".join("<tr><td>"+p.nome+"</td><td>"+str(p.quantidade)+"</td><td>"+str(p.stock_minimo or 5)+"</td><td><form method='POST' action='/ajustar/"+str(p.id)+"' style='display:inline'><input type='hidden' name='acao' value='mais'><button class='g s'>+</button></form> <form method='POST' action='/ajustar/"+str(p.id)+"' style='display:inline'><input type='hidden' name='acao' value='menos'><button class='r s'>-</button></form></td></tr>" for p in ps)
    return render_template_string(T, content='<div class="card"><h2>Stock</h2><table><tr><th>Produto</th><th>Qtd</th><th>Minimo</th><th>Ajustar</th></tr>'+linhas+'</table></div>')

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
    linhas = "".join("<tr><td>"+c.descricao+"</td><td>Kz "+str(int(c.valor))+"</td><td>"+c.data.strftime("%d/%m/%Y")+"</td></tr>" for c in items)
    return render_template_string(T, content='<div class="card"><h2>Compras</h2><form method="POST"><input name="descricao" placeholder="Descricao" required><input type="number" name="valor" placeholder="Valor" required><button>Registar</button></form><table><tr><th>Descricao</th><th>Valor</th><th>Data</th></tr>'+linhas+'</table></div>')

@app.route("/restos", methods=["GET","POST"])
def restos():
    if not is_admin(): return redirect("/")
    uid = session["user_id"]
    if request.method == "POST":
        db.session.add(Resto(user_id=uid, descricao=request.form["descricao"], valor=float(request.form["valor"])))
        db.session.commit()
        return redirect("/restos")
    items = Resto.query.filter_by(user_id=uid).order_by(Resto.data.desc()).all()
    linhas = "".join("<tr><td>"+r.descricao+"</td><td>Kz "+str(int(r.valor))+"</td><td>"+r.data.strftime("%d/%m/%Y")+"</td></tr>" for r in items)
    return render_template_string(T, content='<div class="card"><h2>Restos</h2><form method="POST"><input name="descricao" placeholder="Descricao" required><input type="number" name="valor" placeholder="Valor" required><button>Registar</button></form><table><tr><th>Descricao</th><th>Valor</th><th>Data</th></tr>'+linhas+'</table></div>')

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect("/login")
    if not is_admin():
        return render_template_string(T, content='<div class="card"><h2>Bem-vindo</h2><p>Usa o menu para vender.</p></div>')
    uid = session["user_id"]
    vendas = Venda.query.filter(db.func.date(Venda.data)==date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    lucro = sum(v.lucro or 0 for v in vendas)
    caixa = Caixa.query.filter_by(user_id=uid).first()
    cv = caixa.valor if caixa else 0
    inicio = date.today() - timedelta(days=6)
    semana = []
    for i in range(7):
        d = inicio + timedelta(days=i)
        total = sum(v.valor_total for v in Venda.query.filter(db.func.date(Venda.data)==d).all())
        semana.append((d.strftime("%d/%m"), int(total)))
    max_v = max([s[1] for s in semana] or [1]) or 1
    barras = "".join('<div style="display:inline-block;width:40px;text-align:center;margin:0 4px"><div style="background:#1565c0;height:'+str(max(5,int(80*s[1]/max_v)))+'px;border-radius:4px"></div><div style="font-size:.7rem">'+s[0]+'</div></div>' for s in semana)
    return render_template_string(T, content='<h2>Dashboard</h2><div class="grid"><div class="stat">Vendas Hoje<b>Kz '+str(int(bruto))+'</b></div><div class="stat">Lucro<b>Kz '+str(int(lucro))+'</b></div><div class="stat">Caixa<b>Kz '+str(int(cv))+'</b></div><div class="stat">N Vendas<b>'+str(len(vendas))+'</b></div></div><div class="card" style="margin-top:12px"><h2>Vendas da Semana</h2><div style="display:flex;align-items:flex-end;height:100px">'+barras+'</div></div><form method="POST" action="/reiniciar-dashboard" style="margin-top:12px"><button class="r">Reiniciar Dashboard</button></form>')

@app.route("/reiniciar-dashboard", methods=["POST"])
def reiniciar_dashboard():
    if not is_admin(): return redirect("/")
    Venda.query.filter(db.func.date(Venda.data)==date.today()).delete()
    Compra.query.filter(db.func.date(Compra.data)==date.today()).delete()
    Resto.query.filter(db.func.date(Resto.data)==date.today()).delete()
    db.session.commit()
    flash("Dashboard reiniciado")
    return redirect("/dashboard")

@app.route("/exportar")
def exportar():
    if not is_admin(): return redirect("/")
    return render_template_string(T, content='<div class="card"><h2>Exportar</h2><p><a href="/exportar-csv">Descarregar Excel (CSV)</a></p></div>')

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
        linhas += '<tr><td>'+u.nome+'</td><td>'+u.email+'</td><td>'+(u.tipo or "funcionario")+'</td><td><a href="/permissoes/'+str(u.id)+'">Permissoes</a> | <a href="/redefinir/'+str(u.id)+'">Senha</a> | <a href="/dar-tudo/'+str(u.id)+'">Dar tudo</a></td></tr>'
    return render_template_string(T, content='<div class="card"><h2>Utilizadores</h2><table><tr><th>Nome</th><th>Email</th><th>Tipo</th><th>Acoes</th></tr>'+linhas+'</table></div>')

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
        flash("Todas as permissoes dadas a "+u.nome)
    return redirect("/utilizadores")

@app.route("/permissoes/<int:id>", methods=["GET","POST"])
def permissoes(id):
    if not is_admin(): return redirect("/")
    u = Usuario.query.get_or_404(id)
    if u.tipo == "admin":
        return render_template_string(T, content='<div class="card"><p>O administrador tem acesso total.</p><a href="/utilizadores">Voltar</a></div>')
    if request.method == "POST":
        u.perm_historico = "perm_historico" in request.form
        u.perm_relatorio = "perm_relatorio" in request.form
        u.perm_lucro = "perm_lucro" in request.form
        u.perm_produtos = "perm_produtos" in request.form
        u.perm_stock = "perm_stock" in request.form
        u.perm_caixa = "perm_caixa" in request.form
        u.perm_hoje = "perm_hoje" in request.form
        db.session.commit()
        flash("Permissoes atualizadas para "+u.nome)
        return redirect("/utilizadores")
    checks = ""
    for p, label in [("perm_hoje","Hoje (finalizar dia)"),("perm_historico","Historico"),("perm_relatorio","Relatorio"),("perm_lucro","Lucro"),("perm_produtos","Produtos"),("perm_stock","Stock"),("perm_caixa","Caixa")]:
        checked = " checked" if getattr(u, p) else ""
        checks += '<label style="display:block;margin:8px 0"><input type="checkbox" name="'+p+'"'+checked+'> '+label+'</label>'
    return render_template_string(T, content='<div class="card"><h2>Permissoes de '+u.nome+'</h2><form method="POST">'+checks+'<button>Guardar</button></form><p style="margin-top:10px"><a href="/utilizadores">Voltar</a></p></div>')

@app.route("/redefinir/<int:id>", methods=["GET","POST"])
def redefinir(id):
    if not is_admin(): return redirect("/")
    u = Usuario.query.get_or_404(id)
    if request.method == "POST":
        u.senha = generate_password_hash(request.form["senha"])
        db.session.commit()
        flash("Senha redefinida para "+u.nome)
        return redirect("/utilizadores")
    return render_template_string(T, content='<div class="card"><h2>Redefinir senha de '+u.nome+'</h2><form method="POST"><input type="password" name="senha" placeholder="Nova senha" required><button>Guardar</button></form><p style="margin-top:10px"><a href="/utilizadores">Voltar</a></p></div>')

@app.route("/tornar-admin/<email>")
def tornar_admin(email):
    u = Usuario.query.filter_by(email=email).first()
    if u:
        u.tipo = "admin"
        db.session.commit()
        return "Admin definido para " + email
    return "Utilizador nao encontrado"

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
    return render_template_string(T, content='<div class="card" style="max-width:360px;margin:30px auto"><h2>Entrar</h2><form method="POST"><input type="email" name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button>Entrar</button></form><p style="text-align:center;margin-top:10px"><a href="/registrar">Criar conta</a></p></div>')

@app.route("/registrar", methods=["GET","POST"])
def registrar():
    if request.method == "POST":
        if not Usuario.query.filter_by(email=request.form["email"]).first():
            tipo = "admin" if Usuario.query.count() == 0 else "funcionario"
            db.session.add(Usuario(nome=request.form["nome"], email=request.form["email"], senha=generate_password_hash(request.form["senha"]), tipo=tipo))
            db.session.commit()
            flash("Conta criada")
            return redirect("/login")
        flash("Email ja existe")
    return render_template_string(T, content='<div class="card" style="max-width:360px;margin:30px auto"><h2>Criar Conta</h2><form method="POST"><input name="nome" placeholder="Nome" required><input type="email" name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button>Registar</button></form></div>')

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        try:
            db.session.execute(db.text("ALTER TABLE produto ADD COLUMN IF NOT EXISTS preco_compra FLOAT DEFAULT 0"))
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
            db.session.commit()
        except:
            db.session.rollback()
    app.run(host="0.0.0.0", port=5001, debug=True)