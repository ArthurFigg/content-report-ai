# Relatório Semanal de Performance de Conteúdo com Insight Automático

## Objetivo

Sistema que processa métricas semanais de conteúdo do Instagram (formato realista de exportação do Meta Business Suite), calcula variação semana a semana, usa IA (Gemini) para gerar interpretação e recomendação em linguagem natural, monta um PDF com gráfico e envia automaticamente por email — sem intervenção manual além de soltar o arquivo numa pasta.

Público-alvo do relatório: gestor de pequeno negócio ou criador de conteúdo, sem jargão técnico de marketing.

Este projeto fecha uma lacuna de portfólio: os projetos anteriores automatizam tarefas técnicas/pessoais (monitor de hardware, gerenciador de clipboard, scraper de preços); este automatiza um processo que existe de fato em qualquer operação de marketing/conteúdo — a montagem e distribuição de relatório periódico, hoje feita manualmente por um analista.

## Escopo do MVP

- Uma rede social: Instagram apenas (TikTok/YouTube ficam para evolução futura demonstrável)
- Dado sintético, no formato realista de exportação do Meta Business Suite (seção Content/post-level) — não dado inventado livremente, e não conexão real via OAuth/API
- Disparo por evento: sistema observa uma pasta e processa automaticamente quando um CSV novo é solto ali (sem agendamento por horário, sem clique manual)
- Histórico em SQLite (posts individuais + resumos semanais), usado para calcular variação semana a semana
- IA (Gemini) usada apenas para interpretação/julgamento (resumo, destaque, possível causa, recomendação) — nunca para cálculo, que é feito inteiramente em pandas antes de chamar a IA
- Saída: PDF (gerado via xhtml2pdf a partir de template HTML/Jinja2) enviado por email com anexo (SMTP)
- Primeira semana processada (sem histórico prévio): relatório apresenta só números absolutos, sem variação, sem causa inventada
- **Sem frontend no MVP**: a única interface com o usuário final é o próprio PDF recebido por email. O PDF já cumpre o papel de interface para o público-alvo (gestor de pequeno negócio); um frontend dobraria o escopo (autenticação, hospedagem, estado) sem ganho para o objetivo do projeto. Evolução futura com frontend (ex: histórico de relatórios navegável) fica fora do MVP, não é tarefa pendente.

## Stack

- **Linguagem**: Python
- **Processamento de dados**: pandas
- **IA**: Gemini API via SDK `google-genai` (SDK unificado atual do Google), com structured output (`response_schema` via Pydantic + `response_mime_type="application/json"`, schema forçado, não apenas instrução textual). Modelo configurável via `GEMINI_MODEL` (`.env`, com valor padrão no código) — nomes de modelo Gemini mudam com frequência, por isso não é fixado aqui. Chave via `GEMINI_API_KEY` (`.env`).
- **Banco**: SQLite
- **Geração de PDF**: xhtml2pdf + Jinja2 (template HTML/CSS) + matplotlib (gráfico embutido como imagem, **gráfico de linha com marcador por semana** — padrão de mercado para tendência ao longo do tempo) — xhtml2pdf escolhido no lugar de WeasyPrint por não depender de bibliotecas nativas GTK/Pango, que não funcionam out-of-the-box no Windows
- **Envio de email**: smtplib + email.mime (anexo), especificamente Gmail (`smtp.gmail.com:465` via `smtplib.SMTP_SSL`), autenticando com `SMTP_USER` + `SMTP_PASSWORD` (senha de app, `.env`)
- **Retry com backoff**: módulo compartilhado `src/retry.py` (3 tentativas, 2s/4s/8s), reutilizado por `cliente_gemini.py` e `email_sender.py` — evita duplicar a mesma lógica nos dois lugares
- **Disparo por evento**: watchdog (observa a pasta de entrada)
- **Testes**: pytest (seguindo o padrão já usado em outros projetos do portfólio)
- **Gerenciador de dependências**: `uv` + `pyproject.toml` (alinhado à regra global — sem `requirements.txt` avulso)

## Estrutura de pastas sugerida

```
relatorio_conteudo/
├── PROJETO.md
├── README.md
├── pyproject.toml
├── .env.example
├── dados/
│   ├── entrada/               # pasta observada pelo watchdog — usuário solta o CSV aqui
│   └── processados/           # CSVs movidos para aqui após processamento com sucesso
├── logs/
│   └── pipeline.log          # log do pipeline (INFO para fluxo normal, WARNING/ERROR para falhas e retries)
├── relatorios/
│   └── relatorio_AAAA-MM-DD.pdf   # todo PDF gerado é salvo aqui, independente do envio de email ter sucesso
├── src/
│   ├── __init__.py
│   ├── watcher.py            # observa a pasta, dispara o pipeline ao detectar CSV novo
│   ├── retry.py              # retry com backoff exponencial compartilhado (cliente_gemini.py, email_sender.py)
│   ├── ingestao/
│   │   ├── __init__.py
│   │   └── leitor_csv.py     # lê e valida o CSV no formato Meta Business Suite
│   ├── processamento/
│   │   ├── __init__.py
│   │   ├── calculo_metricas.py   # totais, médias, melhor/pior post (pandas)
│   │   └── comparacao.py         # variação semana atual vs. anterior
│   ├── persistencia/
│   │   ├── __init__.py
│   │   ├── modelos.py         # esquema das tabelas posts / resumos_semanais
│   │   └── repositorio.py     # inserir posts, salvar/buscar resumo semanal
│   ├── ia/
│   │   ├── __init__.py
│   │   ├── prompt.py          # template do prompt
│   │   └── cliente_gemini.py  # chamada à API com structured output
│   ├── relatorio/
│   │   ├── __init__.py
│   │   ├── grafico.py         # gera imagem do gráfico (matplotlib)
│   │   ├── templates/
│   │   │   └── relatorio.html # template Jinja2 do PDF
│   │   └── gerador_pdf.py     # monta HTML final + xhtml2pdf
│   └── entrega/
│       ├── __init__.py
│       └── email_sender.py    # monta e envia o email com anexo
├── ferramentas_dev/
│   └── gerador_dados_sinteticos.py   # NÃO faz parte do produto final — ver regra abaixo
├── tests/
│   ├── test_leitor_csv.py
│   ├── test_calculo_metricas.py
│   ├── test_comparacao.py
│   ├── test_repositorio.py
│   ├── test_gerador_pdf.py
│   ├── test_cliente_gemini.py   # mocka a chamada à API Gemini (payload enviado, parsing do retorno, retry/falha)
│   ├── test_email_sender.py     # mocka smtplib (anexo, destinatário)
│   └── test_watcher.py          # testa a lógica de detecção de arquivo novo disparando o pipeline mockado
└── banco/
    └── historico.db
```

## Regra de escopo importante: gerador de dados sintéticos

O projeto finge que os dados vêm de uma exportação real do Instagram. Por isso, o script em `ferramentas_dev/gerador_dados_sinteticos.py`:

- **NÃO é parte do produto final** — é uma ferramenta de apoio ao desenvolvimento
- Deve ficar isolado numa pasta separada (`ferramentas_dev/`), claramente fora do pacote principal (`src/`)
- Roda **uma única vez**, gerando de uma vez só os CSVs equivalentes a 1 export por semana, por 1 mês (~4 arquivos)
- Depois de gerar os dados de teste, deve ser **excluído** (junto com a pasta `ferramentas_dev/`) antes da entrega/postagem final do projeto
- Lógica do gerador: perfil base de métricas com variação plausível em torno da média; coerência entre métricas no mesmo post (Likes/Comments/Shares/Saves proporcionais ao Reach); Reels com Reach tendencialmente maior que post estático; 1-2 picos plantados de propósito (post que "viralizou"); pequena tendência entre semanas (não tudo estável) — sem inventar estatística complexa, só lógica de faixas de valores

## Colunas do CSV de entrada (formato Meta Business Suite — Content)

| Coluna | Descrição | Aplicável a |
|---|---|---|
| Post ID | identificador do post | todos |
| Post Date | data de publicação | todos |
| Post Type | Photo / Video / Reel / Carousel | todos |
| Post Text | legenda (pode ser vazio/truncado) | todos |
| Reach | alcance único | todos |
| Impressions | impressões totais | todos |
| Likes and Reactions | curtidas/reações | todos |
| Comments | comentários | todos |
| Shares | compartilhamentos | todos |
| Saves | salvamentos | todos |
| Link Clicks | cliques no link (se houver CTA) | todos |
| Plays | reproduções de vídeo | apenas Reels/vídeo — vazio em posts estáticos |
| Watch Time | tempo de exibição total | apenas Reels/vídeo — vazio em posts estáticos |
| Retention | retenção/quanto assistiram | apenas Reels/vídeo — vazio em posts estáticos |

O sistema deve lidar corretamente com campos vazios/não aplicáveis dependendo do `Post Type` (dado esparso é esperado e realista, não erro).

### Validação do CSV

`leitor_csv.py` valida colunas obrigatórias (Post ID, Post Date, Post Type, Reach, Impressions, Likes and Reactions, Comments, Shares, Saves) e tipos básicos antes de seguir. "Tipos básicos" inclui: Post Date parseável como data válida; Post Type dentro do enum {Photo, Video, Reel, Carousel}; valores numéricos (Reach, Impressions, Likes and Reactions, Comments, Shares, Saves, Link Clicks quando presente) não-negativos; Post ID único dentro do próprio arquivo; e pelo menos 1 linha de dados (CSV com cabeçalho mas zero posts é inválido). Se a validação falhar por qualquer um desses motivos (coluna obrigatória faltando, tipo inválido, Post Type fora do enum, valor negativo, Post ID duplicado no arquivo, zero linhas, arquivo corrompido), rejeita o arquivo inteiro: loga o erro específico (qual coluna/linha) e aborta o pipeline para aquele arquivo, sem inserir nada no banco e **sem mover** o arquivo da pasta de entrada (fica em `dados/entrada/` para o usuário corrigir e o watcher não tenta reprocessar sozinho, pois não há novo evento de criação). Se o processamento for bem-sucedido, o CSV é movido para `dados/processados/`.

### Resiliência a falha não prevista

Se qualquer etapa do pipeline lançar uma exceção não prevista pelos casos já tratados (CSV inválido, semana duplicada, falha de Gemini/SMTP), `watcher.py` captura essa exceção no nível do processamento do arquivo, loga o traceback completo em ERROR (nunca silenciosamente — sem `except Exception: pass`) e continua vigiando `dados/entrada/` normalmente. O arquivo problemático não é movido para `dados/processados/`, ficando disponível para investigação manual. Um erro isolado nunca derruba o processo do watcher.

### Tratamento de arquivo em escrita parcial

`watcher.py` não dispara o processamento imediatamente ao detectar o evento de criação do arquivo. Espera o tamanho do arquivo estabilizar (confere o tamanho, espera um intervalo curto, confere de novo — só processa quando o tamanho parar de mudar), evitando ler um CSV que ainda está sendo copiado/escrito na pasta.

### Convenção de nome do arquivo CSV de entrada

A semana à qual um CSV pertence é determinada **pelo nome do arquivo**, não pelas datas dentro do CSV nem pela ordem de chegada. Convenção: `semana_AAAA-MM-DD.csv`, onde a data é a segunda-feira de início da semana (ex: `semana_2026-06-15.csv`). `ferramentas_dev/gerador_dados_sinteticos.py` deve gerar os arquivos seguindo essa convenção.

## Esquema do banco

**Tabela `posts`**: espelha o CSV, uma linha por post, inserida a cada processamento, mais a coluna calculada `taxa_engajamento` (não vem do CSV — ver fórmula abaixo) e a coluna `semana` (identificador derivado do nome do arquivo, mesmo valor passado para `inserir_posts(posts, semana)` — não recalculado a partir de `Post Date`, permite consultar todos os posts de uma semana sem re-derivar do CSV). PK: `post_id` (vem do CSV, assumido globalmente único — nunca se repete entre semanas).

`calculo_metricas.py` define "melhor/pior post da semana" pela métrica **Reach** (alcance único) — não por engajamento nem taxa de engajamento.

**Engajamento total** = Likes and Reactions + Comments + Shares + Saves (soma simples, valores vazios tratados como 0). Não inclui Link Clicks (específico de CTA, nem todo post tem) nem Plays/Watch Time/Retention (métricas de vídeo, unidades diferentes — não são contagem de interação direta).

**Taxa de engajamento** = engajamento ÷ Reach × 100, calculada em dois níveis por `calculo_metricas.py`:
- **Por post** (coluna `taxa_engajamento` em `posts`): engajamento do post ÷ Reach do post × 100
- **Semanal agregada** (coluna `taxa_engajamento_semanal` em `resumos_semanais`): engajamento total da semana ÷ Reach total da semana × 100
- **Reach = 0**: taxa de engajamento = 0 (não null, não exceção) — sem alcance, não há engajamento gerado por ele

O post com a maior `taxa_engajamento` da semana é identificado por `calculo_metricas.py` e enviado no payload para a IA, que pode gerar um destaque do tipo `melhor_taxa_engajamento` (ver "Schema de saída da IA" e "Destaques" no layout do PDF) — distinto do destaque de `melhor_post` (por Reach), já que podem ser posts diferentes.

**Tabela `resumos_semanais`**: uma linha por semana processada — identificador da semana (derivado do nome do arquivo, ver convenção acima, PK/UNIQUE), Reach total, engajamento total (fórmula acima), taxa de engajamento semanal (fórmula acima), quantidade de posts, **melhor post da semana** (`melhor_post_id`, FK para `posts`) e **pior post da semana** (`pior_post_id`, FK para `posts`) — ambos por Reach, consistente com o critério já definido para `calculo_metricas.py`. É essa tabela que sustenta a comparação semana atual vs. anterior (consulta direta, sem recalcular a partir de `posts` toda vez).

A variação percentual (semana atual vs. anterior) é calculada apenas para **Reach total** e **Engajamento total**. A taxa de engajamento semanal não tem variação própria — é derivada das outras duas, então uma terceira variação seria redundante.

`repositorio.listar_resumos_semanais()` retorna todas as semanas já salvas (`semana`, `reach_total`), ordenadas — usada por `grafico.py` para montar a evolução de múltiplas semanas (diferente de `buscar_resumo_anterior()`, que retorna só a mais recente).

**Atomicidade**: a inserção dos posts (`inserir_posts`) e o salvamento do resumo semanal (`salvar_resumo_semanal`) ocorrem dentro de uma única transação de banco, que só abre **depois** que a chamada à IA (com todos os retries) já terminou — nunca durante a chamada de rede externa. Se qualquer exceção ocorrer entre as duas operações, a transação é revertida por completo: nenhum post nem resumo daquela semana fica persistido, evitando posts "órfãos" sem resumo correspondente em caso de falha no meio do processamento.

### Idempotência

Antes de inserir, `repositorio.py` verifica se já existe um resumo para aquele identificador de semana. Se já existir, o pipeline **rejeita o arquivo**: loga um aviso claro, não insere posts duplicados, não recalcula o resumo e não reenvia email. Não há reprocessamento automático — se o usuário precisar corrigir uma semana já processada, isso é tratado fora do escopo do MVP (intervenção manual no banco).

## Fluxo do pipeline (ponta a ponta)

1. Usuário solta um CSV novo em `dados/entrada/`
2. `watcher.py` (watchdog) detecta o arquivo novo e dispara o pipeline
3. `leitor_csv.py` lê e valida o CSV (ver "Validação do CSV" acima) — se inválido, aborta e loga
4. Identifica a semana pelo nome do arquivo e checa idempotência (ver "Idempotência" acima) — se já processada, rejeita e loga
5. `calculo_metricas.py` calcula totais, médias, melhor/pior post da semana (por Reach), o post com maior taxa de engajamento, e taxa de engajamento por post e agregada da semana (pandas)
6. `repositorio.buscar_resumo_anterior()` busca o resumo da semana anterior em `resumos_semanais` (leitura simples, fora de transação)
7. `comparacao.py` calcula variação percentual de Reach total e de Engajamento total (ou identifica que é a primeira semana, sem histórico)
8. Um payload pequeno (totais + variação, ou só totais se for a primeira semana) é montado e enviado para a IA via `cliente_gemini.py`, usando o prompt de `prompt.py` e o schema de structured output. Em caso de falha (timeout, rate limit, erro de API), tenta novamente com backoff exponencial (3 tentativas: 2s, 4s, 8s); se persistir, segue o pipeline com os campos de IA marcados como indisponíveis no relatório
9. A IA retorna o JSON: `resumo_executivo`, `destaques`, `possivel_causa` (ou `null` na primeira semana), `recomendacao`
10. **Transação única e breve** (só agora, depois da IA já ter respondido ou falhado definitivamente): `repositorio.inserir_posts()` insere os posts em `posts` e `repositorio.salvar_resumo_semanal()` salva o novo resumo em `resumos_semanais` (vira "anterior" na próxima rodada) — ver "Atomicidade" em "Esquema do banco"
11. `grafico.py` gera a imagem da evolução do Reach total ao longo das semanas já salvas, usando `repositorio.listar_resumos_semanais()` (fora da transação de escrita)
12. `gerador_pdf.py` monta o HTML (Jinja2) com cabeçalho (usando `NOME_NEGOCIO` do `.env`) → resumo executivo → números-chave → gráfico → destaques → possível causa → recomendação, converte para PDF via xhtml2pdf e salva em `relatorios/relatorio_<semana>.pdf`
13. `email_sender.py` envia o PDF por email, anexado, para `EMAIL_DESTINATARIO` (variável de ambiente). Em caso de falha de envio (SMTP), tenta novamente com backoff exponencial (3 tentativas: 2s, 4s, 8s); se persistir, loga o erro — o PDF já está salvo em `relatorios/` desde o passo 12, disponível para envio manual posterior

## Schema de saída da IA (structured output)

```json
{
  "resumo_executivo": "string — 1-2 frases, visão geral da semana em linguagem simples",
  "destaques": [
    {
      "tipo": "string — ex: 'melhor_post', 'melhor_taxa_engajamento', 'maior_queda', 'maior_alta'",
      "descricao": "string — ex: 'Seu Reel de terça teve 3x o alcance médio'"
    }
  ],
  "possivel_causa": "string ou null — hipótese plausível pra variação; null se não houver semana anterior",
  "recomendacao": "string — 1 ação prática e específica para a próxima semana"
}
```

## Prompt da IA (base)

```
Você é um analista de marketing de conteúdo. Você recebe métricas semanais
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

Responda seguindo exatamente o schema fornecido.
```

## Layout do PDF (ordem dos blocos)

1. Cabeçalho — nome do perfil/negócio (fictício, vem de `NOME_NEGOCIO` no `.env`), período da semana
2. Resumo executivo (IA) — destaque, logo após o cabeçalho
3. Números-chave (Python/pandas) — cards com Reach total, Engajamento total, Taxa de engajamento semanal, variação % de Reach e variação % de Engajamento. Se a variação for `null` (semana anterior com valor 0), o card exibe "sem base de comparação" no lugar do número.
4. Gráfico — evolução do Reach total ao longo das semanas (consistente com o critério de melhor/pior post), **em formato de linha com marcador por semana** (padrão de mercado para tendência ao longo do tempo), posicionado aqui (não no fim) para reforçar visualmente o resumo executivo. Imagem embutida como base64/data URI, sem arquivo temporário em disco. Com menos de 2 semanas de histórico, o bloco exibe "Histórico insuficiente para mostrar evolução — disponível a partir da 2ª semana" em vez do gráfico.
5. Destaques (IA) — lista curta (melhor post por Reach, melhor post por taxa de engajamento, queda notável)
6. Possível causa (IA) — rotulada como "possível explicação", separada visualmente para não parecer fato absoluto. Omitida inteiramente quando `possivel_causa` for `null` (sempre o caso na primeira semana).
7. Recomendação (IA) — destacada em caixa/negrito

Se os campos da IA estiverem marcados como indisponíveis (falha persistente da Gemini), os blocos 2, 5, 6 e 7 exibem uma mensagem de indisponibilidade (ex: "Resumo indisponível nesta semana") no lugar do conteúdo da IA — os números-chave (bloco 3) e o gráfico (bloco 4) continuam normais, pois são calculados em Python, não pela IA.

## Setup do ambiente

Decisões tomadas no setup inicial (antes de implementar a spec `01_persistencia`):

- **Python 3.12** — escolhido sobre o 3.14 (instalado localmente) e sobre o 3.13 disponível via `uv`. Dependências que só entram em specs futuras (`matplotlib`, `xhtml2pdf`, em `05_relatorio_pdf`) têm histórico de suporte mais maduro em 3.12 do que em releases recentes; evita risco de incompatibilidade descoberto tarde.
- **Dependências de produção**: `sqlalchemy>=2.0,<3.0` (spec `01_persistencia`) e `pandas>=2.0,<3.0` (adicionada na spec `03_ingestao_e_metricas`, usada em `calculo_metricas.py`). Demais dependências da stack ficam de fora até a spec correspondente ser implementada:
  - `google-genai` → spec `04_ia_gemini`
  - `xhtml2pdf`, `jinja2`, `matplotlib` → spec `05_relatorio_pdf`
  - `watchdog` → spec `07_watcher`
- **Dependência de dev**: `pytest>=8.0,<9.0`
- **Estrutura criada**: `src/__init__.py`, `src/persistencia/__init__.py`, `tests/`, `banco/` (`banco/historico.db` é gerado em runtime pelo `create_all`, não é versionado — ver `.gitignore`)
- **`.env.example`**: já inclui todas as 6 variáveis da stack completa (`GEMINI_API_KEY`, `GEMINI_MODEL`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_DESTINATARIO`, `NOME_NEGOCIO`), mesmo as usadas só em specs futuras — documentar não tem custo de instalação, só de leitura

## Primeiros passos de desenvolvimento

1. Montar a estrutura de pastas e ambiente (`uv`, `pyproject.toml`, `.env.example` com `GEMINI_API_KEY`, `GEMINI_MODEL`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_DESTINATARIO` e `NOME_NEGOCIO`)
2. Escrever `ferramentas_dev/gerador_dados_sinteticos.py` e gerar os 4 CSVs de teste (~1 mês), seguindo a convenção de nome `semana_AAAA-MM-DD.csv`
3. Implementar `leitor_csv.py` + `calculo_metricas.py` (melhor/pior post por Reach, engajamento total, taxa de engajamento por post e semanal), com testes (pytest) usando os CSVs sintéticos, incluindo casos de CSV inválido
4. Implementar o esquema do banco (`modelos.py`, `repositorio.py`, incluindo as colunas `taxa_engajamento` e `taxa_engajamento_semanal`) e testar inserção/consulta de posts e resumos semanais, incluindo o caso de idempotência (semana já processada)
5. Implementar `comparacao.py` (variação semana atual vs. anterior de Reach total e Engajamento total, incluindo o caso "primeira semana sem histórico")
6. Implementar `cliente_gemini.py` + `prompt.py` com structured output e retry com backoff exponencial (3 tentativas: 2s/4s/8s), testando os dois cenários (com/sem comparação) e o caso de falha persistente (mockado)
7. Implementar `grafico.py` (matplotlib) e o template `relatorio.html` (Jinja2), depois `gerador_pdf.py` (xhtml2pdf), salvando sempre em `relatorios/`
8. Implementar `email_sender.py` (SMTP com anexo, retry com mesmo backoff de 2s/4s/8s), testando com mock de smtplib, incluindo o caso de falha persistente
9. Implementar `watcher.py` (watchdog) ligando todo o pipeline — debounce de tamanho de arquivo antes de processar, captura de exceção não prevista por arquivo sem derrubar o processo (ver "Resiliência a falha não prevista"), e mover CSV para `dados/processados/` após sucesso — com testes mockando o pipeline
10. Configurar logging (arquivo `logs/pipeline.log` + console, INFO para fluxo normal, WARNING/ERROR para falhas e retries)
11. Rodar o fluxo ponta a ponta com os 4 CSVs sintéticos, validando os dois cenários (primeira semana / semanas com comparação)
12. Remover a pasta `ferramentas_dev/` antes de considerar o projeto finalizado/postável

## Regras de desenvolvimento

- Spec-first: este arquivo é a referência; qualquer mudança de escopo relevante deve ser refletida aqui antes de codar
- A IA nunca calcula números — todo cálculo determinístico (totais, variação, identificação de melhor/pior post) é feito em pandas antes de qualquer chamada à API, para economizar custo/token e evitar que a IA "decida" sobre matemática que Python já resolve com certeza
- Usar structured output da Gemini API (schema forçado), não confiar em instrução textual "responda em JSON"
- O prompt deve sempre tratar explicitamente os dois cenários: com histórico (calcula variação e possível causa) e sem histórico/primeira semana (`possivel_causa: null`, sem inventar comparação)
- O CSV sintético deve replicar a "sujeira" real do export do Meta (campos vazios para métricas não aplicáveis ao tipo de post, nomes de coluna como o Meta usa) — autenticidade do dado é parte do valor do projeto
- Não reaproveitar padrões de projetos anteriores apenas por familiaridade (ex: não forçar ABC/herança aqui só porque foi usado em `combate_de_turno`) — usar o padrão que o problema realmente pede
- O gerador de dados sintéticos é descartável: nunca deve aparecer no repositório final nem ser citado como funcionalidade do sistema
- Ao final, gerar um post de LinkedIn cobrindo a entrega (a pedido, seguindo o padrão já estabelecido com outros projetos do portfólio)
- Dependências gerenciadas via `uv` + `pyproject.toml`, alinhado à regra global — sem `requirements.txt` avulso
- PDF gerado com `xhtml2pdf` em vez de WeasyPrint, decisão tomada para evitar a dependência nativa GTK/Pango do WeasyPrint, que não instala de forma simples no Windows (ambiente de desenvolvimento deste projeto)
