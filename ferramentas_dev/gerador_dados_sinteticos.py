import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

CAMINHO_SAIDA = Path(__file__).resolve().parent.parent / "dados" / "entrada"

COLUNAS = [
    "Post ID",
    "Post Date",
    "Post Type",
    "Post Text",
    "Reach",
    "Impressions",
    "Likes and Reactions",
    "Comments",
    "Shares",
    "Saves",
    "Link Clicks",
    "Plays",
    "Watch Time",
    "Retention",
]

TIPOS_POST = ["Reel", "Photo", "Carousel", "Video"]
PESOS_TIPO_POST = [40, 35, 15, 10]

LEGENDAS = [
    "Mais um dia de trabalho por aqui!",
    "Quem também ama essa época do ano?",
    "Novidade chegando em breve, fiquem ligados!",
    "Bastidores de hoje, adoramos compartilhar com vocês.",
    "Gratidão por mais uma semana incrível.",
    "Dica rápida pra você que acompanha por aqui.",
    "Resultado de muito trabalho e dedicação.",
    "Conta pra gente nos comentários o que achou!",
    "Mais um projeto finalizado com sucesso.",
    "Hoje é dia de celebrar pequenas vitórias.",
    "Fechando a semana com chave de ouro.",
    "Esse momento merecia ser registrado.",
    "Obrigado por fazer parte dessa jornada.",
    "Em breve mais detalhes sobre isso!",
    "Sempre bom revisitar momentos assim.",
    "Mais uma entrega feita com muito carinho.",
]

REACH_MINIMO = 300
REACH_MAXIMO = 1500
MULTIPLICADOR_REEL_MINIMO = 1.3
MULTIPLICADOR_REEL_MAXIMO = 1.8
CRESCIMENTO_ACUMULADO_MINIMO = 0.05
CRESCIMENTO_ACUMULADO_MAXIMO = 0.15
MULTIPLICADOR_VIRAL_MINIMO = 5
MULTIPLICADOR_VIRAL_MAXIMO = 10
PROBABILIDADE_LINK_CLICKS = 0.25


def segundas_feiras_recentes(hoje: date) -> list[date]:
    segunda_atual = hoje - timedelta(days=hoje.weekday())
    return [segunda_atual - timedelta(weeks=indice) for indice in (3, 2, 1, 0)]


def sortear_tipo_post() -> str:
    return random.choices(TIPOS_POST, weights=PESOS_TIPO_POST, k=1)[0]


def sortear_legenda() -> str:
    return random.choice(LEGENDAS)


def sortear_data_no_periodo(segunda: date, hoje: date) -> date:
    # semana atual não pode gerar posts no futuro
    limite_superior = min(6, (hoje - segunda).days)
    return segunda + timedelta(days=random.randint(0, limite_superior))


def metricas_a_partir_do_reach(reach: int, tipo_post: str) -> dict:
    impressions = round(reach * random.uniform(1.05, 1.4))
    likes = round(reach * random.uniform(0.03, 0.08))
    comments = round(reach * random.uniform(0.002, 0.01))
    shares = round(reach * random.uniform(0.001, 0.006))
    saves = round(reach * random.uniform(0.005, 0.02))

    link_clicks = None
    if random.random() < PROBABILIDADE_LINK_CLICKS:
        link_clicks = round(reach * random.uniform(0.005, 0.03))

    plays = watch_time = retention = None
    if tipo_post in ("Reel", "Video"):
        plays = round(reach * random.uniform(1.2, 2.0))
        watch_time = round(plays * random.uniform(8, 20), 1)
        retention = round(random.uniform(30, 70), 1)

    return {
        "Impressions": impressions,
        "Likes and Reactions": likes,
        "Comments": comments,
        "Shares": shares,
        "Saves": saves,
        "Link Clicks": link_clicks,
        "Plays": plays,
        "Watch Time": watch_time,
        "Retention": retention,
    }


def gerar_reach_base(tipo_post: str, multiplicador_semana: float) -> int:
    reach = random.uniform(REACH_MINIMO, REACH_MAXIMO) * multiplicador_semana
    if tipo_post == "Reel":
        reach *= random.uniform(MULTIPLICADOR_REEL_MINIMO, MULTIPLICADOR_REEL_MAXIMO)
    return round(reach)


def gerar_post_id(contador_global: int) -> str:
    return f"post_{contador_global:05d}"


def gerar_semana(
    segunda: date,
    hoje: date,
    multiplicador_semana: float,
    contador_global: int,
    semana_viral: bool,
) -> tuple[list[dict], int]:
    quantidade_posts = random.randint(4, 7)
    indice_viral = random.randrange(quantidade_posts) if semana_viral else None

    posts = []
    reaches_normais = []
    for indice in range(quantidade_posts):
        tipo_post = sortear_tipo_post()
        reach_base = gerar_reach_base(tipo_post, multiplicador_semana)
        posts.append({"tipo_post": tipo_post, "reach": reach_base})
        if indice != indice_viral:
            reaches_normais.append(reach_base)

    if semana_viral:
        # reach viral é relativo à média dos outros posts da própria semana,
        # não ao range base — garante o "pelo menos 5x" mesmo com a tendência
        # de crescimento já aplicada
        media_normais = sum(reaches_normais) / len(reaches_normais)
        multiplicador_viral = random.uniform(
            MULTIPLICADOR_VIRAL_MINIMO, MULTIPLICADOR_VIRAL_MAXIMO
        )
        posts[indice_viral]["reach"] = round(media_normais * multiplicador_viral)

    linhas = []
    for post in posts:
        contador_global += 1
        reach = post["reach"]
        tipo_post = post["tipo_post"]
        metricas = metricas_a_partir_do_reach(reach, tipo_post)
        linhas.append(
            {
                "Post ID": gerar_post_id(contador_global),
                "Post Date": sortear_data_no_periodo(segunda, hoje).isoformat(),
                "Post Type": tipo_post,
                "Post Text": sortear_legenda(),
                "Reach": reach,
                **metricas,
            }
        )

    return linhas, contador_global


def formatar_valor(valor: object) -> str:
    return "" if valor is None else str(valor)


def escrever_csv(caminho: Path, linhas: list[dict]) -> None:
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow(
                {coluna: formatar_valor(linha[coluna]) for coluna in COLUNAS}
            )


def main() -> None:
    hoje = date.today()
    semanas = segundas_feiras_recentes(hoje)
    semana_viral = random.choice(semanas)
    crescimento_acumulado = random.uniform(
        CRESCIMENTO_ACUMULADO_MINIMO, CRESCIMENTO_ACUMULADO_MAXIMO
    )

    CAMINHO_SAIDA.mkdir(parents=True, exist_ok=True)

    contador_global = 0
    for indice, segunda in enumerate(semanas):
        multiplicador_semana = 1 + crescimento_acumulado * indice / (len(semanas) - 1)
        linhas, contador_global = gerar_semana(
            segunda,
            hoje,
            multiplicador_semana,
            contador_global,
            semana_viral=(segunda == semana_viral),
        )
        caminho_arquivo = CAMINHO_SAIDA / f"semana_{segunda.isoformat()}.csv"
        escrever_csv(caminho_arquivo, linhas)


if __name__ == "__main__":
    main()
