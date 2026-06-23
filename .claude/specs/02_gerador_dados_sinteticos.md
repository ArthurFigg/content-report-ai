# gerador_dados_sinteticos

**Ordem:** 2 de 7
**Depende de:** nenhuma

## O que faz
Gera 4 arquivos CSV sintéticos (~1 mês, 1 por semana) no formato definido em "Colunas do CSV de entrada" do CLAUDE.md, com dados plausíveis de um perfil de pequeno negócio/criador de conteúdo, prontos para alimentar o restante do pipeline.

## Comportamento
- Gera exatamente 4 arquivos, um por semana, nas últimas 4 segundas-feiras anteriores (ou igual) à data de execução, nomeados `semana_AAAA-MM-DD.csv` (convenção já definida no CLAUDE.md)
- Cada semana tem entre 4 e 7 posts, quantidade sorteada por semana
- Post Type sorteado por post com pesos: 40% Reel, 35% Photo, 15% Carousel, 10% Video
- Reach base por post: 300–1.500, com pequena variação em torno da média
- Reels têm Reach tendencialmente maior que posts estáticos (Photo/Carousel) — multiplicador aplicado sobre a base
- Likes and Reactions, Comments, Shares, Saves calculados como proporção plausível do Reach do post (coerência entre métricas no mesmo post)
- Plays, Watch Time e Retention preenchidos apenas para Video/Reel; vazios para Photo/Carousel (esparsidade esperada, conforme CLAUDE.md)
- Link Clicks preenchido apenas em uma fração dos posts (simulando que nem todo post tem CTA); vazio nos demais
- Post Text sorteado de um banco fixo de ~15-20 legendas genéricas em português
- Post ID gerado garantindo unicidade global entre os 4 arquivos (nunca se repete entre semanas — pré-requisito da PK definida em `01_persistencia`)
- Exatamente 1 post viral plantado, em uma única semana sorteada entre as 4, com Reach 5–10x a média da semana (engajamento proporcionalmente alto também, mantendo a coerência entre métricas)
- Tendência de leve crescimento na média base de Reach ao longo das 4 semanas (~5–15% acumulado), exceto pelo pico viral pontual, que é um evento isolado
- `random.seed` fixa no início do script — execuções repetidas produzem exatamente os mesmos dados
- Re-executar o script sobrescreve os 4 arquivos em `dados/entrada/` sem erro nem checagem prévia (idempotente por construção, já que a seed é fixa)
- CSV usa vírgula como separador e datas em formato ISO (`AAAA-MM-DD`)

## Critérios verificáveis
- [ ] `uv run python ferramentas_dev/gerador_dados_sinteticos.py` executa sem erro e cria 4 arquivos em `dados/entrada/`
- [ ] Os 4 arquivos seguem a convenção `semana_AAAA-MM-DD.csv` com datas de segunda-feira, nas últimas 4 semanas a partir de hoje
- [ ] Cada arquivo tem entre 4 e 7 linhas de dados (mais cabeçalho)
- [ ] Todas as colunas definidas em "Colunas do CSV de entrada" (CLAUDE.md) estão presentes, com Plays/Watch Time/Retention vazios em posts Photo/Carousel e preenchidos em Video/Reel
- [ ] Post IDs são únicos em todos os 4 arquivos combinados (nenhuma repetição)
- [ ] Rodando o script duas vezes seguidas produz arquivos byte-idênticos (confirma seed fixa e idempotência)
- [ ] Existe exatamente 1 post, em uma única semana, com Reach pelo menos 5x maior que a média dos outros posts daquela mesma semana

## Módulos afetados
- `ferramentas_dev/gerador_dados_sinteticos.py` (novo) — script de geração, conforme comportamento acima
- `dados/entrada/` (preenchida em runtime pela execução do script)

## Não mexer
- `src/` inteiro — este script não deve ser importado por nenhum módulo do produto final (regra de isolamento já definida no CLAUDE.md)
- `src/persistencia/` — spec `01_persistencia`, já especificada, não precisa ser tocada aqui

## Decisões tomadas
- Pesquisei o formato real de export do Meta Business Suite e não encontrei confirmação pública de separador/formato de data exatos — optamos por vírgula + ISO (`AAAA-MM-DD`) por ser o mais seguro para parsing posterior, sem comprometer autenticidade (fontes consultadas confirmam só as categorias de colunas, já presentes no CLAUDE.md)
- 4 a 7 posts por semana, sorteado
- Datas relativas à execução (últimas 4 segundas-feiras), não fixas
- Reach base 300–1.500 por post
- 1 pico viral, em 1 semana sorteada, 5–10x a média
- Tendência de leve crescimento ao longo do mês
- Distribuição de Post Type: 40% Reel, 35% Photo, 15% Carousel, 10% Video
- Legendas: banco fixo de frases genéricas em português, sorteadas
- Seed fixa (reprodutibilidade); reexecução sobrescreve os arquivos sem checagem prévia

---
**Status:** concluida em 2026-06-22
