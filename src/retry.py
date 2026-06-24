import logging
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def executar_com_retry(
    funcao: Callable[[], T],
    tentativas: int = 3,
    delays: tuple[float, ...] = (2, 4, 8),
) -> T:
    ultimo_erro: Exception | None = None

    for numero_tentativa in range(1, tentativas + 1):
        try:
            return funcao()
        except Exception as erro:
            ultimo_erro = erro
            if numero_tentativa < tentativas:
                delay = delays[numero_tentativa - 1]
                logger.warning(
                    "Tentativa %d/%d falhou: %s. Tentando novamente em %ds.",
                    numero_tentativa,
                    tentativas,
                    erro,
                    delay,
                )
                time.sleep(delay)

    raise ultimo_erro
