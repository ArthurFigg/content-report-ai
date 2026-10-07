# tendencia_semanas

**Ordem:** 8 de 8
**Depende de:** 01_persistencia, 03_ingestao_e_metricas, 07_watcher (última a mexer em repositorio.py)
**Score:** 1
**Revisão:** aprovada

## O que faz
Compara o Reach total e o Engajamento total da semana atual com a média das últimas 4 semanas já salvas, além da comparação com a semana anterior que já existe.

## Comportamento
- `tendencia.py` recebe os totais da semana atual e o histórico de semanas anteriores (lista de `TotaisAnteriores`, da mais recente para a mais antiga) e calcula a média de Reach total e de Engajamento total dessas semanas.
- Usa no máximo as 4 semanas mais recentes do histórico (`JANELA_TENDENCIA`). Se receber mais, ignora as mais antigas.
- Com 1 a 3 semanas no histórico, calcula a média com as que tiver e informa quantas usou em `semanas_usadas`.
- Com histórico vazio (primeira semana), devolve `tem_historico` falso, `semanas_usadas` 0, médias e variações `None` — sem calcular nada.
- A variação de cada métrica é a diferença percentual entre o valor atual e a média daquela métrica.
- Se a média de uma métrica for 0, a variação dessa métrica é `None` (sem base de comparação), sem afetar a outra métrica — mesmo critério que a `comparacao` usa para valor anterior 0.
- `tendencia.py` é função pura: não acessa o banco. O histórico chega pronto, e não deve conter a semana atual — garantir isso é de quem chama.
- `repositorio.py` ganha `buscar_ultimos_resumos`, que devolve os resumos mais recentes, do maior `semana` para o menor, até a quantidade pedida.
- `buscar_ultimos_resumos` com tabela vazia devolve lista vazia; com menos semanas salvas que a quantidade pedida, devolve todas; com quantidade menor que 1, devolve lista vazia.

## Regras
- QUANDO o histórico estiver vazio, a tendencia DEVE devolver `tem_historico` falso, `semanas_usadas` 0 e médias e variações `None`.
- QUANDO o histórico tiver mais de 4 semanas, a tendencia DEVE usar só as 4 mais recentes.
- QUANDO o histórico tiver de 1 a 3 semanas, a tendencia DEVE calcular a média com as semanas que houver.
- QUANDO a média de uma métrica for 0, a tendencia DEVE devolver `None` como variação dessa métrica.
- QUANDO a tabela `resumos_semanais` estiver vazia, o repositorio DEVE devolver lista vazia em `buscar_ultimos_resumos`.
- QUANDO `buscar_ultimos_resumos` receber quantidade menor que 1, o repositorio DEVE devolver lista vazia.
- QUANDO houver mais semanas salvas que a quantidade pedida, o repositorio DEVE devolver em `buscar_ultimos_resumos` só as de maior `semana`, da maior para a menor.

## Interfaces públicas
- `calcular_tendencia(reach_total_atual, engajamento_total_atual, historico) -> TendenciaSemana` — em `src/processamento/tendencia.py`
- `buscar_ultimos_resumos(sessao, quantidade) -> list[ResumoSemanal]` — em `src/persistencia/repositorio.py`
- `TendenciaSemana` — campos `tem_historico`, `semanas_usadas`, `media_reach_total`, `media_engajamento_total`, `variacao_reach_total`, `variacao_engajamento_total` — em `src/processamento/tendencia.py`
- `JANELA_TENDENCIA` — constante, valor 4 — em `src/processamento/tendencia.py`

## Usa de outras specs
- `TotaisAnteriores` (03_ingestao_e_metricas)
- `ResumoSemanal` (01_persistencia)

## Critérios verificáveis
- [ ] `uv run pytest tests/test_tendencia.py -v` passa
- [ ] `uv run pytest tests/test_repositorio.py -v` passa
- [ ] Histórico vazio → `tem_historico` falso, `semanas_usadas` 0, as duas médias `None` e as duas variações `None`
- [ ] Histórico com 3 semanas (Reach 100, 200, 300) → `media_reach_total` 200 e `semanas_usadas` 3
- [ ] Histórico com 6 semanas → `semanas_usadas` 4 e médias calculadas só com as 4 primeiras da lista
- [ ] Média de Reach 100 e Reach atual 150 → `variacao_reach_total` 50.0
- [ ] Média de Reach 200 e Reach atual 150 → `variacao_reach_total` -25.0
- [ ] Média de Engajamento 0 → `variacao_engajamento_total` `None`, enquanto `variacao_reach_total` continua calculada
- [ ] `buscar_ultimos_resumos` com tabela vazia → lista vazia
- [ ] `buscar_ultimos_resumos` com 6 semanas salvas e quantidade 4 → as 4 semanas mais recentes, da maior para a menor
- [ ] `buscar_ultimos_resumos` com 2 semanas salvas e quantidade 4 → as 2 semanas
- [ ] `buscar_ultimos_resumos` com quantidade 0 → lista vazia
- [ ] `uv run pytest -v` passa inteiro (os 63 testes anteriores continuam passando)

## Módulos afetados
- `src/processamento/tendencia.py` (novo) — `calcular_tendencia`, `TendenciaSemana`, `JANELA_TENDENCIA`
- `src/persistencia/repositorio.py` — nova função `buscar_ultimos_resumos`; as funções existentes não mudam
- `tests/test_tendencia.py` (novo) e `tests/test_repositorio.py` (novos testes)

## Não mexer
- `src/processamento/comparacao.py` e `src/processamento/calculo_metricas.py` — a tendência fica ao lado da comparação, não substitui
- Funções já existentes de `src/persistencia/repositorio.py` e todo o `src/persistencia/modelos.py`
- `src/watcher.py` — ligar a tendência no pipeline é de outra spec
- `src/ia/`, `src/relatorio/`, `src/entrega/`, `src/ingestao/`, `ferramentas_dev/`

## Decisões tomadas
> O usuário delegou as decisões desta spec ("pode ser qualquer uma", "só vai fazendo"); todas abaixo foram tomadas pelo Claude.
- Escopo → só cálculo + busca no banco; PDF, prompt da IA e ligação no watcher ficam para uma spec futura (manter a spec pequena)
- Janela → 4 semanas, constante `JANELA_TENDENCIA`, não variável de ambiente (ninguém pediu para configurar)
- Menos de 4 semanas → média com as que houver + `semanas_usadas`, em vez de exigir 4 (senão o projeto só teria tendência a partir da 5ª semana)
- Média 0 → variação `None`, mesmo critério já decidido na `comparacao` para valor anterior 0
- Histórico entra como lista de `TotaisAnteriores`, não de `ResumoSemanal` — mesmo motivo da spec 03: função pura sem depender do schema do banco; a conversão fica com quem chama
- Quantidade menor que 1 em `buscar_ultimos_resumos` → lista vazia, não exceção (consulta sem resultado não é erro)
- Variação sem arredondamento, igual à `comparacao` — arredondar é papel de quem exibe

## Impacto no CLAUDE.md
- Estrutura de pastas sugerida → adicionar `tendencia.py` em `processamento/` ("variação semana atual vs. média das últimas 4") e `tests/test_tendencia.py`
- Esquema do banco (parágrafo de `listar_resumos_semanais`) → acrescentar `repositorio.buscar_ultimos_resumos(sessao, quantidade)`, que devolve os resumos mais recentes, do mais novo para o mais antigo

---
**Status:** concluida em 2026-10-07
