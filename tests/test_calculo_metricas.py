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


# --- desempenho por tipo (spec 09) ---
# O import fica dentro da função para não derrubar a coleta dos testes antigos
# enquanto a função nova ainda não existe.


def _calcular_por_tipo(posts):
    from src.processamento.calculo_metricas import calcular_metricas_por_tipo

    return calcular_metricas_por_tipo(posts)


def _item_do_tipo(lista, post_type):
    return next(item for item in lista if item.post_type == post_type)


def test_calcular_metricas_por_tipo_retorna_lista_vazia_para_lista_vazia():
    assert _calcular_por_tipo([]) == []


def test_calcular_metricas_por_tipo_inclui_so_tipos_presentes_na_semana():
    posts = [
        _post("p1", "Reel", reach=100),
        _post("p2", "Photo", reach=200),
    ]

    resultado = _calcular_por_tipo(posts)

    assert {item.post_type for item in resultado} == {"Reel", "Photo"}


def test_calcular_metricas_por_tipo_retorna_dois_itens_para_semana_com_dois_tipos():
    posts = [
        _post("p1", "Reel", reach=100),
        _post("p2", "Photo", reach=200),
        _post("p3", "Reel", reach=300),
    ]

    resultado = _calcular_por_tipo(posts)

    assert len(resultado) == 2


def test_calcular_metricas_por_tipo_calcula_reach_medio_do_tipo():
    posts = [
        _post("p1", "Reel", reach=100),
        _post("p2", "Reel", reach=300),
    ]

    item = _item_do_tipo(_calcular_por_tipo(posts), "Reel")

    assert item.reach_medio == 200.0


def test_calcular_metricas_por_tipo_conta_quantidade_de_posts_do_tipo():
    posts = [
        _post("p1", "Reel", reach=100),
        _post("p2", "Reel", reach=300),
    ]

    item = _item_do_tipo(_calcular_por_tipo(posts), "Reel")

    assert item.quantidade_posts == 2


def test_calcular_metricas_por_tipo_calcula_taxa_engajamento_agregada_do_tipo():
    posts = [
        _post("p1", "Photo", reach=100, likes=5, comments=3, shares=1, saves=1),
        _post("p2", "Photo", reach=300, likes=20, comments=5, shares=3, saves=2),
    ]

    item = _item_do_tipo(_calcular_por_tipo(posts), "Photo")

    assert item.taxa_engajamento == 10.0


def test_calcular_metricas_por_tipo_retorna_taxa_zero_quando_todos_os_posts_tem_reach_zero():
    posts = [
        _post("p1", "Video", reach=0, likes=10),
        _post("p2", "Video", reach=0, comments=5),
    ]

    item = _item_do_tipo(_calcular_por_tipo(posts), "Video")

    assert item.taxa_engajamento == 0.0


def test_calcular_metricas_por_tipo_coloca_tipo_de_maior_reach_medio_primeiro():
    posts = [
        _post("p1", "Photo", reach=100),
        _post("p2", "Reel", reach=500),
    ]

    resultado = _calcular_por_tipo(posts)

    assert [item.post_type for item in resultado] == ["Reel", "Photo"]


def test_calcular_metricas_por_tipo_desempata_reach_medio_por_ordem_alfabetica():
    posts = [
        _post("p1", "Photo", reach=200),
        _post("p2", "Carousel", reach=200),
    ]

    resultado = _calcular_por_tipo(posts)

    assert [item.post_type for item in resultado] == ["Carousel", "Photo"]
