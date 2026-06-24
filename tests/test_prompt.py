import json

from src.ia.prompt import montar_prompt
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


def _extrair_payload(prompt: str) -> dict:
    linha_payload = next(linha for linha in prompt.split("\n") if linha.startswith("{"))
    return json.loads(linha_payload)


def test_montar_prompt_omite_semana_anterior_sem_historico():
    variacao = VariacaoSemana(
        tem_historico=False, variacao_reach_total=None, variacao_engajamento_total=None
    )

    payload = _extrair_payload(montar_prompt(_metricas_exemplo(), variacao))

    assert "semana_anterior" not in payload


def test_montar_prompt_inclui_semana_anterior_com_historico():
    variacao = VariacaoSemana(
        tem_historico=True, variacao_reach_total=50.0, variacao_engajamento_total=20.0
    )

    payload = _extrair_payload(montar_prompt(_metricas_exemplo(), variacao))

    assert payload["semana_anterior"] == {
        "variacao_reach_total": 50.0,
        "variacao_engajamento_total": 20.0,
    }


def test_montar_prompt_envia_melhor_post_sem_taxa_engajamento():
    variacao = VariacaoSemana(
        tem_historico=False, variacao_reach_total=None, variacao_engajamento_total=None
    )

    payload = _extrair_payload(montar_prompt(_metricas_exemplo(), variacao))

    assert payload["melhor_post"] == {"post_id": "p1", "post_type": "Reel", "reach": 1000}
