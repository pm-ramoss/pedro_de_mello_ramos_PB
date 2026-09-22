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
| Modeling | 3. Modeling | Feature sets, Model Report | `Code/Modeling/` (próxima etapa) |
| Evaluation | 3. Modeling | Model Performance Report | `Code/Modeling/` (próxima etapa) |
| Deployment | 4. Deployment | Dashboard/app implantado | `app.py` (Streamlit) |
| — | 5. Customer Acceptance | Exit Report | Entrega final do projeto (TP3) |

## 3. Papéis TDSP aplicados ao projeto (trabalho individual/acadêmico)

Como o projeto é conduzido academicamente (possivelmente por um aluno ou pequeno grupo),
os papéis do TDSP — *Group Manager, Team Lead, Project Lead, Data Scientist* — são
acumulados pelo(s) responsável(is) pelo projeto, mas as responsabilidades de cada papel
seguem sendo observadas nos artefatos correspondentes:

- **Project Lead:** mantém o Project Charter e o cronograma atualizados.
- **Data Scientist:** responsável pela coleta (`Code/DataAcquisition`), preparação
  (`Code/DataPreparation`), modelagem (`Code/Modeling`) e pelo Data Summary Report.

## 4. Estado atual do ciclo de vida (TP1)

- ✅ Business Understanding — concluído (Project Charter).
- 🟡 Data Acquisition & Understanding — em andamento (scripts prontos, execução completa
  e Data Summary Report definitivo previstos para o TP2).
- ⬜ Modeling — não iniciado.
- 🟡 Deployment — aplicação demo inicial em Streamlit já disponível (`app.py`).
- ⬜ Customer Acceptance — não iniciado.
