# desempenho_por_tipo

**Ordem:** 9 de 9
**Depende de:** 03_ingestao_e_metricas
**Score:** 1
**Revisão:** aprovada

## O que faz
Separa os posts da semana por tipo (Photo, Video, Reel, Carousel) e calcula, para cada tipo, quantos posts teve, o Reach médio e a taxa de engajamento do tipo.

## Comportamento
- `calcular_metricas_por_tipo` recebe a lista de posts validados da semana e devolve uma lista de `MetricasPorTipo`, um item por tipo de post que apareceu na semana.
- Tipo que não apareceu na semana não entra na lista (sem item com zero posts).
- `reach_medio` de um tipo = soma do Reach dos posts daquele tipo ÷ quantidade de posts do tipo.
- `taxa_engajamento` de um tipo = engajamento total dos posts do tipo ÷ Reach total do tipo × 100, com o mesmo engajamento e a mesma regra de Reach 0 já usados na taxa semanal (ver CLAUDE.md, "Esquema do banco").
- A lista sai ordenada pelo `reach_medio`, do maior para o menor. Empate no `reach_medio`: ordem alfabética do `post_type`.
- Lista de posts vazia → lista vazia, sem erro.
- A função é pura: não acessa banco nem arquivo.

## Regras
- QUANDO a lista de posts estiver vazia, o calculo_metricas DEVE devolver lista vazia em `calcular_metricas_por_tipo`.
- QUANDO um tipo de post não aparecer na semana, o calculo_metricas DEVE deixar esse tipo fora da lista.
- QUANDO o Reach total de um tipo for 0, o calculo_metricas DEVE usar taxa de engajamento 0 para esse tipo.
- QUANDO dois tipos tiverem o mesmo `reach_medio`, o calculo_metricas DEVE ordená-los pelo `post_type` em ordem alfabética.

## Interfaces públicas
- `calcular_metricas_por_tipo(posts) -> list[MetricasPorTipo]` — em `src/processamento/calculo_metricas.py`
- `MetricasPorTipo` — campos `post_type`, `quantidade_posts`, `reach_medio`, `taxa_engajamento` — em `src/processamento/calculo_metricas.py`

## Usa de outras specs
- `PostValidado` (03_ingestao_e_metricas)
- `calcular_taxa_engajamento` (03_ingestao_e_metricas)

## Critérios verificáveis
- [ ] `uv run pytest tests/test_calculo_metricas.py -v` passa
- [ ] Lista vazia → lista vazia
- [ ] Semana só com Reels e Photos → lista com 2 itens, sem Video nem Carousel
- [ ] 2 Reels com Reach 100 e 300 → `reach_medio` 200.0 e `quantidade_posts` 2 no item de Reel
- [ ] Tipo com Reach total 400 e engajamento total 40 → `taxa_engajamento` 10.0
- [ ] Tipo cujos posts têm todos Reach 0 → `taxa_engajamento` 0.0
- [ ] Reel com `reach_medio` maior que Photo → Reel vem antes na lista
- [ ] Carousel e Photo com o mesmo `reach_medio` → Carousel vem antes de Photo
- [ ] `uv run pytest -v` passa inteiro (os 82 testes anteriores continuam passando)

## Módulos afetados
- `src/processamento/calculo_metricas.py` — nova função `calcular_metricas_por_tipo` e nova dataclass `MetricasPorTipo`; o que já existe no arquivo não muda
- `tests/test_calculo_metricas.py` (novos testes)

## Não mexer
- Funções e dataclasses já existentes de `src/processamento/calculo_metricas.py` (`calcular_metricas_semana`, `calcular_taxa_engajamento`, `MetricasSemana`, `PostResumo`)
- `src/processamento/comparacao.py`, `src/processamento/tendencia.py`
- `src/persistencia/`, `src/ingestao/`, `src/watcher.py`, `src/ia/`, `src/relatorio/`, `src/entrega/`, `ferramentas_dev/`

## Decisões tomadas
> O usuário delegou as decisões desta spec ("vai fazendo sem parar"); spec criada para testar o fluxo, decisões tomadas pelo Claude.
- Onde mora → `calculo_metricas.py`, ao lado das outras métricas da semana (mesmo assunto, mesmo dado de entrada), em vez de arquivo novo
- Taxa do tipo → agregada (engajamento total ÷ Reach total), não média das taxas dos posts — mesmo critério da taxa semanal; média de taxas deixaria um post de Reach minúsculo pesar igual a um viral
- Tipo ausente → fora da lista, em vez de item zerado (zero posts não tem média)
- Ordem → `reach_medio` decrescente, empate por nome — saída determinística, sem depender da ordem dos posts no CSV
- Sem ligar no watcher, PDF ou IA — fica para outra spec

## Impacto no CLAUDE.md
- Estrutura de pastas sugerida → comentário de `calculo_metricas.py` passa a citar "desempenho por tipo de post"

---
**Status:** concluida em 2026-10-07
