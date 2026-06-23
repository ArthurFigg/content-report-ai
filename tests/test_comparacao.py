from src.processamento.comparacao import TotaisAnteriores, calcular_variacao


def test_calcular_variacao_retorna_sem_historico_quando_anterior_e_none():
    variacao = calcular_variacao(1000, 100, None)

    assert variacao.tem_historico is False


def test_calcular_variacao_retorna_null_quando_valor_anterior_e_zero():
    anteriores = TotaisAnteriores(reach_total=0, engajamento_total=50)

    variacao = calcular_variacao(1000, 100, anteriores)

    assert variacao.variacao_reach_total is None


def test_calcular_variacao_calcula_percentual_correto():
    anteriores = TotaisAnteriores(reach_total=100, engajamento_total=200)

    variacao = calcular_variacao(150, 300, anteriores)

    assert (variacao.variacao_reach_total, variacao.variacao_engajamento_total) == (50.0, 50.0)
