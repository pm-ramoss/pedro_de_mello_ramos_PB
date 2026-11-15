"""
Funções compartilhadas pelas páginas do app Streamlit (TP3).

Estratégia "API primeiro, arquivos como contingência":
  1. Se a API FastAPI estiver no ar (CONECTA_API_URL), os dados vêm dela.
  2. Se não estiver, o app lê os mesmos CSVs diretamente (via `repositorio`),
     o que mantém a demo funcionando no Streamlit Community Cloud, onde a API
     não é iniciada junto com o app.
Cada função devolve também a ORIGEM dos dados ("API" ou "arquivos locais"), que
as páginas exibem para o usuário.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from pydantic import ValidationError

ROOT_DIR = Path(__file__).resolve().parent
for sub in ("Code/API", "Code/DataPreparation", "Code/Modeling"):
    caminho = str(ROOT_DIR / sub)
    if caminho not in sys.path:
        sys.path.insert(0, caminho)

import repositorio as repo  # noqa: E402

API_URL = os.environ.get("CONECTA_API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT_S = 3
COLUNAS_PROJETO = repo.COLUNAS_PROJETO
ORIGEM_API = "API"
ORIGEM_LOCAL = "arquivos locais"


# --------------------------------------------------------------------------
# Cliente HTTP
# --------------------------------------------------------------------------
@st.cache_data(ttl=10, show_spinner=False)
def status_api() -> dict | None:
    """Resposta de GET /saude ou None se a API estiver fora do ar."""
    try:
        resposta = requests.get(f"{API_URL}/saude", timeout=1.5)
        resposta.raise_for_status()
        return resposta.json()
    except requests.RequestException:
        return None


def chamar_api(metodo: str, caminho: str, **kwargs) -> requests.Response:
    """Chamada genérica (usada também pelo console de testes da página API)."""
    return requests.request(metodo, f"{API_URL}{caminho}", timeout=TIMEOUT_S, **kwargs)


def _api_ativa() -> bool:
    return status_api() is not None


# --------------------------------------------------------------------------
# Leitura de dados
# --------------------------------------------------------------------------
@st.cache_data(ttl=20, show_spinner=False)
def obter_projetos(
    causa: str | None = None, uf: str | None = None, ods: str | None = None, busca: str | None = None
) -> tuple[pd.DataFrame, str]:
    if _api_ativa():
        try:
            params = {k: v for k, v in dict(causa=causa, uf=uf, ods=ods, busca=busca).items() if v}
            r = chamar_api("GET", "/projetos", params={**params, "limite": 1000})
            r.raise_for_status()
            itens = r.json()["itens"]
            return pd.DataFrame(itens, columns=["id", *COLUNAS_PROJETO]), ORIGEM_API
        except (requests.RequestException, KeyError, ValueError):
            pass
    df = repo.filtrar_projetos(repo.carregar_projetos(), causa=causa, uf=uf, ods=ods, busca=busca)
    return df.reset_index(drop=True), ORIGEM_LOCAL


@st.cache_data(ttl=20, show_spinner=False)
def obter_noticias(ods: str | None = None, busca: str | None = None) -> tuple[pd.DataFrame, str]:
    if _api_ativa():
        try:
            params = {k: v for k, v in dict(ods=ods, busca=busca).items() if v}
            r = chamar_api("GET", "/noticias", params=params)
            r.raise_for_status()
            return pd.DataFrame(r.json(), columns=["id", *repo.COLUNAS_NOTICIA]), ORIGEM_API
        except (requests.RequestException, ValueError):
            pass
    df = repo.filtrar_noticias(repo.carregar_noticias(), ods=ods, busca=busca)
    return df.reset_index(drop=True), ORIGEM_LOCAL


@st.cache_data(ttl=20, show_spinner=False)
def obter_estatisticas() -> tuple[dict, str]:
    if _api_ativa():
        try:
            r = chamar_api("GET", "/estatisticas")
            r.raise_for_status()
            return r.json(), ORIGEM_API
        except (requests.RequestException, ValueError):
            pass
    return repo.estatisticas(), ORIGEM_LOCAL


@st.cache_data(ttl=20, show_spinner=False)
def obter_documentos_llm() -> tuple[list[dict], str]:
    if _api_ativa():
        try:
            r = chamar_api("GET", "/llm/documentos")
            r.raise_for_status()
            return r.json(), ORIGEM_API
        except (requests.RequestException, ValueError):
            pass
    return repo.montar_documentos_llm(), ORIGEM_LOCAL


# --------------------------------------------------------------------------
# Escrita
# --------------------------------------------------------------------------
def enviar_projeto(registro: dict) -> tuple[bool, str]:
    """Cadastra um projeto (POST /projetos ou gravação local). Retorna (ok, mensagem)."""
    registro = {k: ("" if pd.isna(v) else str(v)) for k, v in registro.items()}
    if _api_ativa():
        try:
            r = chamar_api("POST", "/projetos", json=registro)
            if r.status_code == 201:
                st.cache_data.clear()
                return True, f"Cadastrado via API (id {r.json()['id']})."
            if r.status_code == 409:
                return False, r.json().get("detail", "Projeto já cadastrado.")
            if r.status_code == 422:
                erros = "; ".join(
                    f"{'.'.join(str(x) for x in e['loc'][1:])}: {e['msg']}" for e in r.json().get("detail", [])
                )
                return False, f"Dados inválidos — {erros}"
            return False, f"A API respondeu {r.status_code}."
        except requests.RequestException:
            pass  # cai na gravação local
    try:
        from schemas import ProjetoIn

        validado = ProjetoIn(**registro).model_dump()
        novo = repo.adicionar_projeto(validado)
        st.cache_data.clear()
        return True, f"Cadastrado nos arquivos locais (id {novo['id']}) — API fora do ar."
    except repo.ProjetoDuplicadoError as exc:
        return False, str(exc)
    except ValidationError as exc:
        erros = "; ".join(f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in exc.errors())
        return False, f"Dados inválidos — {erros}"


# --------------------------------------------------------------------------
# Estado de sessão compartilhado entre as páginas
# --------------------------------------------------------------------------
def iniciar_estado() -> None:
    if "favoritos" not in st.session_state:
        st.session_state.favoritos = set()
    if "projetos_extras" not in st.session_state:
        st.session_state.projetos_extras = pd.DataFrame(columns=COLUNAS_PROJETO)


def rotulo_origem(origem: str) -> str:
    return "🟢 dados via **API**" if origem == ORIGEM_API else "🟠 dados lidos de **arquivos locais** (API fora do ar)"
