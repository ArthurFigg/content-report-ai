# persistencia

**Ordem:** 1 de 7
**Depende de:** nenhuma

## O que faz
Define o esquema do banco SQLite (tabelas `posts` e `resumos_semanais`) e a camada de acesso a dados — inserir posts, buscar o resumo da semana anterior, checar idempotência por semana e salvar um novo resumo semanal.

## Comportamento
- `modelos.py` define a tabela `posts` com todas as colunas do CSV (ver CLAUDE.md "Colunas do CSV de entrada") mais a coluna calculada `taxa_engajamento`. PK: `post_id` (vem do CSV, assumido globalmente único).
- `modelos.py` define a tabela `resumos_semanais` com: `semana` (identificador, vem do nome do arquivo — PK/UNIQUE), `reach_total`, `engajamento_total`, `taxa_engajamento_semanal`, `quantidade_posts`, `melhor_post_id` (FK para `posts.post_id`), `pior_post_id` (FK para `posts.post_id`).
- Ao iniciar a aplicação, `create_all()` cria as tabelas em `banco/historico.db` se ainda não existirem (sem Alembic, conforme regra global do projeto para SQLite em dev).
- `repositorio.inserir_posts(posts, semana)` insere a lista de posts daquela semana na tabela `posts`.
- `repositorio.buscar_resumo_anterior()` retorna o resumo mais recente já salvo em `resumos_semanais` (o de maior `semana`), ou `None` se a tabela estiver vazia (primeira semana processada, sem histórico).
- `repositorio.semana_ja_processada(semana)` retorna `True`/`False` checando se já existe uma linha em `resumos_semanais` para aquela semana — é a base de dados para a checagem de idempotência (a decisão de rejeitar o arquivo inteiro é responsabilidade do `watcher.py`, não deste módulo).
- `repositorio.salvar_resumo_semanal(...)` insere uma nova linha em `resumos_semanais`, incluindo `melhor_post_id` e `pior_post_id`.
- Se `salvar_resumo_semanal` for chamado para uma `semana` que já existe (constraint UNIQUE violada), a inserção falha com erro de integridade do banco — essa é uma rede de segurança; a checagem preventiva via `semana_ja_processada` deve ser usada antes para evitar chegar nesse caso no fluxo normal.
- Se `inserir_posts` receber um `post_id` que já existe no banco (colisão inesperada entre semanas), a inserção falha com erro de integridade. Não há tratamento especial aqui — a exceção propaga para a resiliência genérica do `watcher.py` (já definida no CLAUDE.md: loga traceback completo, não move o arquivo, continua vigiando).

## Critérios verificáveis
- [ ] `uv run pytest tests/test_repositorio.py -v` passa
- [ ] Inserir uma lista de posts via `inserir_posts` e consultar de volta retorna os mesmos dados, incluindo `taxa_engajamento` calculada corretamente para cada post
- [ ] `buscar_resumo_anterior()` retorna `None` quando `resumos_semanais` está vazia
- [ ] `buscar_resumo_anterior()` retorna o resumo da semana mais recente salva, quando há histórico de múltiplas semanas
- [ ] `semana_ja_processada()` retorna `True` para uma semana já salva e `False` para uma semana nova
- [ ] `salvar_resumo_semanal()` persiste `melhor_post_id` e `pior_post_id` corretamente, recuperáveis via JOIN com `posts`
- [ ] Chamar `salvar_resumo_semanal()` duas vezes para a mesma `semana` levanta um erro de integridade na segunda chamada (confirma que o banco protege mesmo se a checagem preventiva for ignorada)

## Módulos afetados
- `src/persistencia/modelos.py` (novo) — define `posts` e `resumos_semanais` via SQLAlchemy, com tipos genéricos (sem dialeto Postgres), `create_all` para dev
- `src/persistencia/repositorio.py` (novo) — `inserir_posts`, `buscar_resumo_anterior`, `semana_ja_processada`, `salvar_resumo_semanal`
- `banco/historico.db` (novo, gerado em runtime pelo `create_all`)

## Não mexer
- `src/ingestao/`, `src/processamento/` — não existem ainda (specs futuras); `repositorio.py` não deve importar nada deles
- `src/ia/`, `src/relatorio/`, `src/entrega/`, `src/watcher.py` — fora de escopo desta spec
- `ferramentas_dev/` — gerador de dados sintéticos é uma spec separada

## Decisões tomadas
- PK de `posts` → `post_id` direto do CSV (não surrogate autoincrement), assumindo unicidade global garantida pelo Meta (e pelo gerador de dados sintéticos)
- Referência ao melhor/pior post em `resumos_semanais` → FK (`melhor_post_id`, `pior_post_id`) para `posts`, não denormalizado
- `pior_post_id` adicionado ao schema — o CLAUDE.md ("Esquema do banco") mencionava que `calculo_metricas.py` calcula o pior post, mas só listava coluna para o melhor. **Sugestão: atualizar essa seção do CLAUDE.md via `/auditar-claude-md` para registrar `pior_post_id` oficialmente.**
- ORM: SQLAlchemy, tipos genéricos, `create_all` no startup, sem Alembic (regra global do projeto para SQLite em desenvolvimento)
- Colisão de `post_id` entre semanas (erro de integridade) não tem tratamento especial em `repositorio.py` — propaga para a resiliência genérica já definida no `watcher.py`
- **[Nota do `/spec-review`]** A spec `07_watcher` identificou duas extensões pontuais necessárias em `repositorio.py`, ainda não cobertas aqui: (1) suporte a transação compartilhada entre `inserir_posts` e `salvar_resumo_semanal`; (2) uma função `listar_resumos_semanais()` (retorna todas as semanas já salvas, ordenadas, com `semana` e `reach_total`) — necessária para `grafico.py` (spec `05_relatorio_pdf`) montar a evolução de múltiplas semanas, já que `buscar_resumo_anterior()` retorna só o registro mais recente. Ambas devem ser implementadas junto com `07_watcher`.
- Coluna `semana` adicionada à tabela `posts` (string, não-PK, índice simples) — decisão tomada durante a implementação: o parâmetro `semana` em `inserir_posts(posts, semana)` precisava ser persistido para permitir consultar todos os posts de uma semana sem re-derivar de `Post Date`. CLAUDE.md ("Esquema do banco") atualizado para refletir essa coluna.

---
**Status:** concluida em 2026-06-22
