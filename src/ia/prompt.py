import json

from src.processamento.calculo_metricas import MetricasSemana, PostResumo
from src.processamento.comparacao import VariacaoSemana

PROMPT_BASE = """Você é um analista de marketing de conteúdo. Você recebe métricas semanais
de um perfil do Instagram e deve gerar uma interpretação curta e prática,
destinada a um pequeno empresário ou criador de conteúdo sem conhecimento
técnico de marketing.

Regras obrigatórias:
- Baseie-se SOMENTE nos números fornecidos. Não invente eventos, campanhas
  ou ações que não estejam implícitos nos dados (ex: não diga "você fez uma
  promoção" se isso não está nos dados).
- Se o campo "semana_anterior" não for fornecido, isso é o primeiro
  relatório: não compare, não calcule variação, e retorne
  "possivel_causa": null.
- Se houver dados da semana anterior, use a variação percentual fornecida
  para fundamentar "possivel_causa" — a causa sugerida deve estar
  diretamente ligada a algo presente nos dados (ex: tipo de post, quantidade
  de posts, dia da semana), nunca uma suposição externa.
- Linguagem simples, direta, sem jargão de marketing (não use termos como
  "funil", "KPI", "ROI").
- "recomendacao" deve ser uma ação concreta e específica, não um conselho
  genérico (ex: não "poste mais", mas "considere postar Reels às terças,
  que teve seu melhor desempenho").

Dados desta semana:
{payload_json}

Responda seguindo exatamente o schema fornecido."""


def montar_prompt(metricas: MetricasSemana, variacao: VariacaoSemana) -> str:
    payload = {
        "reach_total": metricas.reach_total,
        "engajamento_total": metricas.engajamento_total,
        "taxa_engajamento_semanal": metricas.taxa_engajamento_semanal,
        "quantidade_posts": metricas.quantidade_posts,
        "melhor_post": _post_por_reach(metricas.melhor_post),
        "pior_post": _post_por_reach(metricas.pior_post),
        "melhor_taxa_engajamento_post": _post_por_taxa_engajamento(
            metricas.melhor_taxa_engajamento_post
        ),
    }
    if variacao.tem_historico:
        payload["semana_anterior"] = {
            "variacao_reach_total": variacao.variacao_reach_total,
            "variacao_engajamento_total": variacao.variacao_engajamento_total,
        }

    payload_json = json.dumps(payload, ensure_ascii=False)
    return PROMPT_BASE.format(payload_json=payload_json)


def _post_por_reach(post: PostResumo) -> dict:
    return {"post_id": post.post_id, "post_type": post.post_type, "reach": post.reach}


def _post_por_taxa_engajamento(post: PostResumo) -> dict:
    return {
        "post_id": post.post_id,
        "post_type": post.post_type,
        "taxa_engajamento": post.taxa_engajamento,
    }
