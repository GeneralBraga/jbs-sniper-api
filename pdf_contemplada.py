"""
motor/pdf_contemplada.py
Geração do PDF premium de carta contemplada individual.
Extraído do app.py original — sem dependência de Streamlit.
"""
import os
from datetime import datetime
from fpdf import FPDF
from motor.utils import fmt_brl, fmt_pct


def _s(t) -> str:
    return str(t).encode('latin-1', 'replace').decode('latin-1')


def gerar_pdf_contemplada(
    admin: str,
    tipo: str,
    nome_cliente: str,
    credito: float,
    entrada: float,
    n_parcelas: int,
    parcela: float,
    tx_transf: float,
    logo_path: str = "logo_pdf.png",
) -> bytes:
    """
    Gera o PDF premium de carta contemplada e retorna bytes.
    logo_path: caminho para o arquivo de logo (opcional).
    """
    # ── Cálculos financeiros ──────────────────────────
    saldo_devedor  = n_parcelas * parcela
    custo_total    = entrada + saldo_devedor + tx_transf
    cet_total_pct  = ((custo_total / credito) - 1) * 100 if credito > 0 else 0
    cet_mensal_pct = cet_total_pct / n_parcelas if n_parcelas > 0 else 0
    economia_pct   = (entrada / credito) * 100 if credito > 0 else 0

    # ── Tipo de bem ───────────────────────────────────
    tl = tipo.lower()
    if any(k in tl for k in ('imovel', 'imóvel', 'apart', 'casa', 'terreno')):
        tipo_desc = "Imovel / Bem de Raiz"
        uso_txt   = "aquisicao do seu imovel"
        uso_txt2  = "imovel — pronto para uso imediato"
    elif any(k in tl for k in ('pesado', 'caminhao', 'caminhão', 'onibus', 'ônibus')):
        tipo_desc = "Veiculos Pesados / Caminhao"
        uso_txt   = "aquisicao do seu veiculo pesado"
        uso_txt2  = "veiculo pesado — pronto para uso imediato"
    else:
        tipo_desc = "Veiculo / Automovel"
        uso_txt   = "aquisicao do seu automovel"
        uso_txt2  = "automovel — pronto para uso imediato"

    cliente_label = nome_cliente.strip().upper() if nome_cliente.strip() else "CLIENTE"

    # ── Paleta ────────────────────────────────────────
    GR, GG, GB = 132, 117, 78
    DR, DG, DB = 12,  14,  20
    WR, WG, WB = 255, 255, 255
    LR, LG, LB = 248, 247, 242
    SR, SG, SB = 230, 225, 205
    MR, MG, MB = 50,  46,  35

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    def _line(x, y, w, h, r=None, g=None, b=None):
        if r is not None:
            pdf.set_fill_color(r, g, b)
        pdf.rect(x, y, w, h, 'F')

    # ── Cabeçalho ─────────────────────────────────────
    _line(0, 0, 210, 72, DR, DG, DB)
    _line(0, 0, 5, 72, GR, GG, GB)

    if os.path.exists(logo_path):
        pdf.image(logo_path, 14, 9, 32)

    pdf.set_font('Arial', 'B', 28)
    pdf.set_text_color(GR, GG, GB)
    pdf.set_xy(52, 10)
    pdf.cell(0, 11, _s("CARTA CONTEMPLADA"), 0, 1, 'L')

    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(SR, SG, SB)
    pdf.set_xy(52, 22)
    pdf.cell(0, 5, _s(f"Administradora: {admin.upper()}"), 0, 1, 'L')

    _line(52, 29, 60, 8, GR, GG, GB)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(DR, DG, DB)
    pdf.set_xy(53, 30.5)
    pdf.cell(58, 5, _s(tipo_desc.upper()), 0, 0, 'C')

    pdf.set_font('Arial', '', 7.5)
    pdf.set_text_color(130, 118, 80)
    pdf.set_xy(52, 40)
    pdf.cell(0, 5, _s(f"Emitido em {datetime.now().strftime('%d/%m/%Y')}   |   Validade: consultar disponibilidade"), 0, 1, 'L')

    _line(10, 50, 190, 16, 55, 48, 30)
    _line(10, 50, 3, 16, GR, GG, GB)
    pdf.set_font('Arial', '', 7.5)
    pdf.set_text_color(GR, GG, GB)
    pdf.set_xy(17, 52.5)
    pdf.cell(40, 4, _s("CLIENTE"), 0, 0, 'L')
    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(WR, WG, WB)
    pdf.set_xy(17, 57)
    pdf.cell(180, 6, _s(cliente_label), 0, 0, 'L')

    _line(0, 72, 210, 2.5, GR, GG, GB)

    # ── Cards financeiros 3×2 ─────────────────────────
    y0, wc, hc, gap = 80, 62, 28, 2
    xs = [10, 10 + wc + gap, 10 + 2 * (wc + gap)]

    def card(x, y, label, valor, sub=None, gold=False):
        if gold:
            _line(x, y, wc, hc, GR, GG, GB)
            lc, vc, sc = (WR, WG, WB), (WR, WG, WB), (230, 215, 170)
        else:
            _line(x, y, wc, hc, LR, LG, LB)
            lc, vc, sc = (GR, GG, GB), (MR, MG, MB), (120, 110, 80)
        pdf.set_font('Arial', 'B', 7)
        pdf.set_text_color(*lc)
        pdf.set_xy(x + 3, y + 4)
        pdf.cell(wc - 6, 4, _s(label), 0, 0, 'C')
        pdf.set_font('Arial', 'B', 13)
        pdf.set_text_color(*vc)
        pdf.set_xy(x + 2, y + 10)
        pdf.cell(wc - 4, 8, _s(valor), 0, 0, 'C')
        if sub:
            pdf.set_font('Arial', '', 7)
            pdf.set_text_color(*sc)
            pdf.set_xy(x + 2, y + 20)
            pdf.cell(wc - 4, 4, _s(sub), 0, 0, 'C')

    card(xs[0], y0, "CREDITO DA CARTA",        fmt_brl(credito),
         sub=f"{economia_pct:.0f}% de entrada", gold=True)
    card(xs[1], y0, "ENTRADA / INVESTIMENTO",  fmt_brl(entrada),
         sub="Valor para transferencia")
    card(xs[2], y0, "TX DE TRANSFERENCIA",     fmt_brl(tx_transf),
         sub="Custo de formalizacao")

    y1 = y0 + hc + gap
    card(xs[0], y1, "SALDO DEVEDOR",           fmt_brl(saldo_devedor),
         sub=f"{n_parcelas} parcelas restantes")
    card(xs[1], y1, "PARCELA MENSAL",
         f"{n_parcelas}x {fmt_brl(parcela)}",
         sub="Valor fixo por mes")
    card(xs[2], y1, "CUSTO TOTAL DA OPERACAO", fmt_brl(custo_total),
         sub="Entrada + saldo + taxa", gold=True)

    # ── Bloco CET ─────────────────────────────────────
    y_cet = y1 + hc + 6
    _line(10, y_cet, 190, 30, DR, DG, DB)
    _line(10, y_cet, 190, 1.5, GR, GG, GB)

    for i, (lbl, val) in enumerate([
        ("CET MENSAL (a.m.)", fmt_pct(cet_mensal_pct)),
        ("CET TOTAL",         fmt_pct(cet_total_pct)),
        ("PRAZO",             f"{n_parcelas} meses"),
    ]):
        xm = 10 + i * 63 + 3
        pdf.set_font('Arial', 'B', 7.5)
        pdf.set_text_color(GR, GG, GB)
        pdf.set_xy(xm, y_cet + 5)
        pdf.cell(60, 4, _s(lbl), 0, 0, 'L')
        pdf.set_font('Arial', 'B', 19)
        pdf.set_text_color(WR, WG, WB)
        pdf.set_xy(xm, y_cet + 11)
        pdf.cell(60, 10, _s(val), 0, 0, 'L')

    # ── Como funciona — 3 passos ──────────────────────
    y_how = y_cet + 36
    _line(10, y_how, 190, 0.8, GR, GG, GB)

    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(GR, GG, GB)
    pdf.set_xy(10, y_how + 4)
    pdf.cell(190, 5, _s("COMO FUNCIONA — 3 PASSOS SIMPLES"), 0, 0, 'L')

    steps = [
        ("01", "VOCE INVESTE A ENTRADA",
         f"Voce aporta {fmt_brl(entrada)} — equivalente a {economia_pct:.0f}% do credito — "
         f"para formalizar a transferencia da cota contemplada para o seu nome."),
        ("02", "CREDITO LIBERADO IMEDIATAMENTE",
         f"Com o credito de {fmt_brl(credito)} disponivel, voce utiliza diretamente para {uso_txt2}. "
         f"Sem sorteio, sem fila — a contemplacao ja aconteceu."),
        ("03", "PARCELAS ATE O ENCERRAMENTO DO GRUPO",
         f"Voce paga {n_parcelas} parcelas mensais de {fmt_brl(parcela)} ate o encerramento do grupo. "
         f"Os valores sao fixos, sem surpresas."),
    ]
    y_s = y_how + 12
    for num, titulo, desc in steps:
        _line(10, y_s, 190, 18, LR, LG, LB)
        _line(10, y_s, 4, 18, GR, GG, GB)
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(GR, GG, GB)
        pdf.set_xy(17, y_s + 2)
        pdf.cell(12, 12, _s(num), 0, 0, 'C')
        pdf.set_font('Arial', 'B', 8.5)
        pdf.set_text_color(DR, DG, DB)
        pdf.set_xy(31, y_s + 3)
        pdf.cell(166, 5, _s(titulo), 0, 0, 'L')
        pdf.set_font('Arial', '', 7.5)
        pdf.set_text_color(MR, MG, MB)
        pdf.set_xy(31, y_s + 9)
        pdf.cell(166, 5, _s(desc), 0, 0, 'L')
        y_s += 20

    # ── CTA ───────────────────────────────────────────
    y_cta = y_s + 3
    _line(10, y_cta, 190, 38, 45, 39, 22)
    _line(10, y_cta, 190, 2, GR, GG, GB)

    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(GR, GG, GB)
    pdf.set_xy(12, y_cta + 5)
    pdf.cell(186, 7, _s("ESTA COTA ESTA DISPONIVEL — RESERVE AGORA"), 0, 0, 'C')

    pdf.set_font('Arial', '', 8.5)
    pdf.set_text_color(220, 210, 170)
    pdf.set_xy(14, y_cta + 14)
    pdf.multi_cell(182, 5, _s(
        f"Cartas contempladas mudam de status rapidamente. {cliente_label}, voce ja tem o credito "
        f"na mao, sem espera, sem sorteio.\n"
        f"Basta formalizar a transferencia e o credito de {fmt_brl(credito)} e seu — para {uso_txt}."
    ), 0, 'C')

    pdf.set_font('Arial', 'B', 9.5)
    pdf.set_text_color(GR, GG, GB)
    pdf.set_xy(12, y_cta + 30)
    pdf.cell(186, 5, _s("Entre em contato agora com nosso consultor e garanta esta oportunidade."), 0, 0, 'C')

    # ── Rodapé ────────────────────────────────────────
    _line(0, 279, 210, 18, DR, DG, DB)
    _line(0, 279, 210, 1.2, GR, GG, GB)

    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(GR, GG, GB)
    pdf.set_xy(10, 281)
    pdf.cell(190, 5,
        _s("JBS CONTEMPLADAS  |  Inteligencia Comercial  |  Documento gerado automaticamente"),
        0, 0, 'C')

    pdf.set_font('Arial', '', 6.5)
    pdf.set_text_color(100, 90, 60)
    pdf.set_xy(10, 287)
    pdf.cell(190, 4,
        _s("Valores sujeitos a confirmacao. Consulte disponibilidade com nossa equipe antes de qualquer decisao financeira."),
        0, 0, 'C')

    out = pdf.output(dest='S')
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return out.encode('latin-1')
