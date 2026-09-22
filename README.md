# Conecta Impacto — Plataforma de Inteligência para Conexão entre Doadores/Voluntários e Projetos Sociais (ESG + Agenda 2030)

**TP2 — Interface Dinâmica, Coleta de Dados Web, Cache/Estado de Sessão e Upload/Download de Arquivos**

## 1. Visão geral

Este repositório contém o **Conecta Impacto**, uma aplicação que usa Python, APIs, Web
Scraping e (nas próximas etapas) LLMs via engenharia de prompts para conectar
organizações da sociedade civil (OSCs/ONGs) a doadores e voluntários — pessoas físicas
e empresas com agendas ESG — a partir de dados públicos sobre projetos sociais,
indicadores socioeconômicos regionais e notícias sobre a Agenda 2030.

O projeto está organizado segundo o **TDSP (Team Data Science Process)** da Microsoft e
usa o **CRISP-DM** como referencial metodológico para o ciclo analítico (ver
`Docs/Project/tdsp_crispdm_mapping.md`).

- **TP1** entregou a proposta da aplicação, o planejamento inicial e uma demo estática
  em Streamlit.
- **TP2** (esta entrega) evoluiu a aplicação com interface dinâmica em abas, coleta de
  dados via Web Scraping (BeautifulSoup), cache e estado de sessão, e um serviço de
  upload/download de arquivos CSV. Ver `Docs/Project/project_charter.md` e
  `Docs/DataReport/data_summary_report.md` para o detalhamento completo.

## 2. Estrutura de diretórios (TDSP)

```
conecta-impacto/
├── app.py                              # Aplicação Streamlit (TP2)
├── requirements.txt                    # Dependências do projeto
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml                     # Tema visual da aplicação
├── Code/
│   ├── DataAcquisition/                # Scripts de coleta (APIs e Web Scraping)
│   │   ├── coleta_ibge.py
│   │   ├── scraping_observatorio.py
│   │   ├── scraping_causas_sociais.py  # novo — TP2
│   │   └── scraping_noticias_esg.py    # novo — TP2
│   ├── DataPreparation/                # Limpeza, padronização e junção dos dados
│   │   ├── preparar_dados.py           # projetos + notícias — TP2
│   │   └── gerar_nuvem_palavras.py     # novo — TP2
│   └── Modeling/                       # (próximas etapas) classificação por ODS, matching, LLM
├── Data/
│   ├── Raw/                            # Dados brutos coletados
│   │   ├── causas_observatorio.csv
│   │   ├── noticias_esg_ods.csv
│   │   └── noticias_txt/               # corpus para a nuvem de palavras
│   └── Processed/                      # Dados tratados, consumidos pelo app
│       ├── projetos_sociais.csv
│       └── noticias_processadas.csv
├── SampleData/
│   └── projetos_sociais_sample.csv     # Amostra usada como fallback
└── Docs/
    ├── Project/
    │   ├── project_charter.md
    │   ├── tdsp_crispdm_mapping.md
    │   └── ambiente_dev_git_deploy.md  # novo — TP2: Git, GitHub e deploy
    └── DataReport/
        └── data_summary_report.md
```

## 3. Ambiente de desenvolvimento

### pyenv + virtualenv

```bash
pyenv install 3.11.9
pyenv virtualenv 3.11.9 conecta-impacto
pyenv local conecta-impacto
pip install -r requirements.txt
```

### venv padrão (alternativa)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Instruções completas de controle de versão (Git/GitHub) e preparação para deploy no
Streamlit Community Cloud estão em `Docs/Project/ambiente_dev_git_deploy.md`.

## 4. Como rodar a aplicação

```bash
streamlit run app.py
```

A aplicação abre em `http://localhost:8501`, organizada em 4 abas:

| Aba | O que faz |
|---|---|
| 📌 Visão Geral | Problema de negócio, objetivos, ODS atendidos e evolução do projeto |
| 🗂️ Projetos Sociais | Filtros por causa/UF, busca textual, métricas e favoritos (persistidos na sessão) |
| 📰 Notícias & Nuvem de Palavras | Notícias sobre ESG/Agenda 2030 coletadas por Web Scraping, nuvem de palavras e estatísticas do corpus |
| 📤 Meus Dados | Upload de CSV para complementar a base de projetos e download dos dados combinados |

## 5. Coleta e preparação de dados

- `Code/DataAcquisition/coleta_ibge.py`: coleta indicadores socioeconômicos municipais
  via API pública do IBGE (SIDRA/Localidades), usados para contextualizar desigualdade
  regional (ODS 10).
- `Code/DataAcquisition/scraping_observatorio.py`: Web Scraping (BeautifulSoup) do
  Observatório do Terceiro Setor, extraindo projetos sociais por causa.
- `Code/DataAcquisition/scraping_causas_sociais.py`: Web Scraping da taxonomia de
  causas sociais do Observatório do Terceiro Setor, com lista de contingência caso a
  página mude de estrutura.
- `Code/DataAcquisition/scraping_noticias_esg.py`: Web Scraping de notícias sobre ESG e
  Agenda 2030, salvando metadados em CSV e o corpo do texto em `.txt` (usado na nuvem
  de palavras).
- `Code/DataPreparation/preparar_dados.py`: consolida, limpa e padroniza os dados
  brutos de **projetos** e de **notícias** (`python preparar_dados.py {projetos|noticias} --entrada ... --saida ...`).
- `Code/DataPreparation/gerar_nuvem_palavras.py`: gera a nuvem de palavras e as
  estatísticas básicas de texto exibidas na aplicação.

## 6. Cache, estado de sessão e upload/download

- Os datasets de projetos e notícias são carregados com `st.cache_data`, evitando
  releituras desnecessárias do disco a cada interação do usuário.
- `st.session_state` mantém os projetos favoritados e os registros enviados por upload
  durante a navegação do usuário na aplicação.
- Na aba "Meus Dados", o usuário pode baixar um modelo de CSV vazio, enviar seus
  próprios projetos sociais (mesmo schema da base) e baixar a base combinada
  (dados coletados + enviados).

## 7. Documentação do projeto

- `Docs/Project/project_charter.md` — escopo, objetivos, KPIs, stakeholders e
  cronograma (TDSP), atualizado com o progresso do TP2.
- `Docs/DataReport/data_summary_report.md` — fontes de dados, formato, forma de coleta
  e Data Quality Report das coletas executadas até o TP2.
- `Docs/Project/tdsp_crispdm_mapping.md` — mapeamento entre as fases do TDSP e do
  CRISP-DM usadas no projeto.
- `Docs/Project/ambiente_dev_git_deploy.md` — configuração do ambiente, Git, GitHub e
  preparação para deploy.

## 8. Créditos

Este projeto foi desenvolvido com apoio de ferramentas de Inteligência Artificial ao
longo de todo o ciclo de desenvolvimento — da estruturação do código à redação da
documentação. A ferramenta de IA utilizada tanto para o design gráfico/visual da
aplicação (tema de cores, ícones, organização das abas e layout do dashboard) quanto
para apoio ao desenvolvimento e à escrita deste README foi o **Claude, da Anthropic**.