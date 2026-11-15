"""
API do Conecta Impacto (FastAPI) — TP3.

Expõe os dados do projeto (projetos sociais e notícias ESG/Agenda 2030) para a
aplicação Streamlit e para qualquer outro cliente HTTP.

Como executar (a partir da raiz do projeto):

    uvicorn main:app --reload --app-dir Code/API --port 8000

Documentação interativa gerada automaticamente:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc
"""

from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Query

import repositorio as repo
from schemas import (
    DocumentoLLM,
    Estatisticas,
    ListaProjetos,
    Noticia,
    ProjetoIn,
    ProjetoOut,
)

TAGS = [
    {"name": "Projetos", "description": "Consulta e cadastro de projetos sociais."},
    {"name": "Notícias", "description": "Notícias sobre ESG / Agenda 2030 coletadas por scraping."},
    {"name": "Análises", "description": "Estatísticas agregadas e corpus preparado para LLMs."},
    {"name": "Sistema", "description": "Verificação de saúde da API."},
]

app = FastAPI(
    title="Conecta Impacto — API",
    version="0.3.0",
    summary="Dados de projetos sociais e notícias ESG/Agenda 2030.",
    description=(
        "API do projeto **Conecta Impacto** (TP3). Permite consultar projetos sociais "
        "(`GET /projetos`), cadastrar novos (`POST /projetos`), listar notícias, obter "
        "estatísticas e exportar documentos de texto para uso futuro com LLMs."
    ),
    openapi_tags=TAGS,
)


@app.get("/saude", tags=["Sistema"], summary="Verifica se a API está no ar")
def saude() -> dict:
    return {"status": "ok", "versao": app.version}


# --------------------------------------------------------------------------
# Projetos
# --------------------------------------------------------------------------
@app.get("/projetos", response_model=ListaProjetos, tags=["Projetos"], summary="Lista projetos sociais")
def listar_projetos(
    causa: Annotated[str | None, Query(description="Causa exata (sem diferenciar maiúsculas)")] = None,
    uf: Annotated[str | None, Query(description="Sigla da UF, ex.: SP", max_length=2)] = None,
    ods: Annotated[str | None, Query(description="Número ou nome do ODS, ex.: 4 ou 'Educação'")] = None,
    busca: Annotated[str | None, Query(description="Texto livre em nome, organização, causa e descrição")] = None,
    limite: Annotated[int, Query(ge=1, le=1000, description="Itens por página")] = 50,
    offset: Annotated[int, Query(ge=0, description="Quantos itens pular")] = 0,
) -> dict:
    """Retorna os projetos (base curada + enviados via POST), com filtros combináveis e paginação."""
    df = repo.filtrar_projetos(repo.carregar_projetos(), causa=causa, uf=uf, ods=ods, busca=busca)
    pagina = df.iloc[offset: offset + limite]
    return {
        "total": int(len(df)),
        "limite": limite,
        "offset": offset,
        "itens": pagina.to_dict("records"),
    }


@app.get(
    "/projetos/{projeto_id}",
    response_model=ProjetoOut,
    tags=["Projetos"],
    summary="Busca um projeto pelo id",
    responses={404: {"description": "Projeto não encontrado"}},
)
def obter_projeto(projeto_id: Annotated[str, Path(description="Id retornado por GET /projetos")]) -> dict:
    df = repo.carregar_projetos()
    achado = df[df["id"] == projeto_id]
    if achado.empty:
        raise HTTPException(status_code=404, detail=f"Projeto {projeto_id!r} não encontrado.")
    return achado.iloc[0].to_dict()


@app.post(
    "/projetos",
    response_model=ProjetoOut,
    status_code=201,
    tags=["Projetos"],
    summary="Cadastra um novo projeto social",
    responses={409: {"description": "Projeto já cadastrado (mesmo nome + link)"}},
)
def criar_projeto(projeto: ProjetoIn) -> dict:
    """Valida os campos (UF, link, tamanhos) e grava em `Data/Processed/projetos_enviados.csv`."""
    try:
        return repo.adicionar_projeto(projeto.model_dump())
    except repo.ProjetoDuplicadoError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# Notícias
# --------------------------------------------------------------------------
@app.get("/noticias", response_model=list[Noticia], tags=["Notícias"], summary="Lista notícias coletadas")
def listar_noticias(
    ods: Annotated[str | None, Query(description="Número ou nome do ODS")] = None,
    busca: Annotated[str | None, Query(description="Texto livre no título ou resumo")] = None,
) -> list[dict]:
    return repo.filtrar_noticias(repo.carregar_noticias(), ods=ods, busca=busca).to_dict("records")


# --------------------------------------------------------------------------
# Análises
# --------------------------------------------------------------------------
@app.get("/estatisticas", response_model=Estatisticas, tags=["Análises"], summary="Contagens agregadas")
def obter_estatisticas() -> dict:
    return repo.estatisticas()


@app.get(
    "/llm/documentos",
    response_model=list[DocumentoLLM],
    tags=["Análises"],
    summary="Documentos de texto preparados para LLMs",
)
def documentos_llm(
    tipo: Annotated[str | None, Query(pattern="^(projeto|noticia)$", description="projeto ou noticia")] = None,
) -> list[dict]:
    """Projetos e notícias em formato texto + metadados + estimativa de tokens (insumo do TP4)."""
    docs = repo.montar_documentos_llm()
    return [d for d in docs if tipo is None or d["tipo"] == tipo]
