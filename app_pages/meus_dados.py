"""Página 5 — Meus Dados: upload de CSV, cadastro individual e download."""

import json

import pandas as pd
import streamlit as st

import app_utils as utils

COLUNAS = utils.COLUNAS_PROJETO

st.title("📤 Meus Dados")
st.caption(
    "Há dois jeitos de complementar a base: **(1)** enviar um CSV e/ou cadastrar um projeto "
    "individualmente — ambos gravam via `POST /projetos` e **persistem** além da sessão; "
    "**(2)** manter registros apenas na sessão do navegador (herdado do TP2)."
)
_, origem = utils.obter_projetos()
st.caption(utils.rotulo_origem(origem))

aba_cadastro, aba_csv, aba_base = st.tabs(["➕ Cadastrar projeto", "📄 Enviar CSV", "🗃️ Base combinada"])

# ------------------------------------------------------------------ cadastro (POST)
with aba_cadastro:
    with st.form("form_projeto", clear_on_submit=False):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome do projeto *")
        org = c2.text_input("Organização *")
        causa = c1.text_input("Causa *", placeholder="ex.: Educação")
        ods = c2.text_input("ODS relacionado(s)", placeholder="ODS 4 - Educação de Qualidade")
        cidade = c1.text_input("Cidade")
        uf = c2.text_input("UF *", max_chars=2, placeholder="RJ")
        descricao = st.text_area("Descrição", max_chars=1000)
        link = st.text_input("Link (http/https)")
        enviar = st.form_submit_button("Cadastrar via API")

    if enviar:
        ok, msg = utils.enviar_projeto(
            dict(
                nome_projeto=nome, organizacao=org, causa=causa, ods_relacionado=ods,
                cidade=cidade, uf=uf, descricao=descricao, fonte="Cadastro via app", link=link,
            )
        )
        (st.success if ok else st.error)(msg)

# ------------------------------------------------------------------ upload de CSV
with aba_csv:
    st.caption("Colunas esperadas: `" + ", ".join(COLUNAS) + "`.")
    st.download_button(
        "⬇️ Baixar modelo de CSV vazio",
        data=pd.DataFrame(columns=COLUNAS).to_csv(index=False).encode("utf-8"),
        file_name="modelo_projetos.csv",
        mime="text/csv",
    )
    arquivo = st.file_uploader("Selecione um arquivo .csv", type=["csv"])
    if arquivo is not None:
        try:
            novo = pd.read_csv(arquivo, dtype=str).fillna("")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Não foi possível ler o arquivo enviado: {exc}")
            novo = None
        if novo is not None:
            faltando = set(COLUNAS) - set(novo.columns)
            if faltando:
                st.error("Colunas faltando: " + ", ".join(sorted(faltando)))
            else:
                novo = novo[COLUNAS]
                st.dataframe(novo, hide_index=True)
                b1, b2 = st.columns(2)
                if b1.button("💾 Enviar para a base (persistente, via API)"):
                    resultados = [utils.enviar_projeto(r) for r in novo.to_dict("records")]
                    ok = sum(1 for sucesso, _ in resultados if sucesso)
                    st.success(f"{ok} de {len(resultados)} registro(s) cadastrado(s).")
                    for i, (sucesso, msg) in enumerate(resultados, start=1):
                        if not sucesso:
                            st.warning(f"Linha {i}: {msg}")
                if b2.button("➕ Adicionar só à sessão (temporário)"):
                    st.session_state.projetos_extras = pd.concat(
                        [st.session_state.projetos_extras, novo], ignore_index=True
                    ).drop_duplicates(subset=["nome_projeto", "link"])
                    st.success(f"{len(novo)} registro(s) adicionados à sessão.")

# ------------------------------------------------------------------ base combinada
with aba_base:
    persistida, _ = utils.obter_projetos()
    sessao = st.session_state.projetos_extras
    combinado = pd.concat(
        [persistida.drop(columns=["id"]), sessao], ignore_index=True
    ).drop_duplicates(subset=["nome_projeto", "link"])
    st.caption(f"{len(persistida)} projetos na base + {len(sessao)} apenas na sua sessão.")
    st.dataframe(combinado, hide_index=True)

    d1, d2 = st.columns(2)
    d1.download_button(
        "⬇️ Baixar base combinada (CSV)",
        data=combinado.to_csv(index=False).encode("utf-8"),
        file_name="projetos_sociais_combinado.csv",
        mime="text/csv",
    )
    d2.download_button(
        "⬇️ Baixar base combinada (JSON)",
        data=json.dumps(combinado.to_dict("records"), ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="projetos_sociais_combinado.json",
        mime="application/json",
    )
    if not sessao.empty and st.button("🗑️ Limpar registros apenas-sessão"):
        st.session_state.projetos_extras = pd.DataFrame(columns=COLUNAS)
        st.rerun()
