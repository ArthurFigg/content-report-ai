from datetime import date

from src.ingestao.leitor_csv import PostValidado
from src.processamento.calculo_metricas import calcular_metricas_semana


def _post(
    post_id: str,
    post_type: str,
    reach: int,
    likes: int = 0,
    comments: int = 0,
    shares: int = 0,
    saves: int = 0,
) -> PostValidado:
    return PostValidado(
        post_id=post_id,
        post_date=date(2026, 6, 1),
        post_type=post_type,
        post_text=None,
        reach=reach,
        impressions=reach,
        likes_and_reactions=likes,
        comments=comments,
        shares=shares,
        saves=saves,
        link_clicks=None,
        plays=None,
        watch_time=None,
        retention=None,
    )


def test_calcular_metricas_semana_identifica_melhor_e_pior_post_por_reach():
    posts = [
        _post("p1", "Photo", reach=1000),
        _post("p2", "Reel", reach=3000),
        _post("p3", "Carousel", reach=500),
    ]

    metricas = calcular_metricas_semana(posts)

    assert (metricas.melhor_post.post_id, metricas.pior_post.post_id) == ("p2", "p3")


def test_calcular_metricas_semana_retorna_taxa_engajamento_zero_para_reach_zero():
    posts = [_post("p1", "Photo", reach=0, likes=10)]

    metricas = calcular_metricas_semana(posts)

    assert metricas.melhor_post.taxa_engajamento == 0


def test_calcular_metricas_semana_identifica_post_com_maior_taxa_engajamento_distinto_do_melhor_post():
    posts = [
        _post("p1", "Photo", reach=5000, likes=50),
        _post("p2", "Reel", reach=1000, likes=400, comments=100, shares=50, saves=50),
    ]

    metricas = calcular_metricas_semana(posts)

    assert (
        metricas.melhor_post.post_id,
        metricas.melhor_taxa_engajamento_post.post_id,
    ) == ("p1", "p2")
