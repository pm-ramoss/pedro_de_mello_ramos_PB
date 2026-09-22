"""
Geração de nuvem de palavras e estatísticas básicas a partir do corpus de
notícias ESG/ODS coletado via Web Scraping — TP2.

Módulo importado pela aplicação Streamlit (`app.py`). Também pode ser
executado isoladamente para gerar um PNG de teste da nuvem de palavras.

Uso (isolado):
    python gerar_nuvem_palavras.py \
        --entrada-dir ../../Data/Raw/noticias_txt \
        --saida ../../Data/Processed/nuvem_palavras.png
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

# Lista simples de stopwords em português (suficiente para o corpus do
# projeto; para um corpus maior, considerar a lib `nltk` ou `spacy`).
STOPWORDS_PT = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em", "um",
    "uma", "uns", "umas", "para", "com", "por", "no", "na", "nos", "nas",
    "que", "se", "ao", "aos", "à", "às", "é", "são", "foi", "ser", "sua",
    "seu", "suas", "seus", "mais", "menos", "como", "entre", "sobre", "já",
    "não", "sim", "ou", "mas", "também", "há", "num", "numa", "pelo", "pela",
    "pelos", "pelas", "este", "esta", "esse", "essa", "isso", "isto", "cada",
    "quando", "onde", "até", "após", "sem", "após", "durante", "enquanto",
}


def carregar_corpus(diretorio: Path) -> str:
    """Concatena todos os .txt de um diretório em um único corpus textual."""
    textos = []
    for caminho in sorted(diretorio.glob("*.txt")):
        textos.append(caminho.read_text(encoding="utf-8"))
    return "\n".join(textos)


def contar_palavras(texto: str, min_len: int = 3, top_n: int = 50) -> list[tuple[str, int]]:
    """Tokeniza, remove stopwords e retorna as `top_n` palavras mais frequentes."""
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", texto.lower())
    palavras = [p for p in palavras if len(p) >= min_len and p not in STOPWORDS_PT]
    contagem = Counter(palavras)
    return contagem.most_common(top_n)


def estatisticas_basicas(diretorio: Path) -> dict:
    """Estatísticas simples do corpus (nº de textos, palavras, tamanho médio)."""
    arquivos = sorted(diretorio.glob("*.txt"))
    corpus = carregar_corpus(diretorio)
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", corpus.lower())
    n_textos = len(arquivos)
    return {
        "n_textos": n_textos,
        "n_palavras_total": len(palavras),
        "n_palavras_unicas": len(set(palavras)),
        "media_palavras_por_texto": round(len(palavras) / n_textos, 1) if n_textos else 0,
    }


def gerar_figura_nuvem(texto: str):
    """Gera uma figura matplotlib com a nuvem de palavras do texto informado."""
    import matplotlib.pyplot as plt
    from wordcloud import WordCloud

    freq = dict(contar_palavras(texto))
    wc = WordCloud(
        width=900,
        height=450,
        background_color="white",
        colormap="viridis",
    ).generate_from_frequencies(freq or {"sem_dados": 1})

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    fig.tight_layout(pad=0)
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera PNG de teste da nuvem de palavras.")
    parser.add_argument("--entrada-dir", default="../../Data/Raw/noticias_txt")
    parser.add_argument("--saida", default="../../Data/Processed/nuvem_palavras.png")
    args = parser.parse_args()

    diretorio = Path(args.entrada_dir)
    corpus = carregar_corpus(diretorio)
    fig = gerar_figura_nuvem(corpus)

    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida, dpi=150)
    print(f"Nuvem de palavras salva em: {saida}")
    print(f"Estatísticas do corpus: {estatisticas_basicas(diretorio)}")


if __name__ == "__main__":
    main()
