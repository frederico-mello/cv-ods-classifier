"""
Exemplo mínimo de Currículo Lattes (XML) para testes e demonstração.

Contém pistas para:
  - ODS 3 (Saúde)      : disciplinas e publicações sobre saúde
  - ODS 13 (Clima)     : linha de pesquisa e artigo sobre clima/CO2
  - ODS 4 (Educação)   : formação e docência
  - ODS 15 (Vida Terrestre): projeto sobre florestas
  - ODS 9 (Inovação)   : pesquisa em tecnologia
  - (sem ODS forte)    : nada sobre água/mares (ODS 14)
"""

SAMPLE_Lattes = """<?xml version="1.0" encoding="UTF-8"?>
<lattes>
  <tituloPrincipal>Dr. João da Silva</tituloPrincipal>
  <areaConcentracao>CIENCIAS BIOLOGICAS</areaConcentracao>

  <formacao>
    <nivelFormacao>DOUTORADO</nivelFormacao>
    <tituloRealizado>Doutorado em Ciencias Biologicas</tituloRealizado>
    <instituicao>Universidade Exemplo</instituicao>
    <areaEnsino>Biologia</areaEnsino>
    <anoInicio>2015</anoInicio>
  </formacao>

  <linhaPesquisa>
    <nomeDaLinhaPesquisa>Mudancas Climaticas e Ecossistemas Terrestres</nomeDaLinhaPesquisa>
    <areaConcentracaoDaLinhaPesquisa>Elogia</areaConcentracaoDaLinhaPesquisa>
  </linhaPesquisa>

  <publicacao>
    <tipo>ARTIGO_PUBLICADO</tipo>
    <tituloDoTrabalho>Impactos do Aquecimento Global sobre a Biodiversidade Florestal</tituloDoTrabalho>
    <nomeDoPeriodico>Revista Brasileira de Ecologia</nomeDoPeriodico>
  </publicacao>

  <publicacao>
    <tipo>ARTIGO_PUBLICADO</tipo>
    <tituloDoTrabalho>Avaliacao de Tratamentos para Doencas Cronicas</tituloDoTrabalho>
    <nomeDaRevista>Journal of Health Sciences</nomeDaRevista>
  </publicacao>

  <projeto>
    <tipo>PROJETO_PESQUISA</tipo>
    <nomeDoProjeto>Conservacao de Mativa Nativa e Recursos Hidricos</nomeDoProjeto>
    <descricaoDoProjeto>Projeto de conservacao de florestas e recursos hidricos no Cerrado</descricaoDoProjeto>
  </projeto>

  <publicacao>
    <tipo>ARTIGO_PUBLICADO</tipo>
    <tituloDoTrabalho>Tecnologias Digitais para Inovacaao Educacional</tituloDoTrabalho>
    <nomeDoPeriodico>Revista de Ensino</nomeDoPeriodico>
  </publicacao>

  <resumo>
    <resumodoCurriculo>Professor e pesquisador em Biologia com foco em ecologia, educacao de qualidade e mudancas climaticas.</resumodoCurriculo>
  </resumo>

  <palavrasChave>
    <palavraChave>ecologia</palavraChave>
    <palavraChave>mudancas climaticas</palavraChave>
    <palavraChave>biodiversidade</palavraChave>
    <palavraChave>educacao</palavraChave>
  </palavrasChave>
</lattes>
"""


if __name__ == "__main__":
    import sys, io
    sys.stdout.reconfigure(encoding="utf-8")
    from lattes_sdg.parser import parse_lattes_xml
    from lattes_sdg.scorer import Scorer
    from lattes_sdg.sds import build_taxonomy
    import json

    doc = parse_lattes_xml(SAMPLE_Lattes.encode("utf-8"))
    analysis = Scorer(build_taxonomy()).analyze(doc)

    print(f"\n{'ODS':<40} {'Score':>6}")
    print("-" * 50)
    for s in analysis.ranking:
        bar = "█" * int(s.score / 5)
        print(f"{s.title:<40} {s.score:>6.1f}  {bar}")
