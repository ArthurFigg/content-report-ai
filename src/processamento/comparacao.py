from dataclasses import dataclass


@dataclass(frozen=True)
class TotaisAnteriores:
    reach_total: int
    engajamento_total: int


@dataclass(frozen=True)
class VariacaoSemana:
    tem_historico: bool
    variacao_reach_total: float | None
    variacao_engajamento_total: float | None


def calcular_variacao(
    reach_total_atual: int,
    engajamento_total_atual: int,
    totais_anteriores: TotaisAnteriores | None,
) -> VariacaoSemana:
    if totais_anteriores is None:
        return VariacaoSemana(
            tem_historico=False,
            variacao_reach_total=None,
            variacao_engajamento_total=None,
        )

    return VariacaoSemana(
        tem_historico=True,
        variacao_reach_total=_variacao_percentual(
            totais_anteriores.reach_total, reach_total_atual
        ),
        variacao_engajamento_total=_variacao_percentual(
            totais_anteriores.engajamento_total, engajamento_total_atual
        ),
    )


def _variacao_percentual(valor_anterior: int, valor_atual: int) -> float | None:
    if valor_anterior == 0:
        return None
    return (valor_atual - valor_anterior) / valor_anterior * 100
