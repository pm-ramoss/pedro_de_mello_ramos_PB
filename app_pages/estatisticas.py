"""Página 3 — Estatísticas e gráficos."""

import pandas as pd
import streamlit as st

import app_utils as utils

st.title("📊 Estatísticas e Gráficos")

stats, origem = utils.obter_estatisticas()
st.caption(utils.rotulo_origem(origem))


def serie(dicionario: dict, nome: str) -> pd.Series:
    return pd.Series(dicionario, name=nome, dtype="int64").sort_values(ascending=False)


# --- Progresso em relação às metas do Project Charter -------------------------
st.subheader("Progresso em relação às metas do Project Charter")
metas = [
    ("Projetos catalogados", stats["total_projetos"], 100),
    ("ODS cobertos", stats["n_ods"], 8),
    ("UFs representadas", stats["n_ufs"], 10),
]
cols = st.columns(len(metas))
for col, (rotulo, atual, meta) in zip(cols, metas):
    with col:
        st.metric(rotulo, f"{atual} / {meta}")
        st.progress(min(atual / meta, 1.0))

st.divider()

# --- Gráficos --------------------------------------------------------------------
g1, g2 = st.columns(2)
with g1:
    st.markdown("**Projetos por causa**")
    st.bar_chart(serie(stats["projetos_por_causa"], "projetos"), horizontal=True)
with g2:
    st.markdown("**Projetos por UF**")
    st.bar_chart(serie(stats["projetos_por_uf"], "projetos"))

g3, g4 = st.columns(2)
with g3:
    st.markdown("**Projetos por ODS**")
    st.bar_chart(serie(stats["projetos_por_ods"], "projetos"), horizontal=True)
with g4:
    st.markdown("**Notícias por ODS**")
    if stats["noticias_por_ods"]:
        st.bar_chart(serie(stats["noticias_por_ods"], "notícias"), horizontal=True)
    else:
        st.info("Sem notícias processadas.")

with st.expander("Ver tabelas de apoio"):
    t1, t2 = st.columns(2)
    t1.dataframe(serie(stats["projetos_por_causa"], "projetos").rename_axis("causa").reset_index(), hide_index=True)
    t2.dataframe(serie(stats["projetos_por_ods"], "projetos").rename_axis("ODS").reset_index(), hide_index=True)
