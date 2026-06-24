import logging
import os

from google import genai
from pydantic import BaseModel

from src.ia.prompt import montar_prompt
from src.processamento.calculo_metricas import MetricasSemana
from src.processamento.comparacao import VariacaoSemana
from src.retry import executar_com_retry

logger = logging.getLogger(__name__)

MODELO_PADRAO = "gemini-3.5-flash"


class RespostaIAInvalidaError(Exception):
    pass


class Destaque(BaseModel):
    tipo: str
    descricao: str


class RespostaIA(BaseModel):
    resumo_executivo: str
    destaques: list[Destaque]
    possivel_causa: str | None
    recomendacao: str


def gerar_interpretacao(
    metricas: MetricasSemana, variacao: VariacaoSemana
) -> RespostaIA | None:
    prompt = montar_prompt(metricas, variacao)

    def _chamar_api() -> RespostaIA:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        modelo = os.environ.get("GEMINI_MODEL", MODELO_PADRAO)
        resposta = client.models.generate_content(
            model=modelo,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": RespostaIA,
            },
        )
        if resposta.parsed is None:
            raise RespostaIAInvalidaError(
                "Gemini retornou resposta que não valida contra o schema"
            )
        return resposta.parsed

    try:
        resultado = executar_com_retry(_chamar_api)
    except Exception:
        logger.error(
            "Falha persistente ao gerar interpretação com a Gemini", exc_info=True
        )
        return None

    if not variacao.tem_historico:
        resultado = resultado.model_copy(update={"possivel_causa": None})

    return resultado
