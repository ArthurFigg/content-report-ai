from src.processamento.comparacao import TotaisAnteriores
from src.processamento.tendencia import JANELA_TENDENCIA, calcular_tendencia


def _historico_de_reach(valores: list[int], engajamento: int = 10) -> list[TotaisAnteriores]:
    return [TotaisAnteriores(reach_total=v, engajamento_total=engajamento) for v in valores]


def test_janela_tendencia_vale_quatro():
    assert JANELA_TENDENCIA == 4


def test_calcular_tendencia_historico_vazio_informa_que_nao_tem_historico():
    tendencia = calcular_tendencia(150, 30, [])

    assert tendencia.tem_historico is False


def test_calcular_tendencia_historico_vazio_usa_zero_semanas():
    tendencia = calcular_tendencia(150, 30, [])

    assert tendencia.semanas_usadas == 0


def test_calcular_tendencia_historico_vazio_devolve_medias_none():
    tendencia = calcular_tendencia(150, 30, [])

    assert (tendencia.media_reach_total, tendencia.media_engajamento_total) == (None, None)


def test_calcular_tendencia_historico_vazio_devolve_variacoes_none():
    tendencia = calcular_tendencia(150, 30, [])

    assert (
        tendencia.variacao_reach_total,
        tendencia.variacao_engajamento_total,
    ) == (None, None)


def test_calcular_tendencia_tres_semanas_calcula_media_de_reach():
    tendencia = calcular_tendencia(150, 30, _historico_de_reach([100, 200, 300]))

    assert tendencia.media_reach_total == 200


def test_calcular_tendencia_tres_semanas_informa_semanas_usadas():
    tendencia = calcular_tendencia(150, 30, _historico_de_reach([100, 200, 300]))

    assert tendencia.semanas_usadas == 3


def test_calcular_tendencia_com_historico_marca_tem_historico_verdadeiro():
    tendencia = calcular_tendencia(150, 30, _historico_de_reach([100]))

    assert tendencia.tem_historico is True


def test_calcular_tendencia_seis_semanas_usa_so_quatro():
    historico = _historico_de_reach([100, 100, 100, 100, 900, 900])

    tendencia = calcular_tendencia(150, 30, historico)

    assert tendencia.semanas_usadas == 4


def test_calcular_tendencia_seis_semanas_calcula_media_so_com_as_quatro_primeiras():
    historico = _historico_de_reach([100, 200, 300, 400, 9000, 9000])

    tendencia = calcular_tendencia(150, 30, historico)

    assert tendencia.media_reach_total == 250


def test_calcular_tendencia_seis_semanas_calcula_media_de_engajamento_so_com_as_quatro_primeiras():
    historico = [
        TotaisAnteriores(reach_total=100, engajamento_total=valor)
        for valor in [10, 20, 30, 40, 5000, 5000]
    ]

    tendencia = calcular_tendencia(150, 30, historico)

    assert tendencia.media_engajamento_total == 25


def test_calcular_tendencia_reach_acima_da_media_da_variacao_positiva():
    tendencia = calcular_tendencia(150, 30, _historico_de_reach([100]))

    assert tendencia.variacao_reach_total == 50.0


def test_calcular_tendencia_reach_abaixo_da_media_da_variacao_negativa():
    tendencia = calcular_tendencia(150, 30, _historico_de_reach([200]))

    assert tendencia.variacao_reach_total == -25.0


def test_calcular_tendencia_media_de_engajamento_zero_devolve_variacao_none():
    historico = _historico_de_reach([100], engajamento=0)

    tendencia = calcular_tendencia(150, 30, historico)

    assert tendencia.variacao_engajamento_total is None


def test_calcular_tendencia_media_de_engajamento_zero_mantem_variacao_de_reach():
    historico = _historico_de_reach([100], engajamento=0)

    tendencia = calcular_tendencia(150, 30, historico)

    assert tendencia.variacao_reach_total == 50.0
