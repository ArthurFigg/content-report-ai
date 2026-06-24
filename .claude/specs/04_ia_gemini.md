# ia_gemini

**Ordem:** 4 de 7
**Depende de:** 03_ingestao_e_metricas (consome `MetricasSemana` e `VariacaoSemana`)

## O que faz
Recebe as métricas já calculadas da semana e a variação em relação à semana anterior, monta o prompt e chama a Gemini API com structured output, retornando a interpretação em linguagem natural (resumo, destaques, possível causa, recomendação) — ou `None` se a chamada falhar persistentemente.

## Comportamento
- `prompt.py` define `PROMPT_BASE` (template verbatim do CLAUDE.md, seção "Prompt da IA (base)") e a função `montar_prompt(metricas: MetricasSemana, variacao: VariacaoSemana) -> str`, que monta o payload JSON a partir dos dois objetos recebidos e interpola em `{payload_json}`.
- O payload inclui sempre: `reach_total`, `engajamento_total`, `taxa_engajamento_semanal`, `quantidade_posts`, `melhor_post` (post_id, post_type, reach), `pior_post` (post_id, post_type, reach), `melhor_taxa_engajamento_post` (post_id, post_type, taxa_engajamento) — todos vindos de `MetricasSemana`.
- Quando `variacao.tem_historico` é `True`, o payload inclui também a chave `semana_anterior` com `variacao_reach_total` e `variacao_engajamento_total` (podendo ser `null` individualmente se o valor anterior daquela métrica era 0 — já calculado por `comparacao.py`).
- Quando `variacao.tem_historico` é `False` (primeira semana), a chave `semana_anterior` é omitida inteiramente do payload — é esse o sinal que o prompt usa para instruir "não compare, retorne possivel_causa: null".
- `cliente_gemini.py` define os modelos Pydantic do schema de saída, espelhando exatamente o "Schema de saída da IA" do CLAUDE.md: `Destaque` (`tipo: str`, `descricao: str`) e `RespostaIA` (`resumo_executivo: str`, `destaques: list[Destaque]`, `possivel_causa: str | None`, `recomendacao: str`).
- `cliente_gemini.py` expõe `gerar_interpretacao(metricas: MetricasSemana, variacao: VariacaoSemana) -> RespostaIA | None`.
- A chamada à API usa `genai.Client(api_key=GEMINI_API_KEY)` e `client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config={"response_mime_type": "application/json", "response_schema": RespostaIA})`, lendo `GEMINI_API_KEY` e `GEMINI_MODEL` do ambiente a cada chamada (sem cache de client entre chamadas — chamada é pouco frequente, 1x por semana).
- `GEMINI_MODEL` tem valor padrão `"gemini-3.5-flash"` no código, usado apenas se a variável de ambiente não estiver definida (CLAUDE.md já define que deve haver um valor padrão; aqui fixa o valor concreto — modelo flash atual, GA desde maio/2026, adequado ao custo de uma chamada semanal).
- A chamada de rede (incluindo o parsing de `response.parsed`) é envolvida por `executar_com_retry` (de `src/retry.py`). Se `response.parsed` vier `None` (SDK não conseguiu validar contra o schema), `cliente_gemini.py` levanta uma exceção própria (`RespostaIAInvalidaError`) dentro da função tentada — isso conta como tentativa falha para o retry, igual a uma falha de rede.
- `executar_com_retry(funcao, tentativas=3, delays=(2, 4, 8))` (em `src/retry.py`) chama `funcao()`; se levantar exceção, loga WARNING com o número da tentativa e espera o delay correspondente antes de tentar de novo; após esgotar todas as tentativas, deixa a última exceção propagar (não a engole) — quem decide o que fazer com a falha definitiva é o chamador (`cliente_gemini.py` aqui; `email_sender.py` em `06_entrega_email`).
- `gerar_interpretacao` captura a exceção final propagada por `executar_com_retry`, loga ERROR com o detalhe, e retorna `None` — não propaga a exceção para o chamador (watcher.py, spec futura, trata `None` como "resumo indisponível").
- Após receber `RespostaIA` da API com sucesso, se `variacao.tem_historico` for `False`, `cliente_gemini.py` força `possivel_causa = None` no objeto retornado, independente do que a IA respondeu — defesa em profundidade contra a IA não obedecer a instrução do prompt na primeira semana.
- Nenhum cálculo numérico ocorre neste módulo — só montagem de prompt, chamada à API e parsing/validação do retorno.

## Critérios verificáveis
- [ ] `uv run pytest tests/test_cliente_gemini.py -v` passa
- [ ] `montar_prompt()` inclui a chave `semana_anterior` no payload quando `variacao.tem_historico=True`, e a omite quando `False`
- [ ] Com a chamada à API mockada para retornar um `RespostaIA` válido, `gerar_interpretacao()` retorna esse objeto sem alterações (caso com histórico)
- [ ] Com `variacao.tem_historico=False` e a API mockada retornando `possivel_causa` preenchido (simulando desobediência da IA), `gerar_interpretacao()` retorna o objeto com `possivel_causa=None` (override aplicado)
- [ ] Com a API mockada lançando exceção nas 2 primeiras chamadas e retornando sucesso na 3ª, `gerar_interpretacao()` retorna o resultado da 3ª tentativa (confirma uso de `executar_com_retry`)
- [ ] Com a API mockada lançando exceção nas 3 tentativas, `gerar_interpretacao()` retorna `None` sem levantar exceção
- [ ] Com `response.parsed` mockado como `None` (falha de validação de schema), `gerar_interpretacao()` trata como falha de tentativa (entra no fluxo de retry) e não tenta acessar atributos de `None`

## Módulos afetados
- `src/ia/prompt.py` (novo) — `PROMPT_BASE`, `montar_prompt()`
- `src/ia/cliente_gemini.py` (novo) — `Destaque`, `RespostaIA`, `RespostaIAInvalidaError`, `gerar_interpretacao()`
- `src/retry.py` (novo) — `executar_com_retry()`, compartilhado com `06_entrega_email`

## Não mexer
- `src/persistencia/`, `src/ingestao/`, `src/processamento/` — specs `01`-`03`, já especificadas; este módulo só recebe `MetricasSemana`/`VariacaoSemana` já calculados, não acessa banco nem recalcula métricas
- `src/relatorio/`, `src/entrega/`, `src/watcher.py` — fora de escopo desta spec; a decisão de como renderizar `None` (resumo indisponível) é do `gerador_pdf.py` (spec `05`), não daqui
- `ferramentas_dev/` — spec `02_gerador_dados_sinteticos`

## Decisões tomadas
- Falha persistente da IA → `gerar_interpretacao()` retorna `None` (não levanta exceção customizada) — contrato simples, quem chama trata `None` como "indisponível"
- Primeira semana sem histórico → Python força `possivel_causa=None` no retorno, mesmo que a IA desobedeça o prompt — defesa em profundidade, consistente com a regra do projeto de a IA nunca decidir o que o código já pode garantir
- `executar_com_retry` re-levanta a última exceção após esgotar tentativas — não decide sozinho o que fazer com a falha definitiva; cada chamador (`cliente_gemini.py`, `email_sender.py` em `06`) trata a falha à sua maneira, conforme já definido em `06_entrega_email`
- `response.parsed is None` (schema inválido) é tratado como falha de tentativa via `RespostaIAInvalidaError`, entrando no mesmo fluxo de retry de falhas de rede
- SDK: `google-genai`, `client.models.generate_content(config={"response_mime_type": "application/json", "response_schema": RespostaIA})`, lendo `response.parsed` — confirmado via documentação oficial atual do SDK (pesquisado nesta sessão)
- `GEMINI_MODEL` padrão no código: `"gemini-3.5-flash"` — modelo flash GA mais recente disponível (pesquisado nesta sessão), substitui a decisão anterior de não fixar nenhum nome
- Client da API instanciado a cada chamada (sem cache/singleton) — frequência de uso (semanal) não justifica complexidade de gerenciar ciclo de vida do client
- Modelos Pydantic (`Destaque`, `RespostaIA`) espelham exatamente o "Schema de saída da IA" do CLAUDE.md, usados tanto como `response_schema` da API quanto como tipo de retorno de `gerar_interpretacao()`

---
**Status:** concluida em 2026-06-23
