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
