import logging
import os

from groq import Groq
from pydantic import BaseModel, ValidationError

from src.ia.prompt import montar_prompt
from src.processamento.calculo_metricas import MetricasSemana
from src.processamento.comparacao import VariacaoSemana
from src.retry import executar_com_retry

logger = logging.getLogger(__name__)

MODELO_PADRAO = "llama-3.3-70b-versatile"


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
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        modelo = os.environ.get("GROQ_MODEL", MODELO_PADRAO)
        schema_instrucao = (
            "Responda SOMENTE com um objeto JSON válido, sem texto adicional, "
            "usando exatamente estas chaves:\n"
            '{"resumo_executivo": "string", '
            '"destaques": [{"tipo": "string", "descricao": "string"}], '
            '"possivel_causa": "string ou null", '
            '"recomendacao": "string"}'
        )
        completion = client.chat.completions.create(
            model=modelo,
            messages=[
                {"role": "system", "content": schema_instrucao},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        conteudo = completion.choices[0].message.content
        try:
            return RespostaIA.model_validate_json(conteudo)
        except ValidationError as e:
            raise RespostaIAInvalidaError(
                f"Resposta não valida contra o schema: {e}"
            ) from e

    try:
        resultado = executar_com_retry(_chamar_api)
    except Exception:
        logger.error("Falha persistente ao gerar interpretação com a IA", exc_info=True)
        return None

    if not variacao.tem_historico:
        resultado = resultado.model_copy(update={"possivel_causa": None})

    return resultado
