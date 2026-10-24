from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

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

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    preco_compra = db.Column(db.Float, default=0)
    quantidade = db.Column(db.Integer, default=0)

class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    quantidade = db.Column(db.Integer)
    valor_total = db.Column(db.Float)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    produto = db.relationship("Produto")

class FechamentoDia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    data = db.Column(db.Date)
    total_bruto = db.Column(db.Float)
    total_liquido = db.Column(db.Float)
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

T = """<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Cantina FC Pira</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
body{background:#f0f2f5;color:#1a1a1a}
.top{background:linear-gradient(135deg,#0d47a1,#1565c0);color:#fff;padding:14px 16px;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,.15)}
.top h1{font-size:1.15rem;font-weight:600}
.nav{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.nav a{background:rgba(255,255,255,.18);color:#fff;padding:6px 12px;border-radius:20px;text-decoration:none;font-size:.78rem;font-weight:500}
.nav a:hover{background:#fff;color:#1565c0}
.c{max-width:960px;margin:0 auto;padding:14px}
.card{background:#fff;border-radius:12px;padding:16px;margin-bottom:14px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.card h2{font-size:1.05rem;margin-bottom:12px;color:#0d47a1}
input,button{width:100%;padding:11px;margin:5px 0;border-radius:8px;border:1px solid #ddd;font-size:15px}
button{background:#1565c0;color:#fff;border:none;font-weight:600;cursor:pointer}
button:hover{opacity:.9}
.g{background:#2e7d32}.o{background:#ef6c00}.r{background:#c62828}
.s{width:auto;padding:7px 12px;font-size:13px;margin:2px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));gap:12px}
.box{background:#fff;border:1.5px solid #e3f2fd;border-radius:12px;padding:12px;text-align:center;transition:box-shadow .2s}
.box:hover{box-shadow:0 4px 12px rgba(21,101,192,.12)}
.box b{display:block;font-size:.95rem;color:#0d47a1;margin-bottom:4px}
.box div{font-size:.8rem;color:#546e7a;margin:2px 0}
.stat{background:#fff;border-radius:12px;padding:14px;text-align:center;border-top:4px solid #1565c0;box-shadow:0 1px 4px rgba(0,0,0,.05)}
.stat b{display:block;font-size:1.3rem;margin-top:4px;color:#0d47a1}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th{background:#e3f2fd;padding:8px;text-align:left;font-weight:600}
td{padding:8px;border-bottom:1px solid #eee}
.flash{background:#e8f5e9;color:#1b5e20;padding:10px 14px;border-radius:8px;margin-bottom:12px;font-size:.9rem}
</style>
</head>
<body>
{% if session.get('user_id') %}
<div class="top">
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
<div class="c">
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for cat, msg in messages %}
                <div class="flash">{{ msg }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    {{ content|safe }}
</div>
</body>
</html>"""

def dia_fechado(uid):
    return FechamentoDia.query.filter_by(user_id=uid, data=date.today()).first() is not None

@app.route("/")
def index():
    if "user_id" not in session: return redirect(url_for("login"))
    if dia_fechado(session["user_id"]):
        return render_template_string(T, content='<div class="card">Dia finalizado<form method="POST" action="/reiniciar"><button class="o">Reiniciar Venda</button></form></div>')
    busca = request.args.get("busca", "")
    q = Produto.query
    if busca: q = q.filter(Produto.nome.ilike("%"+busca+"%"))
    boxes = ""
    for p in q.order_by(Produto.nome).all():
        boxes += '<div class="box"><b>'+p.nome+'</b><div>Venda: Kz '+str(int(p.preco))+'</div><div>Compra: Kz '+str(int(p.preco_compra or 0))+'</div><div>Stock: '+str(p.quantidade)+'</div><form method="POST" action="/vender"><input type="hidden" name="produto_id" value="'+str(p.id)+'"><button class="g s">Vender</button></form><form method="POST" action="/devolver/'+str(p.id)+'"><button class="o s">Devolver</button></form><form method="POST" action="/eliminar/'+str(p.id)+'"><button class="r s">Eliminar</button></form></div>'
    return render_template_string(T, content='<div class="card"><h2>Vender</h2><form method="GET"><input name="busca" placeholder="Pesquisar produto..." value="'+busca+'"><button>Pesquisar</button></form><div class="grid">'+boxes+'</div></div>')

@app.route("/vender", methods=["POST"])
def vender():
    if "user_id" not in session or dia_fechado(session["user_id"]): return redirect("/")
    p = Produto.query.get(int(request.form["produto_id"]))
    if p and p.quantidade >= 1:
        db.session.add(Venda(produto_id=p.id, user_id=session["user_id"], quantidade=1, valor_total=p.preco))
        p.quantidade -= 1
        db.session.commit()
        flash("Vendido: "+p.nome)
    else:
        flash("Sem stock")
    return redirect("/")

@app.route("/devolver/<int:id>", methods=["POST"])
def devolver(id):
    if "user_id" not in session: return redirect("/login")
    p = Produto.query.get_or_404(id)
    v = Venda.query.filter_by(produto_id=id, user_id=session["user_id"]).order_by(Venda.data.desc()).first()
    if v:
        p.quantidade += v.quantidade
        db.session.delete(v)
        db.session.commit()
        flash("Devolvido")
    return redirect("/")

@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    if "user_id" not in session: return redirect("/login")
    db.session.delete(Produto.query.get_or_404(id))
    db.session.commit()
    flash("Produto eliminado")
    return redirect("/")

@app.route("/reiniciar", methods=["POST"])
def reiniciar():
    if "user_id" not in session: return redirect("/login")
    FechamentoDia.query.filter_by(user_id=session["user_id"], data=date.today()).delete()
    db.session.commit()
    flash("Venda reiniciada")
    return redirect("/")

@app.route("/hoje")
def hoje():
    if "user_id" not in session: return redirect("/login")
    uid = session["user_id"]
    vendas = Venda.query.filter(Venda.user_id==uid, db.func.date(Venda.data)==date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    linhas = "".join("<tr><td>"+v.produto.nome+"</td><td>"+str(v.quantidade)+"</td><td>Kz "+str(int(v.valor_total))+"</td></tr>" for v in vendas)
    return render_template_string(T, content='<div class="card"><h2>Relatório do Dia</h2><p>Bruto: <strong>Kz '+str(int(bruto))+'</strong></p><p>Líquido: <strong>Kz '+str(int(max(0,bruto-5000)))+'</strong></p><form method="POST" action="/finalizar"><button class="o">Finalizar Dia</button></form><table><tr><th>Produto</th><th>Qtd</th><th>Valor</th></tr>'+linhas+'</table></div>')

@app.route("/finalizar", methods=["POST"])
def finalizar():
    if "user_id" not in session: return redirect("/login")
    uid = session["user_id"]
    vendas = Venda.query.filter(Venda.user_id==uid, db.func.date(Venda.data)==date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    caixa = Caixa.query.filter_by(user_id=uid).first()
    if not caixa:
        caixa = Caixa(user_id=uid, valor=0)
        db.session.add(caixa)
    caixa.valor += 5000
    db.session.add(FechamentoDia(user_id=uid, data=date.today(), total_bruto=bruto, total_liquido=max(0,bruto-5000), caixa=caixa.valor, qtd_vendas=len(vendas)))
    db.session.commit()
    flash("Dia finalizado")
    return redirect("/hoje")

@app.route("/relatorio")
def relatorio():
    if "user_id" not in session: return redirect("/login")
    fs = FechamentoDia.query.filter_by(user_id=session["user_id"]).order_by(FechamentoDia.data_fechamento.desc()).all()
    linhas = "".join("<tr><td>"+f.data.strftime("%d/%m/%Y")+"</td><td>Kz "+str(int(f.total_liquido))+"</td><td>Kz "+str(int(f.caixa))+"</td><td>"+str(f.qtd_vendas)+"</td></tr>" for f in fs)
    return render_template_string(T, content='<div class="card"><h2>Relatório</h2><table><tr><th>Data</th><th>Líquido</th><th>Caixa</th><th>Vendas</th></tr>'+linhas+'</table></div>')

@app.route("/caixa", methods=["GET","POST"])
def caixa():
    if "user_id" not in session: return redirect("/login")
    uid = session["user_id"]
    c = Caixa.query.filter_by(user_id=uid).first()
    if not c:
        c = Caixa(user_id=uid, valor=0)
        db.session.add(c)
        db.session.commit()
    if request.method == "POST":
        c.valor = float(request.form["valor"])
        db.session.commit()
        flash("Caixa atualizada")
        return redirect("/caixa")
    return render_template