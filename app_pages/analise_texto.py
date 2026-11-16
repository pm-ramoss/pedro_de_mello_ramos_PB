"""Página 8 — Análise de Texto com LLM local (resumo e sentimento)."""

import pandas as pd
import streamlit as st

import app_utils as utils

st.title("🧠 Análise de Texto (LLM local)")
st.caption(
    "Os textos são enviados a `POST /processar_texto`, que executa modelos da HuggingFace "
    "**na própria máquina** — nenhum dado sai para serviços de nuvem."
)

status = utils.status_llm()
if status is None:
    st.warning(
        "A API está fora do ar. Inicie-a em outro terminal:\n\n"
        "```bash\nuvicorn main:app --reload --app-dir Code/API --port 8000\n```"
    )
else:
    c1, c2 = st.columns(2)
    for col, tarefa, titulo in ((c1, "resumo", "Resumo"), (c2, "sentimento", "Sentimento")):
        info = status[tarefa]
        estado = "✅ carregado em memória" if info["carregado"] else "⏳ será carregado no primeiro uso"
        col.info(f"**{titulo}** — `{info['modelo']}`\n\n{estado}")
        if info.get("ultimo_erro"):
            col.error(f"Último erro de carga: {info['ultimo_erro']}")

aba_livre, aba_noticias = st.tabs(["✍️ Texto livre", "📰 Notícias coletadas"])

# ---------------------------------------------------------------- texto livre
with aba_livre:
    tarefa = st.radio("Tarefa", ["sentimento", "resumo"], horizontal=True, key="llm_tarefa")

    noticias, _ = utils.obter_noticias()
    exemplos = {"(digitar texto)": ""}
    for _, n in noticias.iterrows():
        exemplos[n["titulo"][:80]] = f"{n['titulo']}. {n['resumo']}"
    escolha = st.selectbox("Carregar um exemplo das notícias coletadas", list(exemplos), key="llm_exemplo")

    texto = st.text_area("Texto em português", value=exemplos[escolha], height=200, key=f"llm_texto_{escolha}")
    max_palavras = 60
    if tarefa == "resumo":
        max_palavras = st.slider("Tamanho máximo do resumo (palavras)", 15, 200, 60)
        st.caption("O resumo exige pelo menos 200 caracteres de texto.")

    if st.button("Processar", type="primary", disabled=not texto.strip()):
        with st.spinner("Processando com o modelo local (a primeira chamada pode demorar)…"):
            ok, resposta = utils.processar_texto(tarefa, texto, max_palavras)
        if not ok:
            st.error(resposta)
        else:
            res = resposta["resultado"]
            if res["tarefa"] == "resumo":
                st.subheader("Resumo")
                st.write(res["resumo"])
                st.caption(f"{res['n_palavras_resumo']} palavras · {res['taxa_compressao']:.0%} do tamanho original")
            else:
                st.subheader(f"Sentimento: {res['rotulo']}")
                st.metric("Confiança", f"{res['confianca']:.0%}")
                st.bar_chart(pd.Series(res["pontuacoes"], name="probabilidade"))
            st.caption(f"Modelo `{resposta['modelo']}` · {resposta['tempo_ms']} ms")
            with st.expander("Ver resposta JSON da API"):
                st.json(resposta)

# ---------------------------------------------------------------- lote
with aba_noticias:
    st.write("Classifica o sentimento de todas as notícias coletadas (uma chamada por notícia).")
    if noticias.empty:
        st.info("Não há notícias coletadas.")
    elif st.button("Classificar todas as notícias"):
        linhas, falhas = [], []
        barra = st.progress(0.0)
        for i, (_, n) in enumerate(noticias.iterrows(), start=1):
            ok, resp = utils.processar_texto("sentimento", f"{n['titulo']}. {n['resumo']}")
            if ok:
                r = resp["resultado"]
                linhas.append({"titulo": n["titulo"], "fonte": n["fonte"], "sentimento": r["rotulo"], "confiança": r["confianca"]})
            else:
                falhas.append(resp)
                break  # o mesmo erro tende a se repetir; evita dezenas de chamadas inúteis
            barra.progress(i / len(noticias))
        if falhas:
            st.error(falhas[0])
        if linhas:
            df = pd.DataFrame(linhas)
            st.dataframe(df, hide_index=True)
            st.bar_chart(df["sentimento"].value_counts())
            st.download_button(
                "⬇️ Baixar resultado (CSV)", df.to_csv(index=False).encode("utf-8"),
                "sentimento_noticias.csv", "text/csv",
            )
