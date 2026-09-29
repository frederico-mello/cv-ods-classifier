"""
Testes de aceite A1–A8 da Onda M0 · Ler o mundo real.

Um teste por critério da seção 6 de `docs/12-plano-onda-m0.md`, alinhado às
tarefas 6.1–6.4 de `openspec/changes/onda-m0-ler-cv-real/tasks.md`:

    A1  CV real expurgado → >= 30 campos em >= 5 seções
    A2  >= 3 ODS com nota > 20 e topo coerente com as seções mais pistadas
    A3  CV mínimo (só nome/área) → 17 notas zero
    A4  título de publicação com "climaticas" → ODS 13 em pub_titulo, peso 1,0
    A5  nenhuma combinação campo/ODS gera evidências duplicadas
    A6  duas classificações serializam JSON idêntico byte a byte
    A7  os nove testes de continuidade sobrevivem no fixture em formato real
        (ver `tests/test_classifier.py`, conferido por test_a7_...)
    A8  varredura dos campos extraídos: zero CPF, e-mail ou telefone

Regra de ouro: nenhum teste depende de dados pessoais — só dos fixtures
anônimos de `tests/fixtures/`.

Rode com:
    python -m pytest tests/ -v
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lattes_sdg.parser import parse_lattes_file, parse_lattes_xml
from lattes_sdg.sds import build_taxonomy
from lattes_sdg.scorer import SECAO_BUSCA_AMPLA, SECTION_WEIGHTS, Scorer

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_TESTES = os.path.dirname(os.path.abspath(__file__))
PASTA_FIXTURES = os.path.join(PASTA_TESTES, "fixtures")

FIXTURE_REAL = os.path.join(PASTA_FIXTURES, "cv_lattes_real_anon.xml")
FIXTURE_MINIMO = os.path.join(PASTA_FIXTURES, "cv_lattes_minimo.xml")
FIXTURE_SINTETICO = os.path.join(PASTA_FIXTURES, "cv_sintetico_formato_real.xml")
FIXTURES = (FIXTURE_REAL, FIXTURE_MINIMO, FIXTURE_SINTETICO)

# Currículo mínimo em formato oficial, montado para o aceite A4: apenas um
# título de trabalho em evento cujo texto contém "climaticas". Sem PII.
CV_TITULO_CLIMATICO = b"""<?xml version="1.0" encoding="UTF-8"?>
<CURRICULO-VITAE SISTEMA-ORIGEM-XML="LATTES_OFFLINE">
  <DADOS-GERAIS NOME-COMPLETO="Pesquisador Anonimo">
    <PRODUCAO-BIBLIOGRAFICA>
      <TRABALHOS-EM-EVENTOS>
        <TRABALHO-EM-EVENTOS SEQUENCIA-PRODUCAO="1">
          <DADOS-BASICOS-DO-TRABALHO TITULO-DO-TRABALHO="Mudancas climaticas e riscos na agricultura irrigada" IDIOMA="PORTUGUES" />
          <DETALHAMENTO-DO-TRABALHO NOME-DO-EVENTO="Seminario Nacional de Clima" />
        </TRABALHO-EM-EVENTOS>
      </TRABALHOS-EM-EVENTOS>
    </PRODUCAO-BIBLIOGRAFICA>
  </DADOS-GERAIS>
</CURRICULO-VITAE>
"""

# Padrões de PII usados na varredura do A8 (independentes do parser).
PADROES_PII = {
    "CPF": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b"),
    "e-mail": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]{2,}"),
    "telefone": re.compile(r"\(?\d{2}\)?[\s-]\d{4,5}-\d{4}\b|\b\d{10,11}\b"),
}

# Código do processo filho do A6: classifica o fixture e emite o JSON na
# stdout em bytes (sem newline), para comparação byte a byte.
CODIGO_REPETICAO = (
    "import sys;"
    "sys.path.insert(0, {testes!r});"
    "from test_aceite import serializar_classificacao;"
    "sys.stdout.buffer.write(serializar_classificacao({fixture!r}))"
)


def _analisar(caminho: str):
    """Classifica o fixture com uma taxonomia nova, como faria o consumidor."""
    return Scorer(build_taxonomy()).analyze(parse_lattes_file(caminho))


def serializar_classificacao(caminho: str) -> bytes:
    """Serializa a classificação de `caminho` em JSON determinístico (bytes).

    Mesma forma da saída pública: lista de ODS na ordem da taxonomia, cada um
    com nota, pistas e evidências. Usada in-processo e pelo processo filho do
    A6 — a comparação é byte a byte.
    """
    analysis = _analisar(caminho)
    relatorio = {
        "scores": [
            {
                "sdg_id": s.sdg_id,
                "title": s.title,
                "score": s.score,
                "matched_keywords": s.matched_keywords,
                "evidence": s.evidence,
            }
            for s in analysis.scores
        ]
    }
    return json.dumps(relatorio, ensure_ascii=False, indent=2).encode("utf-8")


# ---------------------------------------------------------------------------
# A1 · O parser lê o CV real expurgado
# ---------------------------------------------------------------------------


def test_a1_cv_real_gera_ao_menos_30_campos_em_5_secoes():
    doc = parse_lattes_file(FIXTURE_REAL)
    secoes = doc.sections()
    assert len(doc.fields) >= 30, f"apenas {len(doc.fields)} campos extraídos"
    assert len(secoes) >= 5, f"apenas {len(secoes)} seções: {sorted(secoes)}"


# ---------------------------------------------------------------------------
# A2 · As notas refletem o conteúdo
# ---------------------------------------------------------------------------


def test_a2_notas_refletem_conteudo_e_topo_coerente():
    taxonomia = build_taxonomy()
    doc = parse_lattes_file(FIXTURE_REAL)
    analysis = Scorer(taxonomia).analyze(doc)

    acima = [s for s in analysis.scores if s.score > 20]
    assert len(acima) >= 3, (
        f"apenas {len(acima)} ODS acima de 20: "
        f"{[(s.sdg_id, s.score) for s in acima]}"
    )

    # Seções do currículo que mais geraram pistas (campos com alguma keyword).
    campos_com_pista = Counter(
        campo.section
        for campo in doc.fields
        if any(sdg.matches(campo.text) for sdg in taxonomia.all())
    )
    assert campos_com_pista, "o CV real não tem nenhum campo com pista"
    secoes_ricas = {secao for secao, _ in campos_com_pista.most_common(3)}

    topo = analysis.top(5)
    # O ODS nº 1 se explica a partir das seções mais pistadas...
    assert {e["section"] for e in topo[0].evidence} & secoes_ricas, (
        f"topo ({topo[0].sdg_id}) não toca as seções ricas {secoes_ricas}"
    )
    # ...e as seções mais pistadas aparecem nas evidências do topo.
    cobertas = {e["section"] for sdg in topo for e in sdg.evidence}
    assert secoes_ricas <= cobertas, (
        f"seções ricas sem evidência no topo: {secoes_ricas - cobertas}"
    )
    # O topo vem do conteúdo do currículo, não só da busca ampla por temas.
    assert any(e["section"] != SECAO_BUSCA_AMPLA for e in topo[0].evidence)


# ---------------------------------------------------------------------------
# A3 · Falso positivo por nome morre
# ---------------------------------------------------------------------------


def test_a3_cv_minimo_resulta_em_17_notas_zero():
    doc = parse_lattes_file(FIXTURE_MINIMO)
    assert doc.fields, "o CV mínimo (nome + área) precisa ser lido pelo parser"

    analysis = _analisar(FIXTURE_MINIMO)
    assert len(analysis.scores) == 17
    assert all(s.score == 0.0 for s in analysis.scores), (
        "notas diferentes de zero em CV só com nome e área: "
        f"{[(s.sdg_id, s.score) for s in analysis.scores if s.score]}"
    )


# ---------------------------------------------------------------------------
# A4 · Título de publicação pontua
# ---------------------------------------------------------------------------


def test_a4_titulo_com_climaticas_pontua_ods_13_em_pub_titulo():
    doc = parse_lattes_xml(CV_TITULO_CLIMATICO)

    titulos = [f for f in doc.fields if f.section == "pub_titulo"]
    assert len(titulos) == 1, f"esperado 1 título, veio {len(titulos)}"
    titulo = titulos[0]
    assert "climaticas" in titulo.text.lower()
    assert titulo.weight == 1.0, f"peso do título veio {titulo.weight}"
    assert SECTION_WEIGHTS[titulo.section] == 1.0
    assert titulo.tag_origem == "DADOS-BASICOS-DO-TRABALHO"

    analysis = Scorer(build_taxonomy()).analyze(doc)
    ods13 = analysis.get(13)
    assert ods13.score > 0, "ODS 13 não pontuou com o título climático"
    assert any(
        e["section"] == "pub_titulo"
        and "climaticas" in e["text"].lower()
        and e["tag_origem"] == "DADOS-BASICOS-DO-TRABALHO"
        for e in ods13.evidence
    ), f"evidências do ODS 13: {ods13.evidence}"


# ---------------------------------------------------------------------------
# A5 · Evidências sem duplicatas
# ---------------------------------------------------------------------------


def test_a5_nenhuma_combinacao_campo_ods_gera_evidencia_duplicada():
    for caminho in FIXTURES:
        nome = os.path.basename(caminho)
        analysis = _analisar(caminho)
        for sdg in analysis.scores:
            campos = [
                (e["section"], e["tag_origem"], e["text"]) for e in sdg.evidence
            ]
            assert len(campos) == len(set(campos)), (
                f"{nome}: ODS {sdg.sdg_id} repete evidência do mesmo campo: "
                f"{sdg.evidence}"
            )


def test_a5_pistas_repetidas_no_mesmo_campo_sao_agrupadas():
    analysis = _analisar(FIXTURE_REAL)
    agrupadas = [
        e for sdg in analysis.scores for e in sdg.evidence if ", " in e["keyword"]
    ]
    assert agrupadas, "nenhuma evidência agrupou duas pistas do mesmo campo"
    for evidencia in agrupadas:
        palavras = [p.strip() for p in evidencia["keyword"].split(",")]
        assert len(palavras) == len(set(palavras)), (
            f"pista repetida na evidência: {evidencia['keyword']}"
        )


# ---------------------------------------------------------------------------
# A6 · Determinismo preservado
# ---------------------------------------------------------------------------


def test_a6_duas_classificacoes_serializam_json_identico():
    primeiro = serializar_classificacao(FIXTURE_REAL)
    segundo = serializar_classificacao(FIXTURE_REAL)
    assert json.loads(primeiro), "a serialização não é JSON válido"
    assert primeiro == segundo, "duas classificações geraram JSON diferente"


def test_a6_json_identico_entre_processos_com_seeds_de_hash_diferentes():
    codigo = CODIGO_REPETICAO.format(testes=PASTA_TESTES, fixture=FIXTURE_REAL)
    saidas = []
    for seed in ("0", "31337"):
        processo = subprocess.run(
            [sys.executable, "-c", codigo],
            cwd=RAIZ,
            env=dict(os.environ, PYTHONHASHSEED=seed),
            capture_output=True,
            timeout=120,
        )
        assert processo.returncode == 0, processo.stderr.decode("utf-8", "replace")
        saidas.append(processo.stdout)
    assert saidas[0] == saidas[1], "JSON divergiu entre processos com seeds distintas"


# ---------------------------------------------------------------------------
# A7 · Os nove testes atuais sobrevivem
# ---------------------------------------------------------------------------


def test_a7_nove_testes_de_continuidade_apontam_para_fixture_sintetico():
    caminho = os.path.join(PASTA_TESTES, "test_classifier.py")
    espec = importlib.util.spec_from_file_location("continuidade_a7", caminho)
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)

    testes = [
        nome
        for nome, objeto in vars(modulo).items()
        if nome.startswith("test_") and callable(objeto)
    ]
    assert len(testes) == 9, f"suíte de continuidade com {len(testes)} testes"
    assert os.path.samefile(modulo.FIXTURE, FIXTURE_SINTETICO), (
        "os nove testes não apontam para cv_sintetico_formato_real.xml"
    )
    # O fixture em formato oficial precisa realmente ser lido (não vazio).
    assert parse_lattes_file(FIXTURE_SINTETICO).fields


# ---------------------------------------------------------------------------
# A8 · Nenhuma informação pessoal vaza
# ---------------------------------------------------------------------------


def test_a8_campos_extraidos_nao_contem_cpf_email_ou_telefone():
    for caminho in FIXTURES:
        nome = os.path.basename(caminho)
        doc = parse_lattes_file(caminho)
        assert doc.fields, f"{nome}: nenhum campo extraído"
        for campo in doc.fields:
            for tipo, padrao in PADROES_PII.items():
                achado = padrao.search(campo.text)
                assert achado is None, (
                    f"{nome}: {tipo} '{achado.group(0)}' em "
                    f"[{campo.section}] {campo.text}"
                )
