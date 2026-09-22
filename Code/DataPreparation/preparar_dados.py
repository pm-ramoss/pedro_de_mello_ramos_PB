"""
Consolidação e limpeza dos dados coletados (Data Preparation - CRISP-DM / TDSP).

TP2: além da limpeza de projetos sociais (já existente no TP1), este script
passou a também consolidar e limpar os dados de notícias ESG/ODS coletados
por `Code/DataAcquisition/scraping_noticias_esg.py`, gerando o dataset
processado consumido pela aba "Notícias & Nuvem de Palavras" da aplicação.

Uso:
    # Projetos sociais (igual ao TP1)
    python preparar_dados.py projetos \
        --entrada ../../Data/Raw/projetos_observatorio.csv \
        --saida ../../Data/Processed/projetos_sociais.csv

    # Notícias (novo no TP2)
    python preparar_dados.py noticias \
        --entrada ../../Data/Raw/noticias_esg_ods.csv \
        --saida ../../Data/Processed/noticias_processadas.csv
"""

import argparse
from pathlib import Path

import pandas as pd


def limpar_projetos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Normalização de texto
    for col in ["nome_projeto", "descricao"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Remove registros sem nome de projeto (dado essencial)
    if "nome_projeto" in df.columns:
        df = df[df["nome_projeto"].str.len() > 0]

    # Remove duplicados por nome do projeto + link
    chave_dedup = [c for c in ["nome_projeto", "link"] if c in df.columns]
    if chave_dedup:
        df = df.drop_duplicates(subset=chave_dedup)

    return df.reset_index(drop=True)


def limpar_noticias(df: pd.DataFrame) -> pd.DataFrame:
    """Limpeza básica do dataset de notícias ESG/ODS coletado via scraping."""
    df = df.copy()

    for col in ["titulo", "resumo", "fonte"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    if "titulo" in df.columns:
        df = df[df["titulo"].str.len() > 0]

    chave_dedup = [c for c in ["titulo", "url"] if c in df.columns]
    if chave_dedup:
        df = df.drop_duplicates(subset=chave_dedup)

    if "data_publicacao" in df.columns:
        df["data_publicacao"] = pd.to_datetime(
            df["data_publicacao"], errors="coerce"
        ).dt.date

    return df.reset_index(drop=True)


LIMPADORES = {
    "projetos": limpar_projetos,
    "noticias": limpar_noticias,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara e consolida os dados coletados.")
    parser.add_argument(
        "tipo", choices=sorted(LIMPADORES), help="Tipo de dataset a processar"
    )
    parser.add_argument("--entrada", required=True, help="CSV bruto de entrada")
    parser.add_argument("--saida", required=True, help="Caminho do CSV processado de saída")
    args = parser.parse_args()

    df = pd.read_csv(args.entrada)
    df_limpo = LIMPADORES[args.tipo](df)

    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    df_limpo.to_csv(saida, index=False)

    print(f"Dataset '{args.tipo}' processado salvo em: {saida} ({len(df_limpo)} registros)")


if __name__ == "__main__":
    main()
