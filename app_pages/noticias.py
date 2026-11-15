"""Página 4 — Notícias e nuvem de palavras."""

import pandas as pd
import streamlit as st

import app_utils as utils
from gerar_nuvem_palavras import (
    carregar_corpus,
    contar_palavras,
    estatisticas_basicas,
    gerar_figura_nuvem,
)

NOTICIAS_TXT_DIR = utils.ROOT_DIR / "Data" / "Raw" / "noticias_txt"

st.title("📰 Notícias e Nuvem de Palavras")
st.caption(
    "Notícias sobre ESG/Agenda 2030 coletadas com `Code/DataAcquisition/scraping_noticias_esg.py` "
    "e entregues pela API (`GET /noticias`)."
)


@st.cache_data(show_spinner=False)
def corpus_e_estatisticas() -> tuple[str, dict]:
    if NOTICIAS_TXT_DIR.exists():
        return carregar_corpus(NOTICIAS_TXT_DIR), estatisticas_basicas(NOTICIAS_TXT_DIR)
    return "", {"n_textos": 0, "n_palavras_total": 0, "n_palavras_unicas": 0, "media_palavras_por_texto": 0}


todas, origem = utils.obter_noticias()
st.caption(utils.rotulo_origem(origem))

if todas.empty:
    st.warning(
        "Nenhuma notícia encontrada em `Data/Processed/noticias_processadas.csv`. "
        "Rode os scripts de coleta e preparação (veja o README)."
    )
    st.stop()

f1, f2 = st.columns([1, 2])
with f1:
    opcoes_ods = sorted({o.strip() for v in todas["ods_relacionado"] for o in v.split(";") if o.strip()})
    ods_sel = st.selectbox("ODS relacionado", ["Todos"] + opcoes_ods, key="n_ods")
with f2:
    busca = st.text_input("🔎 Buscar no título ou resumo", key="n_busca")

noticias, _ = utils.obter_noticias(
    ods=None if ods_sel == "Todos" else ods_sel,
    busca=busca or None,
)

corpus, stats = corpus_e_estatisticas()
s1, s2, s3, s4 = st.columns(4)
s1.metric("Notícias exibidas", len(noticias))
s2.metric("Palavras no corpus", stats["n_palavras_total"])
s3.metric("Palavras únicas", stats["n_palavras_unicas"])
s4.metric("Média palavras/notícia", stats["media_palavras_por_texto"])

st.divider()
col_wc, col_top = st.columns([2, 1])
with col_wc:
    st.markdown("**Nuvem de palavras do corpus**")
    if corpus.strip():
        try:
            st.pyplot(gerar_figura_nuvem(corpus))
        except ImportError:
            st.info("Instale a dependência `wordcloud` (`pip install -r requirements.txt`) para ver a nuvem.")
    else:
        st.info("Corpus de notícias vazio.")
with col_top:
    st.markdown("**Top 10 palavras**")
    st.dataframe(pd.DataFrame(contar_palavras(corpus, top_n=10), columns=["palavra", "ocorrências"]), hide_index=True)

st.divider()
st.markdown("**Notícias coletadas**")
if noticias.empty:
    st.info("Nenhuma notícia com esses filtros.")
for _, n in noticias.iterrows():
    with st.expander(f"{n['titulo']}  ·  {n['fonte']}"):
        st.caption(f"Publicado em {n['data_publicacao'] or '?'} · {n['ods_relacionado']}")
        st.write(n["resumo"])
        if n["url"]:
            st.markdown(f"[Ler mais]({n['url']})")

st.download_button(
    "⬇️ Baixar notícias exibidas (CSV)",
    data=noticias.drop(columns=["id"]).to_csv(index=False).encode("utf-8"),
    file_name="noticias_esg_ods.csv",
    mime="text/csv",
)
