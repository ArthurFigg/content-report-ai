from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.persistencia.modelos import DadosPost, Post, ResumoSemanal, criar_engine, criar_tabelas
from src.persistencia.repositorio import (
    buscar_resumo_anterior,
    inserir_posts,
    salvar_resumo_semanal,
    semana_ja_processada,
)


@pytest.fixture
def sessao():
    engine = criar_engine(":memory:")
    criar_tabelas(engine)
    with Session(engine) as sessao:
        yield sessao


def _inserir_post_simples(sessao: Session, post_id: str, semana: str) -> None:
    dados: DadosPost = {
        "post_id": post_id,
        "post_date": date.fromisoformat(semana),
        "post_type": "Photo",
        "post_text": "legenda",
        "reach": 1000,
        "impressions": 1200,
        "likes_and_reactions": 100,
        "comments": 10,
        "shares": 5,
        "saves": 20,
        "link_clicks": None,
        "plays": None,
        "watch_time": None,
        "retention": None,
        "taxa_engajamento": 13.5,
    }
    inserir_posts(sessao, [dados], semana=semana)


def test_inserir_posts_persiste_dados_incluindo_taxa_engajamento(sessao):
    dados: DadosPost = {
        "post_id": "p1",
        "post_date": date(2026, 6, 15),
        "post_type": "Reel",
        "post_text": "legenda do reel",
        "reach": 5000,
        "impressions": 6000,
        "likes_and_reactions": 400,
        "comments": 30,
        "shares": 20,
        "saves": 50,
        "link_clicks": 10,
        "plays": 8000,
        "watch_time": 1200.5,
        "retention": 45.2,
        "taxa_engajamento": 10.0,
    }

    inserir_posts(sessao, [dados], semana="2026-06-15")

    post_salvo = sessao.get(Post, "p1")
    valores_salvos = {chave: getattr(post_salvo, chave) for chave in dados}
    assert valores_salvos == dados


def test_buscar_resumo_anterior_retorna_none_quando_vazio(sessao):
    assert buscar_resumo_anterior(sessao) is None


def test_buscar_resumo_anterior_retorna_semana_mais_recente(sessao):
    _inserir_post_simples(sessao, "p1", "2026-06-01")
    _inserir_post_simples(sessao, "p2", "2026-06-08")
    salvar_resumo_semanal(
        sessao,
        semana="2026-06-01",
        reach_total=1000,
        engajamento_total=100,
        taxa_engajamento_semanal=10.0,
        quantidade_posts=1,
        melhor_post_id="p1",
        pior_post_id="p1",
    )
    salvar_resumo_semanal(
        sessao,
        semana="2026-06-08",
        reach_total=2000,
        engajamento_total=200,
        taxa_engajamento_semanal=10.0,
        quantidade_posts=1,
        melhor_post_id="p2",
        pior_post_id="p2",
    )

    resumo = buscar_resumo_anterior(sessao)

    assert resumo.semana == "2026-06-08"


def test_semana_ja_processada_retorna_true_para_semana_salva(sessao):
    _inserir_post_simples(sessao, "p1", "2026-06-01")
    salvar_resumo_semanal(
        sessao,
        semana="2026-06-01",
        reach_total=1000,
        engajamento_total=100,
        taxa_engajamento_semanal=10.0,
        quantidade_posts=1,
        melhor_post_id="p1",
        pior_post_id="p1",
    )

    assert semana_ja_processada(sessao, "2026-06-01") is True


def test_semana_ja_processada_retorna_false_para_semana_nova(sessao):
    assert semana_ja_processada(sessao, "2026-06-01") is False


def test_salvar_resumo_semanal_persiste_melhor_e_pior_post_recuperaveis_via_join(sessao):
    _inserir_post_simples(sessao, "p1", "2026-06-01")
    _inserir_post_simples(sessao, "p2", "2026-06-01")
    salvar_resumo_semanal(
        sessao,
        semana="2026-06-01",
        reach_total=2000,
        engajamento_total=200,
        taxa_engajamento_semanal=10.0,
        quantidade_posts=2,
        melhor_post_id="p1",
        pior_post_id="p2",
    )

    melhor_post_id, pior_post_id = sessao.execute(
        select(ResumoSemanal.melhor_post_id, ResumoSemanal.pior_post_id)
        .join(Post, Post.post_id == ResumoSemanal.melhor_post_id)
        .where(ResumoSemanal.semana == "2026-06-01")
    ).one()

    assert (melhor_post_id, pior_post_id) == ("p1", "p2")


def test_salvar_resumo_semanal_duplicado_levanta_erro_de_integridade(sessao):
    _inserir_post_simples(sessao, "p1", "2026-06-01")
    salvar_resumo_semanal(
        sessao,
        semana="2026-06-01",
        reach_total=1000,
        engajamento_total=100,
        taxa_engajamento_semanal=10.0,
        quantidade_posts=1,
        melhor_post_id="p1",
        pior_post_id="p1",
    )

    with pytest.raises(IntegrityError):
        salvar_resumo_semanal(
            sessao,
            semana="2026-06-01",
            reach_total=1000,
            engajamento_total=100,
            taxa_engajamento_semanal=10.0,
            quantidade_posts=1,
            melhor_post_id="p1",
            pior_post_id="p1",
        )
