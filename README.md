# Conecta Impacto — Plataforma de Inteligência para Conexão entre Doadores/Voluntários e Projetos Sociais (ESG + Agenda 2030)

**TP4 — LLM local (HuggingFace) integrado ao FastAPI, Response Models e tratamento de erros**

*(O TP3 — app multipágina, API, scraping dinâmico e preparação de dados — continua descrito abaixo.)*

## 1. Visão geral

O **Conecta Impacto** usa Python, APIs, Web Scraping e (na próxima etapa) LLMs via
engenharia de prompts para conectar organizações da sociedade civil (OSCs/ONGs) a
doadores e voluntários — pessoas físicas e empresas com agendas ESG — a partir de dados
públicos sobre projetos sociais, indicadores socioeconômicos regionais e notícias sobre a
Agenda 2030.

O projeto segue o **TDSP** (Microsoft) com o **CRISP-DM** como referencial metodológico
(`Docs/Project/tdsp_crispdm_mapping.md`).

| Etapa | Entrega |
|---|---|
| TP1 | Proposta, planejamento e demo estática em Streamlit |
| TP2 | Interface em abas, scraping (BeautifulSoup), cache/sessão, upload/download |
| TP3 | App multipágina, API FastAPI (GET/POST), scraping dinâmico (Selenium) e dados preparados para LLMs |
| **TP4** | **LLM local (HuggingFace): resumo e sentimento via `POST /processar_texto`, Response Models, erros HTTP e página 🧠 no app** |

## 2. Estrutura de diretórios (TDSP)

```
.
├── app.py                              # Ponto de entrada Streamlit + menu de navegação (TP3)
├── app_utils.py                        # Cliente da API + contingência por arquivos (TP3)
├── app_pages/                          # Uma página por arquivo (TP3)
│   ├── visao_geral.py
│   ├── projetos.py
│   ├── estatisticas.py
│   ├── noticias.py
│   ├── meus_dados.py
│   ├── analise_texto.py                # novo — TP4
│   ├── api_console.py
│   └── preparacao_llm.py
├── tests/                              # testes automatizados (TP4)
├── requirements.txt
├── .streamlit/config.toml
├── Code/
│   ├── API/                            # API FastAPI (TP3)
│   │   ├── main.py                     # rotas
│   │   ├── schemas.py                  # validação (Pydantic)
│   │   ├── repositorio.py              # leitura/escrita dos CSVs
│   │   └── llm_service.py              # LLM local (HuggingFace) — TP4
│   ├── DataAcquisition/
│   │   ├── coleta_ibge.py
│   │   ├── scraping_observatorio.py
│   │   ├── scraping_causas_sociais.py
│   │   ├── scraping_noticias_esg.py
│   │   └── scraping_dinamico_selenium.py   # novo — TP3 (opcional)
│   ├── DataPreparation/
│   │   ├── preparar_dados.py
│   │   ├── gerar_nuvem_palavras.py
│   │   └── preparar_corpus_llm.py          # novo — TP3
│   └── Modeling/
│       ├── prompts_llm.py                  # prompts-base (TP3)
│       └── baixar_modelos.py               # download dos modelos HF — TP4
├── Data/
│   ├── Raw/                            # Dados brutos coletados
│   └── Processed/                      # CSVs tratados + corpus_llm.jsonl (TP3)
├── SampleData/projetos_sociais_sample.csv
└── Docs/
    ├── Project/    (project_charter, tdsp_crispdm_mapping, ambiente_dev_git_deploy, preparacao_llm, escolha_modelo_llm)
    ├── DataReport/ (data_summary_report)
    └── API/        (api_documentacao)
```

## 3. Ambiente de desenvolvimento

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

(Alternativa com `pyenv`/`virtualenv`: ver `Docs/Project/ambiente_dev_git_deploy.md`.)

### PyTorch (versão CPU, mais leve)

Se não tiver GPU, instale o PyTorch de CPU antes do `requirements.txt` para economizar
espaço: `pip install torch --index-url https://download.pytorch.org/whl/cpu`.

### Modelos do TP4 (download único)

```bash
python Code/Modeling/baixar_modelos.py      # precisa de internet; ~2 GB
```

## 4. Como rodar

Use **dois terminais**, na raiz do projeto:

```bash
# 1) API — http://localhost:8000  (Swagger interativo em /docs)
uvicorn main:app --reload --app-dir Code/API --port 8000

# 2) Aplicação — http://localhost:8501
streamlit run app.py
```

A API é opcional para o app: se ela estiver fora do ar, o app lê os mesmos CSVs e a barra
lateral indica "API offline" (exceto a página 🧠, que exige a API). Para usar outro endereço: `CONECTA_API_URL=http://host:porta`.
Para rodar o LLM sem internet depois do download: `CONECTA_LLM_OFFLINE=1 uvicorn main:app --reload --app-dir Code/API --port 8000`.

### Páginas do app (menu lateral)

| Página | O que faz |
|---|---|
| 📌 Visão Geral | Problema de negócio, métricas, evolução TP1→TP3 e arquitetura |
| 🗂️ Projetos Sociais | Filtros (causa, UF, ODS), busca, favoritos e download |
| 📊 Estatísticas e Gráficos | Gráficos por causa/UF/ODS e progresso das metas do Charter |
| 📰 Notícias e Nuvem de Palavras | Notícias filtráveis, nuvem de palavras e estatísticas do corpus |
| 📤 Meus Dados | Cadastro de projeto e upload de CSV (persistentes via `POST /projetos`); download CSV/JSON |
| 🧠 Análise de Texto (LLM local) | Resumo e sentimento de textos livres ou das notícias coletadas, via `POST /processar_texto` |
| 🔌 Console da API | Documentação das rotas e testes de GET direto na interface |
| 🤖 Preparação para LLMs | Corpus, estimativa de tokens e prompts-base dos casos de uso do TP4 |

## 5. API (FastAPI)

| Método | Rota | Função |
|---|---|---|
| GET | `/saude` | Verifica se a API está no ar |
| GET | `/projetos` | Lista projetos (`causa`, `uf`, `ods`, `busca`, `limite`, `offset`) |
| GET | `/projetos/{id}` | Projeto por id (404 se não existir) |
| POST | `/projetos` | Cadastra projeto (valida UF e link; 409 se duplicado) |
| GET | `/noticias` | Lista notícias (`ods`, `busca`) |
| GET | `/estatisticas` | Contagens por causa, UF e ODS |
| GET | `/llm/documentos` | Documentos de texto + metadados para LLMs |
| POST | `/processar_texto` | **(TP4)** Resumo ou sentimento com LLM local (Response Model + erros 422/500/503/504) |
| GET | `/llm/status` | **(TP4)** Modelos configurados e se já foram carregados |

Detalhes, parâmetros e exemplos em `Docs/API/api_documentacao.md`.

```bash
curl "http://localhost:8000/projetos?uf=SP&ods=4"
curl -X POST http://localhost:8000/projetos -H "Content-Type: application/json" \
  -d '{"nome_projeto":"Cozinha Solidária","organizacao":"Mesa Cheia","causa":"Segurança alimentar","uf":"PE"}'
```

## 6. Coleta e preparação de dados

- `coleta_ibge.py` — indicadores municipais via API pública do IBGE (ODS 10).
- `scraping_observatorio.py`, `scraping_causas_sociais.py`, `scraping_noticias_esg.py` —
  Web Scraping estático (BeautifulSoup) de projetos, causas e notícias.
- `scraping_dinamico_selenium.py` — **opcional**: renderiza com Chrome headless a página de
  causas do Observatório (no scraping estático saíram 7 de 15). Requer Selenium + Chrome.
  Justificativa e limites em `Docs/DataReport/data_summary_report.md` (seção 4).
- `preparar_dados.py` — limpa e padroniza projetos e notícias.
- `gerar_nuvem_palavras.py` — nuvem de palavras e estatísticas de texto.
- `preparar_corpus_llm.py` — gera `Data/Processed/corpus_llm.jsonl` (projetos + notícias).

## 7. LLM local (TP4)

- **Modelos:** `recogna-nlp/ptt5-base-summ` (resumo, PT) e
  `lxyuan/distilbert-base-multilingual-cased-sentiments-student` (sentimento), executados com
  `transformers` em CPU, sem nuvem após o download. Justificativa (desempenho, custo local,
  acessibilidade): `Docs/Project/escolha_modelo_llm.md`.
- **Integração:** `Code/API/llm_service.py` (carga sob demanda, timeout, exceções de domínio) +
  rota `POST /processar_texto` com Response Models em `schemas.py`.
- **Erros:** 422 entrada inválida · 503 modelo indisponível · 504 tempo limite · 500 falha na
  inferência, todos em JSON `{codigo, mensagem, dica}`.
- **Testes:** `pytest tests -q` (pipelines simulados; não baixam modelos).

### Preparação feita no TP3

Casos de uso mapeados — resumo, classificação de sentimento, Q&A, geração de texto e
classificação de projetos por ODS — com dados de entrada, saída esperada e prompts-base
definidos em `Code/Modeling/prompts_llm.py`. Plano completo em
`Docs/Project/preparacao_llm.md`. Resumo e sentimento foram implementados no TP4; Q&A, geração e classificação por ODS seguem planejados.

## 8. Testes manuais sugeridos (checklist)

1. `GET /saude` retorna `{"status":"ok"}` e `/docs` abre.
2. `GET /projetos?uf=SP` retorna só projetos de SP; `/projetos/xxx` retorna 404.
3. `POST /projetos` com UF `ZZ` retorna 422; com dados válidos retorna 201; repetido, 409.
4. No app, com a API ligada, a barra lateral mostra "API online"; desligue-a e recarregue:
   deve mostrar "API offline" e as páginas continuam funcionando.
5. Em **Meus Dados**, cadastre um projeto e confirme que ele aparece em **Projetos Sociais**
   e que `Data/Processed/projetos_enviados.csv` foi criado.
6. Em **Preparação para LLMs**, baixe o JSONL e confira os documentos.
7. `POST /processar_texto` com `tarefa=sentimento` retorna 200 e `resultado.rotulo`; com `tarefa=resumo` e texto curto, 422; sem os modelos instalados/baixados, 503 com `dica`.
8. Na página 🧠, processe um texto e confira `tempo_ms`; preencha a tabela de testes de `Docs/Project/escolha_modelo_llm.md` (seção 8).

## 9. Documentação

- `Docs/Project/project_charter.md` — escopo, KPIs, riscos (revisado no TP3).
- `Docs/DataReport/data_summary_report.md` — fontes, qualidade dos dados e decisão sobre Selenium.
- `Docs/API/api_documentacao.md` — contrato da API.
- `Docs/Project/preparacao_llm.md` — dados, casos de uso e decisões de LLM.
- `Docs/Project/escolha_modelo_llm.md` — escolha dos modelos, integração local e tratamento de erros (TP4).
- `Docs/Project/tdsp_crispdm_mapping.md` e `ambiente_dev_git_deploy.md` — método, ambiente, Git e deploy.

## 10. Créditos

Este projeto foi desenvolvido com apoio de ferramentas de Inteligência Artificial ao
longo de todo o ciclo — da estruturação do código à redação da documentação. A ferramenta
utilizada tanto para o design gráfico/visual da aplicação (tema, ícones, organização das
páginas e layout) quanto para apoio ao desenvolvimento e à escrita deste README foi o
**Claude, da Anthropic**.
