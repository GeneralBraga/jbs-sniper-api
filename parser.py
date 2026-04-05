"""
motor/parser.py
Três parsers para extração de cotas de consórcio:
  1. icontemplados_detalhe  — blocos com "Saldo Devedor:"
  2. icontemplados_cards    — Ctrl+A sem expandir detalhes
  3. generico               — texto livre / WhatsApp
"""
import re
from motor.utils import limpar_moeda, detectar_tipo

# ── Listas de referência ──────────────────────────────────────────────────────

ADMINS = [
    'ITAÚ AUTO', 'ITAU AUTO', 'BRADESCO AUTO', 'BRADESCO IMÓVEIS',
    'BRADESCO', 'SANTANDER', 'ITAÚ', 'ITAU', 'PORTO SEGURO', 'PORTO',
    'CAIXA', 'BANCO DO BRASIL', 'BB', 'RODOBENS', 'EMBRACON',
    'ANCORA', 'ÂNCORA', 'MYCON', 'SICREDI', 'SICOOB', 'MAPFRE',
    'HS', 'YAMAHA', 'ZEMA', 'BANCORBRÁS', 'BANCORBRAS', 'SERVOPA',
    'WOOP', 'SOMPO', 'MAGALU',
]

BANCOS_IC = [
    'Itaú Auto', 'Itau Auto', 'Bradesco Auto', 'Bradesco Imóveis',
    'Bradesco', 'Santander', 'Porto Seguro', 'Caixa',
    'Banco do Brasil', 'BB', 'Rodobens', 'Embracon', 'Mycon',
    'Sicredi', 'Sicoob', 'Mapfre', 'Yamaha', 'Zema',
    'Magalu', 'Woop', 'Sompo', 'Ancora',
]
BANCOS_IC_LOWER = {b.lower() for b in BANCOS_IC}

_SKIP = {
    'selecionar', 'detalhes', 'reservada', 'negociar',
    'disponível', 'disponivel', 'código:', 'codigo:',
    'directions_car', 'directions_home', 'directions_bus',
    'warning', 'info', 'check_circle', 'error',
    'baixar pdf', 'baixar excel', 'selecionar todas', 'criar filtro',
    'compartilhar', 'somar', 'início', 'inicio', 'todos',
    'automóveis', 'automoveis', 'itaú consórcio', 'itau consorcio',
    'cartas contempladas para veículo', 'cartas contempladas para veiculo',
    'cartas contempladas para imovel', 'cartas contempladas para imóvel',
    'imóvel', 'imovel', 'veículo', 'veiculo',
}

_RE_CREDITO = re.compile(
    r'(?:cr[eé]dito|bem|valor[\s_]do[\s_]bem|valor[\s_]carta)[^\d\n]{0,25}?R\$\s*([\d\.,]+)',
    re.IGNORECASE)
_RE_ENTRADA = re.compile(
    r'(?:entrada|[aá]gio|lance[\s_]fixo|pago|quero)[^\d\n]{0,25}?R\$\s*([\d\.,]+)',
    re.IGNORECASE)
_RE_PARCELA = re.compile(r'(\d+)\s*[xX]\s*R?\$?\s*([\d\.,]+)', re.IGNORECASE)
_RE_MOEDA   = re.compile(r'R\$\s*([\d\.,]+)', re.IGNORECASE)


# ── Detector de formato ───────────────────────────────────────────────────────

def detectar_formato(texto: str) -> str:
    if re.search(r'saldo\s+devedor\s*:', texto, re.IGNORECASE):
        return "icontemplados_detalhe"
    tem_entrada  = bool(re.search(r'^entrada\s*:?\s*$', texto, re.IGNORECASE | re.MULTILINE))
    tem_parcelas = bool(re.search(r'^parcelas?\s*:?\s*$', texto, re.IGNORECASE | re.MULTILINE))
    tem_banco    = any(b in texto for b in BANCOS_IC)
    if tem_banco and tem_entrada and tem_parcelas:
        return "icontemplados_cards"
    return "generico"


# ── Parser 1 — iContemplados com Detalhes expandidos ─────────────────────────

def _extrair_icontemplados_detalhe(texto: str, tipo_sel: str) -> list:
    lista, id_c = [], 1
    blocos = re.split(r'(?i)(?=administradora\s*:)', texto)
    for bloco in blocos:
        if 'administradora' not in bloco.lower():
            continue
        if len(bloco.strip()) < 30:
            continue
        try:
            m = re.search(r'administradora\s*:\s*\*?\*?([^\n\*]+)', bloco, re.IGNORECASE)
            admin_raw = m.group(1).strip() if m else "OUTROS"
            admin = admin_raw.upper()
            for adm in ADMINS:
                if adm.lower() in admin_raw.lower():
                    admin = adm.upper()
                    break

            m = re.search(r'cr[eé]dito\s*:\s*\*?\*?\s*R\$\s*([\d\.,]+)', bloco, re.IGNORECASE)
            credito = limpar_moeda(m.group(1)) if m else 0.0
            if credito <= 0:
                continue

            m = re.search(r'segmento\s*:\s*\*?\*?([^\n\*]+)', bloco, re.IGNORECASE)
            tipo_raw = m.group(1).strip().lower() if m else ""
            if any(k in tipo_raw for k in ('imóvel', 'imovel', 'imov')):
                tipo = "Imóvel"
            elif any(k in tipo_raw for k in ('pesado', 'caminhão', 'caminhao')):
                tipo = "Pesados"
            elif any(k in tipo_raw for k in ('veículo', 'veiculo', 'auto', 'carro', 'moto')):
                tipo = "Automóvel"
            else:
                tipo = "Imóvel" if credito > 250000 else "Automóvel"

            if tipo_sel not in ("Todos", "Geral") and tipo != tipo_sel:
                continue

            m = re.search(r'entrada\s*:\s*\*?\*?\s*R\$\s*([\d\.,]+)', bloco, re.IGNORECASE)
            entrada = limpar_moeda(m.group(1)) if m else 0.0
            if entrada <= 0:
                continue

            m = re.search(r'saldo\s+devedor\s*:\s*\*?\*?\s*R\$\s*([\d\.,]+)', bloco, re.IGNORECASE)
            saldo = limpar_moeda(m.group(1)) if m else 0.0

            m = re.search(r'parcelas?\s*:\s*\*?\*?\s*(\d+)\s*[xX]\s*R?\$?\s*([\d\.,]+)', bloco, re.IGNORECASE)
            parcela    = limpar_moeda(m.group(2)) if m else 0.0
            n_parcelas = int(m.group(1)) if m else 0

            if saldo <= 0:
                saldo = max(credito * 1.25 - entrada, credito * 0.20)

            lista.append({
                'ID': id_c, 'Admin': admin, 'Tipo': tipo,
                'Crédito': credito, 'Entrada': entrada,
                'Parcela': parcela, 'NParcelas': n_parcelas,
                'Saldo': saldo, 'CustoTotal': entrada + saldo,
                'EntradaPct': entrada / credito,
            })
            id_c += 1
        except Exception:
            continue
    return lista


# ── Parser 2 — iContemplados cards ───────────────────────────────────────────

def _extrair_icontemplados_cards(texto: str, tipo_sel: str) -> list:
    lista, id_c = [], 1

    # Códigos reservados
    codigos_reservados = set(re.findall(
        r'(\d+)\s*\nSelecionar\s*\nDetalhes\s*\nReservada',
        texto, re.IGNORECASE
    ))
    for m in re.finditer(r'[Cc][oó]digo:\s*\n(\d+)\s*\n.*?Reservada', texto, re.DOTALL):
        codigos_reservados.add(m.group(1))

    # Tipo padrão pelo cabeçalho
    header = texto[:500].lower()
    if any(k in header for k in ('para veículo', 'para veiculo', 'veículo', 'veiculo')):
        tipo_default = "Automóvel"
    elif any(k in header for k in ('para imóvel', 'para imovel', 'imóvel', 'imovel')):
        tipo_default = "Imóvel"
    else:
        tipo_default = "Automóvel"

    # Limpa linhas
    linhas = []
    for ln in texto.replace('\r', '').split('\n'):
        ln = ln.strip()
        if not ln:
            continue
        if ln.lower() in _SKIP:
            continue
        linhas.append(ln)

    i = 0
    while i < len(linhas):
        ln = linhas[i]
        if (ln.lower() in BANCOS_IC_LOWER
                and i + 1 < len(linhas)
                and re.match(r'^R\$\s*[\d\.]+,\d{2}$', linhas[i + 1])):

            admin_raw = ln
            credito   = limpar_moeda(linhas[i + 1])
            if credito <= 0:
                i += 1
                continue

            al = admin_raw.lower()
            if any(k in al for k in ('auto', 'automóvel', 'automovel', 'veículo', 'veiculo', 'carro', 'moto')):
                tipo = "Automóvel"
            elif any(k in al for k in ('imóvel', 'imovel', 'imov')):
                tipo = "Imóvel"
            elif any(k in al for k in ('caminhão', 'caminhao', 'pesado')):
                tipo = "Pesados"
            else:
                tipo = tipo_default

            if tipo_sel not in ("Todos", "Geral") and tipo != tipo_sel:
                i += 2
                continue

            admin = admin_raw.upper()
            for adm in ADMINS:
                if adm.lower() in admin_raw.lower():
                    admin = adm.upper()
                    break

            entrada    = 0.0
            parcela    = 0.0
            n_parcelas = 0
            codigo_cota = None
            j = i + 2

            while j < min(i + 18, len(linhas)):
                lj   = linhas[j]
                lj_l = lj.lower()

                if re.match(r'^\d{3,4}$', lj) and codigo_cota is None:
                    codigo_cota = lj
                    j += 1
                    continue

                if lj.lower() in BANCOS_IC_LOWER:
                    break

                if lj_l == 'entrada:':
                    if j + 1 < len(linhas):
                        entrada = limpar_moeda(linhas[j + 1])
                        j += 2
                        continue

                if re.match(r'^parcelas?\s*:$', lj_l):
                    if j + 1 < len(linhas):
                        m2 = re.match(r'(\d+)\s*[xX]\s*R\$\s*([\d\.]+,\d{2})', linhas[j + 1])
                        if m2:
                            n_parcelas = int(m2.group(1))
                            parcela    = limpar_moeda(m2.group(2))
                    j += 2
                    continue

                m2 = re.search(r'entrada:\s*R\$\s*([\d\.]+,\d{2})', lj, re.IGNORECASE)
                if m2:
                    entrada = limpar_moeda(m2.group(1))
                    j += 1
                    continue

                m2 = re.search(r'parcelas?:\s*(\d+)\s*[xX]\s*R\$\s*([\d\.]+,\d{2})', lj, re.IGNORECASE)
                if m2:
                    n_parcelas = int(m2.group(1))
                    parcela    = limpar_moeda(m2.group(2))
                    j += 1
                    continue

                j += 1

            if codigo_cota and codigo_cota in codigos_reservados:
                i = j
                continue

            if credito > 0 and entrada > 0:
                saldo = (n_parcelas * parcela if n_parcelas > 0 and parcela > 0
                         else max(credito * 1.25 - entrada, credito * 0.20))
                lista.append({
                    'ID': id_c, 'Admin': admin, 'Tipo': tipo,
                    'Crédito': credito, 'Entrada': entrada,
                    'Parcela': parcela, 'NParcelas': n_parcelas,
                    'Saldo': saldo, 'CustoTotal': entrada + saldo,
                    'EntradaPct': entrada / credito,
                    'Disponivel': True,
                })
                id_c += 1

            i = j
            continue

        i += 1
    return lista


# ── Parser 3 — Genérico ───────────────────────────────────────────────────────

def _extrair_generico(texto: str, tipo_sel: str) -> list:
    blocos = re.split(
        r'(?i)(?=\b(?:imóvel|imovel|automóvel|automovel|veículo|veiculo|caminhão|caminhao|moto)\b)',
        texto
    )
    if len(blocos) < 2:
        blocos = re.split(r'\n\s*\n+', texto)
    if len(blocos) < 2:
        blocos = [texto]

    lista, id_c = [], 1
    for bloco in blocos:
        if len(bloco.strip()) < 20:
            continue
        try:
            bl = bloco.lower()
            admin = next((a.upper() for a in ADMINS if a.lower() in bl), "OUTROS")
            if admin == "OUTROS" and "r$" not in bl:
                continue
            tipo = detectar_tipo(bl)
            credito = 0.0
            m = _RE_CREDITO.search(bloco)
            if m:
                credito = limpar_moeda(m.group(1))
            if credito <= 0:
                vals = sorted(
                    [limpar_moeda(v) for v in _RE_MOEDA.findall(bloco) if limpar_moeda(v) > 5000],
                    reverse=True
                )
                credito = vals[0] if vals else 0.0
            if credito <= 5000:
                continue
            if tipo == "Geral":
                tipo = "Imóvel" if credito > 250000 else "Automóvel"
            if tipo_sel not in ("Todos", "Geral") and tipo != tipo_sel:
                continue
            entrada = 0.0
            m = _RE_ENTRADA.search(bloco)
            if m:
                entrada = limpar_moeda(m.group(1))
            if entrada <= 0:
                cands = sorted(
                    [limpar_moeda(v) for v in _RE_MOEDA.findall(bloco)
                     if credito * 0.01 < limpar_moeda(v) < credito * 0.95],
                    reverse=True
                )
                entrada = cands[0] if cands else 0.0
            if entrada <= 0:
                continue
            saldo, parcela, n_parcelas = 0.0, 0.0, 0
            for pz_s, vl_s in _RE_PARCELA.findall(bloco):
                try:
                    pz, vl = int(pz_s), limpar_moeda(vl_s)
                    if pz > 0 and vl > 0:
                        saldo += pz * vl
                        if pz > 1 and vl > parcela:
                            parcela = vl
                            n_parcelas = pz
                except Exception:
                    continue
            if saldo <= 0:
                saldo = max(credito * 1.25 - entrada, credito * 0.20)
            lista.append({
                'ID': id_c, 'Admin': admin, 'Tipo': tipo,
                'Crédito': credito, 'Entrada': entrada,
                'Parcela': parcela, 'NParcelas': n_parcelas,
                'Saldo': saldo, 'CustoTotal': entrada + saldo,
                'EntradaPct': entrada / credito,
            })
            id_c += 1
        except Exception:
            continue
    return lista


# ── Roteador principal ────────────────────────────────────────────────────────

def extrair_dados_universal(texto: str, tipo_sel: str = "Todos") -> list:
    if not texto or not texto.strip():
        return []
    texto_limpo = "\n".join(
        ln.strip() for ln in texto.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        if ln.strip()
    )
    fmt = detectar_formato(texto_limpo)
    if fmt == "icontemplados_detalhe":
        return _extrair_icontemplados_detalhe(texto_limpo, tipo_sel)
    if fmt == "icontemplados_cards":
        return _extrair_icontemplados_cards(texto_limpo, tipo_sel)
    return _extrair_generico(texto_limpo, tipo_sel)
