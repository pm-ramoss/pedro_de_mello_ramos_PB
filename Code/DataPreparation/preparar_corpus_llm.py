"""
Gera o corpus de documentos (projetos + notícias) preparado para LLMs — TP3.

Saída: arquivo JSON Lines (um documento por linha) com id, tipo, título, texto,
metadados e estimativa de tokens. É o insumo dos casos de uso do TP4
(resumo, sentimento, Q&A, geração de texto).

Uso (a partir da raiz do projeto):
    python Code/DataPreparation/preparar_corpus_llm.py \
        --saida Data/Processed/corpus_llm.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "Code" / "API"))

import repositorio  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera corpus JSONL para LLMs.")
    parser.add_argument("--saida", default=str(RAIZ / "Data" / "Processed" / "corpus_llm.jsonl"))
    args = parser.parse_args()

    documentos = repositorio.montar_documentos_llm()
    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", encoding="utf-8") as f:
        for doc in documentos:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    total = sum(d["tokens_estimados"] for d in documentos)
    por_tipo = {t: sum(1 for d in documentos if d["tipo"] == t) for t in ("projeto", "noticia")}
    print(f"{len(documentos)} documentos ({por_tipo}) → {saida}")
    print(f"Tokens estimados (~4 caracteres/token): {total}")


if __name__ == "__main__":
    main()
