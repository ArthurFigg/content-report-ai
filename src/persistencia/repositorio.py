from sqlalchemy import select
from sqlalchemy.orm import Session

from src.persistencia.modelos import DadosPost, Post, ResumoSemanal


def inserir_posts(sessao: Session, posts: list[DadosPost], semana: str) -> None:
    for dados in posts:
        sessao.add(Post(semana=semana, **dados))
    sessao.commit()


def buscar_resumo_anterior(sessao: Session) -> ResumoSemanal | None:
    instrucao = select(ResumoSemanal).order_by(ResumoSemanal.semana.desc()).limit(1)
    return sessao.execute(instrucao).scalar_one_or_none()


def semana_ja_processada(sessao: Session, semana: str) -> bool:
    instrucao = select(ResumoSemanal).where(ResumoSemanal.semana == semana)
    return sessao.execute(instrucao).scalar_one_or_none() is not None


def salvar_resumo_semanal(
    sessao: Session,
    semana: str,
    reach_total: int,
    engajamento_total: int,
    taxa_engajamento_semanal: float,
    quantidade_posts: int,
    melhor_post_id: str,
    pior_post_id: str,
) -> None:
    sessao.add(
        ResumoSemanal(
            semana=semana,
            reach_total=reach_total,
            engajamento_total=engajamento_total,
            taxa_engajamento_semanal=taxa_engajamento_semanal,
            quantidade_posts=quantidade_posts,
            melhor_post_id=melhor_post_id,
            pior_post_id=pior_post_id,
        )
    )
    sessao.commit()
