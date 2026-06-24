# relatorio_pdf

**Ordem:** 5 de 7
**Depende de:** 03_ingestao_e_metricas (consome totais/variação), 04_ia_gemini (consome resumo_executivo/destaques/possivel_causa/recomendacao)

## O que faz
Gera a imagem do gráfico de linha da evolução do Reach total, monta o HTML do relatório semanal e converte para PDF, salvando em `relatorios/`.

## Comportamento
- `grafico.py` recebe uma lista de `(semana, reach_total)` já buscada do banco — via `repositorio.listar_resumos_semanais()` (extensão de `01_persistencia` identificada em `07_watcher`), chamada por `watcher.py`, nunca por `grafico.py` diretamente — e gera um **gráfico de linha com marcador em cada semana** (matplotlib) — padrão de mercado para visualizar tendência ao longo do tempo (pesquisado e confirmado com o usuário).
- Se a lista tiver menos de 2 semanas, `grafico.py` não gera imagem — sinaliza "histórico insuficiente", e o template exibe a mensagem "Histórico insuficiente para mostrar evolução — disponível a partir da 2ª semana" no lugar do gráfico.
- Quando há 2+ semanas, `grafico.py` retorna a imagem como string base64 (PNG), sem salvar arquivo temporário em disco.
- `gerador_pdf.py` monta o HTML via Jinja2 (template `relatorio.html`) seguindo a ordem de blocos já definida no CLAUDE.md ("Layout do PDF"), embutindo a imagem do gráfico como data URI (`<img src="data:image/png;base64,...">`) quando disponível.
- Cabeçalho usa `NOME_NEGOCIO` (`.env`) e o período da semana (segunda a domingo, formato `dd/mm a dd/mm/aaaa`).
- Números formatados com separador de milhar (padrão pt-BR).
- Card de variação % exibe "sem base de comparação" no lugar do número quando a variação calculada for `null` (semana anterior com valor 0).
- Bloco "Possível causa" é omitido inteiramente quando `possivel_causa` for `null` (sempre o caso na primeira semana, por definição do schema da IA).
- Se `gerador_pdf.py` receber `resposta_ia=None` (contrato de falha persistente definido em `04_ia_gemini`: `gerar_interpretacao()` retorna `None`), os blocos de Resumo executivo, Destaques, Possível causa e Recomendação exibem "Resumo indisponível nesta semana" (ou equivalente por bloco) no lugar do conteúdo da IA — os números-chave e o gráfico continuam normais, pois são calculados em Python, não pela IA.
- `gerador_pdf.py` converte o HTML final em PDF via xhtml2pdf e salva em `relatorios/relatorio_<semana>.pdf`, criando a pasta `relatorios/` automaticamente se não existir.

## Critérios verificáveis
- [ ] `uv run pytest tests/test_gerador_pdf.py -v` passa
- [ ] Com histórico de 1 semana, o PDF gerado contém a mensagem de histórico insuficiente, não uma imagem de gráfico
- [ ] Com histórico de 2+ semanas, o PDF contém uma imagem embutida (data URI) no bloco de gráfico, em formato de linha com marcadores
- [ ] Um PDF gerado com `possivel_causa=null` não contém o bloco "Possível causa" no HTML/PDF final
- [ ] Um PDF gerado com variação `null` no card correspondente exibe "sem base de comparação" em vez de um número
- [ ] Um PDF gerado com campos de IA marcados indisponíveis exibe a mensagem de indisponibilidade nos 4 blocos de IA, mantendo números-chave e gráfico normais
- [ ] O arquivo PDF é salvo em `relatorios/relatorio_<semana>.pdf`, e a pasta é criada automaticamente se não existir

## Módulos afetados
- `src/relatorio/grafico.py` (novo)
- `src/relatorio/gerador_pdf.py` (novo)
- `src/relatorio/templates/relatorio.html` (novo)

## Não mexer
- `src/persistencia/`, `src/ingestao/`, `src/processamento/`, `src/ia/`, `src/retry.py` — specs `01`-`04`, já especificadas; este módulo recebe dados já calculados/buscados, não chama `repositorio.py` nem `cliente_gemini.py` diretamente
- `ferramentas_dev/` — spec `02_gerador_dados_sinteticos`
- `src/entrega/`, `src/watcher.py` — fora de escopo desta spec

## Decisões tomadas
- Tipo de gráfico: linha com marcador por semana — confirmado por pesquisa (line charts são o padrão de mercado para tendência ao longo do tempo; bar charts são para comparação entre categorias)
- Imagem do gráfico embutida como base64/data URI, sem arquivo temporário em disco
- Gráfico substituído por mensagem de "histórico insuficiente" quando há menos de 2 semanas de dados
- Mensagens específicas por tipo de ausência: variação `null` → "sem base de comparação"; `possivel_causa` `null` → bloco omitido; falha de IA → mensagem de indisponibilidade nos 4 blocos de IA
- `grafico.py` e `gerador_pdf.py` são funções que recebem dados já calculados/buscados — não acessam banco nem API da IA diretamente, mantendo a separação de camadas já estabelecida no projeto
- **[Correção do `/spec-review`]** A lista de histórico para o gráfico vem de `repositorio.listar_resumos_semanais()`, uma função que ainda não existia na spec `01_persistencia` original — registrada como extensão pontual lá e em `07_watcher`
- Números formatados em padrão pt-BR (separador de milhar)
- Pasta `relatorios/` é criada automaticamente se não existir
- **[Correção do `/spec-review`]** `gerador_pdf.py` recebe `resposta_ia: RespostaIA | None` (tipo definido em `04_ia_gemini`) — `None` já é o próprio sinal de indisponibilidade, sem campo ou wrapper intermediário; `watcher.py` passa o retorno de `gerar_interpretacao()` direto, sem tradução
