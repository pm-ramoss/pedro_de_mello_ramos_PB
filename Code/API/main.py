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

from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse

import repositorio as repo
from llm_service import ServicoLLMError, servico as servico_llm
from schemas import (
    DocumentoLLM,
    ErroResposta,
    Estatisticas,
    ListaProjetos,
    Noticia,
    ProcessarTextoIn,
    ProcessarTextoOut,
    ProjetoIn,
    ProjetoOut,
    ResultadoResumo,
    ResultadoSentimento,
    StatusLLM,
)

TAGS = [
    {"name": "Projetos", "description": "Consulta e cadastro de projetos sociais."},
    {"name": "Notícias", "description": "Notícias sobre ESG / Agenda 2030 coletadas por scraping."},
    {"name": "Análises", "description": "Estatísticas agregadas e corpus preparado para LLMs."},
    {"name": "LLM local", "description": "Resumo e análise de sentimento com modelos HuggingFace executados localmente."},
    {"name": "Sistema", "description": "Verificação de saúde da API."},
]

app = FastAPI(
    title="Conecta Impacto — API",
    version="0.4.0",
    summary="Dados de projetos sociais e notícias ESG/Agenda 2030.",
    description=(
        "API do projeto **Conecta Impacto** (TP3). Permite consultar projetos sociais "
        "(`GET /projetos`), cadastrar novos (`POST /projetos`), listar notícias, obter "
        "estatísticas e processar textos com um LLM local (`POST /processar_texto`)."
    ),
    openapi_tags=TAGS,
)


@app.exception_handler(ServicoLLMError)
async def tratar_erro_llm(_: Request, exc: ServicoLLMError) -> JSONResponse:
    """Converte falhas do serviço de LLM em respostas JSON padronizadas (ErroResposta)."""
    corpo = ErroResposta(codigo=exc.codigo, mensagem=str(exc), dica=exc.dica)
    return JSONResponse(status_code=exc.codigo_http, content=corpo.model_dump())


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


# --------------------------------------------------------------------------
# LLM local (TP4)
# --------------------------------------------------------------------------
ERROS_LLM = {
    422: {"model": ErroResposta, "description": "Texto vazio, curto ou longo demais para a tarefa"},
    500: {"model": ErroResposta, "description": "Falha na inferência do modelo"},
    503: {"model": ErroResposta, "description": "Modelo não instalado/baixado ou não carregou"},
    504: {"model": ErroResposta, "description": "Inferência excedeu o tempo limite"},
}


@app.get("/llm/status", response_model=StatusLLM, tags=["LLM local"], summary="Estado dos modelos locais")
def status_llm() -> dict:
    """Mostra qual modelo está configurado para cada tarefa e se já foi carregado em memória."""
    return servico_llm.status()


@app.post(
    "/processar_texto",
    response_model=ProcessarTextoOut,
    tags=["LLM local"],
    summary="Resume um texto ou classifica seu sentimento com um modelo local",
    responses=ERROS_LLM,
)
def processar_texto(requisicao: ProcessarTextoIn) -> dict:
    """
    Recebe um texto em português e executa a `tarefa` pedida com um modelo HuggingFace
    **rodando na máquina local** (o primeiro uso carrega o modelo em memória, o que pode
    levar alguns segundos).

    - `tarefa="resumo"`: devolve um resumo (texto com pelo menos 200 caracteres).
    - `tarefa="sentimento"`: devolve rótulo (positivo/neutro/negativo), confiança e pontuações.
    """
    bruto = servico_llm.processar(requisicao.tarefa, requisicao.texto, requisicao.max_palavras_resumo)
    if requisicao.tarefa == "resumo":
        n_resumo = len(bruto["resumo"].split())
        n_texto = max(len(requisicao.texto.split()), 1)
        resultado = ResultadoResumo(
            resumo=bruto["resumo"], n_palavras_resumo=n_resumo, taxa_compressao=round(min(n_resumo / n_texto, 1.0), 3)
        )
    else:
        resultado = ResultadoSentimento(
            rotulo=bruto["rotulo"], confianca=bruto["confianca"], pontuacoes=bruto["pontuacoes"]
        )
    return {
        "tarefa": requisicao.tarefa,
        "modelo": bruto["modelo"],
        "texto_entrada": requisicao.texto,
        "n_caracteres_entrada": len(requisicao.texto),
        "tempo_ms": bruto["tempo_ms"],
        "resultado": resultado,
    }
