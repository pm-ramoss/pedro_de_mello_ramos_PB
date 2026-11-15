# Documentação da API — Conecta Impacto (TP3)

API REST construída com **FastAPI** (`Code/API/main.py`). A documentação interativa
(Swagger UI) é gerada automaticamente em `http://localhost:8000/docs`; este arquivo
resume o contrato e explica **para que serve cada rota e como usá-la**.

## Como executar

```bash
pip install -r requirements.txt
uvicorn main:app --reload --app-dir Code/API --port 8000
```

Arquitetura: `main.py` (rotas) → `schemas.py` (validação/serialização com Pydantic) →
`repositorio.py` (leitura/escrita dos CSVs em `Data/Processed/`). O mesmo
`repositorio.py` é usado pelo app Streamlit quando a API está fora do ar.

## Resumo das rotas

| Método | Rota | Função | Códigos |
|---|---|---|---|
| GET | `/saude` | Verifica se a API está no ar | 200 |
| GET | `/projetos` | Lista projetos com filtros e paginação | 200, 422 |
| GET | `/projetos/{projeto_id}` | Retorna um projeto pelo id | 200, 404 |
| **POST** | `/projetos` | Cadastra um novo projeto | 201, 409, 422 |
| GET | `/noticias` | Lista notícias ESG/Agenda 2030 | 200 |
| GET | `/estatisticas` | Contagens por causa, UF e ODS | 200 |
| GET | `/llm/documentos` | Documentos de texto prontos para LLMs | 200, 422 |

## GET /projetos — consulta de dados

**Função:** devolver os projetos sociais (base curada + cadastrados via POST) para
exibição, filtros e análises.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `causa` | string | Causa exata (ignora maiúsculas), ex.: `Educação` |
| `uf` | string (2) | Sigla da UF, ex.: `SP` |
| `ods` | string | Número (`4`, `ODS 4`) ou parte do nome (`Educação`) |
| `busca` | string | Texto livre em nome, organização, causa e descrição |
| `limite` | int 1–1000 | Itens por página (padrão 50) |
| `offset` | int ≥ 0 | Itens a pular (padrão 0) |

```bash
curl "http://localhost:8000/projetos?uf=SP&ods=4&limite=10"
```

Resposta (resumida):

```json
{
  "total": 1, "limite": 10, "offset": 0,
  "itens": [{
    "id": "73b7ea4f45",
    "nome_projeto": "Escola de Robótica Comunitária",
    "organizacao": "Instituto Aprender Mais",
    "causa": "Educação",
    "ods_relacionado": "ODS 4 - Educação de Qualidade",
    "cidade": "São Paulo", "uf": "SP",
    "descricao": "Oficinas gratuitas de robótica ...",
    "fonte": "Observatório do Terceiro Setor",
    "link": "https://observatorio3setor.org.br/"
  }]
}
```

`total` é o número de registros após os filtros, antes da paginação.

## GET /projetos/{projeto_id}

Retorna um único projeto; o `id` é o campo devolvido por `GET /projetos` (hash estável de
nome + link). Responde **404** se não existir.

## POST /projetos — envio de novos dados

**Função:** permitir que OSCs, o app (formulário ou upload de CSV) ou outros sistemas
cadastrem projetos. Os dados são gravados em `Data/Processed/projetos_enviados.csv` e
**persistem** entre execuções.

Corpo (JSON):

| Campo | Obrigatório | Regras |
|---|---|---|
| `nome_projeto` | sim | 3–200 caracteres |
| `organizacao` | sim | 2–200 caracteres |
| `causa` | sim | 2–100 caracteres |
| `uf` | sim | sigla válida das 27 UFs (convertida para maiúsculas) |
| `ods_relacionado` | não | texto; vários ODS separados por `;` |
| `cidade`, `descricao`, `fonte`, `link` | não | `link`, se informado, deve começar com http:// ou https:// |

```bash
curl -X POST http://localhost:8000/projetos \
  -H "Content-Type: application/json" \
  -d '{"nome_projeto":"Cozinha Solidária do Bairro","organizacao":"Associação Mesa Cheia",
       "causa":"Segurança alimentar","ods_relacionado":"ODS 2 - Fome Zero",
       "cidade":"Recife","uf":"PE"}'
```

Respostas: **201** com o projeto criado (incluindo `id`); **409** se já existir projeto
com o mesmo nome + link; **422** se algum campo for inválido (detalhes por campo).

## GET /noticias

Lista as notícias coletadas por scraping. Filtros: `ods` (número ou nome) e `busca`
(título/resumo). Retorna `id`, `titulo`, `fonte`, `url`, `data_publicacao`, `resumo`,
`ods_relacionado`.

## GET /estatisticas

Totais (`total_projetos`, `total_projetos_enviados`, `total_noticias`, `n_causas`,
`n_ufs`, `n_ods`) e contagens `projetos_por_causa`, `projetos_por_uf`,
`projetos_por_ods`, `noticias_por_ods`. Alimenta a página "Estatísticas e Gráficos".

## GET /llm/documentos

Projetos e notícias convertidos em documentos `{id, tipo, titulo, texto, metadados,
tokens_estimados}`, com filtro opcional `tipo=projeto|noticia`. É a ponte para as tarefas
de LLM do TP4 (ver `Docs/Project/preparacao_llm.md`).

## Como o app usa a API

`app_utils.py` consulta `GET /saude`; se a API responder, todas as páginas usam os
endpoints acima, e a barra lateral mostra "API online". Caso contrário, o app lê os mesmos
arquivos via `repositorio.py` e exibe "API offline". Cadastros feitos pelo app usam
`POST /projetos` (ou gravação local equivalente na contingência).

## Limitações

- Sem autenticação nem controle de taxa (uso acadêmico/local).
- Persistência em CSV (sem transações; gravações são serializadas por um *lock* dentro de
  um único processo).
