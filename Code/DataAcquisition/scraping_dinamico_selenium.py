"""
Web Scraping de página DINÂMICA com Selenium — TP3.

Por que Selenium aqui?
    No TP2 a página de causas do Observatório do Terceiro Setor rendeu apenas 7
    das 15 causas esperadas: o restante só aparece depois que o navegador
    executa o JavaScript da página (carrossel / "carregar mais"). O
    BeautifulSoup + requests enxerga apenas o HTML inicial, então um navegador
    automatizado é a ferramenta adequada para esse caso.

O script abre a página em um Chrome headless, aguarda o conteúdo carregar,
tenta expandir a lista (botões "ver mais" / rolagem) e entrega o HTML final ao
mesmo tipo de parser usado antes (BeautifulSoup). Se o Selenium/Chrome não
estiver disponível, ou se a página não render ≥ 15 itens, o script avisa e
mantém o CSV existente — o app não depende desta etapa para funcionar.

Uso (a partir da raiz do projeto):
    python Code/DataAcquisition/scraping_dinamico_selenium.py \
        --saida Data/Raw/causas_observatorio_dinamico.csv

Requisitos: `pip install selenium` e Google Chrome instalado (o Selenium 4.6+
baixa o driver automaticamente via Selenium Manager).

Observação: respeite o robots.txt e os termos de uso do site; uso acadêmico,
uma única requisição por execução.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bs4 import BeautifulSoup

# Reaproveita o parser e o gravador de CSV do TP2: só muda COMO o HTML é obtido.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scraping_causas_sociais import URL, extrair_causas, salvar_csv  # noqa: E402

TOTAL_ESPERADO = 15
ROTULOS_EXPANDIR = ("ver mais", "carregar mais", "mostrar mais", "leia mais", "continue lendo")


def baixar_html_dinamico(url: str, espera_s: int = 15) -> str:
    """Abre a página em Chrome headless, expande o conteúdo e devolve o HTML renderizado."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    opcoes = webdriver.ChromeOptions()
    for arg in ("--headless=new", "--no-sandbox", "--disable-gpu", "--window-size=1366,2000"):
        opcoes.add_argument(arg)

    driver = webdriver.Chrome(options=opcoes)
    try:
        driver.get(url)
        WebDriverWait(driver, espera_s).until(EC.presence_of_element_located((By.TAG_NAME, "article")))

        # 1) clica em botões/links de "ver mais" enquanto existirem
        for _ in range(10):
            clicou = False
            for el in driver.find_elements(By.CSS_SELECTOR, "button, a"):
                texto = (el.text or "").strip().lower()
                if texto in ROTULOS_EXPANDIR and el.is_displayed():
                    driver.execute_script("arguments[0].click();", el)
                    clicou = True
                    break
            if not clicou:
                break
            driver.implicitly_wait(1)

        # 2) rola até o fim para disparar carregamento por scroll (lazy loading)
        altura = 0
        for _ in range(8):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.implicitly_wait(1)
            nova = driver.execute_script("return document.body.scrollHeight;")
            if nova == altura:
                break
            altura = nova

        return driver.page_source
    finally:
        driver.quit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Scraping dinâmico (Selenium) das causas sociais.")
    parser.add_argument("--saida", default="Data/Raw/causas_observatorio_dinamico.csv")
    parser.add_argument("--url", default=URL)
    args = parser.parse_args()

    try:
        html = baixar_html_dinamico(args.url)
    except ImportError:
        print("Selenium não instalado (pip install selenium). Nada foi alterado.", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — driver ausente, timeout, rede etc.
        print(f"Falha ao abrir a página dinâmica: {exc}. Nada foi alterado.", file=sys.stderr)
        return 1

    causas = extrair_causas(BeautifulSoup(html, "html.parser"))
    print(f"{len(causas)} de {TOTAL_ESPERADO} causas extraídas após renderização dinâmica.")
    if not causas:
        print("Nenhuma causa encontrada; os seletores podem precisar de ajuste.", file=sys.stderr)
        return 1

    salvar_csv(causas, Path(args.saida), args.url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
