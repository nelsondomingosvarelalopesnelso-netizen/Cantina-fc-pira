@@ -1,14 +1,12 @@
import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "cantina-fc-pira-2026"
app.secret_key = "cantina-2026"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://neondb_owner:npg_VS5JzKpOFQ3e@ep-wild-cloud-b4vl2kuk-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
@@ -26,108 +24,257 @@ class Produto(db.Model):

class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    quantidade = db.Column(db.Integer)
    valor_total = db.Column(db.Float)
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
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    data = db.Column(db.Date)
    total_bruto = db.Column(db.Float)
    total_liquido = db.Column(db.Float)
    caixa = db.Column(db.Float)
    qtd_vendas = db.Column(db.Integer)
    data_fechamento = db.Column(db.DateTime, default=datetime.utcnow)

class Caixa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    valor = db.Column(db.Float, default=0)

class Compra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float)
    data = db.Column(db.DateTime, default=datetime.utcnow)

class Resto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float)
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
T = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cantina</title><style>*{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}body{background:#f5f5f5}.top{background:#1565c0;color:#fff;padding:10px}.nav{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}.nav a{background:rgba(255,255,255,.2);color:#fff;padding:5px 9px;border-radius:14px;text-decoration:none;font-size:.75rem}.c{max-width:900px;margin:0 auto;padding:10px}.card{background:#fff;border-radius:8px;padding:12px;margin-bottom:10px}input,button{width:100%;padding:9px;margin:3px 0;border-radius:6px;border:1px solid #ccc}button{background:#1565c0;color:#fff;border:none}.g{background:#00c853}.o{background:#ff9800}.r{background:#d32f2f}.s{width:auto;padding:5px 9px;font-size:12px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px}.box{border:2px solid #bbdefb;border-radius:8px;padding:8px;text-align:center}.stat{background:#fff;border-radius:8px;padding:10px;text-align:center;border-top:3px solid #1565c0}table{width:100%;border-collapse:collapse}th,td{padding:6px;border-bottom:1px solid #eee}</style></head><body>{% if session.get('user_id') %}<div class="top"><h1>Cantina FC Pira</h1><div class="nav"><a href="/">Vender</a><a href="/dashboard">Dashboard</a><a href="/hoje">Hoje</a><a href="/relatorio">Relatório</a><a href="/caixa">Caixa</a><a href="/produtos">Produtos</a><a href="/stock">Stock</a><a href="/compras">Compras</a><a href="/restos">Restos</a><a href="/logout">Sair</a></div></div>{% endif %}<div class="c">{% with messages = get_flashed_messages(with_categories=true) %}{% if messages %}{% for cat, msg in messages %}<div class="card">{{ msg }}</div>{% endfor %}{% endif %}{% endwith %}{{ content|safe }}</div></body></html>"""

def dia_fechado(uid):
    return FechamentoDia.query.filter_by(user_id=uid, data=date.today()).first() is not None

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if "user_id" not in session: return redirect(url_for("login"))
    if dia_fechado(session["user_id"]):
        content = '<div class="card">Dia finalizado.<form method="POST" action="/reiniciar"><button class="btn-laranja">Reiniciar</button></form></div>'
        return render_template_string(TEMPLATE, content=content)
    busca =
        return render_template_string(T, content='<div class="card">Dia finalizado<form method="POST" action="/reiniciar"><button class="o">Reiniciar</button></form></div>')
    busca = request.args.get("busca", "")
    q = Produto.query
    if busca: q = q.filter(Produto.nome.ilike("%"+busca+"%"))
    boxes = ""
    for p in q.order_by(Produto.nome).all():
        boxes += '<div class="box"><b>'+p.nome+'</b><div>Venda: '+str(int(p.preco))+'</div><div>Compra: '+str(int(p.preco_compra or 0))+'</div><div>Stock: '+str(p.quantidade)+'</div><form method="POST" action="/vender"><input type="hidden" name="produto_id" value="'+str(p.id)+'"><button class="g s">Vender</button></form><form method="POST" action="/devolver/'+str(p.id)+'"><button class="o s">Devolver</button></form><form method="POST" action="/eliminar/'+str(p.id)+'"><button class="r s">Eliminar</button></form></div>'
    return render_template_string(T, content='<div class="card"><h2>Vender</h2><form method="GET"><input name="busca" placeholder="Pesquisar" value="'+busca+'"><button>OK</button></form><div class="grid">'+boxes+'</div></div>')

@app.route("/vender", methods=["POST"])
def vender():
    if "user_id" not in session or dia_fechado(session["user_id"]): return redirect("/")
    p = Produto.query.get(int(request.form["produto_id"]))
    if p and p.quantidade >= 1:
        db.session.add(Venda(produto_id=p.id, user_id=session["user_id"], quantidade=1, valor_total=p.preco))
        p.quantidade -= 1
        db.session.commit()
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
    return redirect("/")

@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    if "user_id" not in session: return redirect("/login")
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
    if "user_id" not in session: return redirect("/login")
    uid = session["user_id"]
    vendas = Venda.query.filter(Venda.user_id==uid, db.func.date(Venda.data)==date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    linhas = "".join("<tr><td>"+v.produto.nome+"</td><td>"+str(v.quantidade)+"</td><td>"+str(int(v.valor_total))+"</td></tr>" for v in vendas)
    return render_template_string(T, content='<div class="card"><h2>Hoje</h2><p>Bruto: '+str(int(bruto))+'</p><p>Líquido: '+str(int(max(0,bruto-5000)))+'</p><form method="POST" action="/finalizar"><button class="o">Finalizar</button></form><table>'+linhas+'</table></div>')

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
    return redirect("/hoje")

@app.route("/relatorio")
def relatorio():
    if "user_id" not in session: return redirect("/login")
    fs = FechamentoDia.query.filter_by(user_id=session["user_id"]).order_by(FechamentoDia.data_fechamento.desc()).all()
    linhas = "".join("<tr><td>"+f.data.strftime("%d/%m/%Y")+"</td><td>"+str(int(f.total_liquido))+"</td><td>"+str(int(f.caixa))+"</td><td>"+str(f.qtd_vendas)+"</td></tr>" for f in fs)
    return render_template_string(T, content='<div class="card"><h2>Relatório</h2><table>'+linhas+'</table></div>')

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
        return redirect("/caixa")
    return render_template_string(T, content='<div class="card"><h2>Caixa</h2><p>'+str(int(c.valor))+'</p><form method="POST"><input type="number" name="valor" value="'+str(c.valor)+'"><button>Alterar</button></form></div>')

@app.route("/produtos", methods=["GET","POST"])
def produtos():
    if "user_id" not in session: return redirect("/login")
    if request.method == "POST":
        db.session.add(Produto(nome=request.form["nome"], preco=float(request.form["preco"]), preco_compra=float(request.form.get("preco_compra",0)), quantidade=int(request.form["quantidade"])))
        db.session.commit()
        return redirect("/produtos")
    ps = Produto.query.order_by(Produto.nome).all()
    linhas = "".join("<tr><td>"+p.nome+"</td><td>"+str(int(p.preco))+"</td><td>"+str(int(p.preco_compra or 0))+"</td><td>"+str(p.quantidade)+"</td><td><a href='/editar/"+str(p.id)+"'>Editar</a></td></tr>" for p in ps)
    return render_template_string(T, content='<div class="card"><h2>Produtos</h2><form method="POST"><input name="nome" placeholder="Nome" required><input type="number" name="preco" placeholder="Preço venda" required><input type="number" name="preco_compra" placeholder="Preço compra"><input type="number" name="quantidade" placeholder="Qtd" required><button>Cadastrar</button></form><table>'+linhas+'</table></div>')

@app.route("/editar/<int:id>", methods=["GET","POST"])
def editar(id):
    if "user_id" not in session: return redirect("/login")
    p = Produto.query.get_or_404(id)
    if request.method == "POST":
        p.nome = request.form["nome"]
        p.preco = float(request.form["preco"])
        p.preco_compra = float(request.form.get("preco_compra",0))
        p.quantidade = int(request.form["quantidade"])
        db.session.commit()
        return redirect("/produtos")
    return render_template_string(T, content='<div class="card"><h2>Editar</h2><form method="POST"><input name="nome" value="'+p.nome+'"><input type="number" name="preco" value="'+str(p.preco)+'"><input type="number" name="preco_compra" value="'+str(p.preco_compra or 0)+'"><input type="number" name="quantidade" value="'+str(p.quantidade)+'"><button>Guardar</button></form></div>')

@app.route("/stock")
def stock():
    if "user_id" not in session: return redirect("/login")
    ps = Produto.query.order_by(Produto.nome).all()
    linhas = "".join("<tr><td>"+p.nome+"</td><td>"+str(p.quantidade)+"</td><td><form method='POST' action='/ajustar/"+str(p.id)+"'><input type='hidden' name='acao' value='mais'><button class='g s'>+</button></form><form method='POST' action='/ajustar/"+str(p.id)+"'><input type='hidden' name='acao' value='menos'><button class='r s'>-</button></form></td></tr>" for p in ps)
    return render_template_string(T, content='<div class="card"><h2>Stock</h2><table>'+linhas+'</table></div>')

@app.route("/ajustar/<int:id>", methods=["POST"])
def ajustar(id):
    if "user_id" not in session: return redirect("/login")
    p = Produto.query.get_or_404(id)
    p.quantidade = p.quantidade+1 if request.form["acao"]=="mais" else max(0, p.quantidade-1)
    db.session.commit()
    return redirect("/stock")

@app.route("/compras", methods=["GET","POST"])
def compras():
    if "user_id" not in session: return redirect("/login")
    uid = session["user_id"]
    if request.method == "POST":
        db.session.add(Compra(user_id=uid, descricao=request.form["descricao"], valor=float(request.form["valor"])))
        db.session.commit()
        return redirect("/compras")
    items = Compra.query.filter_by(user_id=uid).order_by(Compra.data.desc()).all()
    linhas = "".join("<tr><td>"+c.descricao+"</td><td>"+str(int(c.valor))+"</td></tr>" for c in items)
    return render_template_string(T, content='<div class="card"><h2>Compras</h2><form method="POST"><input name="descricao" placeholder="Descrição" required><input type="number" name="valor" placeholder="Valor" required><button>Registar</button></form><table>'+linhas+'</table></div>')

@app.route("/restos", methods=["GET","POST"])
def restos():
    if "user_id" not in session: return redirect("/login")
    uid = session["user_id"]
    if request.method == "POST":
        db.session.add(Resto(user_id=uid, descricao=request.form["descricao"], valor=float(request.form["valor"])))
        db.session.commit()
        return redirect("/restos")
    items = Resto.query.filter_by(user_id=uid).order_by(Resto.data.desc()).all()
    linhas = "".join("<tr><td>"+r.descricao+"</td><td>"+str(int(r.valor))+"</td></tr>" for r in items)
    return render_template_string(T, content='<div class="card"><h2>Restos</h2><form method="POST"><input name="descricao" placeholder="Descrição" required><input type="number" name="valor" placeholder="Valor" required><button>Registar</button></form><table>'+linhas+'</table></div>')

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect("/login")
    uid = session["user_id"]
    vendas = Venda.query.filter(Venda.user_id==uid, db.func.date(Venda.data)==date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    caixa = Caixa.query.filter_by(user_id=uid).first()
    cv = caixa.valor if caixa else 0
    comps = Compra.query.filter(Compra.user_id==uid, db.func.date(Compra.data)==date.today()).all()
    rests = Resto.query.filter(Resto.user_id==uid, db.func.date(Resto.data)==date.today()).all()
    content = '<div class="grid"><div class="stat">Vendas<br><b>'+str(int(bruto))+'</b></div><div class="stat">Nº<br><b>'+str(len(vendas))+'</b></div><div class="stat">Caixa<br><b>'+str(int(cv))+'</b></div><div class="stat">Compras<br><b>'+str(int(sum(c.valor for c in comps)))+'</b></div><div class="stat">Restos<br><b>'+str(int(sum(r.valor for r in rests)))+'</b></div></div><form method="POST" action="/reiniciar-dashboard"><button class="r">Reiniciar Dashboard</button></form>'
    return render_template_string(T, content=content)

@app.route("/reiniciar-dashboard", methods=["POST"])
def reiniciar_dashboard():
    if "user_id" not in session: return redirect("/login")
    uid = session["user_id"]
    Venda.query.filter(Venda.user_id==uid, db.func.date(Venda.data)==date.today()).delete()
    Compra.query.filter(Compra.user_id==uid, db.func.date(Compra.data)==date.today()).delete()
    Resto.query.filter(Resto.user_id==uid, db.func.date(Resto.data)==date.today()).delete()
    db.session.commit()
    return redirect("/dashboard")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = Usuario.query.filter_by(email=request.form["email"]).first()
        if u and check_password_hash(u.senha, request.form["senha"]):
            session["user_id"] = u.id
            session["nome"] = u.nome
            return redirect("/dashboard")
    return render_template_string(T, content='<div class="card"><h2>Entrar</h2><form method="POST"><input type="email" name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button>Entrar</button></form><a href="/registrar">Criar conta</a></div>')

@app.route("/registrar", methods=["GET","POST"])
def registrar():
    if request.method == "POST":
        if not Usuario.query.filter_by(email=request.form["email"]).first():
            db.session.add(Usuario(nome=request.form["nome"], email=request.form["email"], senha=generate_password_hash(request.form["senha"])))
            db.session.commit()
            return redirect("/login")
    return render_template_string(T, content='<div class="card"><h2>Criar conta</h2><form method="POST"><input name="nome" placeholder="Nome" required><input type="email" name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button>Registar</button></form></div>')

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        try:
            db.session.execute(db.text("ALTER TABLE produto ADD COLUMN IF NOT EXISTS preco_compra FLOAT DEFAULT 0"))
            db.session.commit()
        except:
            db.session.rollback()
    app.run(host="0.0.0.0", port=5001, debug=True)