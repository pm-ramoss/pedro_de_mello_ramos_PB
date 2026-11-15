"""Página 2 — Projetos Sociais (filtros, busca, favoritos, download)."""

import streamlit as st

import app_utils as utils

st.title("🗂️ Projetos Sociais")

# Base completa, só para montar as opções dos filtros.
base_completa, origem = utils.obter_projetos()
st.caption(utils.rotulo_origem(origem))

f1, f2, f3, f4 = st.columns([1, 1, 1, 2])
with f1:
    causa = st.selectbox("Causa", ["Todas"] + sorted(base_completa["causa"].unique().tolist()), key="f_causa")
with f2:
    uf = st.selectbox("UF", ["Todas"] + sorted(base_completa["uf"].unique().tolist()), key="f_uf")
with f3:
    ods = st.selectbox(
        "ODS",
        ["Todos"] + [str(n) for n in range(1, 18)],
        format_func=lambda v: v if v == "Todos" else f"ODS {v}",
        key="f_ods",
    )
with f4:
    busca = st.text_input("🔎 Buscar por nome, organização, causa ou descrição", key="f_busca")

df, _ = utils.obter_projetos(
    causa=None if causa == "Todas" else causa,
    uf=None if uf == "Todas" else uf,
    ods=None if ods == "Todos" else ods,
    busca=busca or None,
)

m1, m2, m3 = st.columns(3)
m1.metric("Projetos exibidos", len(df))
m2.metric("Causas distintas", df["causa"].nunique())
m3.metric("UFs distintas", df["uf"].nunique())

st.divider()

if df.empty:
    st.info("Nenhum projeto encontrado com esses filtros.")

for _, linha in df.iterrows():
    chave = linha["id"]
    with st.container(border=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"**{linha['nome_projeto']}** — {linha['organizacao']}")
            st.caption(f"{linha['causa']} · {linha['ods_relacionado']} · {linha['cidade']}/{linha['uf']}")
            st.write(linha["descricao"])
            if linha["link"]:
                st.markdown(f"[Saiba mais]({linha['link']})")
        with c2:
            favoritado = chave in st.session_state.favoritos
            if st.button("⭐ Favoritado" if favoritado else "☆ Favoritar", key=f"fav_{chave}"):
                if favoritado:
                    st.session_state.favoritos.discard(chave)
                else:
                    st.session_state.favoritos.add(chave)
                st.rerun()

if not df.empty:
    st.download_button(
        "⬇️ Baixar resultados filtrados (CSV)",
        data=df.drop(columns=["id"]).to_csv(index=False).encode("utf-8"),
        file_name="projetos_filtrados.csv",
        mime="text/csv",
    )

if st.session_state.favoritos:
    st.divider()
    st.subheader(f"⭐ Seus favoritos ({len(st.session_state.favoritos)})")
    nomes = base_completa[base_completa["id"].isin(st.session_state.favoritos)]["nome_projeto"]
    for nome in nomes:
        st.markdown(f"- {nome}")
