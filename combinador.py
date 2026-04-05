"""
motor/combinador.py
Motor de combinações: itera cotas com itertools.combinations
e retorna as melhores oportunidades ordenadas por CET.
"""
import itertools
from motor.utils import fmt_brl, fmt_pct, fmt_pct_curto


def _status(cr: float) -> str:
    if cr <= 0.20: return "OURO"
    if cr <= 0.35: return "IMPERDIVEL"
    if cr <= 0.45: return "EXCELENTE"
    if cr <= 0.50: return "OPORTUNIDADE"
    return "PADRAO"


def processar_combinacoes(
    cotas: list,
    min_cred: float,
    max_cred: float,
    max_ent: float,
    max_parc: float,
    max_custo: float,
    tipo_f: str = "Todos",
    admin_f: str = "Todas",
) -> list:
    """
    Retorna lista de dicts com as melhores combinações de cotas.
    max_custo é decimal (ex: 0.55 = 55%).
    """
    MAX_ADM = 400
    TOL = 1.05

    filtradas = [
        c for c in cotas
        if (tipo_f in ("Todos", "Geral") or c['Tipo'] == tipo_f)
        and (admin_f == "Todas" or c['Admin'] == admin_f)
        and c['Admin'] != "OUTROS"
        and c['Entrada'] <= max_ent * TOL
        and c['Crédito'] <= max_cred
        and c.get('Disponivel', True)
    ]

    if not filtradas:
        return []

    por_admin: dict = {}
    for c in filtradas:
        por_admin.setdefault(c['Admin'], []).append(c)

    res = []
    for admin, grupo in por_admin.items():
        grupo.sort(key=lambda x: x['Entrada'])
        cnt = 0
        for r in range(1, 7):
            if cnt >= MAX_ADM:
                break
            for combo in itertools.combinations(grupo, r):
                if cnt >= MAX_ADM:
                    break
                soma_e = sum(c['Entrada'] for c in combo)
                if soma_e > max_ent * TOL:
                    if r >= 2 and sum(c['Entrada'] for c in grupo[:r]) > max_ent * TOL:
                        break
                    continue
                soma_c = sum(c['Crédito'] for c in combo)
                if soma_c < min_cred or soma_c > max_cred:
                    continue
                soma_p = sum(c['Parcela'] for c in combo)
                if soma_p > max_parc * TOL:
                    continue
                soma_s = sum(c['Saldo'] for c in combo)
                custo_t = soma_e + soma_s
                if soma_c <= 0:
                    continue
                cr = (custo_t / soma_c) - 1
                if cr > max_custo:
                    continue
                prazo = int(soma_s / soma_p) if soma_p > 0 else 0
                cet_mensal = (cr / prazo * 100) if prazo > 0 else 0.0
                res.append({
                    'status':          _status(cr),
                    'administradora':  admin,
                    'tipo':            combo[0]['Tipo'],
                    'ids':             " + ".join(str(c['ID']) for c in combo),
                    'credito_total':   soma_c,
                    'entrada_total':   soma_e,
                    'entrada_pct':     (soma_e / soma_c) * 100,
                    'saldo_devedor':   soma_s,
                    'custo_total':     custo_t,
                    'prazo_meses':     prazo,
                    'parcela_mensal':  soma_p,
                    'cet_total_pct':   cr * 100,
                    'cet_mensal_pct':  cet_mensal,
                    'detalhes':        " || ".join(
                        f"[ID {c['ID']}] {c['Admin']} · {fmt_brl(c['Crédito'])}"
                        for c in combo
                    ),
                })
                cnt += 1

    # Ordena por CET total crescente
    res.sort(key=lambda x: x['cet_total_pct'])
    return res
