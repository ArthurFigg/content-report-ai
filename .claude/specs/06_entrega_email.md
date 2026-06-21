# entrega_email

**Ordem:** 6 de 7
**Depende de:** 04_ia_gemini (reutiliza `src/retry.py`), 05_relatorio_pdf (envia o PDF gerado ali)

## O que faz
Envia o PDF do relatório semanal por email, como anexo, para o destinatário configurado, com retry em caso de falha de conexão SMTP.

## Comportamento
- `email_sender.py` monta um email com: assunto `"Relatório semanal — {NOME_NEGOCIO} — {período da semana}"`, corpo de texto simples avisando que o relatório está em anexo, e o PDF (gerado pela spec `05_relatorio_pdf`) como anexo.
- Conecta via `smtplib.SMTP_SSL` em `smtp.gmail.com:465` (Gmail, hardcoded), autenticando com `SMTP_USER` e `SMTP_PASSWORD` (`.env`).
- Envia para `EMAIL_DESTINATARIO` (`.env`, já definido no CLAUDE.md).
- Em caso de falha de conexão/envio (qualquer exceção do `smtplib`), usa `src/retry.py` (módulo compartilhado, criado na spec `04_ia_gemini`) para tentar novamente com backoff exponencial (3 tentativas: 2s, 4s, 8s).
- Se as 3 tentativas falharem, loga o erro e retorna indicação de falha — não levanta exceção para o chamador travar o pipeline; o PDF já está salvo em `relatorios/` desde a etapa anterior, disponível para envio manual.
- Se `SMTP_USER`, `SMTP_PASSWORD` ou `EMAIL_DESTINATARIO` não estiverem configurados (`.env` incompleto), levanta erro imediatamente, sem retry — é um erro de configuração, não uma falha transitória de rede.

## Critérios verificáveis
- [ ] `uv run pytest tests/test_email_sender.py -v` passa
- [ ] Email mockado (`smtplib` mockado) é montado com assunto, corpo e anexo PDF corretos
- [ ] Uma falha simulada (mock lança exceção) nas 2 primeiras tentativas seguida de sucesso na 3ª é aceita normalmente
- [ ] 3 falhas consecutivas simuladas resultam em retorno de falha sem exceção subindo ao chamador
- [ ] Configuração ausente (ex: `EMAIL_DESTINATARIO` não definida) levanta erro imediatamente, sem passar pelas 3 tentativas de retry
- [ ] `src/retry.py` é reutilizado (não duplicado) — o teste de `email_sender` usa o mesmo módulo de retry já testado na spec `04_ia_gemini`

## Módulos afetados
- `src/entrega/email_sender.py` (novo)

## Não mexer
- `src/persistencia/`, `src/ingestao/`, `src/processamento/`, `src/ia/`, `src/relatorio/` — specs `01`-`05`, já especificadas
- `src/retry.py` — já existe (spec `04_ia_gemini`), só é importado/reutilizado aqui, não modificado
- `ferramentas_dev/` — spec `02_gerador_dados_sinteticos`
- `src/watcher.py` — fora de escopo desta spec

## Decisões tomadas
- Provedor SMTP específico: Gmail (`smtp.gmail.com:465`, `smtplib.SMTP_SSL`), credenciais via `SMTP_USER` + `SMTP_PASSWORD` (senha de app) no `.env`
- Assunto e corpo do email simples, sem replicar o resumo da IA — só avisa que o PDF está em anexo
- Erros de configuração ausente falham imediatamente, sem retry — retry é reservado para falhas transitórias de rede/SMTP, não para erro de configuração
- Reaproveita `src/retry.py` (criado na spec `04_ia_gemini`), não duplica a lógica de backoff
