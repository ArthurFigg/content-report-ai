from unittest.mock import Mock

from src.ia.cliente_gemini import Destaque, RespostaIA, gerar_interpretacao
from src.processamento.calculo_metricas import MetricasSemana, PostResumo
from src.processamento.comparacao import VariacaoSemana


def _metricas_exemplo() -> MetricasSemana:
    post = PostResumo(post_id="p1", post_type="Reel", reach=1000, taxa_engajamento=10.0)
    return MetricasSemana(
        reach_total=1000,
        engajamento_total=100,
        taxa_engajamento_semanal=10.0,
        quantidade_posts=1,
        melhor_post=post,
        pior_post=post,
        melhor_taxa_engajamento_post=post,
    )


def _resposta_ia_exemplo(possivel_causa: str | None = None) -> RespostaIA:
    return RespostaIA(
        resumo_executivo="Semana estável, sem grandes variações.",
        destaques=[Destaque(tipo="melhor_post", descricao="Seu Reel teve ótimo alcance.")],
        possivel_causa=possivel_causa,
        recomendacao="Considere postar mais Reels.",
    )


def _mock_client(monkeypatch, respostas: list):
    client_mock = Mock()
    client_mock.models.generate_content = Mock(side_effect=respostas)
    monkeypatch.setattr("src.ia.cliente_gemini.genai.Client", Mock(return_value=client_mock))
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr("src.retry.time.sleep", Mock())


def test_gerar_interpretacao_retorna_resposta_com_historico(monkeypatch):
    resposta_esperada = _resposta_ia_exemplo(possivel_causa="queda no número de posts")
    _mock_client(monkeypatch, [Mock(parsed=resposta_esperada)])
    variacao = VariacaoSemana(
        tem_historico=True, variacao_reach_total=10.0, variacao_engajamento_total=5.0
    )

    resultado = gerar_interpretacao(_metricas_exemplo(), variacao)

    assert resultado == resposta_esperada


def test_gerar_interpretacao_forca_possivel_causa_none_sem_historico(monkeypatch):
    resposta_da_ia = _resposta_ia_exemplo(possivel_causa="causa inventada pela IA")
    _mock_client(monkeypatch, [Mock(parsed=resposta_da_ia)])
    variacao = VariacaoSemana(
        tem_historico=False, variacao_reach_total=None, variacao_engajamento_total=None
    )

    resultado = gerar_interpretacao(_metricas_exemplo(), variacao)

    assert resultado.possivel_causa is None


def test_gerar_interpretacao_tenta_novamente_apos_falha(monkeypatch):
    resposta_esperada = _resposta_ia_exemplo()
    _mock_client(
        monkeypatch,
        [Exception("erro de rede"), Exception("erro de rede"), Mock(parsed=resposta_esperada)],
    )
    variacao = VariacaoSemana(
        tem_historico=True, variacao_reach_total=1.0, variacao_engajamento_total=1.0
    )

    resultado = gerar_interpretacao(_metricas_exemplo(), variacao)

    assert resultado.resumo_executivo == resposta_esperada.resumo_executivo


def test_gerar_interpretacao_retorna_none_apos_falhas_persistentes(monkeypatch):
    _mock_client(monkeypatch, [Exception("erro"), Exception("erro"), Exception("erro")])
    variacao = VariacaoSemana(
        tem_historico=False, variacao_reach_total=None, variacao_engajamento_total=None
    )

    resultado = gerar_interpretacao(_metricas_exemplo(), variacao)

    assert resultado is None


def test_gerar_interpretacao_trata_resposta_invalida_como_falha_de_tentativa(monkeypatch):
    resposta_esperada = _resposta_ia_exemplo()
    _mock_client(monkeypatch, [Mock(parsed=None), Mock(parsed=resposta_esperada)])
    variacao = VariacaoSemana(
        tem_historico=True, variacao_reach_total=1.0, variacao_engajamento_total=1.0
    )

    resultado = gerar_interpretacao(_metricas_exemplo(), variacao)

    assert resultado.resumo_executivo == resposta_esperada.resumo_executivo
