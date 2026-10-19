from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "troque-esta-chave-por-uma-bem-secreta-123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///negocio.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ========== MODELOS ==========
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=0)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    produto = db.relationship("Produto")

# ========== TEMPLATES (tudo em um arquivo só) ==========
TEMPLATE_BASE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Gestão Remota do Negócio</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
        body { background: #f0f2f5; color: #333; }
        .container { max-width: 900px; margin: 30px auto; padding: 20px; }
        .card { background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
        h1, h2 { margin-bottom: 15px; color: #1a73e8; }
        input, button, select { padding: 10px 14px; margin: 6px 0; border-radius: 8px; border: 1px solid #ccc; width: 100%; }
        button { background: #1a73e8; color: white; border: none; cursor: pointer; font-weight: 600; }
        button:hover { background: #1557b0; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; }
        .nav { display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; }
        .nav a { text-decoration: none; color: #1a73e8; font-weight: 500; }
        .flash { background: #d4edda; color: #155724; padding: 12px; border-radius: 8px; margin-bottom: 15px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; }
        .stat { background: #e8f0fe; padding: 18px; border-radius: 10px; text-align: center; }
        .stat strong { display: block; font-size: 1.6rem; color: #1a73e8; }
    </style>
</head>
<body>
    <div class="container">
        {% if session.get('user_id') %}
        <div class="nav">
            <a href="{{ url_for('dashboard') }}">Dashboard</a>
            <a href="{{ url_for('produtos') }}">Produtos</a>
            <a href="{{ url_for('vendas') }}">Vendas</a>
            <a href="{{ url_for('logout') }}">Sair</a>
        </div>
        {% endif %}

        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for msg in messages %}
                    <div class="flash">{{ msg }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {{ content|safe }}
    </div>
</body>
</html>
"""

# ========== ROTAS ==========
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]
        user = Usuario.query.filter_by(email=email).first()
        if user and check_password_hash(user.senha, senha):
            session["user_id"] = user.id
            session["nome"] = user.nome
            flash("Login realizado com sucesso!")
            return redirect(url_for("dashboard"))
        flash("Email ou senha incorretos.")
    content = """
    <div class="card">
        <h1>Entrar no Sistema</h1>
        <form method="POST">
            <input type="email" name="email" placeholder="Seu email" required>
            <input type="password" name="senha" placeholder="Senha" required>
            <button type="submit">Entrar</button>
        </form>
        <p style="margin-top:15px">Ainda não tem conta? <a href="{{ url_for('registrar') }}">Criar conta</a></p>
    </div>
    """
    return render_template_string(TEMPLATE_BASE, content=content)

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = generate_password_hash(request.form["senha"])
        if Usuario.query.filter_by(email=email).first():
            flash("Este email já está cadastrado.")
        else:
            novo = Usuario(nome=nome, email=email, senha=senha)
            db.session.add(novo)
            db.session.commit()
            flash("Conta criada! Faça login.")
            return redirect(url_for("login"))
    content = """
    <div class="card">
        <h1>Criar Conta</h1>
        <form method="POST">
            <input type="text" name="nome" placeholder="Seu nome" required>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="senha" placeholder="Senha" required>
            <button type="submit">Registrar</button>
        </form>
        <p style="margin-top:15px"><a href="{{ url_for('login') }}">Já tenho conta</a></p>
    </div>
    """
    return render_template_string(TEMPLATE_BASE, content=content)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    total_produtos = Produto.query.count()
    valor_estoque = db.session.query(db.func.sum(Produto.preco * Produto.quantidade)).scalar() or 0
    vendas_hoje = Venda.query.filter(db.func.date(Venda.data) == date.today()).all()
    total_vendas_hoje = sum(v.valor_total for v in vendas_hoje)

    content = f"""
    <div class="card">
        <h1>Olá, {session.get('nome')}!</h1>
        <p>Resumo do seu negócio em tempo real</p>
        <div class="stats" style="margin-top:20px">
            <div class="stat">
                <strong>{total_produtos}</strong>
                Produtos cadastrados
            </div>
            <div class="stat">
                <strong>R$ {valor_estoque:,.2f}</strong>
                Valor em estoque
            </div>
            <div class="stat">
                <strong>R$ {total_vendas_hoje:,.2f}</strong>
                Vendas de hoje
            </div>
        </div>
    </div>
    """
    return render_template_string(TEMPLATE_BASE, content=content)

@app.route("/produtos", methods=["GET", "POST"])
def produtos():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        nome = request.form["nome"]
        preco = float(request.form["preco"])
        qtd = int(request.form["quantidade"])
        novo = Produto(nome=nome, preco=preco, quantidade=qtd)
        db.session.add(novo)
        db.session.commit()
        flash("Produto adicionado!")
        return redirect(url_for("produtos"))

    produtos = Produto.query.order_by(Produto.nome).all()
    linhas = ""
    for p in produtos:
        linhas += f"""
        <tr>
            <td>{p.nome}</td>
            <td>R$ {p.preco:.2f}</td>
            <td>{p.quantidade}</td>
            <td>R$ {p.preco * p.quantidade:.2f}</td>
        </tr>
        """

    content = f"""
    <div class="card">
        <h2>Adicionar Produto</h2>
        <form method="POST">
            <input type="text" name="nome" placeholder="Nome do produto" required>
            <input type="number" step="0.01" name="preco" placeholder="Preço (ex: 29.90)" required>
            <input type="number" name="quantidade" placeholder="Quantidade em estoque" required>
            <button type="submit">Salvar Produto</button>
        </form>
    </div>
    <div class="card">
        <h2>Lista de Produtos</h2>
        <table>
            <tr>
                <th>Nome</th>
                <th>Preço</th>
                <th>Estoque</th>
                <th>Valor Total</th>
            </tr>
            {linhas}
        </table>
    </div>
    """
    return render_template_string(TEMPLATE_BASE, content=content)

@app.route("/vendas", methods=["GET", "POST"])
def vendas():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        produto_id = int(request.form["produto_id"])
        qtd = int(request.form["quantidade"])
        produto = Produto.query.get(produto_id)
        if produto and produto.quantidade >= qtd:
            valor = produto.preco * qtd
            venda = Venda(produto_id=produto_id, quantidade=qtd, valor_total=valor)
            produto.quantidade -= qtd
            db.session.add(venda)
            db.session.commit()
            flash(f"Venda registrada! Total: R$ {valor:.2f}")
        else:
            flash("Estoque insuficiente ou produto inválido.")
        return redirect(url_for("vendas"))

    produtos = Produto.query.filter(Produto.quantidade > 0).all()
    opcoes = "".join([f'<option value="{p.id}">{p.nome} (estoque: {p.quantidade})</option>' for p in produtos])

    vendas = Venda.query.order_by(Venda.data.desc()).limit(20).all()
    linhas = ""
    for v in vendas:
        linhas += f"""
        <tr>
            <td>{v.produto.nome}</td>
            <td>{v.quantidade}</td>
            <td>R$ {v.valor_total:.2f}</td>
            <td>{v.data.strftime('%d/%m/%Y %H:%M')}</td>
        </tr>
        """

    content = f"""
    <div class="card">
        <h2>Registrar Venda</h2>
        <form method="POST">
            <select name="produto_id" required>
                <option value="">Escolha o produto</option>
                {opcoes}
            </select>
            <input type="number" name="quantidade" placeholder="Quantidade vendida" min="1" required>
            <button type="submit">Registrar Venda</button>
        </form>
    </div>
    <div class="card">
        <h2>Últimas Vendas</h2>
        <table>
            <tr>
                <th>Produto</th>
                <th>Qtd</th>
                <th>Valor</th>
                <th>Data</th>
            </tr>
            {linhas}
        </table>
    </div>
    """
    return render_template_string(TEMPLATE_BASE, content=content)

# ========== INICIALIZAÇÃO ==========
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # Para acessar de qualquer dispositivo na mesma rede:
    app.run(host="0.0.0.0", port=5000, debug=True)