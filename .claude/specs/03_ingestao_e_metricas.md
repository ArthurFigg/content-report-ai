# ingestao_e_metricas

**Ordem:** 3 de 7
**Depende de:** 01_persistencia (consome o formato do resumo anterior, mas não chama repositorio.py diretamente), 02_gerador_dados_sinteticos (leitor_csv.py assume o formato de CSV definido ali — vírgula, datas ISO)

## O que faz
Lê e valida um CSV semanal, calcula as métricas determinísticas da semana (totais, melhor/pior post, taxa de engajamento) e a variação percentual em relação à semana anterior — produzindo o pacote de dados pronto para persistir e enviar à IA.

## Comportamento
- `leitor_csv.py` lê o CSV e valida: colunas obrigatórias presentes (Post ID, Post Date, Post Type, Reach, Impressions, Likes and Reactions, Comments, Shares, Saves), Post Date parseável como data válida, Post Type dentro do enum {Photo, Video, Reel, Carousel}, valores numéricos (Reach, Impressions, Likes and Reactions, Comments, Shares, Saves, Link Clicks quando presente) não-negativos, Post ID único dentro do próprio arquivo, e pelo menos 1 linha de dados.
- Qualquer falha de validação (coluna ausente, tipo inválido, Post Type fora do enum, valor negativo, Post ID duplicado no arquivo, zero linhas de dados) rejeita o arquivo inteiro com mensagem específica do problema encontrado — mesmo comportamento já definido no CLAUDE.md (loga erro, não move o arquivo, não insere nada no banco).
- `calculo_metricas.py` recebe os posts validados e calcula, por post: `taxa_engajamento` (engajamento do post ÷ Reach do post × 100, ou 0 se Reach=0).
- `calculo_metricas.py` calcula os agregados da semana: Reach total, Engajamento total (soma das 4 métricas já definidas no CLAUDE.md), `taxa_engajamento_semanal`, quantidade de posts, melhor post (maior Reach) e pior post (menor Reach). `melhor_post` e `pior_post` retornados como o registro completo do post (post_id, post_type, reach, taxa_engajamento), não só o ID — é o que `cliente_gemini.py` (spec `04_ia_gemini`) espera consumir.
- `calculo_metricas.py` também identifica o post com a **maior `taxa_engajamento`** da semana (`melhor_taxa_engajamento_post`), distinto do `melhor_post` por Reach quando aplicável — já decidido no CLAUDE.md ("Esquema do banco": "o post com a maior taxa_engajamento da semana é identificado por calculo_metricas.py e enviado no payload para a IA"), mas que ainda não estava no "Comportamento" desta spec.
- `comparacao.py` recebe os totais da semana atual e o resumo da semana anterior (já buscado pelo `repositorio.py`, fora deste módulo) e calcula a variação percentual de Reach total e de Engajamento total.
- Se não houver resumo anterior (`None` — primeira semana), `comparacao.py` retorna indicação explícita de "sem histórico" para ambas as métricas, sem calcular variação.
- Se o valor da métrica na semana anterior for 0, a variação percentual daquela métrica específica é `null` (sem base de comparação válida), mesmo havendo histórico de outras métricas.
- `comparacao.py` é uma função pura — não acessa o banco diretamente; recebe os dois conjuntos de totais já calculados/buscados por quem o chama (orquestração é responsabilidade do `watcher.py`, spec futura).

## Critérios verificáveis
- [ ] `uv run pytest tests/test_leitor_csv.py -v` passa
- [ ] `uv run pytest tests/test_calculo_metricas.py -v` passa
- [ ] `uv run pytest tests/test_comparacao.py -v` passa
- [ ] `leitor_csv.py` rejeita um CSV com coluna obrigatória faltando, com mensagem indicando qual coluna
- [ ] `leitor_csv.py` rejeita um CSV com Post Type fora do enum (ex: "Story")
- [ ] `leitor_csv.py` rejeita um CSV com valor negativo em uma métrica numérica
- [ ] `leitor_csv.py` rejeita um CSV com Post ID duplicado dentro do próprio arquivo
- [ ] `leitor_csv.py` rejeita um CSV com zero linhas de dados
- [ ] `calculo_metricas.py` calcula corretamente melhor_post e pior_post por Reach num conjunto de posts de teste
- [ ] `calculo_metricas.py` retorna `taxa_engajamento = 0` para um post com Reach=0
- [ ] `calculo_metricas.py` identifica corretamente o post com maior `taxa_engajamento` da semana, diferente do `melhor_post` (por Reach) num conjunto de teste onde os dois critérios apontam para posts diferentes
- [ ] `comparacao.py` retorna "sem histórico" quando o resumo anterior é `None`
- [ ] `comparacao.py` retorna variação `null` para uma métrica cujo valor anterior é 0
- [ ] `comparacao.py` calcula a variação percentual correta para um par de valores conhecidos (ex: 100→150 = +50%)

## Módulos afetados
- `src/ingestao/leitor_csv.py` (novo) — leitura e validação do CSV, conforme regras acima
- `src/processamento/calculo_metricas.py` (novo) — totais, melhor/pior post, taxa de engajamento por post e semanal
- `src/processamento/comparacao.py` (novo) — variação percentual de Reach total e Engajamento total, função pura

## Não mexer
- `src/persistencia/` — spec `01_persistencia`, já especificada; este módulo só consome o resumo anterior já buscado, não chama `repositorio.py` diretamente
- `ferramentas_dev/` — spec `02_gerador_dados_sinteticos`, não precisa ser tocada aqui
- `src/ia/`, `src/relatorio/`, `src/entrega/`, `src/watcher.py` — fora de escopo desta spec

## Decisões tomadas
- Zero linhas de dados → tratado como CSV inválido (mesmo fluxo de rejeição de CSV malformado)
- Variação % com valor anterior = 0 → `null`, não 100% nem exceção
- "tipos básicos" do CLAUDE.md → inclui validação de enum de Post Type e rejeição de valores numéricos negativos
- Post ID duplicado dentro do mesmo arquivo → detectado e rejeitado na validação do CSV, com erro específico (não deixa cair no erro de integridade do banco)
- `comparacao.py` é função pura, sem acesso a banco — separação entre lógica de negócio (`processamento/`) e acesso a dados (`persistencia/`), conforme regra global do projeto
- Exceções de validação usam tipo específico de domínio (ex: `CSVInvalidoError`), não exceções genéricas — conforme regra global do projeto ("nunca `except Exception: pass`", exceções específicas do domínio)
- **[Correção do `/spec-review`]** Adicionado o cálculo de `melhor_taxa_engajamento_post` ao comportamento desta spec — já estava decidido no CLAUDE.md e consumido pelo payload de `04_ia_gemini`, mas não estava coberto aqui, gerando uma dependência implícita sem referência cruzada
- **[Correção do `/spec-review`]** Adicionada dependência de `02_gerador_dados_sinteticos` — `leitor_csv.py` assume o formato de CSV (vírgula, datas ISO) definido naquela spec
- `leitor_csv.py` produz `PostValidado` (dataclass próprio de `ingestao/`), não o `DadosPost` de `persistencia/modelos.py` — mantém ingestão e persistência desacopladas; a adaptação entre os dois formatos é responsabilidade do `watcher.py` (spec `07_watcher`)
- `comparacao.py` recebe `TotaisAnteriores` (dataclass próprio, só com `reach_total`/`engajamento_total`), não o `ResumoSemanal` de `persistencia/modelos.py` — pelo mesmo motivo: função pura sem depender do schema do banco

---
**Status:** concluida em 2026-06-22
