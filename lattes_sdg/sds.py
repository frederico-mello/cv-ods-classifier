"""
SDGTaxonomy: os 17 Objetivos de Desenvimento Sustentável da ONU e as pistas
que permitem reconhecê-los num Currículo Lattes.

Cada ODS é representado por:
  - id          : número de 1 a 17
  - title         : nome curto (oficial da ONU)
  - description   : o que o ODS significa
  - keywords      : palavras-chave em pt/en que sinalizam o tema
  - themes        : termos mais amplos / sinônimos conceituais
  - weight        : peso base (0..1) para pistas dessa seção

Fonte: https://sdgs.un.org/sustainable-development-goals

Este módulo é a ÚNICA fonte de verdade sobre os ODS. Alterá-lo aqui altera o
comportamento do sistema inteiro, mas nada mais depende da estrutura interna.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class SDG:
    """Um dos 17 Objetivos de Desenvimento Sustentável."""

    id: int
    title: str
    description: str
    keywords: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)

    def matches(self, text: str) -> List[str]:
        """Retorna as pistas encontradas em `text` (case-insensitive)."""
        if not text:
            return []
        t = text.lower()
        found: List[str] = []
        for kw in self.keywords:
            if kw.lower() in t:
                found.append(kw.lower())
        for th in self.themes:
            if th.lower() in t:
                found.append(th.lower())
        return found


@dataclass
class SDGTaxonomy:
    """Coleção dos 17 ODS com buscas por id, por tema e globais."""

    sdgs: List[SDG]
    _by_id: Dict[int, SDG] = field(default_factory=dict)
    _themes: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._by_id = {s.id: s for s in self.sdgs}
        self._themes = {}
        for s in self.sdgs:
            for th in s.themes:
                self._themes[th.lower()] = s.id

    def get(self, sdg_id: int) -> SDG:
        return self._by_id[sdg_id]

    def all(self) -> Iterable[SDG]:
        return list(self.sdgs)

    def ids(self) -> List[int]:
        return [s.id for s in self.sdgs]


def build_taxonomy() -> SDGTaxonomy:
    """Constrói a taxonomia com os 17 ODS oficiais."""
    sdgs: List[SDG] = [
        SDG(
            id=1, title="Sem Pobreza",
            description="Erradicar a pobreza em todas as formas, em todas as regiões.",
            keywords=["pobreza", "extreme poverty", "fome", "food insecurity",
                      "indigence", "vulneráveis", "vulnerability", "exclusão social",
                      "social exclusion", "desigualdade de renda", "income inequality"],
            themes=["pobreza", "fome", "segurança alimentar", "exclusão social"],
        ),
        SDG(
            id=2, title="Sem Fome e Agricultura Sustentável",
            description="Erradicar a fome, alcançar a alimentação segura e nutritiva e promover a agricultura sustentável.",
            keywords=["agricultura", "agropecuária", "agropecuária", "safra", "safes",
                      "produtos agrícolas", "laticínios", "pecuária", "arroz", "feijão",
                      "soja", "agronegócio", "agronegocio", "segurança alimentar",
                      "food security", "sustainable agriculture", "soil", "irrigation"],
            themes=["agricultura", "alimentação", "pecuária", "recursos hídricos agrícolas"],
        ),
        SDG(
            id=3, title="Vida e Bem-Estar",
            description="Garantir uma vida saudável e promover o bem-estar para todos, em todas as idades.",
            keywords=["saúde", "health", "doença", "disease", "vacina", "vacination",
                      "mortalidade", "mortality", "epidemia", "epidemic", "pandemia",
                      "tratamento", "tratamiento", "clínica", "clínico", "hospital",
                      "medicina", "medicament", "terapi", "físio", "fisio", "reabilit",
                      "rehabilit", "nutrição", "nutrition", "bem-estar", "bemestar",
                      "saúde mental", "mental health"],
            themes=["saúde pública", "medicina", "epidemiologia", "nutrição", "bem-estar"],
        ),
        SDG(
            id=4, title="Educação de Qualidade",
            description="Assegurar a educação inclusiva e equitativa e de qualidade, e promover oportunidades de aprendizagem ao longo da vida.",
            keywords=["educação", "educacao", "ensino", "pedagogia", "pedagogic",
                      "curículo", "curriculo", "aprendizagem", "aprendizagem", "docência",
                      "docente", "professor", "aluno", "alunos", "graduação", "graduacao",
                      "pós-graduação", "pos-graduacao", "mestrado", "doutorado", "ensino",
                      "alfabetização", "alfabetizacao", "ensino superior", "higher education"],
            themes=["educação", "ensino", "pedagogia", "formação de professores"],
        ),
        SDG(
            id=5, title="Igualdade de Gênero",
            description="Conseguir a igualdade de gênero e empoderar todas as mulheres e meninas.",
            keywords=["gênero", "genero", "gêneros", "generos", "feminismo", "feminist",
                      "mulheres", "women", "género", "igualdade de gênero", "gender equality",
                      "violência de gênero", "violencia de genero", "direitos das mulheres",
                      "empoderamento", "empowerment", "inclusão de gênero", "inclusao de genero"],
            themes=["gênero", "igualdade de gênero", "direitos das mulheres"],
        ),
        SDG(
            id=6, title="Água Potável e Saneamento",
            description="Garantir a disponibilidade de água potável e saneamento e assegurar o manejo sustentável dos recursos hídricos.",
            keywords=["água potável", "agua volvel", "água potavel", "saneamento", "saneament",
                      "esgoto", "esgotamento", "tratamento de água", "tratament de agua",
                      "abastecimento de água", "abastecimento de agua", "saneamento basico",
                      "saneamento basico", "acesso a agua", "recursos hídricos",
                      "recursos hidricos", "qualidade da água", "water resources", "water supply",
                      "water sanitation", "sanitation", "aquífero", "aquifero", "manancial",
                      "reservatorio", "reservatorio", "poço artesiano"],
            themes=["água potável", "saneamento", "recursos hídricos"],
        ),
        SDG(
            id=7, title="Energia Acessível e Sustentável",
            description="Assegurar o acesso confiável, sustentável, moderno e a preço justo à energia para todos.",
            keywords=["energia", "energy", "renovável", "renovable", "solar", "eólica",
                      "eolica", "hidrelétrica", "hydroelectric", "biocombustível",
                      "biocombustivel", "fotovoltaico", "fotovoltaico", "gás natural",
                      "petróleo", "petroleo", "eletricidade", "eletricidade", "consumo de energia",
                      "energy efficiency", "renewable energy", "grid", "bateria"],
            themes=["energia", "recursos energéticos", "eficiência energética"],
        ),
        SDG(
            id=8, title="Trabalho Cresimento Econômico",
            description="Promover o crescimento econômico inclusivo e sustentável, o pleno trabalho produtivo e o emprego digno para todos.",
            keywords=["emprego", "empregos", "empregabilidade", "trabalho", "work",
                      "empregável", "empregavel", "economia", "economy", "cresimento",
                      "crescimento", "economic", "desenvolvimento econômico",
                      "desenvolvimento economico", "PIB", "gross domestic product",
                      "microcrédito", "microcredito", "microfinanças", "microfinancas",
                      "setor informal", "informal sector", "carreira", "career"],
            themes=["economia", "emprego", "crescimento econômico", "trabalho digno"],
        ),
        SDG(
            id=9, title="Inovação e Infraestrutura",
            description="Construir infraestrutura resiliente, promover a inclusão e a indústria sustentável e fomentar a inovação.",
            keywords=["inovação", "inovacao", "inovações", "inovacoes", "inovar",
                      "inove", "pesquisa e desenvolvimento", "pesquisa e desenvolvimento",
                      "P&D", "I&D", "indústria", "industria", "industrial", "infraestrutura",
                      "infraestrutura", "infra-estrutura", "tecnologia", "technology",
                      "start-up", "startup", "digital", "digitalização", "digitalizacao",
                      "inteligência artificial", "inteligencia artificial", "IA", "IoT",
                      "iot", "manufatura", "manufacturing", "engenharia"],
            themes=["inovação", "indústria", "infraestrutura", "tecnologia"],
        ),
        SDG(
            id=10, title="Redução de Desigualdades",
            description="Reduzir a desigualdade dentro e entre os países.",
            keywords=["desigualdade", "desigualdades", "desigualdad", "inequality",
                      "inclusão", "inclusao", "inclusivo", "inclusiva", "includente",
                      "acessibilidade", "acessibilidade", "acessível", "acessivel",
                      "minorias", "minorías", "inclusão digital", "inclusao digital",
                      "exclusão social", "social exclusion", "equidade", "equidade"],
            themes=["desigualdade", "inclusão social", "acessibilidade", "equidade"],
        ),
        SDG(
            id=11, title="Cidades e Comunidades Sustentáveis",
            description="Assegurar cidades e comunidades inclusivas, seguras, resilientes e sustentáveis.",
            keywords=["cidade", "cidades", "urban", "urbano", "urbana", "urbanização",
                      "urbanizacao", "comunidade", "communities", "habitação", "habitacao",
                      "mobilidade urbana", "urban mobility", "transporte público",
                      "transporte publico", "transporte coletivo", "resiliência urbana",
                      "urbanization", "city", "housing", "sustainable cities"],
            themes=["cidades", "planejamento urbano", "comunidades", "transporte"],
        ),
        SDG(
            id=12, title="Consumo e Produção Responsáveis",
            description="Assegurar padrões de consumo e produção responsáveis.",
            keywords=["consumo", "consumo", "produção", "producao", "responsável",
                      "responsavel", "sustentável", "sustentavel", "sustainable", "ciclo de vida",
                      "lifecycle", "ecodesign", "eco-design", "resíduo", "residuo", "resíduos",
                      "reciclagem", "reciclagem", "resíduos sólidos", "solid waste",
                      "eficiência de recursos", "resource efficiency", "pegada de carbono",
                      "carbon footprint"],
            themes=["consumo responsável", "produção responsável", "resíduos", "sustentabilidade"],
        ),
        SDG(
            id=13, title="Ação Climática",
            description="Tomar urgência na luta contra a mudança do clima e seus impactos.",
            keywords=["clima", "clima", "climático", "climatico", "climática", "climatica",
                      "mudanças climáticas", "mudanca climatica", "mudança climática",
                      "aquecimento global", "global warming", "CO2", "CO2", "dióxido de carbono",
                      "carbono", "carbon", "metano", "metane", "pegada de carbono",
                      "carbon footprint", "gás de efeito estufa", "greenhouse gas",
                      "emissões", "emissoes", "mitigação climática", "mitigacao climatica",
                      "resiliência climática", "climate change", "climate action"],
            themes=["clima", "mudanças climáticas", "carbono", "mitigação climática"],
        ),
        SDG(
            id=14, title="Vida na Água",
            description="Conservar e usar de forma sustentável os oceanos, os mares e os recursos marinhos para o desenvolvimento sustentável.",
            keywords=["água", "agua", "oceano", "oceanos", "ocean", "mar", "marinho",
                      "marinha", "marine", "peixe", "pescaria", "pesca", "pescado",
                      "coral", "recifal", "recife", "recif", "poluição hídrica",
                      "pollution", "acidificação dos oceanos", "acidification",
                      "recursos marinhos", "marine resources", "aquático", "aquatico",
                      "água doce", "freshwater", "bacia hidrográfica"],
            themes=["recursos marinhos", "oceanos", "água doce", "ecossistemas aquáticos"],
        ),
        SDG(
            id=15, title="Vida Terrestre",
            description="Gerir de forma sustentável as florestas, combater a desertificação, conter a degradação do solo e poner fim à perda de diversidade biológica.",
            keywords=["floresta", "florestas", "forest", "reflorestamento", "reflorestamento",
                      "desertificação", "desertificacion", "desertificacao", "degradação do solo",
                      "degradacao do solo", "diversidade biológica", "diversidade biologica",
                      "biodiversidade", "biodiversity", "fauna", "flora", "espécie",
                      "especie", "espécies", "especies", "conservação", "conservacao",
                      "conservação da natureza", "nature conservation", "mativa nativa",
                      "mata nativa", "vegetação", "vegetacao"],
            themes=["florestas", "biodiversidade", "terra", "conservação da natureza"],
        ),
        SDG(
            id=16, title="Paz e Justiça",
            description="Promover sociedades pacíficas e inclusivas para o desenvolvimento sustentável, proporcionar o acesso à justiça para todos e construir instituições eficazes, responsáveis e inclusivas em todos os níveis.",
            keywords=["paz", "peace", "justiça", "justica", "justiça", "justice",
                      "instituição", "instituicao", "institucional", "institucional", "governança",
                      "governanca", "governança", "transparência", "transparencia", "transparency",
                      "corrupção", "corrupcao", "corrupção", "corrupcao", "direitos humanos",
                      "human rights", "justiça social", "social justice", "segurança",
                      "segurança", "security", "democracia", "democracy"],
            themes=["paz", "justiça", "instituições", "governança", "direitos humanos"],
        ),
        SDG(
            id=17, title="Parcerias e Meios de Implementação",
            description="Reforçar os meios de implementação e revitalizar a parceria global para o desenvolvimento sustentável.",
            keywords=["parceria", "parcerias", "parceria", "partnership", "parceria global",
                      "global partnership", "cooperação", "cooperacao", "cooperation",
                      "financiamento", "financiamento", "finance", "financiamento internacional",
                      "international cooperation", "agência de desenvolvimento",
                      "development agency", "ODS", "SDG", "desenvolvimento sustentável",
                      "sustainable development", "fundos", "fundos", "recursos financeiros"],
            themes=["parcerias", "cooperação internacional", "financiamento", "desenvolvimento sustentável"],
        ),
    ]
    return SDGTaxonomy(sdgs=sdgs)
