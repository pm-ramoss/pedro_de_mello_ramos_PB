# Data Summary Report — Conecta Impacto (Finalizado — TP2)

Este documento relaciona as fontes de dados do projeto **Conecta Impacto**, com o tipo
de dado, formato, forma de coleta e objetivo de uso, e apresenta o Data Quality Report
das coletas executadas até o TP2.

## 1. Fontes de dados

| # | Fonte | Tipo de dado | Formato | Forma de coleta | Objetivo de uso |
|---|---|---|---|---|---|
| 1 | [Observatório do Terceiro Setor — Projetos Sociais](https://observatorio3setor.org.br/carrossel/lista-conheca-projetos-sociais-de-15-causas-diferentes/) | Catálogo de projetos sociais por causa (nome, causa, organização, descrição, link) | HTML (página web) | Web Scraping (`BeautifulSoup`/`requests`) — `Code/DataAcquisition/scraping_observatorio.py` | Base principal de projetos sociais a serem catalogados e classificados por ODS |
| 2 | Observatório do Terceiro Setor — Lista de causas sociais | Lista numerada de 15 causas sociais (taxonomia) | HTML (página web) | Web Scraping (`BeautifulSoup`) — `Code/DataAcquisition/scraping_causas_sociais.py` **(novo — TP2)** | Padronizar a taxonomia de causas usada para classificar os projetos |
| 3 | Portais de notícias sobre ESG / Agenda 2030 (ex.: Portal Tela, Atlas Público, Radar Digital Brasília, Folha de Pernambuco, SECOM UnB) | Notícias e artigos sobre ESG, ODS e Agenda 2030 no Brasil | HTML (página web) | Web Scraping (`BeautifulSoup`) — `Code/DataAcquisition/scraping_noticias_esg.py` **(novo — TP2)** | Alimentar a aba de notícias, gerar nuvem de palavras e estatísticas básicas de texto |
| 4 | API do IBGE — Localidades / SIDRA | Indicadores socioeconômicos por município/UF (ex.: população estimada) | JSON (API REST) | Requisição HTTP (`requests`) — `Code/DataAcquisition/coleta_ibge.py` | Contextualizar geograficamente os projetos sociais e apoiar priorização por regiões com maior desigualdade (ODS 10) |
| 5 | Dados internos gerados pelo projeto (dataset consolidado) | Projetos sociais + notícias, já limpos e padronizados | CSV | Gerado por `Code/DataPreparation/preparar_dados.py` | Alimentar as abas "Projetos Sociais" e "Notícias & Nuvem de Palavras" da aplicação |
| 6 | Upload de CSV pelo próprio usuário **(novo — TP2)** | Projetos sociais adicionais, no mesmo schema da base | CSV | Upload manual via `st.file_uploader` no app | Complementar a base de projetos durante a sessão do usuário, sem alterar código |

## 2. Data Quality Report (coletas executadas até o TP2)

| Dataset | Arquivo | Registros | Colunas essenciais sem valores faltantes | Observações |
|---|---|---|---|---|
| Projetos sociais (base curada) | `Data/Processed/projetos_sociais.csv` | 10 | 100% (`nome_projeto`, `causa`, `uf`) | Herdado da amostra do TP1; usado como entrada de teste do pipeline `preparar_dados.py` enquanto a coleta em produção do Observatório/Conecta Brasil (com classificação por ODS) não está automatizada — ver Riscos no Project Charter. |
| Causas sociais (scraping) | `Data/Raw/causas_observatorio.csv` | 7 de 15 esperadas | 100% | A página do Observatório limita a exibição inicial da lista numerada; os 7 primeiros itens foram extraídos com sucesso. O script cai em lista de contingência (`CAUSAS_FALLBACK`) caso a página fique indisponível. |
| Notícias ESG/ODS (scraping) | `Data/Raw/noticias_esg_ods.csv` + `Data/Raw/noticias_txt/*.txt` | 5 | 100% (`titulo`, `resumo`, `url`) | Coletadas de 5 fontes distintas; corpus de texto usado para nuvem de palavras tem 321 palavras (196 únicas). |
| Notícias processadas | `Data/Processed/noticias_processadas.csv` | 5 | 100% | Gerado por `preparar_dados.py noticias`, com deduplicação por `titulo`+`url` e normalização de data. |

## 3. Amostra utilizada na aplicação

A aplicação usa, por padrão, `Data/Processed/projetos_sociais.csv` (gerado a partir da
amostra do TP1 pelo pipeline de preparação) e cai de volta para
`SampleData/projetos_sociais_sample.csv` caso o arquivo processado não exista — o que
mantém a aplicação funcional mesmo antes de rodar os scripts de coleta. Estrutura de
colunas do dataset de projetos:

| Coluna | Descrição |
|---|---|
| `nome_projeto` | Nome do projeto social |
| `organizacao` | Organização/OSC responsável |
| `causa` | Causa social principal (ex.: educação, meio ambiente, saúde) |
| `ods_relacionado` | ODS(s) da Agenda 2030 relacionado(s) ao projeto |
| `cidade` | Cidade de atuação |
| `uf` | Unidade federativa |
| `descricao` | Descrição curta do projeto |
| `fonte` | Fonte de onde o dado foi obtido |
| `link` | Link para mais informações |

E do dataset de notícias:

| Coluna | Descrição |
|---|---|
| `titulo` | Título da notícia |
| `fonte` | Nome do veículo/portal |
| `url` | Link para a notícia original |
| `data_publicacao` | Data de publicação (normalizada) |
| `resumo` | Resumo de poucas frases (paráfrase, não reprodução literal do texto original) |
| `ods_relacionado` | ODS associado ao conteúdo da notícia |

## 4. Observações e limitações conhecidas

- Os dados de Web Scraping dependem da estrutura HTML atual dos sites-fonte, que pode
  mudar sem aviso — os parsers serão revisados a cada execução relevante; scripts
  possuem fallback para não quebrar o pipeline.
- A API do IBGE fornece dados agregados por município/UF, não por projeto individual; o
  cruzamento com os projetos sociais será feito por localização (cidade/UF) em etapa
  futura de modelagem.
- Os resumos de notícias são escritos como paráfrase curta do conteúdo original (não
  reprodução literal), respeitando direitos autorais dos veículos de origem; o link
  para a fonte original é sempre preservado.
- Dados enviados por upload de CSV (`aba "Meus Dados"`) não são persistidos em disco:
  eles vivem apenas em `st.session_state` durante a sessão do navegador. Persistência
  definitiva (banco de dados) é um item planejado para o TP3.
- Uso de licença/termos de uso de cada fonte deve ser respeitado; os dados são coletados
  para fins acadêmicos e não comerciais.
