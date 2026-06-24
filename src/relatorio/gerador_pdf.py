import os
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from src.ia.cliente_gemini import RespostaIA
from src.processamento.calculo_metricas import MetricasSemana
from src.processamento.comparacao import VariacaoSemana
from src.relatorio.grafico import gerar_grafico_evolucao

DIRETORIO_TEMPLATES = Path(__file__).parent / "templates"
DIRETORIO_RELATORIOS = Path("relatorios")

_ambiente_jinja = Environment(loader=FileSystemLoader(DIRETORIO_TEMPLATES))


def montar_html(
    semana: str,
    metricas: MetricasSemana,
    variacao: VariacaoSemana,
    resposta_ia: RespostaIA | None,
    historico_reach: list[tuple[str, int]],
) -> str:
    contexto = {
        "nome_negocio": os.environ.get("NOME_NEGOCIO", ""),
        "periodo": _formatar_periodo(semana),
        "reach_total": _formatar_milhar(metricas.reach_total),
        "engajamento_total": _formatar_milhar(metricas.engajamento_total),
        "taxa_engajamento_semanal": _formatar_percentual(metricas.taxa_engajamento_semanal),
        "variacao_reach_total": _formatar_variacao(variacao.variacao_reach_total),
        "variacao_engajamento_total": _formatar_variacao(variacao.variacao_engajamento_total),
        "grafico_base64": gerar_grafico_evolucao(historico_reach),
        "resposta_ia": resposta_ia,
    }
    template = _ambiente_jinja.get_template("relatorio.html")
    return template.render(**contexto)


def gerar_pdf(
    semana: str,
    metricas: MetricasSemana,
    variacao: VariacaoSemana,
    resposta_ia: RespostaIA | None,
    historico_reach: list[tuple[str, int]],
) -> str:
    html = montar_html(semana, metricas, variacao, resposta_ia, historico_reach)

    DIRETORIO_RELATORIOS.mkdir(parents=True, exist_ok=True)
    caminho_pdf = DIRETORIO_RELATORIOS / f"relatorio_{semana}.pdf"

    with open(caminho_pdf, "wb") as arquivo_pdf:
        pisa.CreatePDF(html, dest=arquivo_pdf)

    return str(caminho_pdf)


def _formatar_periodo(semana: str) -> str:
    segunda = date.fromisoformat(semana)
    domingo = segunda + timedelta(days=6)
    return f"{segunda.strftime('%d/%m')} a {domingo.strftime('%d/%m/%Y')}"


def _formatar_milhar(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def _formatar_percentual(valor: float) -> str:
    return f"{valor:.1f}".replace(".", ",") + "%"


def _formatar_variacao(valor: float | None) -> str:
    if valor is None:
        return "sem base de comparação"
    sinal = "+" if valor >= 0 else ""
    return f"{sinal}{valor:.1f}".replace(".", ",") + "%"
