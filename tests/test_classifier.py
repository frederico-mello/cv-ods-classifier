"""
Testes do Classificador de Currículo Lattes por ODS.

Continuidade (critério A7 da Onda M0): os nove testes abaixo rodam contra
`tests/fixtures/cv_sintetico_formato_real.xml` — o antigo exemplo do projeto
reescrito no formato oficial do Lattes (tags MAIÚSCULAS com atributos). A
cobertura é a mesma da suíte original; só mudou a régua de entrada.

Rode com:
    python -m pytest tests/ -v
ou, sem pytest:
    python tests/test_classifier.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lattes_sdg.parser import parse_lattes_file, parse_lattes_xml
from lattes_sdg.sds import build_taxonomy
from lattes_sdg.scorer import Scorer

# Fixture em formato oficial usado por toda a suíte de continuidade
# (docs/12-plano-onda-m0.md §5 e §6, critério A7).
FIXTURE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "fixtures",
    "cv_sintetico_formato_real.xml",
)


def _analyze():
    doc = parse_lattes_file(FIXTURE)
    return Scorer(build_taxonomy()).analyze(doc)


def test_17_sdg():
    a = _analyze()
    assert len(a.scores) == 17
    assert {s.sdg_id for s in a.scores} == set(range(1, 18))


def test_scores_range():
    a = _analyze()
    for s in a.scores:
        assert 0.0 <= s.score <= 100.0


def test_climate_is_top():
    a = _analyze()
    assert a.get(13).score > 40  # linha de pesquisa + artigo + keywords climaticas


def test_forest_present():
    a = _analyze()
    assert a.get(15).score > 30  # biodiversidade + florestas


def test_health_medium():
    a = _analyze()
    assert a.get(3).score > 10  # um artigo sobre tratamento


def test_water_absent():
    a = _analyze()
    assert a.get(14).score == 0.0  # nada sobre mares/oceanos


def test_ranking():
    a = _analyze()
    ranked = a.ranking
    assert ranked == sorted(ranked, key=lambda s: s.score, reverse=True)


def test_evidence_explained():
    a = _analyze()
    s13 = a.get(13)
    assert len(s13.evidence) > 0
    assert s13.matched_keywords  # tem pistas rastreaveis


def test_empty_doc():
    doc = parse_lattes_xml(b"<lattes></lattes>")
    a = Scorer(build_taxonomy()).analyze(doc)
    assert all(s.score == 0.0 for s in a.scores)


def _run_all():
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
                passed += 1
            except AssertionError as e:
                print(f"FAIL  {name}: {e}")
                failed += 1
    print(f"\n{passed} pass, {failed} fail")
    return failed


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    failed = _run_all()
    sys.exit(1 if failed else 0)
