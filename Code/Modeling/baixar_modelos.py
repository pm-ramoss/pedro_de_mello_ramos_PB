"""
Baixa para o computador local os modelos HuggingFace usados pela API (TP4).

Rode UMA vez, com internet:
    python Code/Modeling/baixar_modelos.py

Depois disso a API pode funcionar sem rede:
    CONECTA_LLM_OFFLINE=1 uvicorn main:app --app-dir Code/API --port 8000

Os arquivos ficam no cache padrão da HuggingFace (~/.cache/huggingface; altere com
a variável HF_HOME). Para usar outros modelos, defina CONECTA_MODELO_RESUMO e/ou
CONECTA_MODELO_SENTIMENTO antes de rodar.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "API"))

from llm_service import TAREFAS, ServicoLLM  # noqa: E402


def main() -> int:
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("Instale as dependências primeiro: pip install -r requirements.txt", file=sys.stderr)
        return 1

    falhas = 0
    for tarefa in TAREFAS:
        modelo = ServicoLLM.nome_modelo(tarefa)
        print(f"[{tarefa}] baixando {modelo} ...")
        try:
            caminho = snapshot_download(repo_id=modelo)
            print(f"[{tarefa}] ok → {caminho}")
        except Exception as exc:  # noqa: BLE001
            falhas += 1
            print(f"[{tarefa}] FALHA: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
