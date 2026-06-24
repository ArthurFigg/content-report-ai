import base64
import io

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt


def gerar_grafico_evolucao(historico: list[tuple[str, int]]) -> str | None:
    if len(historico) < 2:
        return None

    semanas = [semana for semana, _ in historico]
    reach_totais = [reach_total for _, reach_total in historico]

    figura, eixo = plt.subplots()
    eixo.plot(semanas, reach_totais, marker="o")
    eixo.set_ylabel("Reach total")
    figura.autofmt_xdate(rotation=45)

    buffer = io.BytesIO()
    figura.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(figura)
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode("ascii")
