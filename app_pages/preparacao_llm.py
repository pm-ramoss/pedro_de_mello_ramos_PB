"""Página 7 — Preparação para LLMs (casos de uso planejados para o TP4)."""

import json

import pandas as pd
import streamlit as st

import app_utils as utils
from prompts_llm import CASOS_DE_USO, montar_prompt

st.title("🤖 Preparação para LLMs")
st.caption(
    "Nesta etapa **não há chamadas a modelos**: o objetivo é deixar dados e prompts prontos "
    "para que a integração com LLMs (TP4) seja simples."
)

documentos, origem = utils.obter_documentos_llm()
st.caption(utils.rotulo_origem(origem))
df = pd.DataFrame(documentos)

if df.empty:
    st.warning("Nenhum documento disponível. Rode a coleta e a preparação de dados.")
    st.stop()

# ---------------------------------------------------------------- corpus
st.subheader("Corpus disponível")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Documentos", len(df))
c2.metric("Projetos", int((df["tipo"] == "projeto").sum()))
c3.metric("Notícias", int((df["tipo"] == "noticia").sum()))
c4.metric("Tokens estimados", int(df["tokens_estimados"].sum()))
st.caption("Estimativa de ~4 caracteres por token — aproximação; o valor real depende do tokenizador do modelo.")

tipo = st.radio("Exibir", ["todos", "projeto", "noticia"], horizontal=True)
visivel = df if tipo == "todos" else df[df["tipo"] == tipo]
st.dataframe(visivel[["id", "tipo", "titulo", "tokens_estimados"]], hide_index=True)

jsonl = "\n".join(json.dumps(d, ensure_ascii=False) for d in documentos)
st.download_button(
    "⬇️ Baixar corpus (JSONL)", data=jsonl.encode("utf-8"), file_name="corpus_llm.jsonl", mime="application/jsonl"
)

st.divider()

# ---------------------------------------------------------------- casos de uso
st.subheader("Casos de uso planejados")
abas = st.tabs([c["titulo"] for c in CASOS_DE_USO.values()])
for aba, (chave, caso) in zip(abas, CASOS_DE_USO.items()):
    with aba:
        st.markdown(f"**Dados de entrada:** {caso['dados']}")
        st.markdown(f"**Saída esperada:** {caso['saida']}")

        # Pré-visualização do prompt com um documento real do corpus.
        exemplo = documentos[0]["texto"] if chave != "qa" else "\n".join(
            f"[{d['id']}] {d['texto']}" for d in documentos[:3]
        )
        campos = {
            "texto": exemplo,
            "contexto": exemplo,
            "pergunta": "Quais projetos atuam com educação?",
            "estatisticas": "{...JSON de GET /estatisticas...}",
        }
        st.markdown("**Prompt-base (pré-visualização com dados reais):**")
        st.code(montar_prompt(chave, **{k: campos[k] for k in caso["entrada"]}), language="text")
