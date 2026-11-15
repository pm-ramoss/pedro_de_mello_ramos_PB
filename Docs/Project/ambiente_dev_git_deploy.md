# Ambiente de Desenvolvimento, Controle de Versão (Git) e Preparação para Deploy — TP2

Este documento complementa o `README.md` e descreve como configurar o ambiente
de desenvolvimento do **Conecta Impacto**, versionar o projeto com Git e
prepará-lo para deploy, conforme pedido no TP2.

## 1. Ambiente de desenvolvimento

```bash
pyenv install 3.11.9
pyenv virtualenv 3.11.9 conecta-impacto
pyenv local conecta-impacto
pip install -r requirements.txt
```

Alternativa sem `pyenv` (venv padrão):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Controle de versão com Git

Se o projeto ainda não é um repositório Git:

```bash
git init
git add .
git commit -m "TP1: proposta, planejamento e demo inicial em Streamlit"
```

Para incorporar as mudanças do TP2 (depois de copiar os arquivos deste pacote
para o repositório, conforme o `README.md` na raiz deste `.zip`):

```bash
git add .
git commit -m "TP2: interface dinâmica, scraping de dados, cache/estado de sessão, upload/download de CSV"
```

Recomendações:
- Use branches por etapa/funcionalidade (`git checkout -b feature/nuvem-palavras`)
  e faça merge para `main` ao concluir, mesmo em projetos individuais — isso
  documenta a evolução do trabalho de forma organizada.
- Escreva mensagens de commit descritivas, referenciando a fase do
  CRISP-DM/TDSP à qual a mudança pertence (ex.: "Data Preparation: limpeza do
  dataset de notícias").
- Não versione segredos (chaves de API) nem dados brutos sensíveis — veja o
  `.gitignore` incluído neste pacote.

## 3. GitHub (armazenamento remoto do repositório)

```bash
gh repo create conecta-impacto --public --source=. --remote=origin
# ou, manualmente, crie o repositório pelo site do GitHub e depois:
git remote add origin https://github.com/<seu-usuario>/conecta-impacto.git
git branch -M main
git push -u origin main
```

## 4. Preparação para deploy (Streamlit Community Cloud)

1. Garanta que `requirements.txt` está atualizado na raiz do repositório
   (já incluso neste pacote, com `wordcloud` e `matplotlib` adicionados).
2. Garanta que `app.py` está na raiz do repositório.
3. Publique o repositório no GitHub (passo anterior).
4. Em [share.streamlit.io](https://share.streamlit.io), clique em
   **"New app"**, selecione o repositório, a branch (`main`) e o arquivo
   principal (`app.py`).
5. Caso alguma etapa futura use chaves de API (ex.: `anthropic`), configure-as
   em **Settings → Secrets** do próprio Streamlit Cloud — nunca no código ou
   no Git.
6. Após o deploy, valide manualmente cada aba da aplicação (ver checklist de
   testes no `README.md`).

## 5. Estrutura de diretórios (TDSP/CRISP-DM) — reforço no TP2

A estrutura de diretórios do TP1 foi mantida (ver `README.md` original) e
ampliada com os novos artefatos deste TP2:

```
Code/DataAcquisition/
├── coleta_ibge.py                (TP1)
├── scraping_observatorio.py      (TP1)
├── scraping_causas_sociais.py    (novo — TP2)
└── scraping_noticias_esg.py      (novo — TP2)
Code/DataPreparation/
├── preparar_dados.py             (modificado — TP2: agora processa projetos e notícias)
└── gerar_nuvem_palavras.py       (novo — TP2)
Data/Raw/
├── causas_observatorio.csv       (novo — TP2)
├── noticias_esg_ods.csv          (novo — TP2)
└── noticias_txt/                 (novo — TP2, corpus para nuvem de palavras)
Data/Processed/
├── projetos_sociais.csv          (novo — TP2, gerado por preparar_dados.py)
└── noticias_processadas.csv      (novo — TP2, gerado por preparar_dados.py)
```

## 6. Ambiente, execução e deploy no TP3

### 6.1 Dependências novas

`requirements.txt` ganhou `fastapi`, `uvicorn` (servidor da API) e `selenium` (scraping
dinâmico, opcional). Após atualizar o repositório:

```bash
pip install -r requirements.txt
```

### 6.2 Executando API e aplicação (dois terminais, na raiz do projeto)

```bash
# Terminal 1 — API (http://localhost:8000, Swagger em /docs)
uvicorn main:app --reload --app-dir Code/API --port 8000

# Terminal 2 — aplicação Streamlit (http://localhost:8501)
streamlit run app.py
```

Para apontar o app para outro endereço de API: `export CONECTA_API_URL=http://host:porta`
(Windows PowerShell: `$env:CONECTA_API_URL="http://host:porta"`).

A API é **opcional para o app**: sem ela, o app lê os mesmos CSVs de `Data/Processed/`
(a barra lateral indica qual modo está ativo).

### 6.3 Scripts auxiliares

```bash
python Code/DataPreparation/preparar_corpus_llm.py          # gera Data/Processed/corpus_llm.jsonl
python Code/DataAcquisition/scraping_dinamico_selenium.py   # opcional: requer Selenium + Chrome
```

### 6.4 Git — sugestão de commits do TP3

```bash
git checkout -b tp3-api-multipagina
git add Code/API app_utils.py
git commit -m "Deployment: API FastAPI (GET/POST) com camada de dados compartilhada"
git add app.py app_pages
git commit -m "Deployment: app Streamlit multipágina com st.navigation e contingência sem API"
git add Code/DataAcquisition Code/DataPreparation Code/Modeling Data/Processed/corpus_llm.jsonl
git commit -m "Data Acquisition/Modeling: scraping dinâmico (Selenium) e preparação para LLMs"
git add Docs README.md requirements.txt .gitignore
git commit -m "Docs: revisão do Project Charter e do Data Summary Report (TP3)"
git checkout main && git merge tp3-api-multipagina
```

### 6.5 Deploy

- **Streamlit Community Cloud** executa apenas o `app.py`; a API não sobe junto. Nesse
  cenário o app cai automaticamente no modo "arquivos locais". Como o disco é efêmero,
  cadastros feitos lá podem ser perdidos em reinícios.
- Para publicar a API, use um serviço que execute processos (Render, Railway, Fly.io etc.)
  com o comando `uvicorn main:app --app-dir Code/API --host 0.0.0.0 --port $PORT` e
  defina `CONECTA_API_URL` nos *Secrets*/variáveis do app Streamlit.

### 6.6 Estrutura de diretórios — acréscimos do TP3

```
app.py                              (reescrito — ponto de entrada e menu de navegação)
app_utils.py                        (novo — cliente da API + contingência)
app_pages/                          (novo — 7 páginas)
Code/API/                           (novo — main.py, schemas.py, repositorio.py)
Code/DataAcquisition/scraping_dinamico_selenium.py   (novo)
Code/DataPreparation/preparar_corpus_llm.py          (novo)
Code/Modeling/prompts_llm.py                         (novo)
Data/Processed/corpus_llm.jsonl                      (novo)
Data/Processed/projetos_enviados.csv                 (criado no primeiro POST; ignorado pelo Git)
Docs/API/api_documentacao.md                         (novo)
Docs/Project/preparacao_llm.md                       (novo)
```
