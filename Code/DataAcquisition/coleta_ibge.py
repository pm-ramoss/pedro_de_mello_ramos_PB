"""
Coleta de indicadores socioeconômicos via API pública do IBGE.

Este script consulta a API de Localidades do IBGE para obter a lista de
municípios de um determinado estado (UF) e, em seguida, consulta a API do
SIDRA (Sistema IBGE de Recuperação Automática) para obter um indicador
socioeconômico agregado (ex.: população estimada), usado para contextualizar
regionalmente os projetos sociais catalogados (apoio ao ODS 10).

Uso:
    python coleta_ibge.py --uf SP --saida ../../Data/Raw/ibge_municipios_sp.csv

Observação:
    Este script depende de acesso à internet. Nenhuma chave de API é
    necessária (API pública do IBGE).
"""

import argparse
import csv
import sys
import time
from pathlib import Path

import requests

BASE_LOCALIDADES = "https://servicodados.ibge.gov.br/api/v1/localidades"
BASE_SIDRA = "https://servicodados.ibge.gov.br/api/v3/agregados"


def listar_municipios(uf: str) -> list[dict]:
    """Retorna a lista de municípios de uma UF via API de Localidades do IBGE."""
    url = f"{BASE_LOCALIDADES}/estados/{uf}/municipios"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def obter_populacao_estimada(codigo_municipio: str) -> dict | None:
    """
    Consulta a API SIDRA (agregado 6579 - Estimativas de população) para o
    município informado. Retorna None em caso de indisponibilidade do dado.
    """
    # Agregado 6579: Estimativas de população residente
    url = (
        f"{BASE_SIDRA}/6579/periodos/-1/variaveis/9324"
        f"?localidades=N6[{codigo_municipio}]"
    )
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        dados = resp.json()
        if not dados:
            return None
        serie = dados[0]["resultados"][0]["series"][0]["serie"]
        (ano, valor), = serie.items()
        return {"ano": ano, "populacao_estimada": valor}
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return None


def coletar(uf: str, saida: Path, limite: int | None = None) -> None:
    municipios = listar_municipios(uf)
    if limite:
        municipios = municipios[:limite]

    saida.parent.mkdir(parents=True, exist_ok=True)
    with open(saida, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["codigo_ibge", "municipio", "uf", "ano", "populacao_estimada"]
        )
        writer.writeheader()
        for m in municipios:
            pop = obter_populacao_estimada(str(m["id"]))
            writer.writerow(
                {
                    "codigo_ibge": m["id"],
                    "municipio": m["nome"],
                    "uf": uf,
                    "ano": pop["ano"] if pop else "",
                    "populacao_estimada": pop["populacao_estimada"] if pop else "",
                }
            )
            time.sleep(0.2)  # boa prática: não sobrecarregar a API pública

    print(f"Dados salvos em: {saida}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta dados socioeconômicos do IBGE.")
    parser.add_argument("--uf", required=True, help="Sigla da UF, ex.: SP, MG, RJ")
    parser.add_argument(
        "--saida",
        default="../../Data/Raw/ibge_municipios.csv",
        help="Caminho do arquivo CSV de saída",
    )
    parser.add_argument(
        "--limite", type=int, default=None, help="Limitar nº de municípios (uso em testes)"
    )
    args = parser.parse_args()

    coletar(args.uf.upper(), Path(args.saida), args.limite)


if __name__ == "__main__":
    sys.exit(main())
