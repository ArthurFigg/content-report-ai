import csv
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from src.ingestao.excecoes import CSVInvalidoError

COLUNAS_OBRIGATORIAS = [
    "Post ID",
    "Post Date",
    "Post Type",
    "Reach",
    "Impressions",
    "Likes and Reactions",
    "Comments",
    "Shares",
    "Saves",
]

TIPOS_POST_VALIDOS = {"Photo", "Video", "Reel", "Carousel"}


@dataclass(frozen=True)
class PostValidado:
    post_id: str
    post_date: date
    post_type: str
    post_text: str | None
    reach: int
    impressions: int
    likes_and_reactions: int
    comments: int
    shares: int
    saves: int
    link_clicks: int | None
    plays: int | None
    watch_time: float | None
    retention: float | None


def ler_csv(caminho: Path) -> list[PostValidado]:
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        _validar_colunas_obrigatorias(leitor.fieldnames)
        linhas = list(leitor)

    if not linhas:
        raise CSVInvalidoError("CSV não contém nenhuma linha de dados")

    posts = [_validar_linha(linha, numero) for numero, linha in enumerate(linhas, start=2)]
    _validar_post_id_unico(posts)
    return posts


def _validar_colunas_obrigatorias(colunas: list[str] | None) -> None:
    colunas = colunas or []
    faltantes = [coluna for coluna in COLUNAS_OBRIGATORIAS if coluna not in colunas]
    if faltantes:
        raise CSVInvalidoError(f"Colunas obrigatórias ausentes: {', '.join(faltantes)}")


def _validar_linha(linha: dict[str, str], numero_linha: int) -> PostValidado:
    post_type = linha["Post Type"]
    if post_type not in TIPOS_POST_VALIDOS:
        raise CSVInvalidoError(f"Post Type inválido na linha {numero_linha}: {post_type!r}")

    return PostValidado(
        post_id=linha["Post ID"],
        post_date=_parse_data(linha["Post Date"], numero_linha),
        post_type=post_type,
        post_text=linha.get("Post Text") or None,
        reach=_parse_inteiro_nao_negativo(linha["Reach"], "Reach", numero_linha),
        impressions=_parse_inteiro_nao_negativo(
            linha["Impressions"], "Impressions", numero_linha
        ),
        likes_and_reactions=_parse_inteiro_nao_negativo(
            linha["Likes and Reactions"], "Likes and Reactions", numero_linha
        ),
        comments=_parse_inteiro_nao_negativo(linha["Comments"], "Comments", numero_linha),
        shares=_parse_inteiro_nao_negativo(linha["Shares"], "Shares", numero_linha),
        saves=_parse_inteiro_nao_negativo(linha["Saves"], "Saves", numero_linha),
        link_clicks=_parse_inteiro_opcional(
            linha.get("Link Clicks", ""), "Link Clicks", numero_linha
        ),
        plays=_parse_inteiro_opcional(linha.get("Plays", ""), "Plays", numero_linha),
        watch_time=_parse_float_opcional(linha.get("Watch Time", ""), "Watch Time", numero_linha),
        retention=_parse_float_opcional(linha.get("Retention", ""), "Retention", numero_linha),
    )


def _validar_post_id_unico(posts: list[PostValidado]) -> None:
    contagem = Counter(post.post_id for post in posts)
    duplicados = sorted(post_id for post_id, total in contagem.items() if total > 1)
    if duplicados:
        raise CSVInvalidoError(f"Post ID duplicado no arquivo: {', '.join(duplicados)}")


def _parse_data(valor: str, numero_linha: int) -> date:
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError as erro:
        raise CSVInvalidoError(f"Post Date inválida na linha {numero_linha}: {valor!r}") from erro


def _parse_inteiro_nao_negativo(valor: str, nome_campo: str, numero_linha: int) -> int:
    try:
        numero = int(valor)
    except ValueError as erro:
        raise CSVInvalidoError(
            f"{nome_campo} inválido na linha {numero_linha}: {valor!r}"
        ) from erro
    if numero < 0:
        raise CSVInvalidoError(f"{nome_campo} negativo na linha {numero_linha}: {numero}")
    return numero


def _parse_inteiro_opcional(valor: str, nome_campo: str, numero_linha: int) -> int | None:
    if not valor:
        return None
    return _parse_inteiro_nao_negativo(valor, nome_campo, numero_linha)


def _parse_float_opcional(valor: str, nome_campo: str, numero_linha: int) -> float | None:
    if not valor:
        return None
    try:
        numero = float(valor)
    except ValueError as erro:
        raise CSVInvalidoError(
            f"{nome_campo} inválido na linha {numero_linha}: {valor!r}"
        ) from erro
    if numero < 0:
        raise CSVInvalidoError(f"{nome_campo} negativo na linha {numero_linha}: {numero}")
    return numero
