"""
Camada de acesso a dados do Conecta Impacto (TP3).

Concentra a leitura/escrita dos CSVs do projeto em um único lugar, para que a
API (FastAPI) e a aplicação Streamlit (modo contingência, sem API) usem
exatamente as mesmas regras.

Arquivos usados (diretório `Data/Processed/`):
  - projetos_sociais.csv      base curada (somente leitura)
  - projetos_enviados.csv     projetos cadastrados via POST /projetos (persistente)
  - noticias_processadas.csv  notícias coletadas por Web Scraping
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import threading
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(os.environ.get("CONECTA_ROOT", Path(__file__).resolve().parents[2]))
DATA_PROCESSED = ROOT_DIR / "Data" / "Processed"

PROJETOS_BASE = DATA_PROCESSED / "projetos_sociais.csv"
PROJETOS_SAMPLE = ROOT_DIR / "SampleData" / "projetos_sociais_sample.csv"
PROJETOS_ENVIADOS = DATA_PROCESSED / "projetos_enviados.csv"
NOTICIAS_CSV = DATA_PROCESSED / "noticias_processadas.csv"

COLUNAS_PROJETO = [
    "nome_projeto", "organizacao", "causa", "ods_relacionado",
    "cidade", "uf", "descricao", "fonte", "link",
]
COLUNAS_NOTICIA = ["titulo", "fonte", "url", "data_publicacao", "resumo", "ods_relacionado"]

_LOCK = threading.Lock()


class ProjetoDuplicadoError(ValueError):
    """Já existe um projeto com o mesmo nome + link."""


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def _ler_csv(caminho: Path, colunas: list[str]) -> pd.DataFrame:
    if not caminho.exists():
        return pd.DataFrame(columns=colunas)
    df = pd.read_csv(caminho, dtype=str).fillna("")
    for coluna in colunas:
        if coluna not in df.columns:
            df[coluna] = ""
    return df[colunas]


def gerar_id(*partes: str) -> str:
    """ID curto e estável (hash) a partir de campos que identificam o registro."""
    chave = "|".join(p.strip().lower() for p in partes)
    return hashlib.sha1(chave.encode("utf-8")).hexdigest()[:10]


def _separar_ods(serie: pd.Series) -> pd.Series:
    """Explode 'ODS 2 - Fome Zero; ODS 15 - Vida Terrestre' em um ODS por linha."""
    ods = serie.str.split(";").explode().str.strip()
    return ods[ods != ""]


# --------------------------------------------------------------------------
# Projetos
# --------------------------------------------------------------------------
def carregar_projetos() -> pd.DataFrame:
    """Base curada + projetos enviados, com coluna `id` e sem duplicados."""
    origem = PROJETOS_BASE if PROJETOS_BASE.exists() else PROJETOS_SAMPLE
    partes = [
        df for df in (
            _ler_csv(origem, COLUNAS_PROJETO),
            _ler_csv(PROJETOS_ENVIADOS, COLUNAS_PROJETO),
        ) if not df.empty
    ]
    if not partes:
        return pd.DataFrame(columns=["id", *COLUNAS_PROJETO])
    df = pd.concat(partes, ignore_index=True)
    df.insert(0, "id", [gerar_id(n, l) for n, l in zip(df["nome_projeto"], df["link"])])
    return df.drop_duplicates(subset="id").reset_index(drop=True)


def filtrar_projetos(
    df: pd.DataFrame,
    causa: str | None = None,
    uf: str | None = None,
    ods: str | None = None,
    busca: str | None = None,
) -> pd.DataFrame:
    """Filtros combináveis. `ods` aceita '4' ou 'ODS 4' ou parte do nome."""
    if causa:
        df = df[df["causa"].str.lower() == causa.strip().lower()]
    if uf:
        df = df[df["uf"].str.upper() == uf.strip().upper()]
    if ods:
        numero = re.search(r"\d+", ods)
        if numero:
            padrao = rf"\bODS\s*{numero.group()}\b"
            df = df[df["ods_relacionado"].str.contains(padrao, case=False, regex=True)]
        else:
            df = df[df["ods_relacionado"].str.contains(ods.strip(), case=False, regex=False)]
    if busca:
        termo = busca.strip().lower()
        mascara = pd.Series(False, index=df.index)
        for coluna in ("nome_projeto", "organizacao", "descricao", "causa"):
            mascara |= df[coluna].str.lower().str.contains(termo, regex=False)
        df = df[mascara]
    return df


def adicionar_projeto(dados: dict) -> dict:
    """Persiste um novo projeto em `projetos_enviados.csv` e devolve o registro com id."""
    registro = {c: str(dados.get(c) or "").strip() for c in COLUNAS_PROJETO}
    novo_id = gerar_id(registro["nome_projeto"], registro["link"])
    with _LOCK:
        if (carregar_projetos()["id"] == novo_id).any():
            raise ProjetoDuplicadoError(
                f"Já existe um projeto '{registro['nome_projeto']}' com este link."
            )
        enviados = _ler_csv(PROJETOS_ENVIADOS, COLUNAS_PROJETO)
        enviados = pd.concat([enviados, pd.DataFrame([registro])], ignore_index=True)
        PROJETOS_ENVIADOS.parent.mkdir(parents=True, exist_ok=True)
        enviados.to_csv(PROJETOS_ENVIADOS, index=False, encoding="utf-8")
    return {"id": novo_id, **registro}


# --------------------------------------------------------------------------
# Notícias
# --------------------------------------------------------------------------
def carregar_noticias() -> pd.DataFrame:
    df = _ler_csv(NOTICIAS_CSV, COLUNAS_NOTICIA)
    df.insert(0, "id", [gerar_id(u) for u in df["url"]] if not df.empty else [])
    return df


def filtrar_noticias(df: pd.DataFrame, ods: str | None = None, busca: str | None = None) -> pd.DataFrame:
    if ods:
        numero = re.search(r"\d+", ods)
        if numero:
            df = df[df["ods_relacionado"].str.contains(rf"\bODS\s*{numero.group()}\b", case=False, regex=True)]
        else:
            df = df[df["ods_relacionado"].str.contains(ods.strip(), case=False, regex=False)]
    if busca:
        termo = busca.strip().lower()
        df = df[
            df["titulo"].str.lower().str.contains(termo, regex=False)
            | df["resumo"].str.lower().str.contains(termo, regex=False)
        ]
    return df


# --------------------------------------------------------------------------
# Estatísticas
# --------------------------------------------------------------------------
def _contagem(serie: pd.Series) -> dict[str, int]:
    serie = serie[serie != ""]
    return {str(k): int(v) for k, v in serie.value_counts().items()}


def estatisticas() -> dict:
    projetos = carregar_projetos()
    noticias = carregar_noticias()
    return {
        "total_projetos": int(len(projetos)),
        "total_projetos_enviados": int(len(_ler_csv(PROJETOS_ENVIADOS, COLUNAS_PROJETO))),
        "total_noticias": int(len(noticias)),
        "n_causas": int(projetos["causa"].replace("", pd.NA).nunique()),
        "n_ufs": int(projetos["uf"].replace("", pd.NA).nunique()),
        "n_ods": int(_separar_ods(projetos["ods_relacionado"]).str.extract(r"(ODS\s*\d+)")[0].nunique()),
        "projetos_por_causa": _contagem(projetos["causa"]),
        "projetos_por_uf": _contagem(projetos["uf"]),
        "projetos_por_ods": _contagem(_separar_ods(projetos["ods_relacionado"])),
        "noticias_por_ods": _contagem(_separar_ods(noticias["ods_relacionado"])) if not noticias.empty else {},
    }


# --------------------------------------------------------------------------
# Corpus preparado para LLMs (usado no TP4)
# --------------------------------------------------------------------------
def estimar_tokens(texto: str) -> int:
    """Estimativa grosseira (~4 caracteres por token). Não substitui o tokenizador do modelo."""
    return math.ceil(len(texto) / 4)


def montar_documentos_llm() -> list[dict]:
    """Une projetos e notícias em documentos de texto + metadados, prontos para um LLM."""
    documentos: list[dict] = []
    for p in carregar_projetos().to_dict("records"):
        texto = (
            f"Projeto: {p['nome_projeto']}. Organização: {p['organizacao']}. "
            f"Causa: {p['causa']}. Local: {p['cidade']}/{p['uf']}. "
            f"ODS: {p['ods_relacionado']}. {p['descricao']}"
        ).strip()
        documentos.append({
            "id": f"projeto-{p['id']}",
            "tipo": "projeto",
            "titulo": p["nome_projeto"],
            "texto": texto,
            "metadados": {k: p[k] for k in ("causa", "ods_relacionado", "cidade", "uf", "fonte", "link")},
            "tokens_estimados": estimar_tokens(texto),
        })
    for n in carregar_noticias().to_dict("records"):
        texto = f"{n['titulo']}. {n['resumo']}".strip()
        documentos.append({
            "id": f"noticia-{n['id']}",
            "tipo": "noticia",
            "titulo": n["titulo"],
            "texto": texto,
            "metadados": {k: n[k] for k in ("fonte", "url", "data_publicacao", "ods_relacionado")},
            "tokens_estimados": estimar_tokens(texto),
        })
    return documentos
