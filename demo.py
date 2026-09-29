"""
Demo: analisa um currículo Lattes e imprime fonte, campos, seções,
ranking dos ODS com nota acima de zero e uma evidência por ODS.

Uso:
    python demo.py
    python demo.py caminho/para/curriculo.xml

Sem argumento, o caminho padrão é CAMINHO_PADRAO.
"""

import sys

from lattes_sdg.parser import parse_lattes_file
from lattes_sdg.sds import build_taxonomy
from lattes_sdg.scorer import Scorer

CAMINHO_PADRAO = "cv-frederico.xml"

sys.stdout.reconfigure(encoding="utf-8")


def _imprimir_evidencia(score) -> None:
    """Uma evidência por ODS: seção, tag_origem e o trecho citado."""
    ev = score.evidence[0]
    trecho = ev.get("text") or "(busca ampla: nenhum campo único citado)"
    origem = ev.get("tag_origem") or "-"
    print(f"  ODS {score.sdg_id:>2} · {score.title}")
    print(f"    pista:      {ev.get('keyword', '')}")
    print(f"    seção:      {ev['section']}")
    print(f"    tag_origem: {origem}")
    print(f"    trecho:     \"{trecho}\"")


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else CAMINHO_PADRAO
    doc = parse_lattes_file(path)
    analysis = Scorer(build_taxonomy()).analyze(doc)

    sections = doc.sections()

    print(f"\nFonte: {path}")
    print(f"Campos extraídos: {len(doc.fields)}")
    print(f"Seções ({len(sections)}):")
    for nome, textos in sections.items():
        print(f"  {nome:<20} {len(textos):>4} campo(s)")

    ranking = [s for s in analysis.ranking if s.score > 0]

    print(f"\n{'ODS':<44} {'Nota':>6}")
    print("-" * 58)
    if not ranking:
        print("  (nenhum ODS com nota acima de zero)")
    for s in ranking:
        bar = "█" * int(s.score / 5)
        print(f"{s.sdg_id:>2} {s.title:<41} {s.score:>6.1f}  {bar}")

    print("\nEvidência por ODS (uma por ODS):")
    if not ranking:
        print("  (sem evidências: nenhuma nota acima de zero)")
    for s in ranking:
        if s.evidence:
            _imprimir_evidencia(s)


if __name__ == "__main__":
    main()
