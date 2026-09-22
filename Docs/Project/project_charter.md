# Project Charter — Conecta Impacto

*(Atualizado no TP2 — seções 8 e 9 revisadas; demais seções herdadas do TP1.)*

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

## 3. Objetivos do projeto

### Objetivo de negócio
Aumentar a visibilidade de projetos sociais brasileiros e facilitar decisões de doação,
voluntariado e investimento social por parte de pessoas físicas e empresas.

### Objetivo do projeto de dados
Construir um dashboard interativo (Streamlit) que integre dados coletados via
Web Scraping e APIs públicas, organizados e classificados por causa/ODS, com uma
camada de conteúdo contextual (notícias) e um canal para que os próprios usuários
complementem a base (upload de CSV). Em etapas futuras, usar LLMs para classificar,
resumir e recomendar projetos automaticamente.

## 4. Metas e indicadores de sucesso (KPIs)

| Indicador | Meta (fim do projeto) | Status no TP2 |
|---|---|---|
| Nº de projetos sociais catalogados na base | ≥ 100 projetos | 10 (amostra curada) + upload do usuário |
| Nº de ODS cobertos pela base de projetos | ≥ 8 dos 17 ODS | 8 ODS cobertos na amostra |
| Cobertura geográfica (UFs representadas) | ≥ 10 estados | 9 UFs na amostra |
| Fontes de dados integradas (API + scraping) | ≥ 3 fontes distintas | 3 (IBGE, Observatório do Terceiro Setor, notícias ESG diversas) |
| Disponibilidade da aplicação demo | App Streamlit funcional, pronto para deploy | Concluído (cache, sessão, upload/download) |
| Qualidade dos dados (registros sem valores essenciais faltantes) | ≥ 90% dos registros completos | 100% na amostra curada |

> A expansão para ≥ 100 projetos catalogados depende da execução periódica dos
> scripts de scraping em produção (etapa prevista para o TP3, com agendamento e
> persistência em banco de dados).

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

## 8. Escopo (atualizado no TP2)

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

### Fora do escopo (previsto para o TP3)
- Classificação automática de projetos por ODS via LLM.
- Motor de recomendação/matching doador↔projeto.
- Coleta em produção (agendada/automatizada) e persistência em banco de dados
  (os dados enviados via upload hoje vivem apenas na sessão do usuário).
- Autenticação de usuários e funcionalidades transacionais (doação online, etc.).

## 9. Cronograma de alto nível (fases TDSP)

| Fase TDSP | Entregável principal | Etapa | Status |
|---|---|---|---|
| Business Understanding | Project Charter | TP1 | Concluído |
| Data Acquisition & Understanding | Data Summary Report + scripts de coleta | TP1 (esboço) / TP2 | **Concluído no TP2** |
| Data Preparation | Limpeza/consolidação de projetos e notícias | TP2 | **Concluído no TP2** |
| Modeling | Classificação por ODS, matching | TP3 | Planejado |
| Deployment | Dashboard Streamlit completo em produção | TP2 (preparação) / TP3 (deploy efetivo) | Em andamento |
| Customer Acceptance | Validação final e entrega | TP3 | Planejado |

## 10. Riscos e premissas

- **Risco:** instabilidade ou mudança de estrutura nos sites usados para scraping →
  mitigação: isolar a lógica de parsing em módulos próprios, versionar seletores e
  manter listas de contingência (`CAUSAS_FALLBACK`) para não quebrar o pipeline.
- **Risco:** dados incompletos ou desatualizados nas fontes públicas → mitigação: cruzar
  múltiplas fontes e documentar limitações no Data Summary Report.
- **Risco (novo no TP2):** dados enviados pelo usuário via upload não persistem entre
  sessões (armazenados apenas em `st.session_state`) → mitigação planejada para o TP3:
  persistência em banco de dados ou arquivo compartilhado.
- **Premissa:** as fontes de dados usadas (IBGE, Observatório do Terceiro Setor, portais
  de notícias) permanecem publicamente acessíveis durante o desenvolvimento do projeto.
