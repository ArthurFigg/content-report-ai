# content-report-ai

Sistema que monitora uma pasta local e, ao detectar um CSV de exportação do Instagram (Meta Business Suite), processa automaticamente as métricas da semana, gera interpretação via IA (Groq/Llama) e envia um relatório em PDF por email — sem nenhuma intervenção manual além de soltar o arquivo na pasta.

![Python](https://img.shields.io/badge/Python-3.12-blue) ![uv](https://img.shields.io/badge/gerenciador-uv-blueviolet)

---

## Funcionalidades

- Monitora `dados/entrada/` com watchdog — disparo por evento, sem agendamento por horário
- Aguarda o arquivo estabilizar antes de processar (evita leitura de CSV em escrita parcial)
- Valida o CSV: colunas obrigatórias, tipos, Post Type válido, valores não-negativos, Post ID único, pelo menos uma linha de dados
- Calcula métricas semanais com pandas: Reach total, engajamento total, taxa de engajamento, melhor/pior post por Reach, post com maior taxa de engajamento
- Compara com a semana anterior (variação % de Reach e Engajamento) ou identifica primeira semana sem histórico
- Chama a API Groq (Llama 3.3 70B) para gerar resumo executivo, destaques, possível causa e recomendação em linguagem simples
- Persiste posts e resumo semanal em SQLite numa única transação, após a IA responder
- Gera gráfico de linha com a evolução do Reach ao longo das semanas (matplotlib)
- Monta e converte o relatório para PDF via template HTML/Jinja2 + xhtml2pdf
- Envia o PDF por email como anexo via Gmail (SMTP SSL)
- Retry com backoff exponencial para chamadas à Groq e ao SMTP (3 tentativas: 2s / 4s / 8s)
- Idempotência: rejeita CSV de semana já processada sem reprocessar nem duplicar dados
- Resiliência: falha isolada em um arquivo não derruba o processo do watcher

---

## Pré-requisitos

- Python 3.12
- [uv](https://docs.astral.sh/uv/) instalado
- Conta Groq com [API Key](https://console.groq.com/keys) (gratuito, sem cartão)
- Conta Gmail com [senha de app](https://support.google.com/accounts/answer/185833) habilitada

---

## Instalação

```bash
git clone <url-do-repositorio>
cd content-report-ai
uv sync
```

---

## Configuração

Copie o arquivo de exemplo e preencha as variáveis:

```bash
cp .env.example .env
```

| Variável | Descrição |
|---|---|
| `GROQ_API_KEY` | Chave da API Groq (console.groq.com/keys) |
| `GROQ_MODEL` | Modelo a usar (padrão: `llama-3.3-70b-versatile`) |
| `SMTP_USER` | Endereço Gmail de envio |
| `SMTP_PASSWORD` | Senha de app do Gmail (não a senha da conta) |
| `EMAIL_DESTINATARIO` | Endereço que vai receber o relatório |
| `NOME_NEGOCIO` | Nome do perfil/negócio exibido no cabeçalho do PDF |

---

## Uso

```bash
uv run python src/watcher.py
```

O sistema inicia, processa qualquer CSV pendente em `dados/entrada/` e fica em modo de escuta. Para processar uma nova semana, basta soltar o arquivo na pasta:

```
dados/entrada/semana_2026-06-23.csv
```

**Convenção de nome obrigatória:** `semana_AAAA-MM-DD.csv`, onde a data é a segunda-feira de início da semana. O sistema rejeita arquivos fora desse padrão.

Ao processar com sucesso:

1. O CSV é movido para `dados/processados/`
2. O PDF é salvo em `relatorios/relatorio_2026-06-23.pdf`
3. O relatório é enviado por email com o PDF anexado
4. O log é gravado em `logs/pipeline.log`

Se o envio de email falhar após os retries, o PDF continua disponível em `relatorios/` para envio manual.

---

## Formato do CSV de entrada

O sistema aceita o formato de exportação da seção **Content** do Meta Business Suite. Colunas obrigatórias:

`Post ID`, `Post Date`, `Post Type`, `Reach`, `Impressions`, `Likes and Reactions`, `Comments`, `Shares`, `Saves`

Colunas opcionais (aplicáveis apenas a Reels/vídeo): `Plays`, `Watch Time`, `Retention`, `Link Clicks`

Valores vazios em colunas de vídeo para posts estáticos são esperados e tratados como zero.

---

## Estrutura do projeto

```
src/
  watcher.py              # ponto de entrada — observa a pasta e orquestra o pipeline
  retry.py                # retry com backoff exponencial (compartilhado por Groq e SMTP)
  ingestao/
    leitor_csv.py         # lê e valida o CSV no formato Meta Business Suite
  processamento/
    calculo_metricas.py   # totais, médias, melhor/pior post (pandas)
    comparacao.py         # variação semana atual vs. anterior
  persistencia/
    modelos.py            # esquema das tabelas SQLite (posts, resumos_semanais)
    repositorio.py        # inserção e consulta de posts e resumos
  ia/
    prompt.py             # monta o payload e o prompt para a API
    cliente_gemini.py     # chamada ao Groq com JSON mode e retry
  relatorio/
    grafico.py            # gráfico de linha da evolução do Reach (matplotlib)
    templates/
      relatorio.html      # template Jinja2 do PDF
    gerador_pdf.py        # monta HTML final e converte para PDF (xhtml2pdf)
  entrega/
    email_sender.py       # envia email com PDF anexado (Gmail SMTP SSL)
dados/
  entrada/                # pasta monitorada — soltar o CSV aqui
  processados/            # CSVs movidos após processamento bem-sucedido
relatorios/               # PDFs gerados (sempre salvos, independente do email)
logs/
  pipeline.log            # log do pipeline (INFO para fluxo normal, ERROR para falhas)
banco/
  historico.db            # banco SQLite (gerado automaticamente na primeira execução)
tests/                    # testes pytest espelhando a estrutura de src/
```

---

## Testes

```bash
uv run pytest -v
```

---

## Dependências de produção

| Pacote | Versão | Uso |
|---|---|---|
| `sqlalchemy` | >=2.0,<3.0 | ORM e gerenciamento do banco SQLite |
| `pandas` | >=2.0,<3.0 | Cálculo de métricas semanais |
| `groq` | >=1.5.0,<2.0 | SDK do Groq (JSON mode + Llama 3.3) |
| `pydantic` | >=2.13.4,<3.0 | Schema de saída da IA e validações |
| `jinja2` | >=3.1.6,<4.0 | Template HTML do PDF |
| `xhtml2pdf` | >=0.2.17,<0.3 | Conversão HTML → PDF (sem dependência nativa GTK/Pango) |
| `matplotlib` | >=3.11.0,<4.0 | Gráfico de linha embutido no PDF |
| `watchdog` | >=6.0.0,<7.0 | Monitoramento da pasta de entrada por evento |

---

## Licença

MIT
