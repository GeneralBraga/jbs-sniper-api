"""
motor/whatsapp.py
Geração de mensagem formatada para WhatsApp.
"""
from motor.utils import fmt_brl, fmt_pct


def gerar_msg_whatsapp(row: dict) -> str:
    tipo       = str(row.get('tipo', 'Imóvel'))
    admin      = str(row.get('administradora', ''))
    credito    = float(row.get('credito_total', 0))
    entrada    = float(row.get('entrada_total', 0))
    parcela    = float(row.get('parcela_mensal', 0))
    prazo      = int(row.get('prazo_meses', 0))
    cet_total  = float(row.get('cet_total_pct', 0))
    cet_mensal = float(row.get('cet_mensal_pct', 0))
    ids        = str(row.get('ids', ''))

    if "móvel" in tipo.lower() or "movel" in tipo.lower():
        emoji_tipo = "🏠 *IMÓVEL*"
    elif "pesado" in tipo.lower() or "caminhao" in tipo.lower():
        emoji_tipo = "🚛 *CAMINHÃO*"
    else:
        emoji_tipo = "🚗 *AUTO*"

    parc_str = f"{prazo}x {fmt_brl(parcela)}" if prazo > 0 and parcela > 0 else "A consultar"

    n_cotas = len(ids.split('+')) if ids else 1
    admin_upper = admin.upper()
    if 'ITAÚ' in admin_upper or 'ITAU' in admin_upper:
        tx_transf = 650.0 * n_cotas
    else:
        tx_transf = credito * 0.01

    return (
        f"🔑 *CARTA CONTEMPLADA — {admin}*\n"
        f"\n"
        f"{emoji_tipo}\n"
        f"*Crédito:* {fmt_brl(credito)}\n"
        f"*Entrada:* {fmt_brl(entrada)}\n"
        f"*Parcela:* {parc_str}\n"
        f"*Tx de Transferência:* {fmt_brl(tx_transf)}\n"
        f"\n"
        f"*CET Mensal:* {fmt_pct(cet_mensal)} a.m.\n"
        f"*CET Total:* {fmt_pct(cet_total)}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🏆 *JBS Contempladas*"
    )
