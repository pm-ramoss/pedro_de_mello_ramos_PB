# Organização do Projeto: CRISP-DM x TDSP

## 1. Por que usar os dois frameworks?

- **CRISP-DM** (Cross-Industry Standard Process for Data Mining) fornece o ciclo
  conceitual do trabalho analítico: entendimento do negócio → entendimento dos dados →
  preparação → modelagem → avaliação → implantação. É usado aqui como **guia
  metodológico** do raciocínio analítico.
- **TDSP** (Team Data Science Process, Microsoft) fornece a **estrutura operacional de
  projeto**: papéis, artefatos padronizados (Project Charter, Data Summary Report,
  Model Report), organização de diretórios e ciclo de vida com fases iterativas. É usado
  aqui como o **framework de execução e organização** do repositório.

Na prática, cada fase do CRISP-DM é executada dentro de uma fase equivalente do TDSP,
que por sua vez determina onde os artefatos ficam versionados neste repositório.

## 2. Mapeamento de fases

| CRISP-DM | TDSP (ciclo de vida) | Artefato(s) TDSP | Neste projeto |
|---|---|---|---|
| Business Understanding | 1. Business Understanding | Project Charter | `Docs/Project/project_charter.md` |
| Data Understanding | 2. Data Acquisition & Understanding | Data Summary Report, Data Quality Report | `Docs/DataReport/data_summary_report.md` |
| Data Preparation | 2. Data Acquisition & Understanding | Scripts de ETL/limpeza | `Code/DataAcquisition/`, `Code/DataPreparation/` |
| Modeling | 3. Modeling | Feature sets, Model Report | `Code/Modeling/` (TP3: prompts-base em `prompts_llm.py`; modelagem com LLM no TP4) |
| Evaluation | 3. Modeling | Model Performance Report | `Code/Modeling/` (TP4) |
| Deployment | 4. Deployment | App + API implantáveis | `app.py` + `app_pages/` (Streamlit multipágina), `Code/API/` (FastAPI) |
| — | 5. Customer Acceptance | Exit Report | Entrega final do projeto (TP4) |

## 3. Papéis TDSP aplicados ao projeto (trabalho individual/acadêmico)

Como o projeto é conduzido academicamente (possivelmente por um aluno ou pequeno grupo),
os papéis do TDSP — *Group Manager, Team Lead, Project Lead, Data Scientist* — são
acumulados pelo(s) responsável(is) pelo projeto, mas as responsabilidades de cada papel
seguem sendo observadas nos artefatos correspondentes:

- **Project Lead:** mantém o Project Charter e o cronograma atualizados.
- **Data Scientist:** responsável pela coleta (`Code/DataAcquisition`), preparação
  (`Code/DataPreparation`), modelagem (`Code/Modeling`) e pelo Data Summary Report.

## 4. Estado atual do ciclo de vida (TP3)

- ✅ Business Understanding — Project Charter revisado no TP3 (problema reavaliado com
  FastAPI/Selenium).
- ✅ Data Acquisition & Understanding — scraping estático e dinâmico, API própria e
  corpus para LLMs; Data Summary Report revisado.
- 🟡 Modeling — preparado: casos de uso e prompts-base definidos; execução com LLM no TP4.
- 🟡 Deployment — app multipágina + API FastAPI funcionando localmente; deploy público
  em andamento.
- ⬜ Customer Acceptance — não iniciado (TP4).
