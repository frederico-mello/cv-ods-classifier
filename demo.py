"""
Demo: roda a classificação contra o exemplo_cv.xml e imprime o resultado.

Uso:
    python demo.py
    python demo.py caminho/para/curriculo.xml
"""

import sys
from lattes_sdg.parser import parse_lattes_file
from lattes_sdg.sds import build_taxonomy
from lattes_sdg.scorer import Scorer

import io
sys.stdout.reconfigure(encoding="utf-8")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "exemplo_cv.xml"
    doc = parse_lattes_file(path)
    analysis = Scorer(build_taxonomy()).analyze(doc)

    print(f"\n{'ODS':<42} {'Score':>7}")
    print("-" * 55)
    for s in analysis.ranking:
        bar = "█" * int(s.score / 5)
        print(f"{s.title:<42} {s.score:>7.1f}  {bar}")

    print("\nTop 5 ODS do currículo:")
    for s in analysis.top(5):
        if s.score > 0:
            print(f"  {s.sdg_id:>2} {s.title:<42} {s.score:>6.1f}")
            for ev in s.evidence[:3]:
                print(f"       • {ev['keyword']}  [{ev['section']}]")

    print("\nBottom 5 ODS do currículo:")
    for s in analysis.bottom(5):
        print(f"  {s.sdg_id:>2} {s.title:<42} {s.score:>6.1f}")


if __name__ == "__main__":
    main()
