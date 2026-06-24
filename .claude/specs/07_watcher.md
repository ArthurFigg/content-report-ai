# watcher

**Ordem:** 7 de 7
**Depende de:** 01_persistencia, 02_gerador_dados_sinteticos, 03_ingestao_e_metricas, 04_ia_gemini, 05_relatorio_pdf, 06_entrega_email (orquestra todos)

## O que faz
Orquestra o pipeline completo — vigia a pasta de entrada, dispara o processamento de cada CSV na ordem certa, e garante que o sistema continue rodando mesmo diante de falhas inesperadas.

## Comportamento
- Ao iniciar, valida que todas as variáveis de ambiente obrigatórias estão configuradas (`GEMINI_API_KEY`, `GEMINI_MODEL`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_DESTINATARIO`, `NOME_NEGOCIO`) — se faltar alguma, falha imediatamente com mensagem clara, antes de começar a vigiar a pasta.
- Configura logging: handler de arquivo (`logs/pipeline.log`) + handler de console, nível INFO para fluxo normal, WARNING/ERROR para falhas e retries (conforme já definido no CLAUDE.md).
- Ao iniciar, escaneia `dados/entrada/` por CSVs já presentes, ordena por semana (ascendente, derivada do nome do arquivo) e processa cada um nessa ordem, antes de começar a vigiar novos eventos — garante que nenhum arquivo solto durante downtime do watcher fique esquecido, e que a ordem cronológica das semanas seja respeitada (necessário para a "semana anterior" ficar correta entre processamentos sequenciais).
- A partir daí, vigia `dados/entrada/` via watchdog; ao detectar um arquivo novo, espera o tamanho estabilizar (debounce, já definido no CLAUDE.md) antes de processar.
- Para cada arquivo (do scan inicial ou de um evento novo), executa o pipeline completo na ordem já definida no CLAUDE.md ("Fluxo do pipeline"): `leitor_csv` → identifica semana pelo nome → checa idempotência (`repositorio.semana_ja_processada`) → `calculo_metricas` → `repositorio.buscar_resumo_anterior` (leitura simples, fora de transação) → `comparacao` → `cliente_gemini` (com retry) → **transação única e breve**: `repositorio.inserir_posts` + `repositorio.salvar_resumo_semanal` → `grafico` (usa `repositorio.listar_resumos_semanais`, fora da transação de escrita) → `gerador_pdf` → `email_sender` (com retry).
- A transação de banco só abre depois que `calculo_metricas`, `comparacao` e a chamada à IA (com todas as tentativas de retry) já terminaram — evita manter uma transação aberta durante uma chamada de rede externa (latência de até ~14s com os 3 retries). A transação cobre só `inserir_posts` + `salvar_resumo_semanal`, e nada mais.
- A inserção dos posts e o salvamento do resumo semanal ocorrem dentro dessa transação única — se qualquer exceção ocorrer entre essas duas operações, a transação é revertida por completo: nenhum post nem resumo daquela semana fica persistido, e o arquivo pode ser reprocessado depois sem colisão de `post_id`.
- Se a validação do CSV falhar: loga erro específico, não move o arquivo, segue para o próximo arquivo da fila/vigilância.
- Se a semana já foi processada (idempotência): loga aviso, não insere nada, não reenvia email, não move o arquivo, segue.
- Se qualquer exceção não prevista ocorrer durante o processamento de um arquivo: loga o traceback completo em ERROR, não move o arquivo, e o watcher continua vigiando a pasta normalmente (nunca derruba o processo por causa de um arquivo problemático).
- Em caso de sucesso completo (até o email ser enviado, ou pelo menos o PDF salvo se o email falhar persistentemente), move o CSV processado para `dados/processados/`.
- Antes de `inserir_posts`, converte cada `PostValidado` (formato de `ingestao/`) para `DadosPost` (formato de `persistencia/modelos.py`) — adaptação atribuída a `watcher.py` pela spec `03_ingestao_e_metricas`, já que os dois módulos mantêm dataclasses desacopladas de propósito. Da mesma forma, converte o `ResumoSemanal` retornado por `buscar_resumo_anterior` em `TotaisAnteriores` antes de chamar `comparacao.calcular_variacao`.
- Se `cliente_gemini.gerar_interpretacao()` retornar `None` (falha persistente, contrato definido em `04_ia_gemini`), `watcher.py` passa `None` adiante para `gerador_pdf.py` sem tentar reformular ou repetir a chamada — `gerador_pdf.py` decide a renderização de indisponibilidade (spec `05_relatorio_pdf`).

## Critérios verificáveis
- [ ] `uv run pytest tests/test_watcher.py -v` passa
- [ ] Com 1 CSV válido já presente em `dados/entrada/` antes do watcher iniciar, ele é processado automaticamente na inicialização (sem precisar de um novo evento de criação)
- [ ] Com 2+ CSVs de semanas diferentes presentes na inicialização, são processados em ordem cronológica de semana (não na ordem arbitrária do sistema de arquivos)
- [ ] Uma falha simulada e não prevista no meio do pipeline (mock lança exceção genérica) é logada com traceback, o watcher continua rodando, e nenhum dado parcial fica no banco (posts órfãos sem resumo)
- [ ] Variável de ambiente obrigatória ausente impede o watcher de iniciar, com mensagem de erro clara
- [ ] Um CSV processado com sucesso é movido de `dados/entrada/` para `dados/processados/`
- [ ] Com mocks que registram ordem de chamadas, confirma-se que `cliente_gemini` (incluindo retries) é chamado antes de `inserir_posts`/`salvar_resumo_semanal` — a transação de escrita não engloba a chamada de rede à IA

## Módulos afetados
- `src/watcher.py` (novo) — orquestração completa, debounce, scan inicial, resiliência, logging
- `src/persistencia/repositorio.py` (extensão pontual, spec `01_persistencia`) — duas adições: (1) suporte a transação compartilhada entre `inserir_posts` e `salvar_resumo_semanal` (ex: aceitar uma sessão externa, ou expor uma função combinada que faz as duas operações dentro de uma única transação); (2) `listar_resumos_semanais()`, retornando todas as semanas já salvas (`semana`, `reach_total`), ordenadas — usada por `grafico.py` (spec `05_relatorio_pdf`) para a evolução de múltiplas semanas
- `logs/` (criada em runtime)

## Não mexer
- `src/persistencia/modelos.py` — schema não muda; só `repositorio.py` recebe a extensão pontual descrita acima
- `src/ingestao/`, `src/processamento/`, `src/ia/`, `src/relatorio/`, `src/entrega/`, `src/retry.py` — specs `02`-`06`, já especificadas; `watcher.py` só orquestra, não modifica a lógica interna de nenhum desses módulos
- `ferramentas_dev/` — spec `02_gerador_dados_sinteticos`

## Decisões tomadas
- Validação de variáveis de ambiente obrigatórias no startup, com falha imediata e clara se algo faltar
- Scan inicial de `dados/entrada/` na inicialização, processando arquivos pré-existentes antes de vigiar novos eventos — evita que arquivos soltos durante downtime fiquem esquecidos
- Arquivos pendentes processados em ordem cronológica de semana (ascendente), nunca em ordem arbitrária — necessário para a "semana anterior" ficar correta entre processamentos sequenciais
- Inserção dos posts e salvamento do resumo semanal ocorrem numa única transação de banco — extensão pontual necessária em `repositorio.py` (spec `01_persistencia`), registrada aqui como dependência cross-spec
- Processamento de arquivos é sequencial (um por vez), nunca concorrente — simplicidade e compatibilidade com SQLite (single-writer)
- **[Correção do `/spec-review`]** A transação de escrita (`inserir_posts` + `salvar_resumo_semanal`) só abre depois da chamada à IA, não durante — evita manter o banco com transação aberta ao longo de uma chamada de rede externa com retry (anti-padrão identificado na revisão cruzada com `01_persistencia`)
- **[Correção do `/spec-review`]** `repositorio.py` precisa também de `listar_resumos_semanais()` (não só o suporte a transação) — `grafico.py` (spec `05_relatorio_pdf`) precisa do histórico completo de semanas, e `buscar_resumo_anterior()` só retorna a mais recente
- **[Correção do `/spec-review`]** `watcher.py` é responsável por duas adaptações de dataclass entre camadas, atribuídas a ele por `03_ingestao_e_metricas` mas não explicitadas aqui antes: `PostValidado` → `DadosPost` (antes de `inserir_posts`) e `ResumoSemanal` → `TotaisAnteriores` (antes de `comparacao.calcular_variacao`)
- **[Correção do `/spec-review`]** O retorno `None` de `cliente_gemini.gerar_interpretacao()` (falha persistente, `04_ia_gemini`) é propagado sem alteração para `gerador_pdf.py`, que decide a renderização de indisponibilidade (`05_relatorio_pdf`)
