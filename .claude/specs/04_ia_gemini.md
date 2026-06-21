# ia_gemini

**Ordem:** 4 de 7
**Depende de:** 03_ingestao_e_metricas (consome os totais e a variação calculados ali)

## O que faz
Monta o payload de métricas da semana e envia para a API Gemini com structured output (schema forçado), com retry e fallback caso a IA falhe persistentemente.

## Comportamento
- `prompt.py` define o template de prompt (texto já definido no CLAUDE.md "Prompt da IA") e a função/constante que injeta o `payload_json`.
- `cliente_gemini.py` monta o payload JSON com: `reach_total`, `engajamento_total`, `taxa_engajamento_semanal`, `quantidade_posts`, `melhor_post` (post_id, post_type, reach, taxa_engajamento), `pior_post` (idem), `melhor_taxa_engajamento_post` (post com maior taxa_engajamento, se diferente do melhor_post por Reach), `semana_anterior` (objeto com reach_total/engajamento_total da semana anterior + variação de Reach e de Engajamento, cada uma podendo ser número ou `null`, ou o campo `semana_anterior` totalmente ausente se for a primeira semana).
- `cliente_gemini.py` usa o SDK `google-genai`, chamando `client.models.generate_content()` com `response_schema` (modelo Pydantic espelhando o "Schema de saída da IA" do CLAUDE.md) e `response_mime_type="application/json"`.
- Nome do modelo lido de `GEMINI_MODEL` (`.env`), com um valor padrão definido no código caso a variável não exista — evita quebrar o projeto se o modelo padrão for descontinuado.
- Chave da API lida de `GEMINI_API_KEY` (`.env`).
- Em caso de qualquer exceção na chamada (timeout, rate limit, erro de API, resposta que falha a validação do schema), usa `src/retry.py` para tentar novamente com backoff exponencial (3 tentativas: 2s, 4s, 8s) — módulo compartilhado, que será reaproveitado depois por `entrega_email`.
- Se todas as tentativas falharem, `cliente_gemini.py` retorna um resultado indicando falha explicitamente — não levanta exceção para o chamador. Quem orquestra (`watcher.py`, spec futura) decide como montar o PDF com os campos de IA marcados como indisponíveis.
- A resposta validada (Pydantic) contém os 4 campos do schema já definido no CLAUDE.md: `resumo_executivo`, `destaques` (lista de `tipo` + `descricao`), `possivel_causa` (ou `null`), `recomendacao`.

## Critérios verificáveis
- [ ] `uv run pytest tests/test_cliente_gemini.py -v` passa
- [ ] Payload enviado para a API (mockada) contém todos os campos listados em "Comportamento"
- [ ] Na primeira semana (sem resumo anterior), o payload não inclui o campo `semana_anterior`
- [ ] Uma falha simulada (mock lança exceção) nas 2 primeiras tentativas seguida de sucesso na 3ª é aceita normalmente (confirma que o retry funciona)
- [ ] 3 falhas consecutivas simuladas resultam em retorno de "falha persistente" sem exceção não tratada subindo ao chamador
- [ ] `src/retry.py` tem teste próprio confirmando os intervalos de espera (2s, 4s, 8s) e o número de tentativas (3)

## Módulos afetados
- `src/ia/cliente_gemini.py` (novo)
- `src/ia/prompt.py` (novo)
- `src/retry.py` (novo) — módulo compartilhado de retry com backoff exponencial, reutilizado futuramente por `entrega_email`

## Não mexer
- `src/persistencia/`, `src/ingestao/`, `src/processamento/` — specs `01`-`03`, já especificadas
- `ferramentas_dev/` — spec `02_gerador_dados_sinteticos`
- `src/relatorio/`, `src/entrega/`, `src/watcher.py` — fora de escopo desta spec

## Decisões tomadas
- SDK: `google-genai` (SDK unificado atual do Google), `response_schema` via Pydantic + `response_mime_type="application/json"` — confirmado via pesquisa na documentação oficial (ai.google.dev/gemini-api/docs/structured-output)
- Nome do modelo configurável via `GEMINI_MODEL` no `.env`, com valor padrão no código — os nomes/preços de modelo Gemini mudam com frequência; pesquisa trouxe fontes conflitantes sobre qual é "o modelo atual", então evitamos fixar isso na spec
- Retry/backoff extraído para módulo compartilhado `src/retry.py`, reutilizado por `entrega_email` (spec futura) — evita duplicar a mesma lógica de espera exponencial em dois módulos
- Política de retry uniforme: qualquer exceção na chamada (timeout, rate limit, erro de API, resposta que falha validação de schema) conta como tentativa falha — sem distinção fina de tipo de erro, conforme já fraseado de forma genérica no CLAUDE.md
- `cliente_gemini.py` nunca propaga exceção ao chamador em caso de falha persistente — retorna um resultado de falha explícito; quem orquestra (`watcher.py`) decide o fallback (campos indisponíveis no PDF)
