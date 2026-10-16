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
from typing import Dict, Iterable, List, Optional

from .parser import LattesDocument
from .sds import SDG, SDGTaxonomy, build_taxonomy

# Peso de cada seção do Lattes (relatividade de relevância para ODS).
# Uma publicação científica sobre um tema vale mais que uma menção solta.
SECTION_WEIGHTS: Dict[str, float] = {
    "linhaPesquisa": 1.0,
    "projeto_descricao": 0.9,
    "projeto_titulo": 0.8,
    "resumo": 0.8,
    "atuacao": 0.7,
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
# O iésimo multiplicador é DECAY ** i: 1ª ocorrência fator 1, 2ª 0.55, 3ª 0.3025.
DECAY = 0.55

# Constante de saturação da curva: controla quão rápido um ODS se aproxima de 100.
# Valores maiores exigem mais pistas para chegar alto.
SATURATION_K = 1.4

# Seção usada pela busca ampla (fallback por temas).
SECAO_BUSCA_AMPLA = "busca_ampla"


def _sem_repetidos(itens: Iterable[str]) -> List[str]:
    """Remove repetidos preservando a ordem de entrada (nada de set na saída).

    A ordem de iteração de um `set` de strings varia com `PYTHONHASHSEED`
    entre processos; listas/dicts preservam a ordem de inserção e garantem
    a serialização idêntica byte a byte entre execuções (A6).
    """
    unicos: List[str] = []
    for item in itens:
        if item not in unicos:
            unicos.append(item)
    return unicos


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

            # Varredura principal: no máximo UMA evidência por (campo, ODS).
            # Várias palavras-chave do mesmo ODS no mesmo campo são agrupadas
            # na própria evidência, mantendo seção e tag_origem do campo —
            # campos distintos seguem gerando evidências distintas (A5).
            for field_obj in fields:
                found = sdg.matches(field_obj.text)
                if not found:
                    continue
                counts.append(SECTION_WEIGHTS.get(field_obj.section, 0.3))
                palavras = _sem_repetidos(found)
                for kw in palavras:
                    if kw not in matched:
                        matched.append(kw)
                if len(evidence) < MAX_EVIDENCE_PER_SDG:
                    evidence.append({
                        "keyword": ", ".join(palavras),
                        "section": field_obj.section,
                        "text": field_obj.text[:120],
                        "tag_origem": field_obj.tag_origem,
                    })

            # Fallback por temas: SOMENTE depois da varredura principal e só
            # para ODS sem nenhuma correspondência (`counts` vazio), rodando
            # uma única vez por ODS e emitindo no máximo uma evidência.
            if not counts:
                temas = _sem_repetidos(sdg.matches_temas(doc.as_text()))
                for tema in temas:
                    counts.append(1.0)
                    if tema not in matched:
                        matched.append(tema)
                if temas:
                    evidence.append({
                        "keyword": ", ".join(temas),
                        "section": SECAO_BUSCA_AMPLA,
                        "text": "",
                        "tag_origem": "",
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
