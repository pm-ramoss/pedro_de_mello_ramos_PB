"""
Conecta Impacto — Aplicação Streamlit (TP2)

Evolução da demo do TP1: interface dinâmica em abas, dados alimentados por
Web Scraping (BeautifulSoup), cache e estado de sessão, serviço de upload e
download de arquivos CSV, nuvem de palavras e estatísticas básicas geradas a
partir de notícias coletadas sobre ESG / Agenda 2030.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Permite importar os módulos de Code/DataPreparation a partir de app.py.
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR / "Code" / "DataPreparation"))

from gerar_nuvem_palavras import (  # noqa: E402
    carregar_corpus,
    contar_palavras,
    estatisticas_basicas,
    gerar_figura_nuvem,
)

st.set_page_config(
    page_title="Conecta Impacto | ESG & Agenda 2030",
    page_icon="🌱",
    layout="wide",
)

PROJETOS_PROCESSADOS = ROOT_DIR / "Data" / "Processed" / "projetos_sociais.csv"
PROJETOS_SAMPLE = ROOT_DIR / "SampleData" / "projetos_sociais_sample.csv"
NOTICIAS_PROCESSADAS = ROOT_DIR / "Data" / "Processed" / "noticias_processadas.csv"
NOTICIAS_TXT_DIR = ROOT_DIR / "Data" / "Raw" / "noticias_txt"

COLUNAS_PROJETO = [
    "nome_projeto", "organizacao", "causa", "ods_relacionado",
    "cidade", "uf", "descricao", "fonte", "link",
]

# --------------------------------------------------------------------------
# Cache de carregamento de dados (evita reler CSV/TXT do disco a cada
# interação do usuário — melhora performance conforme pedido no TP2).
# --------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def carregar_projetos_base() -> pd.DataFrame:
    caminho = PROJETOS_PROCESSADOS if PROJETOS_PROCESSADOS.exists() else PROJETOS_SAMPLE
    return pd.read_csv(caminho)


@st.cache_data(show_spinner=False)
def carregar_noticias() -> pd.DataFrame:
    if NOTICIAS_PROCESSADAS.exists():
        return pd.read_csv(NOTICIAS_PROCESSADAS)
    return pd.DataFrame(
        columns=["titulo", "fonte", "url", "data_publicacao", "resumo", "ods_relacionado"]
    )


@st.cache_data(show_spinner=False)
def carregar_corpus_noticias() -> str:
    if NOTICIAS_TXT_DIR.exists():
        return carregar_corpus(NOTICIAS_TXT_DIR)
    return ""


@st.cache_data(show_spinner=False)
def calcular_estatisticas_corpus() -> dict:
    if NOTICIAS_TXT_DIR.exists():
        return estatisticas_basicas(NOTICIAS_TXT_DIR)
    return {"n_textos": 0, "n_palavras_total": 0, "n_palavras_unicas": 0, "media_palavras_por_texto": 0}


# --------------------------------------------------------------------------
# Estado de sessão
# --------------------------------------------------------------------------
if "projetos_extras" not in st.session_state:
    # DataFrame vazio com o mesmo schema, que recebe os uploads do usuário.
    st.session_state.projetos_extras = pd.DataFrame(columns=COLUNAS_PROJETO)

if "favoritos" not in st.session_state:
    st.session_state.favoritos = set()


def projetos_completos() -> pd.DataFrame:
    """Dataset base + o que o usuário enviou nesta sessão (upload de CSV)."""
    base = carregar_projetos_base()
    extras = st.session_state.projetos_extras
    if extras.empty:
        return base
    return pd.concat([base, extras], ignore_index=True)


# --------------------------------------------------------------------------
# Cabeçalho
# --------------------------------------------------------------------------
st.title("🌱 Conecta Impacto")
st.subheader(
    "Plataforma de inteligência de dados para conectar projetos sociais "
    "a doadores, voluntários e empresas com agenda ESG"
)
st.markdown(
    "**TP2 — Ambiente de desenvolvimento, interface dinâmica, coleta de dados web, "
    "cache/estado de sessão e upload/download de arquivos** · "
)

aba_visao, aba_projetos, aba_noticias, aba_dados = st.tabs(
    ["📌 Visão Geral", "🗂️ Projetos Sociais", "📰 Notícias & Nuvem de Palavras", "📤 Meus Dados"]
)

# --------------------------------------------------------------------------
# Aba 1 — Visão Geral (conteúdo herdado do TP1, resumido)
# --------------------------------------------------------------------------
with aba_visao:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("O problema de negócio")
        st.write(
            """
            Organizações da sociedade civil (OSCs), sobretudo de pequeno e médio porte,
            têm dificuldade em ganhar visibilidade e demonstrar, com dados, o impacto de
            seus projetos sociais. Empresas com compromissos **ESG** e pessoas físicas
            dispostas a doar ou atuar como voluntárias não têm um canal simples para
            **descobrir, comparar e priorizar** projetos sociais confiáveis, alinhados às
            causas e aos Objetivos de Desenvolvimento Sustentável (ODS) que desejam apoiar.
            """
        )
        st.header("O que mudou no TP2")
        st.markdown(
            """
            - Interface reorganizada em abas, com filtros, busca e favoritos persistidos
              durante a sessão do usuário (`st.session_state`).
            - Dados de projetos e notícias carregados com **cache** (`st.cache_data`),
              evitando releituras desnecessárias do disco.
            - Novo pipeline de **Web Scraping** (BeautifulSoup) para causas sociais e
              notícias sobre ESG/Agenda 2030 (`Code/DataAcquisition/`).
            - **Nuvem de palavras** e estatísticas básicas geradas a partir do corpus de
              notícias coletado.
            - Serviço de **upload/download de CSV**, permitindo que o usuário complemente
              a base de projetos sem alterar o código.
            """
        )

    with col2:
        st.success("**ODS 17** — Parcerias e Meios de Implementação (principal)")
        st.info("**ODS 10** — Redução das Desigualdades (secundário)")
        st.header("Público-alvo")
        st.markdown(
            "- Empresas com agenda ESG\n"
            "- Doadores e voluntários (pessoa física)\n"
            "- OSCs/ONGs de pequeno e médio porte"
        )

# --------------------------------------------------------------------------
# Aba 2 — Projetos Sociais (filtros dinâmicos, busca, favoritos)
# --------------------------------------------------------------------------
with aba_projetos:
    df = projetos_completos()

    st.caption(
        f"Base atual: {len(carregar_projetos_base())} projetos coletados/curados + "
        f"{len(st.session_state.projetos_extras)} enviados por você nesta sessão."
    )

    f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
    with f_col1:
        causas = ["Todas"] + sorted(df["causa"].dropna().unique().tolist())
        causa_sel = st.selectbox("Filtrar por causa", causas, key="filtro_causa")
    with f_col2:
        ufs = ["Todas"] + sorted(df["uf"].dropna().unique().tolist())
        uf_sel = st.selectbox("Filtrar por UF", ufs, key="filtro_uf")
    with f_col3:
        busca = st.text_input(
            "🔎 Buscar por nome, organização ou descrição", key="busca_projeto"
        )

    df_filtrado = df.copy()
    if causa_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["causa"] == causa_sel]
    if uf_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["uf"] == uf_sel]
    if busca:
        termo = busca.lower()
        mascara = (
            df_filtrado["nome_projeto"].str.lower().str.contains(termo, na=False)
            | df_filtrado["organizacao"].str.lower().str.contains(termo, na=False)
            | df_filtrado["descricao"].str.lower().str.contains(termo, na=False)
        )
        df_filtrado = df_filtrado[mascara]

    m1, m2, m3 = st.columns(3)
    m1.metric("Projetos exibidos", len(df_filtrado))
    m2.metric("Causas distintas", df_filtrado["causa"].nunique())
    m3.metric("Estados (UF) distintos", df_filtrado["uf"].nunique())

    st.divider()
    st.subheader("Resultados")

    for _, linha in df_filtrado.iterrows():
        chave_fav = f"{linha['nome_projeto']}::{linha.get('link', '')}"
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"**{linha['nome_projeto']}** — {linha.get('organizacao', '')}")
                st.caption(
                    f"{linha.get('causa', '')} · {linha.get('ods_relacionado', '')} · "
                    f"{linha.get('cidade', '')}/{linha.get('uf', '')}"
                )
                st.write(linha.get("descricao", ""))
                if linha.get("link"):
                    st.markdown(f"[Saiba mais]({linha['link']})")
            with c2:
                favoritado = chave_fav in st.session_state.favoritos
                rotulo = "⭐ Favoritado" if favoritado else "☆ Favoritar"
                if st.button(rotulo, key=f"fav_{chave_fav}"):
                    if favoritado:
                        st.session_state.favoritos.discard(chave_fav)
                    else:
                        st.session_state.favoritos.add(chave_fav)
                    st.rerun()

    if not df_filtrado.empty:
        st.download_button(
            "⬇️ Baixar resultados filtrados (CSV)",
            data=df_filtrado.to_csv(index=False).encode("utf-8"),
            file_name="projetos_filtrados.csv",
            mime="text/csv",
        )

    if st.session_state.favoritos:
        st.divider()
        st.subheader(f"⭐ Seus favoritos ({len(st.session_state.favoritos)})")
        for chave in st.session_state.favoritos:
            nome = chave.split("::")[0]
            st.markdown(f"- {nome}")

# --------------------------------------------------------------------------
# Aba 3 — Notícias & Nuvem de Palavras (dados extraídos via Web Scraping)
# --------------------------------------------------------------------------
with aba_noticias:
    st.subheader("Notícias sobre ESG e Agenda 2030 coletadas via Web Scraping")
    st.caption(
        "Coletadas com `Code/DataAcquisition/scraping_noticias_esg.py` (BeautifulSoup) "
        "e processadas com `Code/DataPreparation/preparar_dados.py`."
    )

    noticias = carregar_noticias()

    if noticias.empty:
        st.warning(
            "Nenhuma notícia processada encontrada em "
            "`Data/Processed/noticias_processadas.csv`. Rode os scripts de coleta "
            "e preparação de dados (veja o README) para popular esta aba."
        )
    else:
        stats = calcular_estatisticas_corpus()
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Notícias coletadas", stats["n_textos"])
        s2.metric("Palavras no corpus", stats["n_palavras_total"])
        s3.metric("Palavras únicas", stats["n_palavras_unicas"])
        s4.metric("Média palavras/notícia", stats["media_palavras_por_texto"])

        st.divider()
        col_wc, col_top = st.columns([2, 1])
        with col_wc:
            st.markdown("**Nuvem de palavras do corpus de notícias**")
            corpus = carregar_corpus_noticias()
            if corpus.strip():
                fig = gerar_figura_nuvem(corpus)
                st.pyplot(fig, use_container_width=True)
            else:
                st.info("Corpus de notícias vazio.")
        with col_top:
            st.markdown("**Top 10 palavras mais frequentes**")
            corpus = carregar_corpus_noticias()
            top10 = contar_palavras(corpus, top_n=10)
            st.dataframe(
                pd.DataFrame(top10, columns=["palavra", "ocorrências"]),
                hide_index=True,
                use_container_width=True,
            )

        st.divider()
        st.markdown("**Notícias coletadas**")
        for _, n in noticias.iterrows():
            with st.expander(f"{n['titulo']}  ·  {n.get('fonte', '')}"):
                st.caption(f"Publicado em {n.get('data_publicacao', '?')} · {n.get('ods_relacionado', '')}")
                st.write(n.get("resumo", ""))
                if n.get("url"):
                    st.markdown(f"[Ler mais]({n['url']})")

        st.download_button(
            "⬇️ Baixar notícias processadas (CSV)",
            data=noticias.to_csv(index=False).encode("utf-8"),
            file_name="noticias_esg_ods.csv",
            mime="text/csv",
        )

# --------------------------------------------------------------------------
# Aba 4 — Meus Dados (upload / download; complementa a base de projetos)
# --------------------------------------------------------------------------
with aba_dados:
    st.subheader("Envie mais projetos sociais para a base (CSV)")
    st.caption(
        "O arquivo enviado deve ter as colunas: `"
        + ", ".join(COLUNAS_PROJETO)
        + "`. Os dados ficam disponíveis apenas durante esta sessão."
    )

    st.download_button(
        "⬇️ Baixar modelo de CSV vazio",
        data=pd.DataFrame(columns=COLUNAS_PROJETO).to_csv(index=False).encode("utf-8"),
        file_name="modelo_projetos.csv",
        mime="text/csv",
    )

    arquivo = st.file_uploader("Selecione um arquivo .csv", type=["csv"])
    if arquivo is not None:
        try:
            novo_df = pd.read_csv(arquivo)
            colunas_faltantes = set(COLUNAS_PROJETO) - set(novo_df.columns)
            if colunas_faltantes:
                st.error(
                    "O arquivo não tem o formato esperado. Colunas faltando: "
                    + ", ".join(sorted(colunas_faltantes))
                )
            else:
                novo_df = novo_df[COLUNAS_PROJETO]
                if st.button("➕ Adicionar estes registros à base da sessão"):
                    st.session_state.projetos_extras = pd.concat(
                        [st.session_state.projetos_extras, novo_df], ignore_index=True
                    ).drop_duplicates(subset=["nome_projeto", "link"])
                    st.success(f"{len(novo_df)} registro(s) adicionado(s) à base da sessão.")
                    st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Não foi possível ler o arquivo enviado: {exc}")

    st.divider()
    st.subheader("Base combinada (dados coletados + enviados por você)")
    combinado = projetos_completos()
    st.dataframe(combinado, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Baixar base combinada (CSV)",
        data=combinado.to_csv(index=False).encode("utf-8"),
        file_name="projetos_sociais_combinado.csv",
        mime="text/csv",
    )

    if not st.session_state.projetos_extras.empty:
        if st.button("🗑️ Limpar registros enviados nesta sessão"):
            st.session_state.projetos_extras = pd.DataFrame(columns=COLUNAS_PROJETO)
            st.rerun()

st.divider()
st.caption(
    "Conecta Impacto · TP2 · Projeto desenvolvido com Python, Streamlit, APIs, "
    "Web Scraping (BeautifulSoup) e geração de nuvem de palavras, alinhado à "
    "Agenda 2030 da ONU."
)
