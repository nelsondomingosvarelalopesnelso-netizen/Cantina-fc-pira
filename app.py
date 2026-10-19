from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "cantina-fc-pira-2026"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///negocio.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), default="funcionario")

class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), unique=True, nullable=False)
    produtos = db.relationship("Produto", backref="categoria", lazy=True)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=0)
    estoque_minimo = db.Column(db.Integer, default=5)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"))

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
    qtd_vendas = db.Column(db.Integer, nullable=False)
    valor_caixa = db.Column(db.Float, default=0)
    data_fechamento = db.Column(db.DateTime, default=datetime.utcnow)

class Caixa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), unique=True, nullable=False)
    valor = db.Column(db.Float, default=0.0)

class Movimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)

TEMPLATE = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Cantina FC Pira</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
        body { background: #f4f6f9; color: #1a237e; }
        .topbar { background: linear-gradient(135deg, #0d47a1, #1565c0); color: white; padding: 12px 16px; position: sticky; top: 0; z-index: 100; }
        .topbar h1 { font-size: 1.2rem; }
        .nav { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
        .nav a { background: rgba(255,255,255,0.2); color: white; padding: 6px 11px; border-radius: 18px; text-decoration: none; font-size: 0.78rem; }
        .nav a:hover { background: white; color: #0d47a1; }
        .container { max-width: 1000px; margin: 0 auto; padding: 12px; }
        .card { background: white; border-radius: 12px; padding: 14px; margin-bottom: 12px; box-shadow: 0 1px 8px rgba(0,0,0,0.06); }
        input, select, button { width: 100%; padding: 11px; margin: 4px 0; border-radius: 8px; border: 1px solid #ccc; font-size: 15px; }
        button { background: #0d47a1; color: white; border: none; font-weight: 600; cursor: pointer; }
        .btn-verde { background: #00c853; }
        .btn-laranja { background: #ff9800; color: #333; }
        .btn-vermelho { background: #d32f2f; }
        .btn-pequeno { width: auto; padding: 6px 12px; font-size: 13px; margin: 2px; }
        .flash { background: #e8f5e9; color: #1b5e20; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
        .flash.erro { background: #ffebee; color: #b71c1c; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
        .produto-box { background: #fff; border: 2px solid #e3f2fd; border-radius: 12px; padding: 12px; text-align: center; }
        .produto-box h3 { font-size: 0.95rem; margin-bottom: 4px; color: #0d47a1; }
        .produto-box .preco { font-weight: 700; color: #1565c0; }
        .produto-box .stock { font-size: 0.8rem; color: #546e7a; margin: 4px 0; }
        .stat { background: white; border-radius: 12px; padding: 14px; text-align: center; border-top: 4px solid #0d47a1; }
        .stat.verde { border-top-color: #00c853; }
        .stat.laranja { border-top-color: #ff9800; }
        .stat .valor { font-size: 1.4rem; font-weight: 700; }
        .stat .label { font-size: 0.75rem; color: #546e7a; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { background: #e3f2fd; padding: 8px; text-align: left; }
        td { padding: 8px; border-bottom: 1px solid #eee; }
        .caixa-box { background: #fff3e0; border: 2px solid #ff9800; padding: 14px; border-radius: 12px; text-align: center; }
        .caixa-box .valor { font-size: 1.6rem; font-weight: 700; color: #e65100; }
        .fechado { background: #e8f5e9; border: 2px solid #00c853; padding: 14px; border-radius: 12px; text-align: center; }
    </style>
</head>
<body>
    {% if session.get('user_id') %}
    <div class="topbar">
        <h1>Cantina FC Pira</h1>
        <div style="font-size:0.75rem;">Olá, {{ session.get('nome') }}</div>
        <div class="nav">
            <a href="/">Vender</a>
            <a href="/dashboard">Dashboard</a>
            <a href="/hoje">Hoje</a>
            <a href="/relatorio">Relatório</a>
            <a href="/caixa">Caixa</a>
            <a href="/movimentos">Compra / Restos</a>
            <a href="/historico">Histórico</a>
            <a href="/produtos">Produtos</a>
            <a href="/stock">Stock</a>
            <a href="/categorias">Categorias</a>
            <a href="/logout">Sair</a>
        </div>
    </div>
    {% endif %}
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for cat, msg in messages %}
                    <div class="flash {{ 'erro' if cat == 'erro' else '' }}">{{ msg }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {{ content|safe }}
    </div>
</body>
</html>
"""

def dia_fechado(user_id):
    return FechamentoDia.query.filter_by(user_id=user_id, data=date.today()).first() is not None

def get_caixa(user_id):
    caixa = Caixa.query.filter_by(user_id=user_id).first()
    if not caixa:
        caixa = Caixa(user_id=user_id, valor=0)
        db.session.add(caixa)
        db.session.commit()
    return caixa

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if dia_fechado(session["user_id"]):
        content = '<div class="fechado">Dia finalizado.</div><form method="POST" action="/reiniciar"><button class="btn-laranja">Reiniciar Venda</button></form>'
        return render_template_string(TEMPLATE, content=content)

    produtos = Produto.query.order_by(Produto.nome).all()
    boxes = ""
    for p in produtos:
        boxes += '<div class="produto-box"><h3>' + p.nome + '</h3><div class="preco">Kz ' + str(int(p.preco)) + '</div><div class="stock">Stock: ' + str(p.quantidade) + '</div>'
        boxes += '<form method="POST" action="/vender" style="margin:0;"><input type="hidden" name="produto_id" value="' + str(p.id) + '"><button class="btn-verde btn-pequeno">Vender</button></form>'
        boxes += '<form method="POST" action="/devolver/' + str(p.id) + '" style="margin:0;display:inline;"><button class="btn-laranja btn-pequeno">Devolver</button></form>'
        boxes += '<form method="POST" action="/eliminar_produto/' + str(p.id) + '" style="margin:0;display:inline;" onsubmit="return confirm(\'Eliminar?\')"><button class="btn-vermelho btn-pequeno">Eliminar</button></form></div>'

    content = '<div class="card"><h2>Vender</h2><div class="grid">' + (boxes if boxes else '<p>Nenhum produto</p>') + '</div></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/vender", methods=["POST"])
def vender():
    if "user_id" not in session or dia_fechado(session["user_id"]):
        return redirect(url_for("index"))
    p = Produto.query.get(int(request.form["produto_id"]))
    if p and p.quantidade >= 1:
        db.session.add(Venda(produto_id=p.id, user_id=session["user_id"], quantidade=1, valor_total=p.preco))
        p.quantidade -= 1
        db.session.commit()
        flash("Vendido: 1x " + p.nome)
    else:
        flash("Sem stock", "erro")
    return redirect(url_for("index"))

@app.route("/devolver/<int:id>", methods=["POST"])
def devolver(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    p = Produto.query.get_or_404(id)
    venda = Venda.query.filter_by(produto_id=id, user_id=session["user_id"]).filter(db.func.date(Venda.data) == date.today()).order_by(Venda.data.desc()).first()
    if venda:
        p.quantidade += venda.quantidade
        db.session.delete(venda)
        db.session.commit()
        flash("Devolvido")
    else:
        flash("Nada para devolver", "erro")
    return redirect(url_for("index"))

@app.route("/eliminar_produto/<int:id>", methods=["POST"])
def eliminar_produto(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    p = Produto.query.get_or_404(id)
    if Venda.query.filter_by(produto_id=id).first():
        flash("Tem vendas, não pode eliminar", "erro")
    else:
        db.session.delete(p)
        db.session.commit()
        flash("Eliminado")
    return redirect(url_for("index"))

@app.route("/reiniciar", methods=["POST"])
def reiniciar():
    if "user_id" not in session:
        return redirect(url_for("login"))
    FechamentoDia.query.filter_by(user_id=session["user_id"], data=date.today()).delete()
    db.session.commit()
    flash("Venda reiniciada")
    return redirect(url_for("index"))

@app.route("/reiniciar_tudo", methods=["POST"])
def reiniciar_tudo():
    if "user_id" not in session:
        return redirect(url_for("login"))
    uid = session["user_id"]
    Venda.query.filter(Venda.user_id == uid, db.func.date(Venda.data) == date.today()).delete()
    FechamentoDia.query.filter_by(user_id=uid, data=date.today()).delete()
    db.session.commit()
    flash("Dashboard reiniciado. Relatório guardado.")
    return redirect(url_for("dashboard"))

@app.route("/hoje")
def hoje():
    if "user_id" not in session:
        return redirect(url_for("login"))
    uid = session["user_id"]
    vendas = Venda.query.filter(Venda.user_id == uid, db.func.date(Venda.data) == date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    liquido = max(0, bruto - 5000)
    fechado = dia_fechado(uid)
    caixa = get_caixa(uid)
    linhas = ""
    for v in vendas:
        linhas += "<tr><td>" + v.produto.nome + "</td><td>" + str(v.quantidade) + "</td><td>Kz " + str(int(v.valor_total)) + "</td><td>" + v.data.strftime("%H:%M") + "</td></tr>"
    content = '<div class="caixa-box"><div>Caixa</div><div class="valor">Kz ' + str(int(caixa.valor)) + '</div></div>'
    content += '<div class="card"><h2>Relatório do Dia</h2><p>Vendas: <strong>Kz ' + str(int(bruto)) + '</strong></p><p>Líquido (após -5.000): <strong>Kz ' + str(int(liquido)) + '</strong></p>'
    if fechado:
        content += '<div class="fechado">Dia finalizado</div>'
    content += '<form method="POST" action="/finalizar"><button class="btn-laranja">Finalizar Dia (+5.000 Kz à caixa)</button></form>'
    content += '<table style="margin-top:10px;"><tr><th>Produto</th><th>Qtd</th><th>Valor</th><th>Hora</th></tr>' + (linhas if linhas else "<tr><td colspan=4>Nenhuma</td></tr>") + '</table></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/finalizar", methods=["POST"])
def finalizar():
    if "user_id" not in session:
        return redirect(url_for("login"))
    uid = session["user_id"]
    vendas = Venda.query.filter(Venda.user_id == uid, db.func.date(Venda.data) == date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    liquido = max(0, bruto - 5000)
    caixa = get_caixa(uid)
    db.session.add(FechamentoDia(
        user_id=uid,
        data=date.today(),
        total_bruto=bruto,
        total_liquido=liquido,
        qtd_vendas=len(vendas),
        valor_caixa=caixa.valor + 5000
    ))
    caixa.valor += 5000
    db.session.commit()
    flash("Dia finalizado! Líquido: Kz " + str(int(liquido)) + " | +5.000 Kz na caixa")
    return redirect(url_for("hoje"))

@app.route("/relatorio")
def relatorio():
    if "user_id" not in session:
        return redirect(url_for("login"))
    uid = session["user_id"]
    fechamentos = FechamentoDia.query.filter_by(user_id=uid).order_by(FechamentoDia.data_fechamento.desc()).all()
    linhas = ""
    for f in fechamentos:
        linhas += '<tr><td>' + f.data.strftime("%d/%m/%Y") + '</td><td>' + f.data_fechamento.strftime("%H:%M") + '</td><td>Kz ' + str(int(f.total_bruto)) + '</td><td>Kz ' + str(int(f.total_liquido)) + '</td><td>Kz ' + str(int(f.valor_caixa)) + '</td><td>' + str(f.qtd_vendas) + '</td></tr>'
    content = '<div class="card"><h2>Relatório de Dias Finalizados</h2><table><tr><th>Data</th><th>Hora</th><th>Vendas</th><th>Líquido</th><th>Caixa</th><th>Nº Vendas</th></tr>' + (linhas if linhas else "<tr><td colspan=6>Nenhum relatório</td></tr>") + '</table></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/caixa")
def caixa():
    if "user_id" not in session:
        return redirect(url_for("login"))
    caixa = get_caixa(session["user_id"])
    content = '<div class="caixa-box"><div>Valor na Caixa</div><div class="valor">Kz ' + str(int(caixa.valor)) + '</div></div>'
    content += '<div class="card"><h2>Alterar Caixa</h2><form method="POST" action="/editar_caixa"><input type="number" step="0.01" name="valor" value="' + str(caixa.valor) + '" required><button>Alterar</button></form></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/editar_caixa", methods=["POST"])
def editar_caixa():
    if "user_id" not in session:
        return redirect(url_for("login"))
    caixa = get_caixa(session["user_id"])
    caixa.valor = float(request.form["valor"])
    db.session.commit()
    flash("Caixa alterada")
    return redirect(url_for("caixa"))

@app.route("/stock")
def stock():
    if "user_id" not in session:
        return redirect(url_for("login"))
    produtos = Produto.query.order_by(Produto.nome).all()
    linhas = ""
    for p in produtos:
        linhas += '<tr><td>' + p.nome + '</td><td>' + str(p.quantidade) + '</td><td>'
        linhas += '<form method="POST" action="/ajustar_stock/' + str(p.id) + '" style="display:inline;"><input type="hidden" name="acao" value="mais"><button class="btn-pequeno btn-verde">+</button></form> '
        linhas += '<form method="POST" action="/ajustar_stock/' + str(p.id) + '" style="display:inline;"><input type="hidden" name="acao" value="menos"><button class="btn-pequeno btn-vermelho">-</button></form></td></tr>'
    content = '<div class="card"><h2>Stock</h2><table><tr><th>Produto</th><th>Qtd</th><th>Ajustar</th></tr>' + linhas + '</table></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/ajustar_stock/<int:id>", methods=["POST"])
def ajustar_stock(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    p = Produto.query.get_or_404(id)
    if request.form["acao"] == "mais":
        p.quantidade += 1
    else:
        p.quantidade = max(0, p.quantidade - 1)
    db.session.commit()
    return redirect(url_for("stock"))

@app.route("/produtos", methods=["GET","POST"])
def produtos():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        cat_id = request.form.get("categoria_id") or None
        db.session.add(Produto(nome=request.form["nome"], preco=float(request.form["preco"]), quantidade=int(request.form["quantidade"]), categoria_id=int(cat_id) if cat_id else None))
        db.session.commit()
        flash("Cadastrado")
        return redirect(url_for("produtos"))
    prods = Produto.query.order_by(Produto.nome).all()
    cats = Categoria.query.all()
    linhas = ""
    for p in prods:
        linhas += '<tr><td>' + p.nome + '</td><td>Kz ' + str(int(p.preco)) + '</td><td>' + str(p.quantidade) + '</td><td><a href="/eliminar_produto_lista/' + str(p.id) + '" onclick="return confirm(\'Eliminar?\')">Eliminar</a></td></tr>'
    opts = ""
    for c in cats:
        opts += '<option value="' + str(c.id) + '">' + c.nome + '</option>'
    content = '<div class="card"><h2>Cadastrar Produto</h2><form method="POST"><input name="nome" placeholder="Nome" required><select name="categoria_id"><option value="">Sem categoria</option>' + opts + '</select><input type="number" step="0.01" name="preco" placeholder="Preço" required><input type="number" name="quantidade" placeholder="Quantidade" required><button>Cadastrar</button></form></div>'
    content += '<div class="card"><table><tr><th>Nome</th><th>Preço</th><th>Stock</th><th></th></tr>' + linhas + '</table></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/eliminar_produto_lista/<int:id>")
def eliminar_produto_lista(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    p = Produto.query.get_or_404(id)
    if not Venda.query.filter_by(produto_id=id).first():
        db.session.delete(p)
        db.session.commit()
        flash("Eliminado")
    else:
        flash("Tem vendas", "erro")
    return redirect(url_for("produtos"))

@app.route("/movimentos", methods=["GET", "POST"])
def movimentos():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        db.session.add(Movimento(user_id=session["user_id"], tipo=request.form["tipo"], descricao=request.form.get("descricao",""), valor=float(request.form["valor"])))
        db.session.commit()
        flash("Registado")
        return redirect(url_for("movimentos"))
    movs = Movimento.query.filter_by(user_id=session["user_id"]).order_by(Movimento.data.desc()).limit(30).all()
    linhas = ""
    for m in movs:
        linhas += '<tr><td>' + m.data.strftime("%d/%m %H:%M") + '</td><td>' + m.tipo + '</td><td>' + (m.descricao or "-") + '</td><td>Kz ' + str(int(m.valor)) + '</td><td><a href="/eliminar_movimento/' + str(m.id) + '">Eliminar</a></td></tr>'
    content = '<div class="card"><h2>Compra / Restos</h2><form method="POST"><select name="tipo"><option value="compra">Compra</option><option value="resto">Resto</option></select><input name="descricao" placeholder="Descrição"><input type="number" step="0.01" name="valor" placeholder="Valor" required><button>Registar</button></form></div>'
    content += '<div class="card"><table><tr><th>Data</th><th>Tipo</th><th>Descrição</th><th>Valor</th><th></th></tr>' + linhas + '</table></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/eliminar_movimento/<int:id>")
def eliminar_movimento(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    m = Movimento.query.get_or_404(id)
    if m.user_id == session["user_id"]:
        db.session.delete(m)
        db.session.commit()
        flash("Eliminado")
    return redirect(url_for("movimentos"))

@app.route("/categorias", methods=["GET","POST"])
def categorias():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        nome = request.form["nome"].strip()
        if nome and not Categoria.query.filter_by(nome=nome).first():
            db.session.add(Categoria(nome=nome))
            db.session.commit()
            flash("Criada")
        return redirect(url_for("categorias"))
    cats = Categoria.query.all()
    boxes = ""
    for c in cats:
        boxes += '<div class="produto-box"><h3>' + c.nome + '</h3><div>' + str(len(c.produtos)) + ' produtos</div></div>'
    content = '<div class="card"><h2>Categorias</h2><form method="POST"><input name="nome" placeholder="Nova categoria" required><button>Criar</button></form><div class="grid" style="margin-top:12px;">' + boxes + '</div></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/historico")
def historico():
    if "user_id" not in session:
        return redirect(url_for("login"))
    uid = session["user_id"]
    inicio = request.args.get("inicio", (date.today()-timedelta(days=7)).isoformat())
    fim = request.args.get("fim", date.today().isoformat())
    vendas = Venda.query.filter(Venda.user_id==uid, db.func.date(Venda.data)>=inicio, db.func.date(Venda.data)<=fim).all()
    total = sum(v.valor_total for v in vendas)
    linhas = ""
    for v in vendas:
        linhas += '<tr><td>' + v.data.strftime("%d/%m %H:%M") + '</td><td>' + v.produto.nome + '</td><td>' + str(v.quantidade) + '</td><td>Kz ' + str(int(v.valor_total)) + '</td></tr>'
    content = '<div class="card"><h2>Histórico</h2><form method="GET"><input type="date" name="inicio" value="' + inicio + '"><input type="date" name="fim" value="' + fim + '"><button>Filtrar</button></form><p><strong>Total: Kz ' + str(int(total)) + '</strong></p><table><tr><th>Data</th><th>Produto</th><th>Qtd</th><th>Valor</th></tr>' + linhas + '</table></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    uid = session["user_id"]
    vendas = Venda.query.filter(Venda.user_id == uid, db.func.date(Venda.data) == date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    liquido = max(0, bruto - 5000)
    caixa = get_caixa(uid)
    content = '<h2 style="margin-bottom:10px;">Dashboard</h2><div class="grid">'
    content += '<div class="stat verde"><div class="label">Vendas Hoje</div><div class="valor">Kz ' + str(int(bruto)) + '</div></div>'
    content += '<div class="stat"><div class="label">Líquido (após -5.000)</div><div class="valor">Kz ' + str(int(liquido)) + '</div></div>'
    content += '<div class="stat laranja"><div class="label">Caixa</div><div class="valor">Kz ' + str(int(caixa.valor)) + '</div></div>'
    content += '<div class="stat"><div class="label">Nº Vendas</div><div class="valor">' + str(len(vendas)) + '</div></div></div>'
    content += '<form method="POST" action="/reiniciar_tudo" style="margin-top:12px;"><button class="btn-vermelho">Reiniciar Tudo</button></form>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = Usuario.query.filter_by(email=request.form["email"]).first()
        if user and check_password_hash(user.senha, request.form["senha"]):
            session["user_id"] = user.id
            session["nome"] = user.nome
            return redirect(url_for("dashboard"))
        flash("Email ou senha incorretos", "erro")
    content = '<div class="card" style="max-width:380px;margin:30px auto;"><h2>Entrar — Cantina FC Pira</h2><form method="POST"><input type="email" name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button>Entrar</button></form><p style="text-align:center;margin-top:10px"><a href="/registrar">Criar conta</a></p></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/registrar", methods=["GET","POST"])
def registrar():
    if request.method == "POST":
        if Usuario.query.filter_by(email=request.form["email"]).first():
            flash("Email já existe", "erro")
        else:
            tipo = request.form.get("tipo", "funcionario")
            db.session.add(Usuario(nome=request.form["nome"], email=request.form["email"], senha=generate_password_hash(request.form["senha"]), tipo=tipo))
            db.session.commit()
            flash("Conta criada!")
            return redirect(url_for("login"))
    content = '<div class="card" style="max-width:380px;margin:30px auto;"><h2>Criar Conta</h2><form method="POST"><input name="nome" placeholder="Nome" required><input type="email" name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><select name="tipo"><option value="funcionario">Funcionário</option><option value="dono">Dono</option></select><button>Registrar</button></form><p style="text-align:center;margin-top:10px"><a href="/login">Já tenho conta</a></p></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5001, debug=True)