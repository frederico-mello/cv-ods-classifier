"""
LattesParser: extrai, do XML oficial do Currículo Lattes (cv.xml), as peças
relevantes para a análise por ODS.

O XML do Lattes é um XML bem estruturado (namespace LattesXML). Este parser
não precisa de regras por tag — ele usa o *conteúdo text* dos nós, categorizado
pela estrutura do documento. Cada "campo" extraído carrega:
  - section: categoria semântica (formacao / linhaPesquisa / publicacao / ...)
  - text:    o texto bruto (concatenado dos filhos do nó)
  - weight:  peso da seção no score (definido no Scorer)

O parser é tolerante a diferenças de indentação e a atributos ausentes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
from xml.etree import ElementTree as ET

# Mapeia a tag do XML do Lattes -> categoria semântica do campo.
# As tags do Lattes usam namespace "{http://lattes.org/2023/06/01/XMLSchema}".
# Como as tags podem variar entre versões, casamos pelo localname (sem namespace).

TAG_TO_SECTION = {
    "tituloPrincipal": "titulo",
    "nome": "titulo",
    "areaPrincipal": "formacao",
    "areaConcentracao": "formacao",
    "linhaPesquisa": "linhaPesquisa",
    "linhasPesquisa": "linhaPesquisa",
    "areaConcentracaoDaLinhaPesquisa": "linhaPesquisa",
    # Formação acadêmica
    "nivelFormacao": "formacao_nivel",
    "tituloRealizado": "formacao_titulo",
    "instituicao": "formacao_instituicao",
    "areaEnsino": "formacao_area",
    "anoInicio": "formacao_ano",
    # Publicações
    "tipo": "pub_tipo",
    "titulo": "pub_titulo",
    "subtitle": "pub_titulo",
    "nomeDaRevista": "pub_revista",
    "nomeDoPeriodico": "pub_periodico",
    "nomeDoEvento": "pub_evento",
    "nomeDoTrabalho": "pub_trabalho",
    "tituloDaObra": "pub_obra",
    "tituloDoProjeto": "projeto_titulo",
    "nomeDoProjeto": "projeto_titulo",
    "descricaoDoProjeto": "projeto_descricao",
    "descricao": "descricao",
    "resumo": "resumo",
    "sinopse": "sinopse",
    "resumoAnalise": "resumo",
    "areaDeEstudo": "formacao_area",
    "palavrasChave": "palavra_chave",
    "palavraChave": "palavra_chave",
    "keywords": "palavra_chave",
    "assunto": "formacao_assunto",
    "descricaoDoCurriculo": "descricao_curriculo",
    "objetivo": "objetivo",
    "objetivoDoCurriculo": "objetivo",
    "objetivoDoTrabalho": "objetivo",
}


def _localname(tag: str) -> str:
    """Remove namespace de uma tag ElementTree: '{ns}tag' -> 'tag'."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _text(node: ET.Element) -> str:
    """Concatena todo o texto (e sub- textos) de um nó, limpo."""
    parts = [node.text or ""]
    parts.extend(_text(child) for child in node)
    parts.append(node.tail or "")
    return " ".join(parts).replace("\n", " ").strip()


@dataclass
class Field:
    """Um campo extraído do currículo."""

    section: str
    text: str
    weight: float = 1.0

    def __post_init__(self) -> None:
        self.text = " ".join(self.text.split())


@dataclass
class LattesDocument:
    """Representação estruturada do currículo."""

    fields: List[Field] = field(default_factory=list)

    def as_text(self) -> str:
        """Todo o conteúdo concatenado (útil para buscas amplas)."""
        return " ".join(f.text for f in self.fields if f.text)

    def by_section(self, section: str) -> List[str]:
        return [f.text for f in self.fields if f.section == section and f.text]

    def sections(self) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        for f in self.fields:
            if not f.text:
                continue
            out.setdefault(f.section, []).append(f.text)
        return out


def _iter_section(node: ET.Element, section: str, depth: int) -> str:
    """Busca o primeiro descendente da tag que gera `section` (até 3 níveis)."""
    local = _localname(node.tag)
    if local in TAG_TO_SECTION and TAG_TO_SECTION[local] == section and depth <= 3:
        return _text(node)
    return ""


def _walk(node: ET.Element, fields: List[Field]) -> None:
    """Varredura recursiva que categoriza cada nó relevante."""
    local = _localname(node.tag)
    section = TAG_TO_SECTION.get(local)
    if section:
        text = _text(node)
        if text:
            fields.append(Field(section=section, text=text))
    for child in node:
        _walk(child, fields)


def parse_lattes_xml(xml_bytes: bytes) -> LattesDocument:
    """Parseia o XML do Lattes e devolve um LattesDocument estruturado."""
    if isinstance(xml_bytes, str):
        xml_bytes = xml_bytes.encode("utf-8")
    root = ET.fromstring(xml_bytes)
    doc = LattesDocument()
    _walk(root, doc.fields)
    return doc


def parse_lattes_file(path: str) -> LattesDocument:
    with open(path, "rb") as f:
        return parse_lattes_xml(f.read())
