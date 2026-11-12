from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
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
    tipo = db.Column(db.String(20), default="funcionario")

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    preco_compra = db.Column(db.Float, default=0)
    quantidade = db.Column(db.Integer, default=0)
    unidades_caixa = db.Column(db.Integer, default=1)

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
    data = db.Column(db.Date)
    total_bruto = db.Column(db.Float)
    total_liquido = db.Column(db.Float)
    lucro = db.Column(db.Float)
    caixa = db.Column(db.Float)
    qtd_vendas = db.Column(db.Integer)
    data_fechamento = db.Column(db.DateTime, default=datetime.utcnow)

class Caixa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Float, default=0)

class Compra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float)
    data = db.Column(db.DateTime, default=datetime.utcnow)

class Resto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float)
    data = db.Column(db.DateTime, default=datetime.utcnow)

T = """<!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cantina FC Pira</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>
*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,sans-serif}
body{background:#f8fafc;color:#1e293b}
.top{background:linear-gradient(135deg,#1e3a8a,#1e40af);color:#fff;padding:14px;position:sticky;top:0;z-index:50}
.nav{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.nav a{background:rgba(255,255,255,.15);color:#fff;padding:6px 12px;border-radius:20px;text-decoration:none;font-size:.8rem}
.c{max-width:960px;margin:0 auto;padding:16px}
.card{background:#fff;border-radius:12px;padding:18px;margin-bottom:16px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}
.stat{background:#fff;border-radius:12px;padding:16px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,.06);border-top:4px solid #3b82f6}
.stat b{display:block;font-size:1.5rem;margin-top:6px;font-weight:700}
.venda{border-top-color:#2563eb}.lucro{border-top-color:#16a34a}.caixa{border-top-color:#7c3aed}
button{background:#2563eb;color:#fff;border:none;padding:10px;border-radius:8px;cursor:pointer}
.flash{background:#ecfdf5;padding:10px;border-radius:8px;margin-bottom:12px}
</style></head><body>{% if session.get('user_id') %}<div class="top"><h1>Cantina FC Pira</h1><div class="nav"><a href="/">Vender</a><a href="/dashboard">Dashboard</a><a href="/hoje">Hoje</a><a href="/relatorio">Relatório</a><a href="/caixa">Caixa</a><a href="/logout">Sair</a></div></div>{% endif %}<div class="c">{% with messages = get_flashed_messages() %}{% if messages %}{% for msg in messages %}<div class="flash">{{ msg }}</div>{% endfor %}{% endif %}{% endwith %}{{ content|safe }}</div></body></html>"""

def is_admin():
    return session.get("tipo") == "admin"

def get_caixa():
    c = Caixa.query.first()
    if not c:
        c = Caixa(valor=0)
        db.session.add(c)
        db.session.commit()
    return c

@app.route("/")
def index():
    if "user_id" not in session: return redirect("/login")
    boxes = ""
    for p in Produto.query.order_by(Produto.nome).all():
        boxes += f'''
        <div style="border:1px solid #e2e8f0;border-radius:10px;padding:12px;text-align:center">
            <b>{p.nome}</b><br>
            Venda: Kz {int(p.preco)}<br>
            Stock: {p.quantidade}<br>
            <form method="POST" action="/vender">
                <input type="hidden" name="produto_id" value="{p.id}">
                <input type="number" name="quantidade" value="1" min="1" max="{p.quantidade}" style="width:60px">
                <button>Vender</button>
            </form>
        </div>
        '''
    return render_template_string(T, content=f'<div class="card"><h2>Vender</h2><div class="grid">{boxes}</div></div>')

@app.route("/vender", methods=["POST"])
def vender():
    if "user_id" not in session: return redirect("/login")
    p = Produto.query.get(int(request.form["produto_id"]))
    qtd = int(request.form.get("quantidade", 1))
    if p and qtd > 0 and p.quantidade >= qtd:
        lucro_un = p.preco - (p.preco_compra / (p.unidades_caixa or 1) if p.preco_compra else 0)
        db.session.add(Venda(produto_id=p.id, user_id=session["user_id"], quantidade=qtd, valor_total=p.preco*qtd, lucro=lucro_un*qtd))
        p.quantidade -= qtd
        db.session.commit()
        flash(f"Vendido {qtd}x {p.nome}")
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect("/login")
    hoje = date.today()
    vendas = Venda.query.filter(db.func.date(Venda.data)==hoje).all()
    bruto = sum(v.valor_total for v in vendas)
    lucro = sum(v.lucro or 0 for v in vendas)
    caixa = get_caixa().valor
    
    chart_data = f"[{int(bruto)},{int(lucro)},{int(caixa)}]"
    
    return render_template_string(T, content=f'''
    <h2>Dashboard</h2>
    <div class="grid">
        <div class="stat venda">Vendas Hoje<b>Kz {int(bruto)}</b></div>
        <div class="stat lucro">Lucro<b>Kz {int(lucro)}</b></div>
        <div class="stat caixa">Caixa<b>Kz {int(caixa)}</b></div>
    </div>
    <div class="card" style="margin-top:16px">
        <canvas id="chart" height="120"></canvas>
    </div>
    <script>
    new Chart(document.getElementById('chart'), {{
        type: 'bar',
        data: {{
            labels: ['Vendas', 'Lucro', 'Caixa'],
            datasets: [{{
                data: {chart_data},
                backgroundColor: ['#2563eb', '#16a34a', '#7c3aed']
            }}]
        }},
        options: {{plugins: {{legend: {{display: false}}}}}}
    }});
    </script>
    ''')

@app.route("/caixa", methods=["GET","POST"])
def caixa():
    if "user_id" not in session: return redirect("/login")
    c = get_caixa()
    if request.method == "POST" and is_admin():
        c.valor = float(request.form["valor"])
        db.session.commit()
        return redirect("/caixa")
    form = f'<form method="POST"><input type="number" name="valor" value="{c.valor}"><button>Alterar</button></form>' if is_admin() else ""
    return render_template_string(T, content=f'<div class="card"><h2>Caixa</h2><p style="font-size:1.5rem">Kz {int(c.valor)}</p>{form}</div>')

@app.route("/hoje")
def hoje():
    if "user_id" not in session: return redirect("/login")
    vendas = Venda.query.filter(db.func.date(Venda.data)==date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    return render_template_string(T, content=f'<div class="card"><h2>Hoje</h2><p>Total: Kz {int(bruto)}</p><form method="POST" action="/finalizar"><button>Finalizar Dia</button></form></div>')

@app.route("/finalizar", methods=["POST"])
def finalizar():
    if "user_id" not in session: return redirect("/login")
    vendas = Venda.query.filter(db.func.date(Venda.data)==date.today()).all()
    bruto = sum(v.valor_total for v in vendas)
    lucro = sum(v.lucro or 0 for v in vendas)
    caixa = get_caixa().valor
    liquido = max(0, bruto - 5000)
    db.session.add(FechamentoDia(data=date.today(), total_bruto=bruto, total_liquido=liquido, lucro=lucro, caixa=caixa, qtd_vendas=len(vendas)))
    db.session.commit()
    flash("Dia finalizado")
    return redirect("/hoje")

@app.route("/relatorio")
def relatorio():
    if "user_id" not in session: return redirect("/login")
    fs = FechamentoDia.query.order_by(FechamentoDia.data.desc()).all()
    linhas = "".join(f"<tr><td>{f.data.strftime('%d/%m/%Y')}</td><td>Kz {int(f.total_bruto or 0)}</td><td>Kz {int(f.total_liquido or 0)}</td><td>Kz {int(f.lucro or 0)}</td></tr>" for f in fs)
    return render_template_string(T, content=f'<div class="card"><h2>Relatório</h2><table><tr><th>Data</th><th>Bruto</th><th>Líquido</th><th>Lucro</th></tr>{linhas}</table></div>')

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = Usuario.query.filter_by(email=request.form["email"]).first()
        if u and check_password_hash(u.senha, request.form["senha"]):
            session["user_id"] = u.id
            session["nome"] = u.nome
            session["tipo"] = u.tipo or "funcionario"
            return redirect("/dashboard")
        flash("Email ou senha incorretos")
    return render_template_string(T, content='<div class="card" style="max-width:360px;margin:40px auto"><h2>Entrar</h2><form method="POST"><input type="email" name="email" required><input type="password" name="senha" required><button>Entrar</button></form></div>')

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5001, debug=True)