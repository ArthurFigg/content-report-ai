import logging
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from src.retry import executar_com_retry

logger = logging.getLogger(__name__)


class ConfiguracaoEmailAusenteError(Exception):
    pass


def enviar_relatorio(caminho_pdf: str, periodo: str) -> bool:
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    destinatario = os.environ.get("EMAIL_DESTINATARIO")
    if not smtp_user or not smtp_password or not destinatario:
        raise ConfiguracaoEmailAusenteError(
            "SMTP_USER, SMTP_PASSWORD e EMAIL_DESTINATARIO precisam estar configurados"
        )

    nome_negocio = os.environ.get("NOME_NEGOCIO", "")
    mensagem = _montar_mensagem(caminho_pdf, periodo, nome_negocio, smtp_user, destinatario)

    def _enviar() -> None:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(smtp_user, smtp_password)
            servidor.send_message(mensagem)

    try:
        executar_com_retry(_enviar)
    except Exception:
        logger.error("Falha persistente ao enviar o relatório por email", exc_info=True)
        return False

    return True


def _montar_mensagem(
    caminho_pdf: str, periodo: str, nome_negocio: str, remetente: str, destinatario: str
) -> MIMEMultipart:
    mensagem = MIMEMultipart()
    mensagem["Subject"] = f"Relatório semanal — {nome_negocio} — {periodo}"
    mensagem["From"] = remetente
    mensagem["To"] = destinatario
    mensagem.attach(MIMEText("O relatório semanal está em anexo."))

    caminho = Path(caminho_pdf)
    anexo = MIMEApplication(caminho.read_bytes(), _subtype="pdf")
    anexo.add_header("Content-Disposition", "attachment", filename=caminho.name)
    mensagem.attach(anexo)

    return mensagem
