# Changelog — oracle-core-ptbr

## [1.5.0] - 2026-11-06
- Feature — quadro de versões suportadas com fontes (06/11/2026): 19c (Premier até 31/12/2029, Extended até 31/12/2032, upgrade direto para 26ai), 26ai, APEX 26.2/26.1/24.2 (baseline, patch 24.2.22, alerta CVE-2026-101521), ORDS 26.3.1, SQLcl 26.3.1. Stack alvo: APEX 24.2 a 26.2.
- Feature — roteamento para a skill irmã oracle-26ai-helper-ptbr (Vector/Duality/RAFT).

## [1.4.1] - 2026-11-06
- Fix — ambientes unificados na suíte: dev → hom → prod (branches develop → hom → main); antes o core citava "dev → hml → main", misturando branch e ambiente.
- Fix — removidos nomes de clientes reais (SKILL.md e `brand/tema-msbrasil.yaml`), vindos da versão instalada.
- Fix — bloco de versão no corpo dizia 1.3.1 e "1 recurso"; corrigido para 1.4.1 e 2 recursos (= `suite_size`).

## [1.4.0] - 2026-09-15
- MINOR — identidade visual dos entregáveis: `brand/tema-msbrasil.yaml` publicado na convenção da `theme-factory-ptbr` (bloco `brand:` + `extends: tech-innovation`), com seção nova no SKILL.md sobre quando usar o tema da M&S, quando usar o do cliente e o fato de ser provisório até existir paleta oficial. `suite_size` 1 → 2.

## [1.3.1] - 2026-09-15
- Docs — convenção de padrão de código registra que Trivadis 4.4 é a versão final (projeto arquivado em fev/2026) e aponta o dbLinter como catálogo vivo.

## [1.3.0] - 2026-09-15
- MINOR — roteamento para a nova oracle-lab-ptbr (instalação/ambiente local); suíte passa a 10 skills; cenário "não tenho banco para começar".

## [1.2.0] - 2026-09-15
- MINOR — roteamento e convenção "19c por padrão" para a nova oracle-26ai-ptbr; suíte passa a 9 skills; cenários multidisciplinares de upgrade/26ai.

## [1.1.0] - 2026-09-15
- changelog movido do frontmatter para CHANGELOG.md em toda a suíte (SKILL.md mais enxuto no carregamento); nota de manutenção atualizada; release_date sincronizada.

## [1.0.0]
- Skill central da suíte unificada. Roteamento sintoma→módulo, cenários multidisciplinares com ordem de carregamento, convenções transversais canônicas e mapa completo dos 7 módulos técnicos.
