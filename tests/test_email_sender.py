from email.message import Message
from unittest.mock import MagicMock, Mock

import pytest

import src.retry as modulo_retry
from src.entrega import email_sender
from src.entrega.email_sender import ConfiguracaoEmailAusenteError, enviar_relatorio


def _configurar_env(monkeypatch):
    monkeypatch.setenv("SMTP_USER", "remetente@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "senha-app")
    monkeypatch.setenv("EMAIL_DESTINATARIO", "dest@example.com")
    monkeypatch.setenv("NOME_NEGOCIO", "Padaria Pão Dourado")


def _criar_pdf_falso(tmp_path) -> str:
    caminho_pdf = tmp_path / "relatorio_2026-06-08.pdf"
    caminho_pdf.write_bytes(b"%PDF-1.4 conteudo falso")
    return str(caminho_pdf)


def _mock_smtp_sucesso(monkeypatch) -> MagicMock:
    servidor_mock = MagicMock()
    smtp_mock = MagicMock()
    smtp_mock.__enter__.return_value = servidor_mock
    monkeypatch.setattr(
        "src.entrega.email_sender.smtplib.SMTP_SSL", Mock(return_value=smtp_mock)
    )
    monkeypatch.setattr("src.retry.time.sleep", Mock())
    return servidor_mock


def _enviar_e_capturar_mensagem(monkeypatch, tmp_path) -> Message:
    _configurar_env(monkeypatch)
    servidor_mock = _mock_smtp_sucesso(monkeypatch)
    caminho_pdf = _criar_pdf_falso(tmp_path)

    enviar_relatorio(caminho_pdf, "08/06 a 14/06/2026")

    return servidor_mock.send_message.call_args[0][0]


def test_enviar_relatorio_monta_assunto_com_nome_do_negocio_e_periodo(monkeypatch, tmp_path):
    mensagem = _enviar_e_capturar_mensagem(monkeypatch, tmp_path)

    assert mensagem["Subject"] == "Relatório semanal — Padaria Pão Dourado — 08/06 a 14/06/2026"


def test_enviar_relatorio_inclui_corpo_avisando_sobre_o_anexo(monkeypatch, tmp_path):
    mensagem = _enviar_e_capturar_mensagem(monkeypatch, tmp_path)

    parte_texto = next(
        parte for parte in mensagem.walk() if parte.get_content_type() == "text/plain"
    )
    assert "anexo" in parte_texto.get_payload(decode=True).decode()


def test_enviar_relatorio_inclui_anexo_pdf_com_nome_do_arquivo(monkeypatch, tmp_path):
    mensagem = _enviar_e_capturar_mensagem(monkeypatch, tmp_path)

    anexos = [parte for parte in mensagem.walk() if parte.get_filename()]
    assert anexos[0].get_filename() == "relatorio_2026-06-08.pdf"


def test_enviar_relatorio_retorna_true_em_caso_de_sucesso(monkeypatch, tmp_path):
    _configurar_env(monkeypatch)
    _mock_smtp_sucesso(monkeypatch)
    caminho_pdf = _criar_pdf_falso(tmp_path)

    resultado = enviar_relatorio(caminho_pdf, "08/06 a 14/06/2026")

    assert resultado is True


def test_enviar_relatorio_tenta_novamente_apos_falha(monkeypatch, tmp_path):
    _configurar_env(monkeypatch)
    servidor_mock = MagicMock()
    smtp_mock = MagicMock()
    smtp_mock.__enter__.return_value = servidor_mock
    monkeypatch.setattr(
        "src.entrega.email_sender.smtplib.SMTP_SSL",
        Mock(side_effect=[Exception("erro de conexão"), Exception("erro de conexão"), smtp_mock]),
    )
    monkeypatch.setattr("src.retry.time.sleep", Mock())
    caminho_pdf = _criar_pdf_falso(tmp_path)

    resultado = enviar_relatorio(caminho_pdf, "08/06 a 14/06/2026")

    assert resultado is True


def test_enviar_relatorio_retorna_false_apos_falhas_persistentes(monkeypatch, tmp_path):
    _configurar_env(monkeypatch)
    monkeypatch.setattr(
        "src.entrega.email_sender.smtplib.SMTP_SSL",
        Mock(side_effect=Exception("erro de conexão")),
    )
    monkeypatch.setattr("src.retry.time.sleep", Mock())
    caminho_pdf = _criar_pdf_falso(tmp_path)

    resultado = enviar_relatorio(caminho_pdf, "08/06 a 14/06/2026")

    assert resultado is False


def test_enviar_relatorio_levanta_erro_imediato_com_configuracao_ausente(monkeypatch, tmp_path):
    monkeypatch.delenv("EMAIL_DESTINATARIO", raising=False)
    monkeypatch.setenv("SMTP_USER", "remetente@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "senha-app")
    sleep_mock = Mock()
    monkeypatch.setattr("src.retry.time.sleep", sleep_mock)
    caminho_pdf = _criar_pdf_falso(tmp_path)

    with pytest.raises(ConfiguracaoEmailAusenteError):
        enviar_relatorio(caminho_pdf, "08/06 a 14/06/2026")

    sleep_mock.assert_not_called()


def test_email_sender_reutiliza_modulo_retry_compartilhado():
    assert email_sender.executar_com_retry is modulo_retry.executar_com_retry
