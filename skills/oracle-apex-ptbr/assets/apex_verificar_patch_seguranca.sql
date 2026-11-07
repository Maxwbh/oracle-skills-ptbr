--==============================================================================
-- Verificação de patch level do APEX contra o CPU de outubro/2026
--
-- Fonte (consultada em 06/11/2026):
--   Oracle Critical Patch Update — October 2026 (Rev 1: 20/10/2026)
--     https://www.oracle.com/security-alerts/cpuoct2026.html
--     https://www.oracle.com/security-alerts/cpuoct2026verbose.html#APEX
--   CVE List: https://github.com/CVEProject/cvelistV5 (CVE-2026-101521)
--
--   CVE-2026-101521 — CVSS 3.1 = 9.8 (CRITICAL), componente General.
--     "unauthenticated attacker with network access via HTTPS ...
--      can result in takeover of Oracle APEX."
--     Afetadas: 24.1.0-24.1.21, 24.2.0-24.2.20 e 26.1.0-26.1.4.
--   CVE-2026-66010 — CVSS 3.1 = 6.1, componente General (DOMPurify),
--     exige interação do usuário.
--     Afetadas: 24.1.0-24.1.19, 24.2.0-24.2.18 e 26.1.0-26.1.2.
--
-- O QUE O ADVISORY NÃO DIZ (a verificar):
--   - Qual versão corrige: o CPU só lista as faixas afetadas e remete ao
--     documento CPU359 da Oracle Support. Estar ACIMA da faixa afetada não
--     está escrito como "corrigido" no advisory.
--   - Se a 26.2 é afetada: ela não aparece na lista de afetadas.
--   - Que APEX_RELEASE.VERSION_NO reflete o patch set aplicado: a coluna
--     VERSION_NO aparece na doc de instalação (26.1, configuring ORDS), mas
--     a view não é descrita; confirme também em App Builder > Help > About.
--
-- Patch sets mais recentes nas páginas de download em 04/11/2026:
--   24.1.23 · 24.2.22 · 26.1.6 · 26.2.1 — todos fora das faixas acima.
--   Ação recomendada: aplicar o Patch Set Bundle mais recente da sua versão.
--==============================================================================

WITH versao AS (
  SELECT version_no,
         TO_NUMBER(REGEXP_SUBSTR(version_no, '[0-9]+', 1, 1))         AS maior,
         TO_NUMBER(REGEXP_SUBSTR(version_no, '[0-9]+', 1, 2))         AS menor,
         NVL(TO_NUMBER(REGEXP_SUBSTR(version_no, '[0-9]+', 1, 3)), 0) AS patch
    FROM apex_release
)
SELECT version_no,
       CASE
         WHEN (maior = 24 AND menor = 1 AND patch <= 21)
           OR (maior = 24 AND menor = 2 AND patch <= 20)
           OR (maior = 26 AND menor = 1 AND patch <= 4)
           THEN 'VULNERÁVEL — CVE-2026-101521 (CVSS 9.8): aplique o Patch Set Bundle mais recente'
         WHEN maior < 24
           THEN 'NÃO AVALIADA — versão fora das faixas do CPU out/2026; verificar suporte e patches'
         ELSE 'Fora das faixas afetadas da CVE-2026-101521 no CPU out/2026'
       END AS cve_2026_101521,
       CASE
         WHEN (maior = 24 AND menor = 1 AND patch <= 19)
           OR (maior = 24 AND menor = 2 AND patch <= 18)
           OR (maior = 26 AND menor = 1 AND patch <= 2)
           THEN 'VULNERÁVEL — CVE-2026-66010 (CVSS 6.1)'
         WHEN maior < 24
           THEN 'NÃO AVALIADA'
         ELSE 'Fora das faixas afetadas da CVE-2026-66010'
       END AS cve_2026_66010
  FROM versao;
