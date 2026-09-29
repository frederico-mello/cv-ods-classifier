# Tasks

## 1. Reconciliação dos documentos

- [x] 1.1 Atualizar `docs/03-modelo-de-dados.md` com as 24 entradas de `SECTION_WEIGHTS`, usando chaves idênticas e pesos em ordem decrescente, mais a nota de que o código é a fonte da verdade; verificar cada par contra `lattes_sdg/scorer.py`.
- [x] 1.2 Atualizar `docs/03-modelo-de-dados.md` para registrar `SATURATION_K = 1.4`, `DECAY = 0.55` e `MAX_EVIDENCE_PER_SDG = 6`; verificar os três valores contra as constantes do scorer.
- [x] 1.3 Atualizar `docs/04-algoritmo.md` para descrever `DECAY ** i` e os fatores geométricos `1`, `0.55`, `0.3025` com procedência; verificar os fatores e a procedência contra `_raw_score` e `DECAY`.
- [x] 1.4 Substituir o exemplo de nota em `docs/04-algoritmo.md` pelo resultado obtido executando `_raw_score` e `_normalize` em uma instância `Scorer`, registrando entradas e comando de reprodução no documento; executar o comando documentado e conferir bruto `1.7617500000000001` e normalizado `71.6` para `counts=[1.0, 1.0, 0.7]`.

## 2. Comentário e verificação de escopo

- [x] 2.1 Corrigir somente o comentário junto a `DECAY` em `lattes_sdg/scorer.py` para refletir a primeira ocorrência com fator 1, a segunda 0.55 e a terceira 0.3025; verificar que as linhas executáveis do scorer permanecem inalteradas.
- [x] 2.2 Conferir o diff de escopo para confirmar que só mudaram `docs/03-modelo-de-dados.md`, `docs/04-algoritmo.md` e o comentário de `lattes_sdg/scorer.py`, sem mudanças em lógica executável ou testes; validar que D9 e D10 não foram incluídos.