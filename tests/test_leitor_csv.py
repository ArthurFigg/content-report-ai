from datetime import date
from pathlib import Path

import pytest

from src.ingestao.excecoes import CSVInvalidoError
from src.ingestao.leitor_csv import PostValidado, ler_csv

CABECALHO = (
    "Post ID,Post Date,Post Type,Post Text,Reach,Impressions,"
    "Likes and Reactions,Comments,Shares,Saves,Link Clicks,Plays,"
    "Watch Time,Retention"
)


def _escrever_csv(tmp_path: Path, linhas: list[str]) -> Path:
    caminho = tmp_path / "semana_2026-06-01.csv"
    caminho.write_text("\n".join([CABECALHO, *linhas]) + "\n", encoding="utf-8")
    return caminho


def test_ler_csv_retorna_posts_validados_para_csv_valido(tmp_path):
    linha = "p1,2026-06-01,Photo,legenda,1000,1200,100,10,5,20,,,,"
    caminho = _escrever_csv(tmp_path, [linha])

    posts = ler_csv(caminho)

    assert posts == [
        PostValidado(
            post_id="p1",
            post_date=date(2026, 6, 1),
            post_type="Photo",
            post_text="legenda",
            reach=1000,
            impressions=1200,
            likes_and_reactions=100,
            comments=10,
            shares=5,
            saves=20,
            link_clicks=None,
            plays=None,
            watch_time=None,
            retention=None,
        )
    ]


def test_ler_csv_rejeita_coluna_obrigatoria_faltando(tmp_path):
    caminho = tmp_path / "semana_2026-06-01.csv"
    caminho.write_text("Post ID,Post Date,Post Type\np1,2026-06-01,Photo\n", encoding="utf-8")

    with pytest.raises(CSVInvalidoError, match="Reach"):
        ler_csv(caminho)


def test_ler_csv_rejeita_post_type_fora_do_enum(tmp_path):
    linha = "p1,2026-06-01,Story,legenda,1000,1200,100,10,5,20,,,,"
    caminho = _escrever_csv(tmp_path, [linha])

    with pytest.raises(CSVInvalidoError, match="Post Type"):
        ler_csv(caminho)


def test_ler_csv_rejeita_valor_numerico_negativo(tmp_path):
    linha = "p1,2026-06-01,Photo,legenda,-10,1200,100,10,5,20,,,,"
    caminho = _escrever_csv(tmp_path, [linha])

    with pytest.raises(CSVInvalidoError, match="Reach"):
        ler_csv(caminho)


def test_ler_csv_rejeita_post_id_duplicado(tmp_path):
    linha1 = "p1,2026-06-01,Photo,legenda,1000,1200,100,10,5,20,,,,"
    linha2 = "p1,2026-06-02,Reel,legenda,2000,2200,150,15,8,30,,3000,500.0,40.0"
    caminho = _escrever_csv(tmp_path, [linha1, linha2])

    with pytest.raises(CSVInvalidoError, match="p1"):
        ler_csv(caminho)


def test_ler_csv_rejeita_zero_linhas_de_dados(tmp_path):
    caminho = tmp_path / "semana_2026-06-01.csv"
    caminho.write_text(CABECALHO + "\n", encoding="utf-8")

    with pytest.raises(CSVInvalidoError):
        ler_csv(caminho)
