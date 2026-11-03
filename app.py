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
    '''+botao_reiniciar)