import base64

from src.relatorio.grafico import gerar_grafico_evolucao

ASSINATURA_PNG = b"\x89PNG\r\n\x1a\n"


def test_gerar_grafico_evolucao_retorna_none_com_menos_de_2_semanas():
    resultado = gerar_grafico_evolucao([("2026-06-01", 1000)])

    assert resultado is None


def test_gerar_grafico_evolucao_retorna_png_valido_com_2_ou_mais_semanas():
    historico = [("2026-06-01", 1000), ("2026-06-08", 1500)]

    resultado = gerar_grafico_evolucao(historico)

    assert base64.b64decode(resultado).startswith(ASSINATURA_PNG)
