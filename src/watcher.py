import logging
import os
import re
import time
from datetime import date, timedelta

from dotenv import load_dotenv

load_dotenv()
from pathlib import Path

from sqlalchemy import Engine
from sqlalchemy.orm import Session
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.entrega.email_sender import enviar_relatorio
from src.ia.cliente_gemini import gerar_interpretacao
from src.ingestao.excecoes import CSVInvalidoError
from src.ingestao.leitor_csv import PostValidado, ler_csv
from src.persistencia.modelos import DadosPost, ResumoSemanal, criar_engine, criar_tabelas
from src.persistencia.repositorio import (
    buscar_resumo_anterior,
    inserir_posts,
    listar_resumos_semanais,
    salvar_resumo_semanal,
    semana_ja_processada,
)
from src.processamento.calculo_metricas import calcular_metricas_semana, calcular_taxa_engajamento
from src.processamento.comparacao import TotaisAnteriores, calcular_variacao
from src.relatorio.gerador_pdf import gerar_pdf

logger = logging.getLogger(__name__)

DIRETORIO_ENTRADA = Path("dados/entrada")
DIRETORIO_PROCESSADOS = Path("dados/processados")
PADRAO_NOME_ARQUIVO = re.compile(r"^semana_(\d{4}-\d{2}-\d{2})\.csv$")
VARIAVEIS_OBRIGATORIAS = (
    "GROQ_API_KEY",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "EMAIL_DESTINATARIO",
    "NOME_NEGOCIO",
)


class VariavelAmbienteFaltandoError(Exception):
    pass


class SemanaJaProcessadaError(Exception):
    pass


def validar_variaveis_ambiente() -> None:
    faltantes = [nome for nome in VARIAVEIS_OBRIGATORIAS if not os.environ.get(nome)]
    if faltantes:
        raise VariavelAmbienteFaltandoError(
            f"Variáveis de ambiente obrigatórias ausentes: {', '.join(faltantes)}"
        )


def configurar_logging() -> None:
    Path("logs").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def processar_arquivo(caminho: Path, engine: Engine) -> None:
    try:
        semana = _extrair_semana_do_nome(caminho.name)
        _executar_pipeline(caminho, semana, engine)
    except CSVInvalidoError as erro:
        logger.error("CSV inválido (%s): %s", caminho.name, erro)
        return
    except SemanaJaProcessadaError:
        logger.warning("Semana já processada — arquivo %s ignorado", caminho.name)
        return
    except Exception:
        logger.error("Falha não prevista ao processar %s", caminho.name, exc_info=True)
        return

    _mover_para_processados(caminho)


def _executar_pipeline(caminho: Path, semana: str, engine: Engine) -> None:
    posts_validados = ler_csv(caminho)

    with Session(engine) as sessao_leitura:
        if semana_ja_processada(sessao_leitura, semana):
            raise SemanaJaProcessadaError(semana)
        resumo_anterior = buscar_resumo_anterior(sessao_leitura)

    metricas = calcular_metricas_semana(posts_validados)
    totais_anteriores = _resumo_para_totais_anteriores(resumo_anterior)
    variacao = calcular_variacao(
        metricas.reach_total, metricas.engajamento_total, totais_anteriores
    )

    resposta_ia = gerar_interpretacao(metricas, variacao)

    dados_posts = [_post_validado_para_dados_post(post) for post in posts_validados]

    with Session(engine) as sessao_escrita:
        with sessao_escrita.begin():
            inserir_posts(sessao_escrita, dados_posts, semana)
            salvar_resumo_semanal(
                sessao_escrita,
                semana=semana,
                reach_total=metricas.reach_total,
                engajamento_total=metricas.engajamento_total,
                taxa_engajamento_semanal=metricas.taxa_engajamento_semanal,
                quantidade_posts=metricas.quantidade_posts,
                melhor_post_id=metricas.melhor_post.post_id,
                pior_post_id=metricas.pior_post.post_id,
            )
        historico = listar_resumos_semanais(sessao_escrita)

    caminho_pdf = gerar_pdf(semana, metricas, variacao, resposta_ia, historico)

    if not enviar_relatorio(caminho_pdf, _formatar_periodo(semana)):
        logger.warning(
            "Falha ao enviar email do relatório da semana %s; PDF salvo em %s",
            semana,
            caminho_pdf,
        )


def _resumo_para_totais_anteriores(
    resumo: ResumoSemanal | None,
) -> TotaisAnteriores | None:
    if resumo is None:
        return None
    return TotaisAnteriores(
        reach_total=resumo.reach_total, engajamento_total=resumo.engajamento_total
    )


def _post_validado_para_dados_post(post: PostValidado) -> DadosPost:
    engajamento = post.likes_and_reactions + post.comments + post.shares + post.saves
    return {
        "post_id": post.post_id,
        "post_date": post.post_date,
        "post_type": post.post_type,
        "post_text": post.post_text,
        "reach": post.reach,
        "impressions": post.impressions,
        "likes_and_reactions": post.likes_and_reactions,
        "comments": post.comments,
        "shares": post.shares,
        "saves": post.saves,
        "link_clicks": post.link_clicks,
        "plays": post.plays,
        "watch_time": post.watch_time,
        "retention": post.retention,
        "taxa_engajamento": calcular_taxa_engajamento(engajamento, post.reach),
    }


def _extrair_semana_do_nome(nome_arquivo: str) -> str:
    correspondencia = PADRAO_NOME_ARQUIVO.match(nome_arquivo)
    if not correspondencia:
        raise CSVInvalidoError(
            f"Nome de arquivo fora da convenção semana_AAAA-MM-DD.csv: {nome_arquivo!r}"
        )
    return correspondencia.group(1)


def _formatar_periodo(semana: str) -> str:
    segunda = date.fromisoformat(semana)
    domingo = segunda + timedelta(days=6)
    return f"{segunda.strftime('%d/%m')} a {domingo.strftime('%d/%m/%Y')}"


def _mover_para_processados(caminho: Path) -> None:
    DIRETORIO_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    caminho.rename(DIRETORIO_PROCESSADOS / caminho.name)


def listar_csvs_pendentes(diretorio: Path) -> list[Path]:
    arquivos = [caminho for caminho in diretorio.glob("semana_*.csv") if caminho.is_file()]
    return sorted(arquivos, key=lambda caminho: _extrair_semana_do_nome(caminho.name))


def processar_pendentes(diretorio: Path, engine: Engine) -> None:
    for caminho in listar_csvs_pendentes(diretorio):
        processar_arquivo(caminho, engine)


def esperar_arquivo_estavel(caminho: Path, intervalo: float = 1.0) -> None:
    tamanho_anterior = -1
    while True:
        tamanho_atual = caminho.stat().st_size
        if tamanho_atual == tamanho_anterior:
            return
        tamanho_anterior = tamanho_atual
        time.sleep(intervalo)


class ManipuladorCSV(FileSystemEventHandler):
    def __init__(self, engine: Engine):
        self._engine = engine

    def on_created(self, event):
        if event.is_directory:
            return
        caminho = Path(event.src_path)
        if caminho.suffix != ".csv":
            return
        esperar_arquivo_estavel(caminho)
        processar_arquivo(caminho, self._engine)


def iniciar() -> None:
    validar_variaveis_ambiente()
    configurar_logging()

    engine = criar_engine()
    criar_tabelas(engine)

    DIRETORIO_ENTRADA.mkdir(parents=True, exist_ok=True)
    processar_pendentes(DIRETORIO_ENTRADA, engine)

    observador = Observer()
    observador.schedule(ManipuladorCSV(engine), str(DIRETORIO_ENTRADA))
    observador.start()
    logger.info("Watcher iniciado, vigiando %s", DIRETORIO_ENTRADA)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observador.stop()
    observador.join()


if __name__ == "__main__":
    iniciar()
