from dataclasses import dataclass

import pandas as pd

from src.ingestao.leitor_csv import PostValidado


@dataclass(frozen=True)
class PostResumo:
    post_id: str
    post_type: str
    reach: int
    taxa_engajamento: float


@dataclass(frozen=True)
class MetricasSemana:
    reach_total: int
    engajamento_total: int
    taxa_engajamento_semanal: float
    quantidade_posts: int
    melhor_post: PostResumo
    pior_post: PostResumo
    melhor_taxa_engajamento_post: PostResumo


def calcular_taxa_engajamento(engajamento: float, reach: float) -> float:
    if reach == 0:
        return 0.0
    return engajamento / reach * 100


def calcular_metricas_semana(posts: list[PostValidado]) -> MetricasSemana:
    dataframe = pd.DataFrame(
        [
            {
                "post_id": post.post_id,
                "post_type": post.post_type,
                "reach": post.reach,
                "engajamento": post.likes_and_reactions
                + post.comments
                + post.shares
                + post.saves,
            }
            for post in posts
        ]
    )
    dataframe["taxa_engajamento"] = dataframe.apply(
        lambda linha: calcular_taxa_engajamento(linha["engajamento"], linha["reach"]), axis=1
    )

    reach_total = int(dataframe["reach"].sum())
    engajamento_total = int(dataframe["engajamento"].sum())

    return MetricasSemana(
        reach_total=reach_total,
        engajamento_total=engajamento_total,
        taxa_engajamento_semanal=calcular_taxa_engajamento(engajamento_total, reach_total),
        quantidade_posts=len(dataframe),
        melhor_post=_linha_para_resumo(dataframe.loc[dataframe["reach"].idxmax()]),
        pior_post=_linha_para_resumo(dataframe.loc[dataframe["reach"].idxmin()]),
        melhor_taxa_engajamento_post=_linha_para_resumo(
            dataframe.loc[dataframe["taxa_engajamento"].idxmax()]
        ),
    )


def _linha_para_resumo(linha: pd.Series) -> PostResumo:
    return PostResumo(
        post_id=linha["post_id"],
        post_type=linha["post_type"],
        reach=int(linha["reach"]),
        taxa_engajamento=float(linha["taxa_engajamento"]),
    )
