"""
LattesParser: extrai, do XML do Currículo Lattes, as peças relevantes para a
análise por ODS.

Formatos aceitos:
  - exportação oficial (LATTES_OFFLINE): tags MAIÚSCULAS com hífen, conteúdo
    em ATRIBUTOS, arquivo ISO-8859-1 (com fallback para UTF-8);
  - formato legado camelCase do projeto: conteúdo no texto dos elementos,
    mantido por compatibilidade.

Fluxo por atributo, nesta ordem:
  1. denylist de dados pessoais — aplicada antes de qualquer mapeamento;
  2. descarte de valor vazio ou sem conteúdo;
  3. tabela explícita elemento -> atributo -> seção -> peso;
  4. rede de segurança por padrão de nome (TITULO-, NOME-DA-, DESCRICAO- e
     *PALAVRA-CHAVE*) com peso conservador 0.5;
  5. fora das duas camadas -> ignorado.

Regra especial: atributos com sufixo -INGLES (tradução automática do Lattes)
recebem o peso da linha correspondente multiplicado por 0.5. Cada campo
extraído carrega tag_origem (localname da tag de onde o valor veio).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
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

PESO_SEGURANCA = 0.5

SUFIXO_TRADUCAO = "-INGLES"

PII_DENYLIST = frozenset({
    "NOME-COMPLETO",
    "NOME-EM-CITACOES-BIBLIOGRAFICAS",
    "CPF",
    "NUMERO-IDENTIDADE",
    "DATA-NASCIMENTO",
    "TELEFONE",
    "E-MAIL",
    "LOGRADOURO",
    "BAIRRO",
    "NOME-DO-PAI",
    "NOME-DA-MAE",
    "AUTORES",
})

PADROES_SEGURANCA: Tuple[Tuple[str, str, str], ...] = (
    ("prefixo", "TITULO-", "titulo"),
    ("prefixo", "NOME-DA-", "formacao_area"),
    ("prefixo", "DESCRICAO-", "descricao"),
    ("contem", "PALAVRA-CHAVE", "palavra_chave"),
)

_FORMACAO: Dict[str, Tuple[str, float]] = {
    "NOME-CURSO": ("formacao_area", 0.5),
    "NOME-INSTITUICAO": ("formacao_instituicao", 0.2),
    "TITULO-DO-TRABALHO-DE-CONCLUSAO-DE-CURSO": ("formacao_titulo", 0.7),
    "TITULO-DA-MONOGRAFIA": ("formacao_titulo", 0.7),
    "ANO-DE-INICIO": ("formacao_ano", 0.1),
    "ANO-DE-CONCLUSAO": ("formacao_ano", 0.1),
}

TABELA_ATRIBUTOS: Dict[Tuple[str, ...], Dict[str, Tuple[str, float]]] = {
    ("RESUMO-CV",): {
        "TEXTO-RESUMO-CV-RH": ("resumo", 0.8),
    },
    ("LINHA-DE-PESQUISA",): {
        "TITULO-DA-LINHA-DE-PESQUISA": ("linhaPesquisa", 1.0),
        "NOME-DA-LINHA-DE-PESQUISA": ("linhaPesquisa", 1.0),
        "OBJETIVOS-LINHA-DE-PESQUISA": ("objetivo", 0.6),
    },
    ("PALAVRAS-CHAVE",): {
        "PALAVRA-CHAVE-1": ("palavra_chave", 0.7),
        "PALAVRA-CHAVE-2": ("palavra_chave", 0.7),
        "PALAVRA-CHAVE-3": ("palavra_chave", 0.7),
        "PALAVRA-CHAVE-4": ("palavra_chave", 0.7),
        "PALAVRA-CHAVE-5": ("palavra_chave", 0.7),
        "PALAVRA-CHAVE-6": ("palavra_chave", 0.7),
    },
    ("PROJETO-DE-PESQUISA",): {
        "NOME-DO-PROJETO": ("projeto_titulo", 0.8),
        "DESCRICAO-DO-PROJETO": ("projeto_descricao", 0.9),
    },
    ("ARTIGO-PUBLICADO", "DADOS-BASICOS-DO-ARTIGO"): {
        "TITULO-DO-ARTIGO": ("pub_titulo", 1.0),
    },
    ("TRABALHO-EM-EVENTOS", "DADOS-BASICOS-DO-TRABALHO"): {
        "TITULO-DO-TRABALHO": ("pub_titulo", 1.0),
    },
    ("TRABALHO-EM-EVENTOS", "DETALHAMENTO-DO-TRABALHO"): {
        "NOME-DO-EVENTO": ("pub_evento", 0.5),
        "TITULO-DOS-ANAIS-OU-PROCEEDINGS": ("pub_evento", 0.5),
        "NOME-DA-EDITORA": ("pub_revista", 0.3),
    },
    ("LIVRO-PUBLICADO-OU-ORGANIZADO", "DADOS-BASICOS-DO-LIVRO"): {
        "TITULO-DO-LIVRO": ("pub_obra", 1.0),
    },
    ("DETALHAMENTO-DO-ARTIGO",): {
        "TITULO-DO-PERIODICO-OU-REVISTA": ("pub_periodico", 0.3),
    },
    ("DETALHAMENTO-DO-LIVRO",): {
        "NOME-DA-EDITORA": ("pub_revista", 0.3),
    },
    ("PARTICIPACAO-EM-CONGRESSO", "DADOS-BASICOS-DA-PARTICIPACAO-EM-CONGRESSO"): {
        "TITULO": ("pub_titulo", 1.0),
    },
    ("PARTICIPACAO-EM-CONGRESSO", "DETALHAMENTO-DA-PARTICIPACAO-EM-CONGRESSO"): {
        "NOME-DO-EVENTO": ("pub_evento", 0.5),
    },
    ("AREA-DE-ATUACAO",): {
        "NOME-GRANDE-AREA-DO-CONHECIMENTO": ("formacao_area", 0.5),
        "NOME-DA-AREA-DO-CONHECIMENTO": ("formacao_area", 0.5),
        "NOME-DA-SUB-AREA-DO-CONHECIMENTO": ("formacao_area", 0.5),
        "NOME-DA-ESPECIALIDADE": ("formacao_assunto", 0.4),
    },
    ("INFORMACAO-ADICIONAL-CURSO",): {
        "NOME-GRANDE-AREA-DO-CONHECIMENTO": ("formacao_area", 0.5),
        "NOME-DA-AREA-DO-CONHECIMENTO": ("formacao_area", 0.5),
        "NOME-DA-SUB-AREA-DO-CONHECIMENTO": ("formacao_area", 0.5),
        "NOME-DA-ESPECIALIDADE": ("formacao_assunto", 0.4),
    },
    ("OUTRA-ATIVIDADE-TECNICO-CIENTIFICA",): {
        "ATIVIDADE-REALIZADA": ("atuacao", 0.7),
    },
    ("DIRECAO-E-ADMINISTRACAO",): {
        "CARGO-OU-FUNCAO": ("atuacao", 0.4),
    },
    ("CONSELHO-COMISSAO-E-CONSULTORIA",): {
        "ESPECIFICACAO": ("atuacao", 0.7),
    },
    ("GRADUACAO",): _FORMACAO,
    ("MESTRADO",): _FORMACAO,
    ("DOUTORADO",): _FORMACAO,
    ("ESPECIALIZACAO",): _FORMACAO,
}

_NAO_ASCII = re.compile("[^\x00-\x7f]")

_DECLARACAO_ENCODING = re.compile(
    r'(?i)^(\s*<\?xml[^>]*?encoding\s*=\s*)("[^"]*"|\'[^\']*\')'
)

_PADRAO_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]{2,}")
_PADRAO_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b")
_PADRAO_TELEFONE = re.compile(r"\(?\d{2}\)?[\s-]\d{4,5}-\d{4}\b")


def _localname(tag: str) -> str:
    """Remove namespace de uma tag ElementTree: '{ns}tag' -> 'tag'."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _text(node: ET.Element) -> str:
    """Concatena todo o texto (e sub-textos) de um nó, limpo."""
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
    tag_origem: str = ""

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


def _decodificar(xml_bytes: bytes) -> str:
    """Decodifica bytes do XML: UTF-8 válido com multibyte -> UTF-8, senão ISO-8859-1."""
    try:
        texto = xml_bytes.decode("utf-8")
    except UnicodeDecodeError:
        texto = xml_bytes.decode("iso-8859-1")
    else:
        if not _NAO_ASCII.search(texto):
            texto = xml_bytes.decode("iso-8859-1")
    return texto.lstrip("\ufeffï»¿")


def _para_elemento(texto: str) -> ET.Element:
    """Converte texto decodificado em elemento, neutralizando a declaração de encoding."""
    texto = _DECLARACAO_ENCODING.sub(r'\1"UTF-8"', texto, count=1)
    return ET.fromstring(texto.encode("utf-8"))


def _bloqueado(*nomes: str) -> bool:
    """True se algum nome de tag/atributo está na denylist de dados pessoais."""
    for nome in nomes:
        if nome in PII_DENYLIST:
            return True
        if any(nome.startswith(bloqueio + "-") for bloqueio in PII_DENYLIST):
            return True
    return False


def _valor_util(valor: str) -> bool:
    """False para valor vazio, só espaços/símbolos ou com cara de dado pessoal."""
    if not valor or not valor.strip():
        return False
    if not any(c.isalnum() for c in valor):
        return False
    if _PADRAO_EMAIL.search(valor):
        return False
    if _PADRAO_CPF.search(valor):
        return False
    if _PADRAO_TELEFONE.search(valor):
        return False
    return True


def _consultar_tabela(
    caminho: Tuple[str, ...], nome: str
) -> Optional[Tuple[str, float]]:
    """Busca (seção, peso) na tabela explícita, pelo sufixo mais longo do caminho."""
    for tamanho in range(len(caminho), 0, -1):
        regras = TABELA_ATRIBUTOS.get(caminho[-tamanho:])
        if regras is not None and nome in regras:
            return regras[nome]
    return None


def _secao_por_padrao(nome: str) -> Optional[str]:
    """Rede de segurança: seção genérica para atributos com padrão de nome reconhecido."""
    for modo, padrao, secao in PADROES_SEGURANCA:
        if modo == "prefixo" and nome.startswith(padrao):
            return secao
        if modo == "contem" and padrao in nome:
            return secao
    return None


def _extrair_atributos(
    node: ET.Element, caminho: Tuple[str, ...], campos: List[Field]
) -> None:
    local = _localname(node.tag)
    elemento_bloqueado = _bloqueado(local)
    for nome_attr, valor in node.attrib.items():
        nome = nome_attr.upper()
        traducao = nome.endswith(SUFIXO_TRADUCAO)
        nome_base = nome[: -len(SUFIXO_TRADUCAO)] if traducao else nome
        if elemento_bloqueado or _bloqueado(nome):
            continue
        if traducao and _bloqueado(nome_base):
            continue
        if not _valor_util(valor):
            continue
        regra = _consultar_tabela(caminho, nome_base)
        if regra is not None:
            secao, peso = regra
        else:
            secao = _secao_por_padrao(nome)
            if secao is None:
                continue
            peso = PESO_SEGURANCA
        if traducao:
            peso *= 0.5
        campos.append(
            Field(section=secao, text=valor, weight=peso, tag_origem=local)
        )


def _walk(
    node: ET.Element, campos: List[Field], caminho: Tuple[str, ...] = ()
) -> None:
    """Varredura recursiva: atributos da exportação oficial + texto legado."""
    local = _localname(node.tag)
    caminho = caminho + (local,)
    _extrair_atributos(node, caminho, campos)
    secao = TAG_TO_SECTION.get(local)
    if secao:
        texto = _text(node)
        if _valor_util(texto):
            campos.append(Field(section=secao, text=texto, tag_origem=local))
    for child in node:
        _walk(child, campos, caminho)


def parse_lattes_xml(xml_bytes: bytes) -> LattesDocument:
    """Parseia o XML do Lattes e devolve um LattesDocument estruturado."""
    if isinstance(xml_bytes, str):
        xml_bytes = xml_bytes.encode("utf-8")
    root = _para_elemento(_decodificar(xml_bytes))
    doc = LattesDocument()
    _walk(root, doc.fields)
    return doc


def parse_lattes_file(path: str) -> LattesDocument:
    with open(path, "rb") as f:
        return parse_lattes_xml(f.read())
