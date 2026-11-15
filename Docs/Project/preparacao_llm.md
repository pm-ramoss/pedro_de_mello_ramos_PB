# Preparação para IA com LLMs — Conecta Impacto (TP3)

Este documento descreve **quais dados o projeto já tem**, **como eles poderão alimentar
LLMs** na próxima etapa e **o que foi preparado no TP3**. Nenhum LLM é chamado nesta
entrega.

## 1. Dados disponíveis

| Dado | Onde | Tamanho atual | Natureza |
|---|---|---|---|
| Projetos sociais | `Data/Processed/projetos_sociais.csv` (+ `projetos_enviados.csv`) | 10 registros | Texto curto estruturado (nome, causa, ODS, descrição) |
| Notícias ESG/Agenda 2030 | `Data/Processed/noticias_processadas.csv`, `Data/Raw/noticias_txt/` | 5 notícias | Texto corrido (título + resumo) |
| Estatísticas agregadas | `GET /estatisticas` | — | Números por causa/UF/ODS |
| Corpus unificado | `Data/Processed/corpus_llm.jsonl`, `GET /llm/documentos` | 15 documentos (~940 tokens estimados) | Texto + metadados |

## 2. Casos de uso e dados que os alimentam

| Caso de uso (enunciado) | Aplicação no projeto | Dado de entrada | Saída esperada |
|---|---|---|---|
| **Resumo automático** | Resumir notícias longas para o doador | Notícias (texto completo coletado) | Resumo de ≤ 3 frases |
| **Classificação de sentimentos** | Medir o tom da cobertura de ESG/ODS | `titulo` + `resumo` das notícias | positivo / negativo / neutro + justificativa |
| **Perguntas e respostas (Q&A)** | "Quais projetos de educação existem no Nordeste?" | Documentos de `/llm/documentos` como contexto | Resposta citando o id do documento |
| **Geração de texto** | Relatório de insights para empresas ESG | `GET /estatisticas` | Parágrafo descritivo com 3 insights |
| **Classificação por ODS** (já prevista no Charter) | Rotular projetos novos enviados por upload/API | `nome_projeto` + `causa` + `descricao` | Lista de ODS em JSON |

## 3. O que foi preparado

1. **Corpus JSONL** — `Code/DataPreparation/preparar_corpus_llm.py` converte projetos e
   notícias em documentos `{id, tipo, titulo, texto, metadados, tokens_estimados}`.
2. **Endpoint** `GET /llm/documentos` — entrega o mesmo corpus pela API, sempre atualizado
   com os projetos cadastrados via POST.
3. **Prompts-base** — `Code/Modeling/prompts_llm.py` define, por caso de uso, os campos de
   entrada, a saída esperada e o prompt; `montar_prompt(caso, **campos)` valida os campos.
4. **Página "Preparação para LLMs"** no app — mostra o corpus, a estimativa de tokens e a
   pré-visualização de cada prompt com dados reais.
5. **Dependência e segredo** — `anthropic` já consta em `requirements.txt`; a chave deverá
   ficar em `.env`/Secrets (já ignorados pelo `.gitignore`), nunca no Git.

## 4. Decisões de projeto para facilitar o TP4

- **Id estável por documento** permite citar fontes nas respostas de Q&A.
- **Metadados separados do texto** (causa, ODS, UF, link) permitem filtrar o contexto antes
  de enviá-lo ao modelo, reduzindo custo de tokens.
- **Prompts pedem JSON** onde há rótulo (sentimento, ODS), para validar a saída
  automaticamente.
- **Contagem de tokens é estimativa** (~4 caracteres/token); no TP4 deve-se usar o
  tokenizador do modelo escolhido antes de calcular custos.

## 5. Riscos e cuidados

- **Corpus pequeno:** 15 documentos servem para validar o pipeline, não para avaliar a
  qualidade do modelo; é necessário ampliar a base antes de conclusões.
- **Alucinação:** em Q&A, o prompt restringe a resposta ao contexto e manda admitir quando
  a informação não existe; isso deve ser testado com perguntas sem resposta nos dados.
- **Direitos autorais:** os resumos de notícias são paráfrases curtas, com link para a fonte;
  o TP4 não deve reproduzir integralmente textos dos veículos.
- **Dados enviados por usuários** podem conter conteúdo inadequado; revisar antes de usar
  como contexto de um LLM.
