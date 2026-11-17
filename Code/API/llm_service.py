"""
Serviço de LLM local (HuggingFace Transformers) — TP4.

Carrega, sob demanda e uma única vez, modelos da HuggingFace executados na
máquina local (sem chamadas a serviços de nuvem após o download inicial) e
expõe duas tarefas de PLN usadas pela API:

  - "resumo":     resumo automático de textos em português
  - "sentimento": classificação positivo / neutro / negativo

Os modelos podem ser trocados por variáveis de ambiente, sem alterar código:
  CONECTA_MODELO_RESUMO      (padrão: recogna-nlp/ptt5-base-summ)
  CONECTA_MODELO_SENTIMENTO  (padrão: lxyuan/distilbert-base-multilingual-cased-sentiments-student)
  CONECTA_LLM_OFFLINE=1      usa somente arquivos já baixados (HF_HUB_OFFLINE)
  CONECTA_LLM_TIMEOUT_S      tempo máximo por inferência (padrão: 60)

Erros são traduzidos em exceções de domínio (ver abaixo), que a API converte em
códigos HTTP adequados (422, 503, 504, 500).
"""

from __future__ import annotations

import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from typing import Any, Callable

# Modo offline: as bibliotecas da HuggingFace leem estas variáveis ao serem importadas,
# por isso são definidas aqui, antes de qualquer `import transformers`. (Passar
# `local_files_only` manualmente ao pipeline causa "multiple values for keyword
# argument" nas versões recentes do transformers.)
if os.environ.get("CONECTA_LLM_OFFLINE") == "1":
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

MODELO_RESUMO_PADRAO = "recogna-nlp/ptt5-base-summ"
MODELO_SENTIMENTO_PADRAO = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"

TAREFAS = ("resumo", "sentimento")
TRADUCAO_ROTULOS = {
    "positive": "positivo", "negative": "negativo", "neutral": "neutro",
    "positivo": "positivo", "negativo": "negativo", "neutro": "neutro",
    "label_0": "negativo", "label_1": "neutro", "label_2": "positivo",
}

MIN_CARACTERES_RESUMO = 200   # abaixo disso não há o que resumir
MAX_CARACTERES = 20_000       # limite de segurança de entrada


# --------------------------------------------------------------------------
# Exceções de domínio
# --------------------------------------------------------------------------
class ServicoLLMError(Exception):
    """Base das falhas do serviço de LLM."""

    codigo_http = 500
    codigo = "erro_interno"
    dica = "Consulte os logs do servidor."

    def __init__(self, mensagem: str = "", dica: str | None = None) -> None:
        super().__init__(mensagem)
        if dica:
            self.dica = dica


class EntradaInvalidaError(ServicoLLMError):
    codigo_http = 422
    codigo = "entrada_invalida"
    dica = "Revise o texto enviado e tente novamente."


class ModeloIndisponivelError(ServicoLLMError):
    codigo_http = 503
    codigo = "modelo_indisponivel"
    dica = (
        "Instale as dependências (pip install transformers torch), baixe o modelo "
        "(python Code/Modeling/baixar_modelos.py) e reinicie a API."
    )


class TempoLimiteError(ServicoLLMError):
    codigo_http = 504
    codigo = "tempo_limite_excedido"
    dica = "Envie um texto menor ou aumente CONECTA_LLM_TIMEOUT_S."


class InferenciaError(ServicoLLMError):
    codigo_http = 500
    codigo = "falha_na_inferencia"
    dica = "O modelo carregou, mas falhou ao processar este texto."


# --------------------------------------------------------------------------
# Criação do pipeline (isolada para poder ser substituída em testes)
# --------------------------------------------------------------------------
DICA_DEPENDENCIAS = "Instale as dependências: pip install -r requirements.txt (transformers, torch, sentencepiece)."
DICA_CARGA = (
    "Confira o detalhe do erro acima. Se o modelo ainda não foi baixado, rode "
    "'python Code/Modeling/baixar_modelos.py'; se mudou de versão do transformers, "
    "veja 'GET /llm/status' e os logs do servidor."
)


DICA_TOKENIZADOR = (
    "Incompatibilidade entre sentencepiece e protobuf. Rode: pip install -U protobuf sentencepiece "
    "e reinicie a API."
)


def _criar_resumidor(modelo: str) -> Callable[..., Any]:
    """Resumidor baseado em AutoTokenizer + AutoModelForSeq2SeqLM.

    Não usa `pipeline("summarization")`, que mudou/foi removido em versões recentes do
    transformers; assim o código independe dessa API.
    """
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    try:
        tokenizador = AutoTokenizer.from_pretrained(modelo)
    except Exception as exc_rapido:  # noqa: BLE001
        # Contorno: o tokenizador "lento" lê o spiece.model direto com a biblioteca sentencepiece,
        # sem a conversão que depende de protobuf compatível (causa comum de falha no Windows).
        try:
            tokenizador = AutoTokenizer.from_pretrained(modelo, use_fast=False)
        except Exception:  # noqa: BLE001
            raise exc_rapido from None
    rede = AutoModelForSeq2SeqLM.from_pretrained(modelo)
    rede.eval()

    def resumir(texto: str, max_length: int = 96, min_length: int = 10, num_beams: int = 4,
                no_repeat_ngram_size: int = 3, **_ignorados: Any) -> list[dict]:
        entradas = tokenizador(texto, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            ids = rede.generate(
                **entradas, max_length=max_length, min_length=min_length, num_beams=num_beams,
                no_repeat_ngram_size=no_repeat_ngram_size, early_stopping=True,
            )
        return [{"summary_text": tokenizador.decode(ids[0], skip_special_tokens=True)}]

    return resumir


def criar_pipeline_hf(tarefa: str, modelo: str) -> Callable[..., Any]:
    """Carrega o modelo HuggingFace localmente (cache em disco; sem nuvem após o download)."""
    try:
        import transformers  # noqa: F401
        import torch  # noqa: F401
    except ImportError as exc:
        raise ModeloIndisponivelError(
            f"Biblioteca ausente: {exc}. O transformers e o PyTorch precisam estar instalados.",
            dica=DICA_DEPENDENCIAS,
        ) from exc

    try:
        if tarefa == "resumo":
            return _criar_resumidor(modelo)
        from transformers import pipeline

        return pipeline(task="text-classification", model=modelo, top_k=None)
    except Exception as exc:  # noqa: BLE001 — arquivo ausente, memória, versão incompatível...
        problema_tokenizador = re.search(r"protobuf|sentencepiece|spiece|tiktoken", str(exc), re.IGNORECASE)
        raise ModeloIndisponivelError(
            f"Não foi possível carregar o modelo '{modelo}': {type(exc).__name__}: {exc}",
            dica=DICA_TOKENIZADOR if problema_tokenizador else DICA_CARGA,
        ) from exc


# --------------------------------------------------------------------------
# Serviço
# --------------------------------------------------------------------------
class ServicoLLM:
    def __init__(
        self,
        fabrica_pipeline: Callable[[str, str], Callable[..., Any]] = criar_pipeline_hf,
        timeout_s: float | None = None,
    ) -> None:
        self._fabrica = fabrica_pipeline
        self._pipelines: dict[str, Callable[..., Any]] = {}
        self._erros_carga: dict[str, str] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="llm")
        self.timeout_s = timeout_s if timeout_s is not None else float(os.environ.get("CONECTA_LLM_TIMEOUT_S", "60"))

    # ---- configuração -----------------------------------------------------
    @staticmethod
    def nome_modelo(tarefa: str) -> str:
        if tarefa == "resumo":
            return os.environ.get("CONECTA_MODELO_RESUMO", MODELO_RESUMO_PADRAO)
        return os.environ.get("CONECTA_MODELO_SENTIMENTO", MODELO_SENTIMENTO_PADRAO)

    def status(self) -> dict[str, dict]:
        return {
            t: {
                "modelo": self.nome_modelo(t),
                "carregado": t in self._pipelines,
                "ultimo_erro": self._erros_carga.get(t),
            }
            for t in TAREFAS
        }

    # ---- carga ----------------------------------------------------------------
    def _obter_pipeline(self, tarefa: str) -> Callable[..., Any]:
        with self._lock:
            if tarefa not in self._pipelines:
                try:
                    self._pipelines[tarefa] = self._fabrica(tarefa, self.nome_modelo(tarefa))
                    self._erros_carga.pop(tarefa, None)
                except ServicoLLMError as exc:
                    self._erros_carga[tarefa] = str(exc)
                    raise
                except Exception as exc:  # noqa: BLE001
                    self._erros_carga[tarefa] = str(exc)
                    raise ModeloIndisponivelError(f"Falha ao carregar o modelo: {exc}") from exc
            return self._pipelines[tarefa]

    def carregar(self, tarefa: str) -> None:
        """Pré-carrega o modelo (útil para falhar cedo ou aquecer a API)."""
        self._obter_pipeline(tarefa)

    # ---- inferência -------------------------------------------------------------
    def processar(self, tarefa: str, texto: str, max_palavras_resumo: int = 60) -> dict:
        if tarefa not in TAREFAS:
            raise EntradaInvalidaError(f"Tarefa desconhecida: {tarefa!r}. Use: {', '.join(TAREFAS)}.")
        texto = (texto or "").strip()
        if not texto:
            raise EntradaInvalidaError("O texto está vazio.")
        if len(texto) > MAX_CARACTERES:
            raise EntradaInvalidaError(f"Texto muito longo ({len(texto)} caracteres; máximo {MAX_CARACTERES}).")
        if tarefa == "resumo" and len(texto) < MIN_CARACTERES_RESUMO:
            raise EntradaInvalidaError(
                f"Texto curto demais para resumir ({len(texto)} caracteres; mínimo {MIN_CARACTERES_RESUMO})."
            )

        pipe = self._obter_pipeline(tarefa)
        inicio = time.perf_counter()
        futuro = self._executor.submit(self._executar, tarefa, pipe, texto, max_palavras_resumo)
        try:
            resultado = futuro.result(timeout=self.timeout_s)
        except FutureTimeout as exc:
            futuro.cancel()
            raise TempoLimiteError(f"A inferência excedeu {self.timeout_s:.0f}s.") from exc
        except ServicoLLMError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise InferenciaError(f"{type(exc).__name__}: {exc}") from exc

        resultado["tempo_ms"] = round((time.perf_counter() - inicio) * 1000)
        resultado["modelo"] = self.nome_modelo(tarefa)
        return resultado

    # ---- execução de cada tarefa ----------------------------------------------------
    @staticmethod
    def _executar(tarefa: str, pipe: Callable[..., Any], texto: str, max_palavras: int) -> dict:
        if tarefa == "resumo":
            saida = pipe(
                texto,
                max_length=max(16, int(max_palavras * 1.6)),  # ~1,6 token por palavra em PT
                min_length=10,
                num_beams=4,
                no_repeat_ngram_size=3,
                truncation=True,
            )
            resumo = (saida[0].get("summary_text") or "").strip()
            if not resumo:
                raise InferenciaError("O modelo devolveu um resumo vazio.")
            return {"resumo": resumo}

        saida = pipe(texto, truncation=True, max_length=512)
        # Dependendo da versão, a saída é [[{...}, ...]] ou [{...}, ...].
        itens = saida[0] if saida and isinstance(saida[0], list) else saida
        pontuacoes = {}
        for item in itens:
            rotulo = TRADUCAO_ROTULOS.get(str(item["label"]).lower(), str(item["label"]).lower())
            pontuacoes[rotulo] = round(float(item["score"]), 4)
        if not pontuacoes:
            raise InferenciaError("O modelo não devolveu pontuações de sentimento.")
        rotulo = max(pontuacoes, key=pontuacoes.get)
        return {"rotulo": rotulo, "confianca": pontuacoes[rotulo], "pontuacoes": pontuacoes}


# Instância única usada pela API.
servico = ServicoLLM()
