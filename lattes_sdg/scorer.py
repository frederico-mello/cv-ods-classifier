"""
Scorer: o motor de classificação.

Pega o LattesDocument estruturado (parser.py) e a SDGTaxonomy (sds.py) e calcula,
para cada um dos 17 ODS, uma pontuação de 0 a 100 — mostrando quais pistas foram
encontradas e de onde vieram (explicabilidade).

Método: correspondência dirigida por conhecimento (keywords + pesos), NÃO IA
generativa. Resultado determinístico, reproduzível e auditável.

Fluxo:
  1. Para cada campo do currículo, busca as pistas de cada ODS.
  2. Pondera cada pistas pelo peso da seção (publicação > menção solta).
  3. Aplica retorno decrescente: pistas repetidas do mesmo ODS somam menos.
  4. Normaliza a soma bruta em nota 0–100 por ODS (curva de saturação).
  5. Monta justificativas tracejáveis.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .parser import LattesDocument
from .sds import SDG, SDGTaxonomy, build_taxonomy

# Peso de cada seção do Lattes (relatividade de relevância para ODS).
# Uma publicação científica sobre um tema vale mais que uma menção solta.
SECTION_WEIGHTS: Dict[str, float] = {
    "linhaPesquisa": 1.0,
    "projeto_descricao": 0.9,
    "projeto_titulo": 0.8,
    "resumo": 0.8,
    "palavra_chave": 0.7,
    "descricao_curriculo": 0.7,
    "objetivo": 0.6,
    "sinopse": 0.6,
    "pub_titulo": 1.0,          # título de publicação é pista forte
    "pub_trabalho": 1.0,
    "pub_obra": 1.0,
    "pub_evento": 0.5,
    "formacao_area": 0.5,
    "formacao_nivel": 0.5,
    "formacao_assunto": 0.4,
    "pub_tipo": 0.4,
    "formacao_titulo": 0.4,
    "descricao": 0.5,
    "titulo": 0.3,
    "pub_revista": 0.3,
    "pub_periodico": 0.3,
    "formacao_instituicao": 0.2,
    "formacao_ano": 0.1,
}

# Limite de pistas por ODS nas justificativas (para não poluir a saída).
MAX_EVIDENCE_PER_SDG = 6

# Fator de decaimento para repetição de pistas de um mesmo ODS.
# A 1ª ocorrência conta 100%, a 2ª 70%, a 3ª 50%, etc.
DECAY = 0.55

# Constante de saturação da curva: controla quão rápido um ODS se aproxima de 100.
# Valores maiores exigem mais pistas para chegar alto.
SATURATION_K = 1.4


@dataclass
class SDGScore:
    """Resultado da classificação de um ODS."""

    sdg_id: int
    title: str
    score: float
    matched_keywords: List[str] = field(default_factory=list)
    evidence: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class CVAnalysis:
    """Resultado completo da análise de um currículo."""

    scores: List[SDGScore]

    @property
    def ranking(self) -> List[SDGScore]:
        return sorted(self.scores, key=lambda s: s.score, reverse=True)

    def top(self, n: int = 5) -> List[SDGScore]:
        return self.ranking[:n]

    def bottom(self, n: int = 5) -> List[SDGScore]:
        return self.ranking[-n:][::-1]

    def get(self, sdg_id: int) -> Optional[SDGScore]:
        for s in self.scores:
            if s.sdg_id == sdg_id:
                return s
        return None


class Scorer:
    """Classifica um currículo contra os 17 ODS."""

    def __init__(self, taxonomy: Optional[SDGTaxonomy] = None) -> None:
        self.taxonomy = taxonomy or build_taxonomy()

    def _raw_score(self, counts: List[float]) -> float:
        """Soma ponderada com retorno decrescente.

        counts[i] é o peso da iª ocorrência da pista do ODS. A iª ocorrência
        vale DECAY**i da origem, evitando inflar scores por repetição.
        """
        total = 0.0
        for i, c in enumerate(counts):
            total += c * (DECAY ** i)
        return total

    def _normalize(self, raw: float) -> float:
        """Converte a soma bruta em nota 0–100 via curva de saturação."""
        return round(100.0 * (1.0 - math.exp(-raw / SATURATION_K)), 1)

    def analyze(self, doc: LattesDocument) -> CVAnalysis:
        """Classifica o `doc` contra os 17 ODS."""
        fields = [f for f in doc.fields if f.text]
        if not fields:
            return CVAnalysis(scores=[
                SDGScore(sdg_id=s.id, title=s.title, score=0.0)
                for s in self.taxonomy.all()
            ])

        results: List[SDGScore] = []

        for sdg in self.taxonomy.all():
            counts: List[float] = []
            evidence: List[Dict[str, str]] = []
            matched: List[str] = []

            for field_obj in fields:
                weight = SECTION_WEIGHTS.get(field_obj.section, 0.3)
                found = sdg.matches(field_obj.text)
                if found:
                    counts.append(weight)
                    for kw in found:
                        if kw not in matched:
                            matched.append(kw)
                        if len(evidence) < MAX_EVIDENCE_PER_SDG:
                            evidence.append({
                                "keyword": kw,
                                "section": field_obj.section,
                                "text": field_obj.text[:120],
                            })

            # Se nenhuma pista direta, tenta busca por temas amplos.
            if not counts:
                text = doc.as_text().lower()
                for th in sdg.themes:
                    if th.lower() in text:
                        counts.append(1.0)
                        if th.lower() not in matched:
                            matched.append(th.lower())
                        evidence.append({
                            "keyword": th,
                            "section": "busca_ampla",
                            "text": "",
                        })

            raw = self._raw_score(counts)
            score = self._normalize(raw)
            results.append(SDGScore(
                sdg_id=sdg.id,
                title=sdg.title,
                score=score,
                matched_keywords=matched,
                evidence=evidence,
            ))

        return CVAnalysis(scores=results)
