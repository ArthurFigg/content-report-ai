from pathlib import Path

from src.ia.cliente_gemini import Destaque, RespostaIA
from src.processamento.calculo_metricas import MetricasSemana, PostResumo
from src.processamento.comparacao import VariacaoSemana
from src.relatorio.gerador_pdf import gerar_pdf, montar_html


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


def test_montar_html_exibe_historico_insuficiente_com_1_semana(monkeypatch):
    monkeypatch.setenv("NOME_NEGOCIO", "Loja Teste")
    variacao = VariacaoSemana(
        tem_historico=False, variacao_reach_total=None, variacao_engajamento_total=None
    )

    html = montar_html(
        "2026-06-08", _metricas_exemplo(), variacao, _resposta_ia_exemplo(), [("2026-06-08", 1000)]
    )

    assert "Histórico insuficiente" in html
    assert "data:image/png;base64" not in html


def test_montar_html_exibe_grafico_com_2_ou_mais_semanas(monkeypatch):
    monkeypatch.setenv("NOME_NEGOCIO", "Loja Teste")
    variacao = VariacaoSemana(
        tem_historico=True, variacao_reach_total=50.0, variacao_engajamento_total=10.0
    )
    historico = [("2026-06-01", 800), ("2026-06-08", 1000)]

    html = montar_html(
        "2026-06-08", _metricas_exemplo(), variacao, _resposta_ia_exemplo(), historico
    )

    assert "data:image/png;base64" in html


def test_montar_html_omite_bloco_possivel_causa_quando_null(monkeypatch):
    monkeypatch.setenv("NOME_NEGOCIO", "Loja Teste")
    variacao = VariacaoSemana(
        tem_historico=False, variacao_reach_total=None, variacao_engajamento_total=None
    )

    html = montar_html(
        "2026-06-08",
        _metricas_exemplo(),
        variacao,
        _resposta_ia_exemplo(possivel_causa=None),
        [("2026-06-08", 1000)],
    )

    assert "Possível explicação" not in html


def test_montar_html_exibe_sem_base_de_comparacao_quando_variacao_null(monkeypatch):
    monkeypatch.setenv("NOME_NEGOCIO", "Loja Teste")
    variacao = VariacaoSemana(
        tem_historico=False, variacao_reach_total=None, variacao_engajamento_total=None
    )

    html = montar_html(
        "2026-06-08", _metricas_exemplo(), variacao, _resposta_ia_exemplo(), [("2026-06-08", 1000)]
    )

    assert "sem base de comparação" in html


def test_montar_html_exibe_indisponibilidade_quando_resposta_ia_none(monkeypatch):
    monkeypatch.setenv("NOME_NEGOCIO", "Loja Teste")
    variacao = VariacaoSemana(
        tem_historico=False, variacao_reach_total=None, variacao_engajamento_total=None
    )

    html = montar_html(
        "2026-06-08", _metricas_exemplo(), variacao, None, [("2026-06-08", 1000)]
    )

    assert "Resumo indisponível nesta semana" in html
    assert "Destaques indisponíveis nesta semana" in html
    assert "Recomendação indisponível nesta semana" in html
    assert "Possível explicação" in html


def test_montar_html_mantem_numeros_chave_normais_quando_resposta_ia_none(monkeypatch):
    monkeypatch.setenv("NOME_NEGOCIO", "Loja Teste")
    variacao = VariacaoSemana(
        tem_historico=False, variacao_reach_total=None, variacao_engajamento_total=None
    )

    html = montar_html(
        "2026-06-08", _metricas_exemplo(), variacao, None, [("2026-06-08", 1000)]
    )

    assert "1.000" in html


def test_gerar_pdf_salva_arquivo_em_relatorios_com_nome_da_semana(monkeypatch, tmp_path):
    monkeypatch.setenv("NOME_NEGOCIO", "Loja Teste")
    monkeypatch.setattr("src.relatorio.gerador_pdf.DIRETORIO_RELATORIOS", tmp_path / "relatorios")
    variacao = VariacaoSemana(
        tem_historico=False, variacao_reach_total=None, variacao_engajamento_total=None
    )

    caminho = gerar_pdf(
        "2026-06-08", _metricas_exemplo(), variacao, _resposta_ia_exemplo(), [("2026-06-08", 1000)]
    )

    conteudo = Path(caminho).read_bytes()
    assert caminho.endswith("relatorio_2026-06-08.pdf")
    assert conteudo.startswith(b"%PDF")
