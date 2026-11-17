"""Testes do serviço de LLM com pipelines simulados (não baixam modelos)."""

import time

import pytest

import llm_service as ls
from llm_service import (
    EntradaInvalidaError, InferenciaError, ModeloIndisponivelError, ServicoLLM, TempoLimiteError,
)

TEXTO_LONGO = ("O programa de educação comunitária ampliou o acesso de jovens à robótica e à programação. " * 4).strip()


def fabrica_ok(tarefa, modelo):
    if tarefa == "resumo":
        return lambda texto, **kw: [{"summary_text": "Programa amplia acesso de jovens à robótica."}]
    return lambda texto, **kw: [[
        {"label": "positive", "score": 0.81}, {"label": "neutral", "score": 0.15}, {"label": "negative", "score": 0.04},
    ]]


@pytest.fixture
def servico():
    return ServicoLLM(fabrica_pipeline=fabrica_ok, timeout_s=2)


def test_resumo_ok(servico):
    r = servico.processar("resumo", TEXTO_LONGO)
    assert r["resumo"].startswith("Programa amplia")
    assert r["modelo"] == ls.MODELO_RESUMO_PADRAO
    assert r["tempo_ms"] >= 0


def test_sentimento_ok_e_traducao_de_rotulos(servico):
    r = servico.processar("sentimento", "Adorei o projeto, muito bom!")
    assert r["rotulo"] == "positivo"
    assert r["confianca"] == 0.81
    assert set(r["pontuacoes"]) == {"positivo", "neutro", "negativo"}


def test_sentimento_aceita_saida_sem_lista_aninhada():
    s = ServicoLLM(lambda t, m: (lambda x, **k: [{"label": "LABEL_0", "score": 0.7}, {"label": "LABEL_2", "score": 0.3}]))
    assert s.processar("sentimento", "ruim")["rotulo"] == "negativo"


def test_modelo_e_carregado_uma_unica_vez():
    chamadas = []

    def fabrica(t, m):
        chamadas.append(t)
        return fabrica_ok(t, m)

    s = ServicoLLM(fabrica, timeout_s=2)
    s.processar("sentimento", "ok bom")
    s.processar("sentimento", "ok bom de novo")
    assert chamadas == ["sentimento"]
    assert s.status()["sentimento"]["carregado"] is True
    assert s.status()["resumo"]["carregado"] is False


@pytest.mark.parametrize("tarefa,texto", [
    ("sentimento", ""), ("sentimento", "   "), ("resumo", "curto demais"),
    ("sentimento", "x" * (ls.MAX_CARACTERES + 1)), ("traduzir", "texto qualquer"),
])
def test_entradas_invalidas_retornam_422(servico, tarefa, texto):
    with pytest.raises(EntradaInvalidaError) as e:
        servico.processar(tarefa, texto)
    assert e.value.codigo_http == 422


def test_falha_ao_carregar_modelo_retorna_503_e_registra_erro():
    def fabrica(t, m):
        raise ModeloIndisponivelError("sem internet para baixar o modelo")

    s = ServicoLLM(fabrica, timeout_s=2)
    with pytest.raises(ModeloIndisponivelError) as e:
        s.processar("sentimento", "texto ok")
    assert e.value.codigo_http == 503
    assert "sem internet" in s.status()["sentimento"]["ultimo_erro"]


def test_excecao_generica_na_carga_vira_503():
    def fabrica(t, m):
        raise OSError("disco cheio")

    with pytest.raises(ModeloIndisponivelError):
        ServicoLLM(fabrica).processar("sentimento", "texto ok")


def test_timeout_retorna_504():
    def fabrica(t, m):
        return lambda x, **k: (time.sleep(0.4), [[{"label": "positive", "score": 1.0}]])[1]

    s = ServicoLLM(fabrica, timeout_s=0.05)
    with pytest.raises(TempoLimiteError) as e:
        s.processar("sentimento", "texto ok")
    assert e.value.codigo_http == 504


def test_erro_na_inferencia_retorna_500():
    def fabrica(t, m):
        def pipe(x, **k):
            raise RuntimeError("out of memory")
        return pipe

    with pytest.raises(InferenciaError) as e:
        ServicoLLM(fabrica, timeout_s=2).processar("sentimento", "texto ok")
    assert e.value.codigo_http == 500 and "out of memory" in str(e.value)


def test_resumo_vazio_retorna_500():
    s = ServicoLLM(lambda t, m: (lambda x, **k: [{"summary_text": "  "}]), timeout_s=2)
    with pytest.raises(InferenciaError):
        s.processar("resumo", TEXTO_LONGO)


def test_modelo_configuravel_por_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("CONECTA_MODELO_SENTIMENTO", "meu/modelo-local")
    assert ServicoLLM.nome_modelo("sentimento") == "meu/modelo-local"


def test_sem_transformers_instalado_retorna_503():
    try:
        import transformers  # noqa: F401
        pytest.skip("transformers instalado")
    except ImportError:
        pass
    with pytest.raises(ModeloIndisponivelError):
        ls.criar_pipeline_hf("sentimento", "qualquer/modelo")


# ---------------------------------------------------------------------------
# Regressão: "got multiple values for keyword argument 'local_files_only'"
# ---------------------------------------------------------------------------
import sys
import types


def _instalar_transformers_falso(monkeypatch):
    """Simula o transformers recente: o pipeline já injeta local_files_only por conta própria."""
    registro = {}

    def pipeline(task=None, model=None, model_kwargs=None, **kw):
        registro["pipeline"] = {"task": task, "model": model, "model_kwargs": model_kwargs, **kw}
        if model_kwargs and "local_files_only" in model_kwargs:
            raise TypeError("AutoConfig.from_pretrained() got multiple values for keyword argument 'local_files_only'")
        return lambda texto, **k: [[{"label": "neutral", "score": 1.0}]]

    class FakeTok:
        @classmethod
        def from_pretrained(cls, modelo, **kw):
            registro["tok"] = (modelo, kw)
            return cls()

        def __call__(self, texto, **kw):
            return {"input_ids": [[1, 2, 3]]}

        def decode(self, ids, skip_special_tokens=True):
            return "resumo gerado"

    class FakeModel:
        @classmethod
        def from_pretrained(cls, modelo, **kw):
            registro["model"] = (modelo, kw)
            return cls()

        def eval(self):
            return self

        def generate(self, **kw):
            registro["generate"] = kw
            return [[7, 8]]

    tf = types.ModuleType("transformers")
    tf.pipeline, tf.AutoTokenizer, tf.AutoModelForSeq2SeqLM = pipeline, FakeTok, FakeModel
    torch = types.ModuleType("torch")

    class _NoGrad:
        def __enter__(self): return self
        def __exit__(self, *a): return False

    torch.no_grad = _NoGrad
    monkeypatch.setitem(sys.modules, "transformers", tf)
    monkeypatch.setitem(sys.modules, "torch", torch)
    return registro


def test_sentimento_nao_passa_local_files_only_ao_pipeline(monkeypatch):
    registro = _instalar_transformers_falso(monkeypatch)
    pipe = ls.criar_pipeline_hf("sentimento", "lxyuan/modelo")
    assert pipe("ok")[0][0]["label"] == "neutral"
    assert "local_files_only" not in str(registro["pipeline"])
    assert registro["pipeline"]["task"] == "text-classification" and registro["pipeline"]["top_k"] is None


def test_resumo_usa_automodel_sem_pipeline(monkeypatch):
    registro = _instalar_transformers_falso(monkeypatch)
    pipe = ls.criar_pipeline_hf("resumo", "recogna-nlp/ptt5-base-summ")
    saida = pipe("texto", max_length=96, min_length=10, num_beams=4, no_repeat_ngram_size=3, truncation=True)
    assert saida == [{"summary_text": "resumo gerado"}]
    assert "pipeline" not in registro                      # não passou por pipeline("summarization")
    assert registro["generate"]["max_length"] == 96
    assert "local_files_only" not in str(registro["tok"][1]) + str(registro["model"][1])


def test_servico_completo_com_transformers_falso(monkeypatch):
    _instalar_transformers_falso(monkeypatch)
    s = ServicoLLM(timeout_s=5)  # fábrica real, bibliotecas simuladas
    assert s.processar("sentimento", "texto qualquer")["rotulo"] == "neutro"
    assert s.processar("resumo", TEXTO_LONGO)["resumo"] == "resumo gerado"


def test_erro_de_carga_traz_dica_especifica(monkeypatch):
    tf = types.ModuleType("transformers")
    tf.pipeline = lambda **kw: (_ for _ in ()).throw(OSError("arquivo de pesos não encontrado"))
    monkeypatch.setitem(sys.modules, "transformers", tf)
    monkeypatch.setitem(sys.modules, "torch", types.ModuleType("torch"))
    with pytest.raises(ModeloIndisponivelError) as e:
        ls.criar_pipeline_hf("sentimento", "x/y")
    assert "arquivo de pesos" in str(e.value) and "baixar_modelos" in e.value.dica
    assert "pip install" not in e.value.dica


def test_modo_offline_usa_variaveis_de_ambiente():
    """Roda em subprocesso para não recarregar o módulo (e suas classes) dentro da suíte."""
    import os
    import subprocess
    from pathlib import Path

    api = str(Path(__file__).resolve().parents[1] / "Code" / "API")
    env = {k: v for k, v in os.environ.items() if k not in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")}
    env["CONECTA_LLM_OFFLINE"] = "1"
    codigo = (
        f"import sys; sys.path.insert(0, {api!r}); import llm_service, os; "
        "print(os.environ.get('HF_HUB_OFFLINE'), os.environ.get('TRANSFORMERS_OFFLINE'))"
    )
    saida = subprocess.run([sys.executable, "-I", "-c", codigo], env=env, capture_output=True, text=True)
    assert saida.stdout.strip() == "1 1", saida.stderr


# ---------------------------------------------------------------------------
# Regressão: sentencepiece/protobuf incompatíveis (Windows) ao carregar o tokenizador T5
# ---------------------------------------------------------------------------
def _tf_com_tokenizador(monkeypatch, falha_rapido: bool, falha_lento: bool):
    chamadas = []

    class Tok:
        @classmethod
        def from_pretrained(cls, modelo, **kw):
            chamadas.append(kw)
            if kw.get("use_fast") is False and falha_lento:
                raise ValueError("falha no tokenizador lento")
            if kw.get("use_fast") is not False and falha_rapido:
                raise ValueError("Error parsing line b'\\x0e' in spiece.model (Protobuf gencode 7.36.1 runtime 7.36.0)")
            return cls()

        def __call__(self, texto, **kw): return {"input_ids": [[1]]}
        def decode(self, ids, skip_special_tokens=True): return "ok"

    class Model:
        @classmethod
        def from_pretrained(cls, modelo, **kw): return cls()
        def eval(self): return self
        def generate(self, **kw): return [[1]]

    tf = types.ModuleType("transformers")
    tf.AutoTokenizer, tf.AutoModelForSeq2SeqLM = Tok, Model
    torch = types.ModuleType("torch")
    torch.no_grad = type("G", (), {"__enter__": lambda s: s, "__exit__": lambda s, *a: False})
    monkeypatch.setitem(sys.modules, "transformers", tf)
    monkeypatch.setitem(sys.modules, "torch", torch)
    return chamadas


def test_tokenizador_rapido_falha_e_o_lento_resolve(monkeypatch):
    chamadas = _tf_com_tokenizador(monkeypatch, falha_rapido=True, falha_lento=False)
    pipe = ls.criar_pipeline_hf("resumo", "recogna-nlp/ptt5-base-summ")
    assert pipe("texto")[0]["summary_text"] == "ok"
    assert chamadas == [{}, {"use_fast": False}]


def test_tokenizador_falha_nos_dois_caminhos_traz_dica_de_protobuf(monkeypatch):
    _tf_com_tokenizador(monkeypatch, falha_rapido=True, falha_lento=True)
    with pytest.raises(ModeloIndisponivelError) as e:
        ls.criar_pipeline_hf("resumo", "recogna-nlp/ptt5-base-summ")
    assert "spiece.model" in str(e.value)                 # mantém o erro original
    assert "pip install -U protobuf sentencepiece" in e.value.dica
