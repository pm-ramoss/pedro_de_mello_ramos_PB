# Project Charter — Conecta Impacto

*(Revisado no TP4 — seções 4, 8, 9 e 10 atualizadas com a integração de LLM local; seções 2 e 3 revisadas no TP3.)*

## 1. Nome do projeto
**Conecta Impacto** — Plataforma de inteligência de dados para conexão entre projetos
sociais e doadores/voluntários alinhados a agendas ESG.

## 2. Contexto e problema de negócio

Organizações da sociedade civil (OSCs), sobretudo de pequeno e médio porte, têm
dificuldade em ganhar visibilidade e em demonstrar, com dados, o impacto de seus
projetos sociais. Do outro lado, empresas com compromissos ESG e pessoas físicas
dispostas a doar ou atuar como voluntárias não têm um canal simples para **descobrir,
comparar e priorizar** projetos sociais confiáveis, alinhados às causas e aos Objetivos
de Desenvolvimento Sustentável (ODS) que desejam apoiar.

Esse descompasso entre oferta (projetos sociais que precisam de recursos/voluntários) e
demanda (doadores/voluntários que precisam de projetos confiáveis e mensuráveis) reduz a
eficiência da filantropia e do investimento social privado no Brasil.

**Problema de negócio:** como identificar, organizar e apresentar, de forma confiável e
navegável, informações sobre projetos sociais brasileiros — cruzadas com indicadores
socioeconômicos regionais — para facilitar a conexão entre esses projetos e
doadores/voluntários/empresas com agenda ESG?

### 2.1 Reavaliação do problema à luz das novas ferramentas (TP3)

O problema de negócio **permanece o mesmo**, mas as ferramentas do TP3 mudam a forma de
atacá-lo:

- **FastAPI** transforma a base de projetos em um *serviço*: deixa de ser apenas um CSV
  lido pelo dashboard e passa a poder ser consultada (`GET`) e **alimentada por terceiros
  (`POST`)**. Isso ataca diretamente o lado da *oferta* do problema — OSCs podem cadastrar
  seus próprios projetos — e resolve o risco do TP2 de que os dados enviados se perdiam
  ao fim da sessão.
- **Selenium** responde a uma limitação medida no TP2: a página de causas do Observatório
  rendeu só 7 das 15 causas porque parte do conteúdo depende de JavaScript. Ele é usado de
  forma **restrita e opcional** (um único script), seguindo a orientação de manter a
  simplicidade: o restante da coleta continua em BeautifulSoup/`requests`.
- A **aplicação multipágina** separa as tarefas de cada tipo de usuário (explorar projetos,
  ver indicadores, cadastrar dados) em vez de concentrá-las em abas de uma só tela.

**Meta ajustada:** além de "catalogar ≥ 100 projetos", passa a ser meta que a base possa
crescer **sem alterar código**, via API ou upload persistente (ver KPIs, seção 4).

## 3. Objetivos do projeto

### Objetivo de negócio
Aumentar a visibilidade de projetos sociais brasileiros e facilitar decisões de doação,
voluntariado e investimento social por parte de pessoas físicas e empresas.

### Objetivo do projeto de dados
Construir uma aplicação interativa (Streamlit, multipágina) apoiada em uma **API própria
(FastAPI)**, que integre dados coletados via Web Scraping (estático e dinâmico) e APIs
públicas, organizados e classificados por causa/ODS, com uma camada de conteúdo contextual
(notícias) e um canal persistente para que os próprios usuários complementem a base
(cadastro/upload via `POST /projetos`). Na próxima etapa (TP4), usar LLMs para classificar,
resumir e recomendar projetos automaticamente — os dados e os prompts-base já ficam
preparados no TP3.

## 4. Metas e indicadores de sucesso (KPIs)

| Indicador | Meta (fim do projeto) | Status no TP3 |
|---|---|---|
| Nº de projetos sociais catalogados na base | ≥ 100 projetos | 10 (base curada) + cadastros via API/upload (persistentes) |
| Nº de ODS cobertos pela base de projetos | ≥ 8 dos 17 ODS | **12 ODS** cobertos (meta atingida) |
| Cobertura geográfica (UFs representadas) | ≥ 10 estados | 9 UFs |
| Fontes de dados integradas (API + scraping) | ≥ 3 fontes distintas | 3 fontes externas + API própria do projeto |
| Disponibilidade da aplicação | App Streamlit funcional, pronto para deploy | Concluído: 7 páginas com menu de navegação; modo contingência sem API |
| Qualidade dos dados (registros sem valores essenciais faltantes) | ≥ 90% dos registros completos | 100% na base curada; `POST /projetos` valida UF, link e tamanhos |
| **(novo)** Endpoints da API documentados e testados | ≥ 2 rotas (GET e POST) | 7 rotas (6 GET + 1 POST), documentação em `/docs` e em `Docs/API/` |
| **(novo)** Corpus preparado para LLMs | Documentos texto + metadados | 15 documentos (10 projetos + 5 notícias) em `corpus_llm.jsonl` |
| **(novo — TP4)** Integração com LLM local | ≥ 1 tarefa de PLN via FastAPI, sem nuvem | 2 tarefas (resumo e sentimento) em `POST /processar_texto`; modelos justificados em `Docs/Project/escolha_modelo_llm.md` |
| **(novo — TP4)** Robustez da API | Erros HTTP específicos e respostas validadas | 422/500/503/504 padronizados + Response Models; 12 testes automatizados do serviço |

> A expansão para ≥ 100 projetos catalogados depende de coleta em escala (scraping
> agendado) e do uso da API de cadastro por OSCs. O TP3 entrega a infraestrutura para
> isso (API + persistência em CSV); agendamento e banco de dados permanecem como evolução.

## 5. ODS (Agenda 2030) atendido(s)

- **ODS 17 — Parcerias e Meios de Implementação (principal):** o projeto atua
  diretamente como um facilitador de parcerias entre setor privado, sociedade civil e
  cidadãos, ampliando o acesso à informação necessária para viabilizar apoio financeiro
  e voluntário a iniciativas sociais.
- **ODS 10 — Redução das Desigualdades (secundário):** ao cruzar os projetos sociais com
  indicadores socioeconômicos regionais (ex.: IBGE), a plataforma ajuda a direcionar
  recursos para regiões e causas com maior necessidade, contribuindo para reduzir
  desigualdades territoriais.

**Justificativa:** a proposta não presta um serviço social diretamente, mas atua como
**infraestrutura de informação** que reduz o custo de coordenação entre quem tem
recursos (doadores/empresas ESG) e quem precisa deles (OSCs), o que é exatamente o
espírito do ODS 17. Ao priorizar visibilidade de dados regionais de desigualdade, a
solução também instrumentaliza decisões que favorecem o ODS 10.

## 6. Público-alvo

- **Empresas com agenda ESG** que buscam projetos sociais para patrocínio, investimento
  social privado ou voluntariado corporativo.
- **Pessoas físicas doadoras/voluntárias** interessadas em causas específicas.
- **OSCs/ONGs de pequeno e médio porte** que ganham visibilidade ao terem seus projetos
  catalogados e contextualizados com dados.

## 7. Stakeholders

| Papel | Stakeholder |
|---|---|
| Patrocinador acadêmico | Professor(a)/disciplina responsável pela avaliação do projeto |
| Equipe do projeto | Aluno(a) responsável pelo desenvolvimento (coleta, modelagem, app) |
| Usuários finais | Empresas ESG, doadores/voluntários pessoa física |
| Beneficiários indiretos | OSCs/ONGs catalogadas na plataforma |
| Fontes de dados | IBGE, Observatório do Terceiro Setor, Conecta Brasil, portais de notícias ESG/ODS |

## 8. Escopo (atualizado no TP3)

### Concluído no TP1
- Definição do problema, metas, ODS e público-alvo.
- Estruturação do projeto em CRISP-DM/TDSP.
- Organização de diretórios e artefatos iniciais (Project Charter, Data Summary Report).
- Aplicação demo em Streamlit com dados de amostra estática.

### Concluído no TP2
- Configuração formal do ambiente de desenvolvimento, Git e preparação para deploy
  (`Docs/Project/ambiente_dev_git_deploy.md`).
- Interface Streamlit reorganizada em abas dinâmicas (visão geral, projetos, notícias,
  meus dados), com filtros, busca textual e favoritos.
- Extração de conteúdo web com BeautifulSoup: causas sociais
  (`scraping_causas_sociais.py`) e notícias ESG/Agenda 2030
  (`scraping_noticias_esg.py`), com dados salvos em CSV/TXT em `Data/`.
- Nuvem de palavras e estatísticas básicas geradas a partir do corpus de notícias.
- Cache (`st.cache_data`) e estado de sessão (`st.session_state`) para performance e
  persistência de filtros/favoritos/uploads durante a sessão do usuário.
- Serviço de upload/download de arquivos CSV, permitindo que o usuário complemente a
  base de projetos sociais.
- Finalização do Project Charter e do Data Summary Report.

### Concluído no TP3
- **Aplicação multipágina** em Streamlit (`st.navigation`), com 7 páginas: Visão Geral,
  Projetos, Estatísticas e Gráficos, Notícias, Meus Dados, Console da API e Preparação
  para LLMs (`app.py` + `app_pages/`).
- **API FastAPI** (`Code/API/`) com 7 rotas — consulta (`GET /projetos`, `/projetos/{id}`,
  `/noticias`, `/estatisticas`, `/llm/documentos`, `/saude`) e envio de dados
  (`POST /projetos`) — documentada em `Docs/API/api_documentacao.md` e em `/docs`.
- **Persistência** dos dados enviados (`Data/Processed/projetos_enviados.csv`), mitigando
  o risco aberto no TP2.
- **Integração app ↔ API** com contingência: se a API estiver fora do ar, o app lê os
  mesmos arquivos (útil para deploy no Streamlit Community Cloud).
- **Scraping dinâmico** com Selenium (`scraping_dinamico_selenium.py`), restrito ao caso
  que o BeautifulSoup não resolve (lista de causas carregada via JavaScript).
- **Preparação para LLMs:** corpus JSONL (`preparar_corpus_llm.py`), endpoint
  `/llm/documentos`, prompts-base por caso de uso (`Code/Modeling/prompts_llm.py`) e
  documento `Docs/Project/preparacao_llm.md`.
- Revisão do Project Charter e do Data Summary Report.

### Concluído no TP4
- **LLM local (HuggingFace):** resumo (`recogna-nlp/ptt5-base-summ`) e sentimento
  (`lxyuan/distilbert-base-multilingual-cased-sentiments-student`), carregados sob demanda
  por `Code/API/llm_service.py` e expostos em `POST /processar_texto` e `GET /llm/status`.
- **Response Models** com tipo discriminado por tarefa e **tratamento de erros** com
  exceções específicas (422, 500, 503, 504) em formato padronizado.
- Página **🧠 Análise de Texto** no app (texto livre e sentimento em lote das notícias).
- Justificativa da escolha dos modelos, custo local e testes: `Docs/Project/escolha_modelo_llm.md`.

### Fora do escopo (previsto para a entrega final)
- Classificação automática de projetos por ODS e Q&A sobre os projetos com LLM (prompts já preparados no TP3).
- Avaliação quantitativa dos modelos com dados rotulados.
- Motor de recomendação/matching doador↔projeto.
- Coleta agendada em produção e banco de dados relacional (hoje: arquivos CSV).
- Autenticação de usuários na API e funcionalidades transacionais (doação online, etc.).

## 9. Cronograma de alto nível (fases TDSP)

| Fase TDSP | Entregável principal | Etapa | Status |
|---|---|---|---|
| Business Understanding | Project Charter | TP1 | Concluído |
| Data Acquisition & Understanding | Data Summary Report + scripts de coleta | TP1 (esboço) / TP2 | **Concluído no TP2** |
| Data Preparation | Limpeza/consolidação de projetos e notícias | TP2 | **Concluído no TP2** |
| Data Acquisition & Understanding (revisão) | Novas fontes: scraping dinâmico, API própria, corpus LLM | TP3 | **Concluído no TP3** |
| Deployment (parcial) | App multipágina + API FastAPI | TP3 | **Concluído no TP3** (deploy público em andamento) |
| Modeling | Resumo e sentimento com LLM local via API | TP4 | **Concluído no TP4** (avaliação com dados rotulados pendente) |
| Modeling (cont.) | Classificação por ODS, Q&A, matching | Entrega final | Planejado |
| Customer Acceptance | Validação final e apresentação | Entrega final | Planejado |

## 10. Riscos e premissas

- **Risco:** instabilidade ou mudança de estrutura nos sites usados para scraping →
  mitigação: isolar a lógica de parsing em módulos próprios, versionar seletores e
  manter listas de contingência (`CAUSAS_FALLBACK`) para não quebrar o pipeline.
- **Risco:** dados incompletos ou desatualizados nas fontes públicas → mitigação: cruzar
  múltiplas fontes e documentar limitações no Data Summary Report.
- **Risco (TP2) — mitigado no TP3:** dados enviados pelo usuário não persistiam entre
  sessões → agora `POST /projetos` grava em `Data/Processed/projetos_enviados.csv`.
  *Risco residual:* em hospedagens de disco efêmero (ex.: Streamlit Community Cloud) o
  arquivo pode ser perdido em reinícios → solução definitiva é um banco de dados (TP4+).
- **Risco (novo no TP3):** a API não tem autenticação, então qualquer cliente pode
  cadastrar projetos → mitigação: validação de campos (UF, link, tamanhos), bloqueio de
  duplicados (409) e uso restrito a ambiente local/acadêmico; autenticação fica como
  evolução.
- **Risco (novo no TP3):** o scraping com Selenium depende de Chrome instalado e da
  estrutura da página → mitigação: o script é opcional, falha sem alterar dados
  existentes, e reaproveita o parser testado do TP2.
- **Risco (novo no TP4):** o modelo local pode falhar ao carregar (falta de RAM/disco, sem internet no primeiro download) → mitigação: erro 503 explicativo, `GET /llm/status`, modo offline após `baixar_modelos.py` e app que continua funcionando sem o LLM.
- **Risco (novo no TP4):** qualidade limitada de modelos pequenos (resumos podem omitir fatos; sentimento de notícias tende ao neutro) → mitigação: a API devolve texto de entrada e pontuações para conferência; avaliação com dados rotulados na etapa final.
- **Risco (novo no TP3):** a base tem só 10 projetos, o que limita a qualidade de testes
  com LLM no TP4 → mitigação: ampliar a base via scraping/API antes da modelagem.
- **Premissa:** as fontes de dados usadas (IBGE, Observatório do Terceiro Setor, portais
  de notícias) permanecem publicamente acessíveis durante o desenvolvimento do projeto.
