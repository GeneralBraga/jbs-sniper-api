"""
motor/utils.py
Funções utilitárias: formatação BR e limpeza de moeda.
"""
import re


def fmt_brl(valor) -> str:
    try:
        s = f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {s}"
    except Exception:
        return "R$ 0,00"


def fmt_pct(valor) -> str:
    try:
        return f"{float(valor):.2f}%".replace(".", ",")
    except Exception:
        return "0,00%"


def fmt_pct_curto(valor) -> str:
    try:
        return f"{float(valor):.0f}%"
    except Exception:
        return "0%"


def limpar_moeda(texto) -> float:
    if not texto:
        return 0.0
    try:
        t = (str(texto).lower().strip()
             .replace('\xa0', '').replace('&nbsp;', '')
             .replace('r$', '').replace(' ', ''))
        t = re.sub(r'[^\d\.,]', '', t)
        if not t:
            return 0.0
        if ',' in t and '.' in t:
            return float(t.replace('.', '').replace(',', '.'))
        if ',' in t:
            p = t.split(',')
            return float(t.replace(',', '.')) if len(p) == 2 and len(p[1]) <= 2 else float(t.replace(',', ''))
        if '.' in t:
            p = t.split('.')
            return float(t) if len(p) == 2 and len(p[1]) == 2 else float(t.replace('.', ''))
        return float(t)
    except Exception:
        return 0.0


def detectar_tipo(b: str) -> str:
    if any(k in b for k in ('imóvel', 'imovel', 'apartamento', 'casa', 'terreno', 'comercial')):
        return "Imóvel"
    if any(k in b for k in ('caminhão', 'caminhao', 'pesado', 'truck', 'ônibus', 'onibus')):
        return "Pesados"
    if any(k in b for k in ('automóvel', 'automovel', 'veículo', 'veiculo', 'carro', 'moto')):
        return "Automóvel"
    return "Geral"
