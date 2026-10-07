# Domínio — content-report-ai

> Glossário mínimo criado em 2026-10-07, na conversão das specs 01 e 03 para o formato novo.
> Cobre só os nomes das specs no formato novo (01, 03, 08). Specs antigas não foram varridas.

## Entidades

- **Post** — uma linha do CSV exportado do Meta; tabela `posts`, chave `post_id`. Campos usados nas specs: `post_id`, `post_type`, `reach`, `taxa_engajamento`, `semana`.
- **Resumo semanal** — totais de uma semana processada; tabela `resumos_semanais`, chave `semana`. Campos: `reach_total`, `engajamento_total`, `taxa_engajamento_semanal`, `quantidade_posts`, `melhor_post_id`, `pior_post_id`.
- **Semana** — identificador vindo do nome do arquivo (`semana_AAAA-MM-DD.csv`); nunca derivado de Post Date.

## Termos

- **Melhor post / pior post** — `melhor_post`, `pior_post`: maior e menor Reach da semana.
- **Melhor taxa** — `melhor_taxa_engajamento_post`: maior `taxa_engajamento` da semana.
- **Variação** — diferença percentual contra a semana anterior: `tem_historico`, `variacao_reach_total`, `variacao_engajamento_total`.
- **Desempenho por tipo** — métricas separadas por `post_type`: `quantidade_posts`, `reach_medio`, `taxa_engajamento`.
- **Tendência** — diferença percentual contra a média das últimas semanas: `semanas_usadas`, `media_reach_total`, `media_engajamento_total`.
- Evitar: "alcance" no código (usar `reach`), "engajamento bruto" (usar `engajamento_total`).

## Componentes (módulos)

leitor_csv, calculo_metricas, comparacao, tendencia, repositorio, modelos, cliente_gemini, grafico, watcher

## Termos técnicos aceitos

create_all, Session, Engine
