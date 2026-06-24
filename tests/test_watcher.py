from datetime import date
from unittest.mock import Mock

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src import watcher
from src.ingestao.excecoes import CSVInvalidoError
from src.ingestao.leitor_csv import PostValidado
from src.persistencia.modelos import Post, ResumoSemanal, criar_engine, criar_tabelas
from src.processamento.calculo_metricas import MetricasSemana, PostResumo
from src.processamento.comparacao import VariacaoSemana


@pytest.fixture
def engine():
    motor = criar_engine(":memory:")
    criar_tabelas(motor)
    return motor


def _post_validado(post_id: str = "p1", reach: int = 1000) -> PostValidado:
    return PostValidado(
        post_id=post_id,
        post_date=date(2026, 6, 8),
        post_type="Reel",
        post_text="legenda",
        reach=reach,
        impressions=1200,
        likes_and_reactions=100,
        comments=10,
        shares=5,
        saves=20,
        link_clicks=None,
        plays=2000,
        watch_time=300.0,
        retention=50.0,
    )


def _metricas_para(post_id: str) -> MetricasSemana:
    resumo = PostResumo(post_id=post_id, post_type="Reel", reach=1000, taxa_engajamento=13.5)
    return MetricasSemana(
        reach_total=1000,
        engajamento_total=135,
        taxa_engajamento_semanal=13.5,
        quantidade_posts=1,
        melhor_post=resumo,
        pior_post=resumo,
        melhor_taxa_engajamento_post=resumo,
    )


def _registrar(nome: str, ordem: list[str], retorno=None):
    def _fn(*args, **kwargs):
        ordem.append(nome)
        return retorno

    return _fn


def _mockar_pipeline_de_sucesso(monkeypatch, ordem: list[str], post_id: str = "p1") -> None:
    monkeypatch.setattr(
        watcher, "ler_csv", Mock(side_effect=_registrar("ler_csv", ordem, [_post_validado(post_id)]))
    )
    monkeypatch.setattr(
        watcher,
        "semana_ja_processada",
        Mock(side_effect=_registrar("semana_ja_processada", ordem, False)),
    )
    monkeypatch.setattr(
        watcher,
        "buscar_resumo_anterior",
        Mock(side_effect=_registrar("buscar_resumo_anterior", ordem, None)),
    )
    monkeypatch.setattr(
        watcher,
        "calcular_metricas_semana",
        Mock(side_effect=_registrar("calcular_metricas_semana", ordem, _metricas_para(post_id))),
    )
    monkeypatch.setattr(
        watcher,
        "calcular_variacao",
        Mock(
            side_effect=_registrar(
                "calcular_variacao", ordem, VariacaoSemana(False, None, None)
            )
        ),
    )
    monkeypatch.setattr(
        watcher, "gerar_interpretacao", Mock(side_effect=_registrar("gerar_interpretacao", ordem, None))
    )
    monkeypatch.setattr(
        watcher, "inserir_posts", Mock(side_effect=_registrar("inserir_posts", ordem))
    )
    monkeypatch.setattr(
        watcher,
        "salvar_resumo_semanal",
        Mock(side_effect=_registrar("salvar_resumo_semanal", ordem)),
    )
    monkeypatch.setattr(
        watcher,
        "listar_resumos_semanais",
        Mock(side_effect=_registrar("listar_resumos_semanais", ordem, [])),
    )
    monkeypatch.setattr(
        watcher,
        "gerar_pdf",
        Mock(side_effect=_registrar("gerar_pdf", ordem, "relatorios/relatorio_x.pdf")),
    )
    monkeypatch.setattr(
        watcher, "enviar_relatorio", Mock(side_effect=_registrar("enviar_relatorio", ordem, True))
    )


def test_extrair_semana_do_nome_aceita_convencao_valida():
    assert watcher._extrair_semana_do_nome("semana_2026-06-08.csv") == "2026-06-08"


def test_extrair_semana_do_nome_rejeita_nome_fora_da_convencao():
    with pytest.raises(CSVInvalidoError):
        watcher._extrair_semana_do_nome("relatorio.csv")


def test_listar_csvs_pendentes_ordena_por_semana_ascendente(tmp_path):
    (tmp_path / "semana_2026-06-08.csv").write_text("x")
    (tmp_path / "semana_2026-06-01.csv").write_text("x")

    pendentes = watcher.listar_csvs_pendentes(tmp_path)

    assert [caminho.name for caminho in pendentes] == [
        "semana_2026-06-01.csv",
        "semana_2026-06-08.csv",
    ]


def test_processar_pendentes_processa_arquivos_em_ordem_cronologica(monkeypatch, tmp_path, engine):
    diretorio = tmp_path / "entrada"
    diretorio.mkdir()
    (diretorio / "semana_2026-06-08.csv").write_text("x")
    (diretorio / "semana_2026-06-01.csv").write_text("x")
    chamadas = []
    monkeypatch.setattr(
        watcher, "processar_arquivo", lambda caminho, eng: chamadas.append(caminho.name)
    )

    watcher.processar_pendentes(diretorio, engine)

    assert chamadas == ["semana_2026-06-01.csv", "semana_2026-06-08.csv"]


def test_validar_variaveis_ambiente_levanta_erro_com_variavel_ausente(monkeypatch):
    for nome in watcher.VARIAVEIS_OBRIGATORIAS:
        monkeypatch.setenv(nome, "valor")
    monkeypatch.delenv("EMAIL_DESTINATARIO", raising=False)

    with pytest.raises(watcher.VariavelAmbienteFaltandoError, match="EMAIL_DESTINATARIO"):
        watcher.validar_variaveis_ambiente()


def test_validar_variaveis_ambiente_aceita_quando_tudo_configurado(monkeypatch):
    for nome in watcher.VARIAVEIS_OBRIGATORIAS:
        monkeypatch.setenv(nome, "valor")

    watcher.validar_variaveis_ambiente()


def test_processar_arquivo_move_para_processados_em_caso_de_sucesso(monkeypatch, tmp_path, engine):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dados" / "entrada").mkdir(parents=True)
    caminho_csv = tmp_path / "dados" / "entrada" / "semana_2026-06-08.csv"
    caminho_csv.write_text("conteudo")
    ordem = []
    _mockar_pipeline_de_sucesso(monkeypatch, ordem)

    watcher.processar_arquivo(caminho_csv, engine)

    assert not caminho_csv.exists()
    assert (tmp_path / "dados" / "processados" / "semana_2026-06-08.csv").exists()


def test_processar_arquivo_chama_ia_antes_de_persistir(monkeypatch, tmp_path, engine):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dados" / "entrada").mkdir(parents=True)
    caminho_csv = tmp_path / "dados" / "entrada" / "semana_2026-06-08.csv"
    caminho_csv.write_text("conteudo")
    ordem = []
    _mockar_pipeline_de_sucesso(monkeypatch, ordem)

    watcher.processar_arquivo(caminho_csv, engine)

    assert ordem.index("gerar_interpretacao") < ordem.index("inserir_posts")
    assert ordem.index("gerar_interpretacao") < ordem.index("salvar_resumo_semanal")


def test_processar_arquivo_csv_invalido_nao_move_arquivo(monkeypatch, tmp_path, engine):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dados" / "entrada").mkdir(parents=True)
    caminho_csv = tmp_path / "dados" / "entrada" / "semana_2026-06-08.csv"
    caminho_csv.write_text("conteudo")
    monkeypatch.setattr(watcher, "ler_csv", Mock(side_effect=CSVInvalidoError("coluna faltando")))

    watcher.processar_arquivo(caminho_csv, engine)

    assert caminho_csv.exists()


def test_processar_arquivo_semana_ja_processada_nao_move_arquivo(monkeypatch, tmp_path, engine):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dados" / "entrada").mkdir(parents=True)
    caminho_csv = tmp_path / "dados" / "entrada" / "semana_2026-06-08.csv"
    caminho_csv.write_text("conteudo")
    monkeypatch.setattr(watcher, "ler_csv", Mock(return_value=[_post_validado()]))
    monkeypatch.setattr(watcher, "semana_ja_processada", Mock(return_value=True))

    watcher.processar_arquivo(caminho_csv, engine)

    assert caminho_csv.exists()


def test_processar_arquivo_falha_nao_prevista_reverte_transacao_sem_dados_orfaos(
    monkeypatch, tmp_path, engine
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dados" / "entrada").mkdir(parents=True)
    caminho_csv = tmp_path / "dados" / "entrada" / "semana_2026-06-08.csv"
    caminho_csv.write_text("conteudo")

    monkeypatch.setattr(watcher, "ler_csv", Mock(return_value=[_post_validado("p1")]))
    monkeypatch.setattr(watcher, "semana_ja_processada", Mock(return_value=False))
    monkeypatch.setattr(watcher, "buscar_resumo_anterior", Mock(return_value=None))
    monkeypatch.setattr(watcher, "calcular_metricas_semana", Mock(return_value=_metricas_para("p1")))
    monkeypatch.setattr(
        watcher, "calcular_variacao", Mock(return_value=VariacaoSemana(False, None, None))
    )
    monkeypatch.setattr(watcher, "gerar_interpretacao", Mock(return_value=None))
    monkeypatch.setattr(
        watcher, "salvar_resumo_semanal", Mock(side_effect=Exception("falha simulada"))
    )

    watcher.processar_arquivo(caminho_csv, engine)

    with Session(engine) as sessao:
        assert sessao.execute(select(Post)).first() is None
        assert sessao.execute(select(ResumoSemanal)).first() is None
    assert caminho_csv.exists()


def test_esperar_arquivo_estavel_retorna_quando_tamanho_nao_muda(monkeypatch, tmp_path):
    caminho = tmp_path / "arquivo.csv"
    caminho.write_text("conteudo fixo")
    monkeypatch.setattr(watcher.time, "sleep", Mock())

    watcher.esperar_arquivo_estavel(caminho)


def test_manipulador_csv_ignora_diretorios(monkeypatch, engine):
    monkeypatch.setattr(watcher, "esperar_arquivo_estavel", Mock())
    processar_mock = Mock()
    monkeypatch.setattr(watcher, "processar_arquivo", processar_mock)
    manipulador = watcher.ManipuladorCSV(engine)
    evento = Mock(is_directory=True, src_path="dados/entrada/pasta")

    manipulador.on_created(evento)

    processar_mock.assert_not_called()


def test_manipulador_csv_processa_arquivo_csv_apos_estabilizar(monkeypatch, engine):
    monkeypatch.setattr(watcher, "esperar_arquivo_estavel", Mock())
    processar_mock = Mock()
    monkeypatch.setattr(watcher, "processar_arquivo", processar_mock)
    manipulador = watcher.ManipuladorCSV(engine)
    evento = Mock(is_directory=False, src_path="dados/entrada/semana_2026-06-08.csv")

    manipulador.on_created(evento)

    processar_mock.assert_called_once()
