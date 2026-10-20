from flask import Flask, render_template_string, request, redirect, url_for, session, flash, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "armazem-cerveja-refrigerante-2026"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///armazem.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), default="funcionario")

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=0)
    estoque_minimo = db.Column(db.Integer, default=10)

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
    qtd_vendas = db.Column(db.Integer, nullable=False)
    data_fechamento = db.Column(db.DateTime, default=datetime.utcnow)

class Reabastecimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    produto = db.relationship("Produto")

TEMPLATE = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Armazém">
    <meta name="theme-color" content="#b71c1c">
    <link rel="manifest" href="/manifest.json">
    <link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect fill='%23b71c1c' width='100' height='100'/><text y='.7em' x='50' text-anchor='middle' font-size='50' fill='white'>A</text></svg>">
    <title>Armazém — Cerveja e Refrigerante</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
        body { background: #fafafa; color: #333; }
        .topbar { background: linear-gradient(135deg, #b71c1c, #e53935); color: white; padding: 12px 16px; position: sticky; top: 0; z-index: 100; }
        .topbar h1 { font-size: 1.2rem; }
        .nav { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
        .nav a { background: rgba(255,255,255,0.2); color: white; padding: 6px 11px; border-radius: 18px; text-decoration: none; font-size: 0.78rem; }
        .nav a:hover { background: white; color: #b71c1c; }
        .container { max-width: 1000px; margin: 0 auto; padding: 12px; }
        .card { background: white; border-radius: 12px; padding: 14px; margin-bottom: 12px; box-shadow: 0 1px 8px rgba(0,0,0,0.06); }
        input, select, button { width: 100%; padding: 11px; margin: 4px 0; border-radius: 8px; border: 1px solid #ccc; font-size: 15px; }
        button { background: #b71c1c; color: white; border: none; font-weight: 600; cursor: pointer; }
        .btn-verde { background: #00c853; }
        .btn-laranja { background: #ff9800; color: #333; }
        .btn-vermelho { background: #d32f2f; }
        .btn-azul { background: #1565c0; }
        .btn-pequeno { width: auto; padding: 6px 12px; font-size: 13px; margin: 2px; }
        .flash { background: #e8f5e9; color: #1b5e20; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
        .flash.erro { background: #ffebee; color: #b71c1c; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
        .produto-box { background: #fff; border: 2px solid #ffcdd2; border-radius: 12px; padding: 12px; text-align: center; }
        .produto-box.baixo { border-color: #ff9800; background: #fff8e1; }
        .produto-box h3 { font-size: 0.95rem; margin-bottom: 4px; color: #b71c1c; }
        .produto-box .preco { font-weight: 700; color: #c62828; }
        .produto-box .stock { font-size: 0.8rem; color: #546e7a; margin: 4px 0; }
        .produto-box .tipo { font-size: 0.7rem; color: #9e9e9e; text-transform: uppercase; }
        .stat { background: white; border-radius: 12px; padding: 14px; text-align: center; border-top: 4px solid #b71c1c; }
        .stat.verde { border-top-color: #00c853; }
        .stat.laranja { border-top-color: #ff9800; }
        .stat.azul { border-top-color: #1565c0; }
        .stat .valor { font-size: 1.4rem; font-weight: 700; }
        .stat .label { font-size: 0.75rem; color: #546e7a; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { background: #ffcdd2; padding: 8px; text-align: left; }
        td { padding: 8px; border-bottom: 1px solid #eee; }
        .fechado { background: #e8f5e9; border: 2px solid #00c853; padding: 14px; border-radius: 12px; text-align: center; }
        .pesquisa { margin-bottom: 12px; }
        .install-btn { position: fixed; bottom: 16px; right: 16px; background: #b71c1c; color: white; padding: 12px 16px; border-radius: 24px; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.3); cursor: pointer; display: none; z-index: 999; }
    </style>
</head>
<body>
    {% if session.get('user_id') %}
    <div class="topbar">
        <h1>Armazém</h1>
        <div style="font-size:0.75rem;">Olá, {{ session.get('nome') }}</div>
        <div class="nav">
            <a href="/">Vender</a>
            <a href="/dashboard">Dashboard</a>
            <a href="/hoje">Hoje</a>
            <a href="/relatorio">Relatório</a>
            <a href="/reabastecer">Reabastecer</a>
            <a href="/historico">Histórico</a>
            <a href="/produtos">Produtos</a>
            <a href="/stock">Stock</a>
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
    <div id="installBtn" class="install-btn" onclick="installPWA()">Instalar App</div>
    <script>
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            document.getElementById('installBtn').style.display = 'block';
        });
        function installPWA() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then(() => {
                    deferredPrompt = null;
                    document.getElementById('installBtn').style.display = 'none';
                });
            }
        }
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js');
        }
    </script>
</body>
</html>
"""

def dia_fechado(user_id):
    return FechamentoDia.query.filter_by(user_id=user_id, data=date.today()).first() is not None

@app.route("/manifest.json")
def manifest():
    return Response('''{
        "name": "Armazém Cerveja e Refrigerante",
        "short_name": "Armazém",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#fafafa",
        "theme_color": "#b71c1c",
        "icons": [{"src": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect fill='%23b71c1c' width='100' height='100'/><text y='.7em' x='50' text-anchor='middle' font-size='50' fill='white'>A</text></svg>", "sizes": "192x192", "type": "image/svg+xml"}]
    }''', mimetype='application/json')

@app.route("/sw.js")
def service_worker():
    return Response('''self.addEventListener('fetch', e => {});''', mimetype='application/javascript')

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if dia_fechado(session["user_id"]):
        content = '<div class="fechado">Dia finalizado.</div><form method="POST" action="/reiniciar"><button class="btn-laranja">Reiniciar Venda</button></form>'
        return render_template_string(TEMPLATE, content=content)

    busca = request.args.get("busca", "").strip().lower()
    produtos = Produto.query.order_by(Produto.nome).all()
    if busca:
        produtos = [p for p in produtos if busca in p.nome.lower()]

    boxes = ""
    for p in produtos:
        cls = "produto-box baixo" if p.quantidade <= p.estoque_minimo else "produto-box"
        boxes += '<div class="' + cls + '"><h3>' + p.nome + '</h3><div class="tipo">' + p.tipo + '</div><div class="preco">Kz ' + str(int(p.preco)) + '</div><div class="stock">Stock: ' + str(p.quantidade) + '</div>'
        boxes += '<form method="POST" action="/vender" style="margin:0;"><input type="hidden" name="produto_id" value="' + str(p.id) + '"><button class="btn-verde btn-pequeno">Vender</button></form>'
        boxes += '<form method="POST" action="/devolver/' + str(p.id) + '" style="margin:0;display:inline;"><button class="btn-laranja btn-pequeno">Devolver</button></form>'
        boxes += '<form method="POST" action="/eliminar_produto/' + str(p.id) + '" style="margin:0;display:inline;" onsubmit="return confirm(\'Eliminar?\')"><button class="btn-vermelho btn-pequeno">Eliminar</button></form></div>'

    content = '<div class="card"><h2>Vender</h2><form method="GET" class="pesquisa"><input name="busca" placeholder="Procurar produto..." value="' + busca + '"></form><div class="grid">' + (boxes if boxes else '<p>Nenhum produto encontrado</p>') + '</div></div>'
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

@app.route("/hoje")
def hoje():
    if "user_id" not in session:
        return redirect(url_for("login"))
    uid = session["user_id"]
    vendas = Venda.query.filter(Venda.user_id == uid, db.func.date(Venda.data) == date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    fechado = dia_fechado(uid)
    linhas = ""
    for v in vendas:
        linhas += "<tr><td>" + v.produto.nome + "</td><td>" + str(v.quantidade) + "</td><td>Kz " + str(int(v.valor_total)) + "</td><td>" + v.data.strftime("%H:%M") + "</td></tr>"
    content = '<div class="card"><h2>Relatório do Dia</h2><p>Total: <strong>Kz ' + str(int(bruto)) + '</strong></p><p>Vendas: <strong>' + str(len(vendas)) + '</strong></p>'
    if fechado:
        content += '<div class="fechado">Dia finalizado</div>'
    content += '<form method="POST" action="/finalizar"><button class="btn-laranja">Finalizar Dia</button></form>'
    content += '<table style="margin-top:10px;"><tr><th>Produto</th><th>Qtd</th><th>Valor</th><th>Hora</th></tr>' + (linhas if linhas else "<tr><td colspan=4>Nenhuma</td></tr>") + '</table></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/finalizar", methods=["POST"])
def finalizar():
    if "user_id" not in session:
        return redirect(url_for("login"))
    uid = session["user_id"]
    vendas = Venda.query.filter(Venda.user_id == uid, db.func.date(Venda.data) == date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    db.session.add(FechamentoDia(user_id=uid, data=date.today(), total_bruto=bruto, qtd_vendas=len(vendas)))
    db.session.commit()
    flash("Dia finalizado! Total: Kz " + str(int(bruto)))
    return redirect(url_for("hoje"))

@app.route("/relatorio")
def relatorio():
    if "user_id" not in session:
        return redirect(url_for("login"))
    uid = session["user_id"]
    fechamentos = FechamentoDia.query.filter_by(user_id=uid).order_by(FechamentoDia.data_fechamento.desc()).all()
    linhas = ""
    for f in fechamentos:
        linhas += '<tr><td>' + f.data.strftime("%d/%m/%Y") + '</td><td>' + f.data_fechamento.strftime("%H:%M") + '</td><td>Kz ' + str(int(f.total_bruto)) + '</td><td>' + str(f.qtd_vendas) + '</td></tr>'
    content = '<div class="card"><h2>Relatório de Dias</h2><table><tr><th>Data</th><th>Hora</th><th>Total</th><th>Nº Vendas</th></tr>' + (linhas if linhas else "<tr><td colspan=4>Nenhum</td></tr>") + '</table></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/reabastecer", methods=["GET", "POST"])
def reabastecer():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        p = Produto.query.get(int(request.form["produto_id"]))
        qtd = int(request.form["quantidade"])
        if p and qtd > 0:
            p.quantidade += qtd
            db.session.add(Reabastecimento(produto_id=p.id, user_id=session["user_id"], quantidade=qtd))
            db.session.commit()
            flash("Reabastecido: " + str(qtd) + "x " + p.nome)
        return redirect(url_for("reabastecer"))
    produtos = Produto.query.order_by(Produto.nome).all()
    opts = ""
    for p in produtos:
        opts += '<option value="' + str(p.id) + '">' + p.nome + ' (Stock: ' + str(p.quantidade) + ')</option>'
    reabs = Reabastecimento.query.filter_by(user_id=session["user_id"]).order_by(Reabastecimento.data.desc()).limit(20).all()
    linhas = ""
    for r in reabs:
        linhas += '<tr><td>' + r.data.strftime("%d/%m %H:%M") + '</td><td>' + r.produto.nome + '</td><td>' + str(r.quantidade) + '</td></tr>'
    content = '<div class="card"><h2>Reabastecer Stock</h2><form method="POST"><select name="produto_id">' + opts + '</select><input type="number" name="quantidade" placeholder="Quantidade" required min="1"><button class="btn-azul">Reabastecer</button></form></div>'
    content += '<div class="card"><h2>Últimos Reabastecimentos</h2><table><tr><th>Data</th><th>Produto</th><th>Qtd</th></tr>' + linhas + '</table></div>'
    return render_template_string(TEMPLATE, content=content)

@app.route("/stock")
def stock():
    if "user_id" not in session:
        return redirect(url_for("login"))
    produtos = Produto.query.order_by(Produto.nome).all()
    linhas = ""
    for p in produtos:
        linhas += '<tr><td>' + p.nome + '</td><td>' + p.tipo + '</td><td>' + str(p.quantidade) + '</td><td>'
        linhas += '<form method="POST" action="/ajustar_stock/' + str(p.id) + '" style="display:inline;"><input type="hidden" name="acao" value="mais"><button class="btn-pequeno btn-verde">+</button></form> '
        linhas += '<form method="POST" action="/ajustar_stock/' + str(p.id) + '" style="display:inline;"><input type="hidden" name="acao" value="menos"><button class="btn-pequeno btn-vermelho">-</button></form></td></tr>'
    content = '<div class="card"><h2>Stock</h2><table><tr><th>Produto</th><th>Tipo</th><th>Qtd</th><th>Ajustar</th></tr>' + linhas + '</table></div>'
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
        db.session.add(Produto(
            nome=request.form["nome"],
            tipo=request.form["tipo"],
            preco=float(request.form["preco"]),
            quantidade=int(request.form["quantidade"]),
            estoque_minimo=int(request.form.get("estoque_minimo", 10))
        ))
        db.session.commit()
        flash("Cadastrado")
        return redirect(url_for("produtos"))
    prods = Produto.query.order_by(Produto.nome).all()
    linhas = ""
    for p in prods:
        linhas += '<tr><td>' + p.nome + '</td><td>' + p.tipo + '</td><td>Kz ' + str(int(p.preco)) + '</td><td>' + str(p.quantidade) + '</td><td><a href="/eliminar_produto_lista/' + str(p.id) + '" onclick="return confirm(\'Eliminar?\')">Eliminar</a></td></tr>'
    content = '<div class="card"><h2>Cadastrar Produto</h2><form method="POST"><input name="nome" placeholder="Nome" required><select name="tipo"><option value="Cerveja">Cerveja</option><option value="Refrigerante">Refrigerante</option></select><input type="number" step="0.01" name="preco" placeholder="Preço" required><input type="number" name="quantidade" placeholder="Quantidade inicial" required><input type="number" name="estoque_minimo" placeholder="Stock mínimo (alerta)" value="10"><button>Cadastrar</button></form></div>'
    content += '<div class="card"><table><tr><th>Nome</th><th>Tipo</th><th>Preço</th><th>Stock</th><th></th></tr>' + linhas + '</table></div>'
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
    baixo = Produto.query.filter(Produto.quantidade <= Produto.estoque_minimo).count()
    content = '<h2 style="margin-bottom:10px;">Dashboard</h2><div class="grid">'
    content += '<div class="stat verde"><div class="label">Vendas Hoje</div><div class="valor">Kz ' + str(int(bruto)) + '</div></div>'
    content += '<div class="stat"><div class="label">Nº Vendas</div><div class="valor">' + str(len(vendas)) + '</div></div>'
    content += '<div class="stat laranja"><div class="label">Stock Baixo</div><div class="valor">' + str(baixo) + '</div></div>'
    content += '<div class="stat azul"><div class="label">Produtos</div><div class="valor">' + str(Produto.query.count()) + '</div></div></div>'
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
    content = '<div class="card" style="max-width:380px;margin:30px auto;"><h2>Entrar — Armazém</h2><form method="POST"><input type="email" name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button>Entrar</button></form><p style="text-align:center;margin-top:10px"><a href="/registrar">Criar conta</a></p></div>'
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
    app.run(host="0.0.0.0", port=5002, debug=True)