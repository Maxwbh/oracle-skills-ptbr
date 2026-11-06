# Matriz de Versões Oracle APEX — 24.1, 24.2 e 26.1

Referência para distinguir o que é exclusivo de cada release e decidir o que é
seguro usar conforme a versão-alvo do ambiente. **Sempre que uma feature
depender de versão e a versão-alvo não estiver clara na conversa, PERGUNTE ao
usuário para qual versão do APEX (e, quando relevante, qual versão de banco) o
código se destina antes de gerar algo que dependa de versão.**

Todas as informações abaixo foram verificadas nas release notes oficiais da
Oracle (docs.oracle.com / apex.oracle.com).

## Índice

- [Linha do tempo e suporte](#linha-do-tempo-e-suporte)
- [Requisitos por versão](#requisitos-por-versão)
- [Exclusivo do APEX 26.1](#exclusivo-do-apex-261)
- [Exclusivo do APEX 24.2](#exclusivo-do-apex-242)
- [Exclusivo do APEX 24.1](#exclusivo-do-apex-241)
- [Base comum (24.1+)](#base-comum-241)
- [Dependências de versão de BANCO](#dependências-de-versão-de-banco)
- [Quando perguntar a versão](#quando-perguntar-a-versão)

## Linha do tempo e suporte

| Release | Lançamento | Suporte até | Observação |
|---|---|---|---|
| 23.2 | nov/2023 | mai/2026 | Introduziu Workflow nativo e Working Copy |
| 24.1 | jun/2024 | dez/2026 | Primeiro release com IA generativa (APEX Assistant, APEX_AI) |
| 24.2 | jan/2025 | jul/2027 | RAG declarativo, JSON Sources Shared Component |
| 26.1 | mai/2026 (re-release 25/mai) | atual | Salto de IA: APEXlang, AI Interactive Reports, AI Agents |

Não houve release "25.x" — a Oracle pulou de 24.2 direto para 26.1, alinhando a
numeração ao Oracle AI Database 26ai. Upgrade direto só é suportado a partir do
APEX 18.1; instalações anteriores devem ir a 24.2 e então a 26.1.

## Requisitos por versão

| Item | 24.1 / 24.2 | 26.1 |
|---|---|---|
| Banco mínimo | 19c (19.x) ou 23ai | 19c com RU 19.18 (jan/2023)+; em 26ai, ao menos 23.26.0 (out/2025) |
| ORDS | compatível com versões correntes | **26.1.1+ obrigatório** (recomenda-se instalar ORDS antes do APEX) |
| Edições | EE, SE2, Free | EE, SE2, 26ai Free |

## Exclusivo do APEX 26.1

Recursos presentes no 26.1 e ausentes no 24.2 e anteriores:

- **APEXlang** — linguagem de especificação aberta e legível (`.apx`) para apps
  APEX. Substitui o export SQL cheio de IDs internos por arquivos estruturados
  versionáveis, diffáveis e revisáveis em Git, geráveis/editáveis por agentes de
  IA. Tem View no Page Designer, validação via SQLcl e suporte no Oracle SQL
  Developer for VS Code. Exige ORDS 26.1.1+.
- **AI Interactive Reports (NL2IR)** — o usuário descreve em linguagem natural
  ("clientes europeus agrupados por indústria") e o APEX traduz para
  configurações nativas do IR (filtros, highlights, sort, control break,
  group by, agregações, pivôs, charts). **Não executa SQL gerado por IA** — só
  aplica settings declarativos do IR, preservando regras de acesso a dados.
- **AI Agents (com Tools)** — agentes que chamam ferramentas "On Demand"
  definidas na app; o APEX executa as tools e devolve resultados ao serviço de
  IA num loop até a resposta final. Torna apps APEX agênticas, não só "com chat".
- **Data Reporter** — nova experiência de relatório para usuários de negócio
  criarem/gerenciarem relatórios sobre datasets aprovados por administradores,
  sem usar o App Builder/Page Designer.
- **Criar páginas por linguagem natural** — descrever a tabela/dados em
  linguagem natural e a IA sugere nome, tipo de página e fonte no wizard.
- **Universal Theme 26.1 "Iris"** — novo estilo padrão, com hierarquia
  tipográfica mais nítida e acessibilidade aprimorada; **Font APEX 2.5** (mais
  ícones: utilidades, construção, infraestrutura).
- **Template Components — client-side partials, template directives e
  autocomplete**; Template Directives estendidos para item, region, list e page
  templates.
- **Workflow — Parallel Flow** (execução de atividades em duas ou mais branches
  em paralelo), novas APIs de extensibilidade e consciência de multi-tenancy.
- **Segurança REST Data Sources** — Dynamic OAuth scopes, signed assertions,
  password flows; melhorias de Content Security Policy e segurança de Fusion
  Extensions.
- **Maps** — suporte a vector tile layers e maior controle via JavaScript.
- **Tipos de aplicação** — apps existentes passam a ter tipo "Standard"; há
  boilerplate/library/theme applications como base.
- **Document Generator** — suporte a PDFs protegidos por senha.
- **Infinite scroll** para Select One, Select Many, Combobox e Autocomplete
  (deixa de cortar no "Maximum Values in List").
- **Quick Picks dinâmicos** via SQL.
- **(somente em banco 26ai)** Session state **BOOLEAN** nativo para Checkbox,
  Switch e Hidden — ver seção de dependências de banco.

## Exclusivo do APEX 24.2

Recursos introduzidos no 24.2 (presentes também no 26.1, ausentes no 24.1 e
anteriores):

- **JSON Sources Shared Component** — novo componente compartilhado para fontes
  de dados JSON.
- **RAG declarativo para IA** — configurar retrieval-augmented generation para
  chamadas de IA de forma declarativa.
- **Criar modelos de dados por linguagem natural** e nova **Dynamic Action para
  gerar texto**; **vector search support**; melhorias na configuração do
  APEX AI Assistant/Builder AI.
- **Grouping em Template Components**.
- **Visual object dependency reporting** — relatório visual de dependências
  entre objetos.
- **Melhorias em Workflows e REST Data Sources**.
- **Integração aprimorada com Oracle Fusion Cloud Applications**.
- **Text Message substitution** com melhor suporte e acesso no Page Designer.
- **Font APEX 2.4** e updates do Universal Theme.

## Exclusivo do APEX 24.1

Recursos introduzidos no 24.1 (presentes em 24.2 e 26.1):

- **IA generativa — primeira leva:** APEX Assistant; configuração declarativa
  de serviços de IA; **API `APEX_AI`** com métodos `chat()` e `generate()`;
  diálogos de IA conversacional no app; escolha do LLM.
- **Select One e Select Many** — novos page items (seleção única/múltipla com
  filtro/search, estilização via Template Directives, ícones e grupos).
- **Template Components — Slots** (antes "Display Points"/"Positions"); permite
  aninhar regions/items/buttons em Page/Region/Template Component Slots.
- **REST Data Source Profiles hierárquicos** + colunas do tipo array (modelar
  toda a hierarquia JSON); `APEX_EXEC` estendido para JSON hierárquico.
- **Component Groups**.
- **Working Copies aprimoradas** (recurso nasceu no 23.2): indicador visual no
  Page Designer de página alterada/bloqueada em outra working copy; opção
  "Compare Current Page with Main".
- **Workflow** (engine nativo nasceu no 23.2): workflow dashboard, workflow
  diagram region, vacation rules, iniciador pode aprovar/rejeitar/completar a
  task, função de terminação para activity plugins assíncronos.
- **Document Generator** (integração).
- **Read-only items acessíveis** — `APEX_PLUGIN_UTIL.PRINT_READ_ONLY` para
  rendering acessível; Font APEX 2.3.

## Base comum (24.1+)

Recursos anteriores ao 24.1 que valem em todas as versões cobertas por esta
skill e podem ser usados sem ressalva de versão (origem entre parênteses):

- Interactive Report, Interactive Grid, Classic Report, Faceted Search.
- Dynamic Actions, Page Process, AJAX Callback (`apex.server.process`),
  Validations, Authorization/Authentication Schemes.
- `APEX_ERROR`, `APEX_JSON`, `APEX_DEBUG`, `APEX_COLLECTION`,
  `APEX_APPLICATION_TEMP_FILES`, `APEX_DATA_EXPORT`/`APEX_REGION.EXPORT_DATA`.
- Native Map Region (21.1+), Automations (`APEX_AUTOMATION`, 20.2+).
- Background Page Processing — Execution Chain "Run in Background" +
  `APEX_BACKGROUND_PROCESS` (set_progress/set_status/get_execution/terminate) e
  view `APEX_APPL_PAGE_BG_PROC_STATUS` (**23.1+**).
- Workflow engine + Working Copy (**23.2+**).

## Dependências de versão de BANCO

Algumas features dependem da versão do **banco**, não só do APEX:

- **Session state BOOLEAN nativo** (Checkbox/Switch/Hidden ligando-se a
  `BOOLEAN` PL/SQL/JS) — **APEX 26.1 + Oracle AI Database 26ai**. Em 19c o item
  continua mapeando string ('Y'/'N'). Não gere código que dependa de bind
  BOOLEAN sem confirmar banco 26ai.
- **AI Vector Search / RAG** — depende de capacidades de vetor do banco (23ai+
  / 26ai). Em 19c, recursos de vetor não estão disponíveis.
- **Validação de saída de IA em background** — disponível a partir de
  Oracle Database 26ai.

## Quando perguntar a versão

Faça **uma** pergunta curta de versão-alvo (APEX e, se aplicável, banco) **antes
de gerar código** quando o pedido envolver:

- IA no app: APEX Assistant, `APEX_AI`, AI Interactive Reports, AI Agents,
  geração por linguagem natural, RAG, vector search (24.1 / 24.2 / 26.1
  divergem bastante).
- APEXlang / export para source control em `.apx` (somente 26.1 + ORDS 26.1.1).
- Page items Select One/Select Many, Slots, Template Components com partials
  (24.1 introduziu; partials client-side só no 26.1).
- Background jobs/Execution Chain (23.1+) e Workflow/Working Copy (23.2+/24.1).
- Session state BOOLEAN, ou qualquer item que dependa de banco 26ai.
- Universal Theme/estilo (Iris é padrão só no 26.1).

Se a versão-alvo já estiver clara na conversa (ex.: o usuário disse "estou no
26.1" ou a app do cliente já foi descrita como 26.1), **não pergunte de novo** — use o que já foi
informado e apenas sinalize a dependência de versão quando relevante.

---

## Segurança — CPU de outubro/2026 (consultado em 06/11/2026)

Fontes: [Oracle CPU out/2026](https://www.oracle.com/security-alerts/cpuoct2026.html) (Rev 1 em 20/10/2026; [Text Form](https://www.oracle.com/security-alerts/cpuoct2026verbose.html#APEX)) e [CVE List — CVE-2026-101521](https://github.com/CVEProject/cvelistV5).

| CVE | CVSS 3.1 | Ataque | Versões afetadas (texto do advisory) |
|---|---|---|---|
| **CVE-2026-101521** | **9.8** (CRITICAL) — `AV:N/AC:L/PR:N/UI:N` | sem autenticação, via HTTPS; "can result in takeover of Oracle APEX" | 24.1.0–24.1.21, 24.2.0–24.2.20, 26.1.0–26.1.4 |
| CVE-2026-66010 | 6.1 — exige interação do usuário | componente General (DOMPurify), via HTTP | 24.1.0–24.1.19, 24.2.0–24.2.18, 26.1.0–26.1.2 |

**O que fazer:** aplicar o **Patch Set Bundle mais recente** da versão em uso. Nas páginas de download, em 04/11/2026, eram: **24.1.23**, **24.2.22**, **26.1.6** e **26.2.1** — todos fora das faixas afetadas acima. Verificar a instância com `assets/apex_verificar_patch_seguranca.sql`.

**A verificar (não está no advisory):**
- qual é a **primeira versão corrigida** de cada linha (24.1.22? 24.2.21? 26.1.5?) — o CPU lista só as faixas afetadas e remete ao documento CPU359 da Oracle Support;
- se a **26.2** é afetada — ela não aparece na lista de afetadas, mas não há frase explícita;
- se `APEX_RELEASE.VERSION_NO` reflete o patch set aplicado — a view não é descrita na documentação consultada; confirme também em *Help > About* do App Builder.

O mesmo CPU traz **35 CVEs do ORDS** (faixa geral 24.2.0–26.2.2) — ver `oracle-ords-ptbr`.

