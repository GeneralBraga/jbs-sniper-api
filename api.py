"""
api.py — JBS Sniper API
FastAPI pronto para Railway.
Todos os endpoints do motor de consórcio expostos via HTTP.
"""
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import io
import os

from motor.parser import extrair_dados_universal
from motor.combinador import processar_combinacoes
from motor.pdf_contemplada import gerar_pdf_contemplada
from motor.whatsapp import gerar_msg_whatsapp
from motor.utils import fmt_brl, fmt_pct

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="JBS Sniper API",
    description="Motor de análise de cotas de consórcio contempladas — JBS Contempladas",
    version="1.0.0",
)

# CORS — permite chamadas do frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # em produção, trocar por ["https://jbscontempladas.com.br"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chave de API simples para proteger os endpoints
# Configure a variável de ambiente API_KEY no Railway
API_KEY = os.environ.get("API_KEY", "jbs-sniper-dev-key")


def verificar_chave(x_api_key: str = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Chave de API inválida")


# ── Schemas ───────────────────────────────────────────────────────────────────

class AnalisarRequest(BaseModel):
    texto: str = Field(..., description="Texto copiado do portal / WhatsApp")
    tipo_sel: str = Field("Todos", description="Imóvel | Automóvel | Pesados | Todos")


class CombinarRequest(BaseModel):
    texto: str
    tipo_sel: str   = "Todos"
    admin_f: str    = "Todas"
    min_cred: float = 60_000.0
    max_cred: float = 710_000.0
    max_ent: float  = 200_000.0
    max_parc: float = 4_500.0
    max_custo: float = 0.55       # decimal — 0.55 = 55%


class PDFContempladaRequest(BaseModel):
    admin: str
    tipo: str
    nome_cliente: str = ""
    credito: float
    entrada: float
    n_parcelas: int
    parcela: float
    tx_transf: float


class WhatsAppRequest(BaseModel):
    tipo: str
    administradora: str
    credito_total: float
    entrada_total: float
    parcela_mensal: float
    prazo_meses: int
    cet_total_pct: float
    cet_mensal_pct: float
    ids: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["status"])
def root():
    return {"status": "ok", "produto": "JBS Sniper API", "versao": "1.0.0"}


@app.get("/health", tags=["status"])
def health():
    return {"status": "healthy"}


@app.post("/analisar", tags=["motor"])
def analisar(req: AnalisarRequest, x_api_key: str = Header(default=None)):
    """
    Extrai cotas do texto e retorna lista de cotas identificadas.
    """
    verificar_chave(x_api_key)
    cotas = extrair_dados_universal(req.texto, req.tipo_sel)
    if not cotas:
        return {"total": 0, "cotas": []}
    admins = sorted(set(c['Admin'] for c in cotas if c['Admin'] != "OUTROS"))
    tipos  = {}
    for c in cotas:
        tipos[c['Tipo']] = tipos.get(c['Tipo'], 0) + 1
    return {
        "total":       len(cotas),
        "admins":      admins,
        "por_tipo":    tipos,
        "cotas":       cotas,
    }


@app.post("/combinar", tags=["motor"])
def combinar(req: CombinarRequest, x_api_key: str = Header(default=None)):
    """
    Motor principal: extrai cotas e retorna melhores combinações ordenadas por CET.
    """
    verificar_chave(x_api_key)
    cotas = extrair_dados_universal(req.texto, req.tipo_sel)
    if not cotas:
        raise HTTPException(status_code=422, detail="Nenhuma cota identificada no texto.")

    resultado = processar_combinacoes(
        cotas      = cotas,
        min_cred   = req.min_cred,
        max_cred   = req.max_cred,
        max_ent    = req.max_ent,
        max_parc   = req.max_parc,
        max_custo  = req.max_custo,
        tipo_f     = req.tipo_sel,
        admin_f    = req.admin_f,
    )

    if not resultado:
        return {"total": 0, "combinacoes": []}

    return {
        "total":       len(resultado),
        "menor_cet":   fmt_pct(resultado[0]['cet_total_pct']),
        "combinacoes": resultado,
    }


@app.post("/pdf-contemplada", tags=["pdf"])
def pdf_contemplada(req: PDFContempladaRequest, x_api_key: str = Header(default=None)):
    """
    Gera o PDF premium de carta contemplada individual.
    Retorna o arquivo PDF como download.
    """
    verificar_chave(x_api_key)
    if req.credito <= 0 or req.entrada <= 0 or req.parcela <= 0:
        raise HTTPException(status_code=422, detail="Crédito, entrada e parcela são obrigatórios.")
    try:
        pdf_bytes = gerar_pdf_contemplada(
            admin        = req.admin,
            tipo         = req.tipo,
            nome_cliente = req.nome_cliente,
            credito      = req.credito,
            entrada      = req.entrada,
            n_parcelas   = req.n_parcelas,
            parcela      = req.parcela,
            tx_transf    = req.tx_transf,
        )
        nome = f"contemplada_{req.admin.lower().replace(' ', '_')}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={nome}"},
        )
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(ex)}")


@app.post("/whatsapp", tags=["mensagem"])
def whatsapp(req: WhatsAppRequest, x_api_key: str = Header(default=None)):
    """
    Gera a mensagem formatada para WhatsApp a partir dos dados de uma combinação.
    """
    verificar_chave(x_api_key)
    msg = gerar_msg_whatsapp(req.dict())
    return {"mensagem": msg}
