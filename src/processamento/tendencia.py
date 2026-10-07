from dataclasses import dataclass

from src.processamento.comparacao import TotaisAnteriores

JANELA_TENDENCIA = 4


@dataclass(frozen=True)
class TendenciaSemana:
    tem_historico: bool
    semanas_usadas: int
    media_reach_total: float | None
    media_engajamento_total: float | None
    variacao_reach_total: float | None
    variacao_engajamento_total: float | None


def calcular_tendencia(
    reach_total_atual: int,
    engajamento_total_atual: int,
    historico: list[TotaisAnteriores],
) -> TendenciaSemana:
    if not historico:
        return TendenciaSemana(
            tem_historico=False,
            semanas_usadas=0,
            media_reach_total=None,
            media_engajamento_total=None,
            variacao_reach_total=None,
            variacao_engajamento_total=None,
        )

    amostra = historico[:JANELA_TENDENCIA]
    semanas_usadas = len(amostra)
    media_reach = sum(item.reach_total for item in amostra) / semanas_usadas
    media_engajamento = sum(item.engajamento_total for item in amostra) / semanas_usadas

    return TendenciaSemana(
        tem_historico=True,
        semanas_usadas=semanas_usadas,
        media_reach_total=media_reach,
        media_engajamento_total=media_engajamento,
        variacao_reach_total=_variacao_percentual(media_reach, reach_total_atual),
        variacao_engajamento_total=_variacao_percentual(
            media_engajamento, engajamento_total_atual
        ),
    )


def _variacao_percentual(media: float, valor_atual: int) -> float | None:
    if media == 0:
        return None
    return (valor_atual - media) / media * 100
