# Tasks

## 1. T0 · Higiene mínima

- [x] 1.1 Criar `.gitignore` com regras para ignorar `__pycache__/`, `.pytest_cache/`, arquivos compilados e `cv-frederico.xml`; verificar com `git check-ignore` que esses caminhos são ignorados e confirmar que nenhum CV pessoal é adicionado ao repositório.
- [x] 1.2 Remover `__pycache__/` e `.pytest_cache/` já versionados sem apagar fontes; verificar que não constam mais no índice do Git e que os diretórios continuam ignorados.
- [x] 1.3 Corrigir `requirements.txt`, cuja restrição atual de `mcp` é impossível de satisfazer, estabelecendo uma declaração instalável e compatível com o ambiente do projeto; verificar a resolução/instalação das dependências e a inicialização do servidor MCP.

## 2. T1 · Fixtures

- [x] 2.1 Criar `tests/fixtures/cv_lattes_real_anon.xml` a partir do CV real após expurgo de nome e dados pessoais, preservando conteúdo acadêmico; verificar manualmente o checklist de anonimização e confirmar que o original permanece ignorado pelo Git.
- [x] 2.2 Criar `tests/fixtures/cv_lattes_minimo.xml` no formato oficial com apenas nome e área, sem trabalhos; verificar que contém somente esses dados e nenhum identificador pessoal.
- [x] 2.3 Criar `tests/fixtures/cv_sintetico_formato_real.xml` reescrevendo o fixture sintético no formato oficial; verificar que tags e atributos seguem a estrutura oficial e que não há PII.

## 3. T2 · Parser do XML oficial

- [x] 3.1 Implementar decodificação ISO-8859-1 e UTF-8 e extração de atributos oficiais por tabela explícita e padrões de segurança, incluindo títulos de artigo/trabalho/livro, pesos e redução de peso para traduções `-INGLES`; verificar extração e pesos com os fixtures reais e sintético, cobrindo ambos os encodings.
- [x] 3.2 Aplicar denylist de dados pessoais antes de qualquer mapeamento e ignorar valores vazios; acrescentar `tag_origem` a cada campo preservando a API `parse_lattes_xml() -> LattesDocument`; verificar que os campos extraídos têm origem e não incluem atributos pessoais.

## 4. T3 · Busca por pistas

- [x] 4.1 Implementar normalização única de minúsculas, acentos e espaços para texto e pistas, fronteira de palavra incluindo hífen e ban-list para pistas com menos de quatro letras com exceções explícitas da taxonomia; verificar acentos, caixa, ausência de falsos positivos por substring (`ia` em “Ciências”, `mar` em “Maria”), compostos hifenizados e exceção `CO2` apenas como palavra inteira.

## 5. T4 · Dedupe e fallback

- [x] 5.1 Agrupar palavras-chave correspondentes em no máximo uma evidência por campo e ODS, incluindo seção e `tag_origem`; verificar que múltiplas pistas no mesmo campo não duplicam evidências e campos distintos permanecem rastreáveis.
- [x] 5.2 Executar busca ampla somente após a varredura principal, uma vez por ODS sem correspondência de palavra-chave e com no máximo uma evidência; preservar ordem determinística sem iterar conjuntos para produzir saída; verificar fallback condicionado, limite e igualdade byte a byte da saída em execuções repetidas.

## 6. T5 · Testes de aceite A1–A8

- [x] 6.1 Automatizar A1 e A2: CV real anonimizado produz ao menos 30 campos em 5 seções e ao menos 3 ODS com nota acima de 20, com topo coerente com as seções mais pontuadas; verificar execução dos critérios na suíte.
- [x] 6.2 Automatizar A3 e A4: CV mínimo de nome e área resulta em 17 notas zero e título de publicação com “climaticas” pontua ODS 13 em `pub_titulo` com peso 1,0; verificar ambos os cenários.
- [x] 6.3 Automatizar A5 e A6: nenhuma combinação campo/ODS gera evidências duplicadas e duas classificações serializam JSON idêntico byte a byte; verificar os invariantes com testes determinísticos.
- [x] 6.4 Automatizar A7 e A8: re-apontar os nove testes existentes para o fixture sintético oficial e validar que todos passam; varrer os campos extraídos para padrões de CPF, e-mail e telefone e confirmar zero ocorrências.
- [x] 6.5 Executar a suíte completa e confirmar os oito critérios A1–A8 verdes e os nove testes de continuidade aprovados.

## 7. T6 · Demo e documentação

- [x] 7.1 Atualizar `demo.py` para usar `tests/fixtures/cv_lattes_real_anon.xml`; executar a demo e verificar que apresenta campos/evidências derivados do conteúdo real sem PII.
- [x] 7.2 Sincronizar `docs/03-modelo-de-dados.md`, `docs/04-algoritmo.md` e `docs/10-estrutura.md` apenas para refletir seções, origem/evidências, fronteira de palavra e fallback alterados nesta onda; verificar consistência com implementação e critérios, sem reconciliar números reservados à M1.
