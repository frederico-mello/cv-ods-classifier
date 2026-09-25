"""
Servidor MCP do Classificador de Currículo Lattes por ODS da ONU.

Expõe duas ferramentas ao cliente MCP:
  - analyze_cv:       analisa um currículo (por XML inline ou caminho de arquivo)
  - get_sdg_report:  gera um relatório estruturado dos scores por ODS

Execução:
  python -m lattes_sdg.server

O servidor comunica via stdio (JSON-RPC 2.0 sobre stdio) — padrão para clientes locais.
"""

from __future__ import annotations

import base64
import json
from typing import Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
    EmptyResult,
    Prompt,
)

from .parser import LattesDocument, parse_lattes_xml, parse_lattes_file
from .sds import build_taxonomy
from .scorer import CVAnalysis, Scorer

# ---------------------------------------------------------------------------
# Helpers de parsing (aceitam XML inline em base64, JSON ou caminho de arquivo)
# ---------------------------------------------------------------------------


def _decode_input(lattes_xml: Optional[str] = None,
                  file_path: Optional[str] = None) -> LattesDocument:
    """Converte a entrada do cliente em um LattesDocument."""
    if file_path:
        return parse_lattes_file(file_path)
    if not lattes_xml:
        raise ValueError("Forneça `lattes_xml` (conteúdo do XML) ou `file_path` (caminho do arquivo).")

    # Tenta JSON contendo base64, XML cru, ou base64 puro.
    candidate = lattes_xml.strip()
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            candidate = parsed.get("lattes_xml") or parsed.get("content") or candidate
    except (ValueError, json.JSONDecodeError):
        pass

    # Tenta decodificar base64.
    try:
        decoded = base64.b64decode(candidate).decode("utf-8")
        if decoded:
            candidate = decoded
    except Exception:
        pass

    return parse_lattes_xml(candidate.encode("utf-8"))


def _score_to_dict(score) -> Dict:
    return {
        "sdg_id": score.sdg_id,
        "title": score.title,
        "score": score.score,
        "matched_keywords": score.matched_keywords,
        "evidence": score.evidence,
    }


def _analysis_to_report(analysis: CVAnalysis) -> Dict:
    ranking = analysis.ranking
    top = [score for score in ranking[:3] if score.score > 0]
    return {
        "scores": [_score_to_dict(s) for s in ranking],
        "ranking": [_score_to_dict(s) for s in ranking],
        "top_sdg": [
            {"sdg_id": s.sdg_id, "title": s.title, "score": s.score}
            for s in top
        ],
        "summary": {
            "analyzed_sdg": len([s for s in ranking if s.score > 0]),
            "max_score": ranking[0].score if ranking else 0,
            "min_score": ranking[-1].score if ranking else 0,
            "avg_score": round(sum(s.score for s in ranking) / len(ranking), 1) if ranking else 0,
        },
    }


def _analysis_to_result(analysis: CVAnalysis) -> Dict:
    """Formato compacto para a ferramenta analyze_cv."""
    return {
        "scores": [_score_to_dict(s) for s in analysis.ranking],
        "top_sdg": [
            {"sdg_id": s.sdg_id, "title": s.title, "score": s.score}
            for s in analysis.top(5) if s.score > 0
        ],
        "bottom_sdg": [
            {"sdg_id": s.sdg_id, "title": s.title, "score": s.score}
            for s in analysis.bottom(5)
        ],
        "summary": {
            "analyzed_sdg": len([s for s in analysis.ranking if s.score > 0]),
            "max_score": analysis.ranking[0].score if analysis.ranking else 0,
            "min_score": analysis.ranking[-1].score if analysis.ranking else 0,
        },
    }


# ---------------------------------------------------------------------------
# Servidor MCP
# ---------------------------------------------------------------------------

server: Server = Server("lattes-sdg")

TOOL_DESCRIPTORS: Dict[str, Dict] = {
    "analyze_cv": {
        "name": "analyze_cv",
        "description": (
            "Analisa um Currículo Lattes (arquivo XML oficial) e classifica o quanto "
            "esse currículo atende a cada um dos 17 ODS da ONU. "
            "Retorna score 0-100 por ODS, ranking, top 5 ODS e bottom 5 ODS."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "lattes_xml": {
                    "type": "string",
                    "description": "Conteúdo do arquivo XML do Lattes (pode ser XML cru ou base64).",
                },
                "file_path": {
                    "type": "string",
                    "description": "Caminho para o arquivo .xml do Lattes (alternativa ao lattes_xml).",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    "get_sdg_report": {
        "name": "get_sdg_report",
        "description": (
            "Gera um relatório estruturado com a classificação de um Currículo Lattes "
            "contra os 17 ODS da ONU, incluindo scores, top ODS, evidências por ODS e resumo."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "lattes_xml": {
                    "type": "string",
                    "description": "Conteúdo do arquivo XML do Lattes (pode ser XML cru ou base64).",
                },
                "file_path": {
                    "type": "string",
                    "description": "Caminho para o arquivo .xml do Lattes (alternativa ao lattes_xml).",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
}


@server.list_tools()
async def list_tools() -> List[Tool]:
    return [Tool(**d) for d in TOOL_DESCRIPTORS.values()]


@server.call_tool()
async def call_tool(name: str, arguments: Optional[Dict]) -> List[TextContent]:
    if name not in TOOL_DESCRIPTORS:
        raise ValueError(f"Ferramenta desconhecida: {name}")
    args = arguments or {}

    doc = _decode_input(
        lattes_xml=args.get("lattes_xml"),
        file_path=args.get("file_path"),
    )
    analysis = Scorer().analyze(doc)

    if name == "analyze_cv":
        report = _analysis_to_result(analysis)
    else:  # get_sdg_report
        report = _analysis_to_report(analysis)

    return [TextContent(type="text", text=json.dumps(report, ensure_ascii=False, indent=2))]


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, {
            "name": "lattes-sdg",
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "lattes-sdg",
                "version": "1.0.0",
            },
        })


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
