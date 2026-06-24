from unittest.mock import Mock

import pytest

from src.retry import executar_com_retry


def test_executar_com_retry_retorna_resultado_na_primeira_tentativa(monkeypatch):
    monkeypatch.setattr("src.retry.time.sleep", Mock())
    funcao = Mock(return_value="ok")

    resultado = executar_com_retry(funcao)

    assert resultado == "ok"


def test_executar_com_retry_tenta_novamente_apos_falha(monkeypatch):
    monkeypatch.setattr("src.retry.time.sleep", Mock())
    funcao = Mock(side_effect=[ValueError("erro"), ValueError("erro"), "ok"])

    resultado = executar_com_retry(funcao)

    assert resultado == "ok"


def test_executar_com_retry_levanta_ultimo_erro_apos_esgotar_tentativas(monkeypatch):
    monkeypatch.setattr("src.retry.time.sleep", Mock())
    funcao = Mock(side_effect=ValueError("falha definitiva"))

    with pytest.raises(ValueError, match="falha definitiva"):
        executar_com_retry(funcao)


def test_executar_com_retry_usa_delays_configurados(monkeypatch):
    sleep_mock = Mock()
    monkeypatch.setattr("src.retry.time.sleep", sleep_mock)
    funcao = Mock(side_effect=[ValueError("erro"), ValueError("erro"), "ok"])

    executar_com_retry(funcao, delays=(2, 4, 8))

    assert sleep_mock.call_args_list == [((2,),), ((4,),)]
