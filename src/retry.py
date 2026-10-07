import logging
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)

def executar_com_retry[T](
    funcao: Callable[[], T],
    tentativas: int = 3,
    delays: tuple[float, ...] = (2, 4, 8),
) -> T:
    ultimo_erro: Exception | None = None

    for numero_tentativa in range(1, tentativas + 1):
        try:
            return funcao()
        # Qualquer erro conta como falha da tentativa; o último sobe no fim.
        except Exception as erro:  # noqa: BLE001
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
