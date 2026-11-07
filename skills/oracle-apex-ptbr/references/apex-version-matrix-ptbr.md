# Matriz de Versões Oracle APEX — 24.1, 24.2, 26.1 e 26.2

Referência para distinguir o que é exclusivo de cada release e decidir o que é
seguro usar conforme a versão-alvo do ambiente. **A versão padrão da suíte é o
APEX 26.2:** sem versão declarada, o código sai para 26.2 (banco 19c, na
dúvida) e a resposta diz isso em uma linha, com a alternativa para 24.2/26.1
quando o recurso for 26.x. Ver [Versão padrão e quando perguntar](#versão-padrão-e-quando-perguntar).

Todas as informações abaixo foram verificadas nas release notes oficiais da
Oracle (docs.oracle.com / apex.oracle.com). Revisão de **06/11/2026**, completada em **07/11/2026** (mudanças de comportamento,
deprecated e desupported do 26.2): 26.2, requisitos e segurança conferidos nas fontes citadas em cada seção; o que não
foi confirmado está marcado como **a verificar**.

## Índice

- [Linha do tempo e suporte](#linha-do-tempo-e-suporte)
- [Requisitos por versão](#requisitos-por-versão)
- [Exclusivo do APEX 26.2](#exclusivo-do-apex-262)
- [Mudanças de comportamento, deprecated e desupported no 26.2](#mudanças-de-comportamento-deprecated-e-desupported-no-262)
- [Exclusivo do APEX 26.1](#exclusivo-do-apex-261)
- [Exclusivo do APEX 24.2](#exclusivo-do-apex-242)
- [Exclusivo do APEX 24.1](#exclusivo-do-apex-241)
- [Base comum (24.1+)](#base-comum-241)
- [Dependências de versão de BANCO](#dependências-de-versão-de-banco)
- [Versão padrão e quando perguntar](#versão-padrão-e-quando-perguntar)
- [Segurança — CPU de outubro/2026](#segurança--cpu-de-outubro2026-consultado-em-06112026)

## Linha do tempo e suporte

| Release | Lançamento | Patch set mais recente (04/11/2026) | Suporte | Observação |
|---|---|---|---|---|
| 23.2 | nov/2023 | — | a verificar | Introduziu Workflow nativo e Working Copy |
| 24.1 | jun/2024 | 24.1.23 | a verificar | Primeiro release com IA generativa (APEX Assistant, APEX_AI) |
| 24.2 | 15/01/2025 | **24.2.22** | **versão mínima coberta pela suíte** ("fully supported" na página de download; data de fim **a verificar**) | RAG declarativo, JSON Sources Shared Component |
| 26.1 | 14/05/2026 (re-release 25/05) | 26.1.6 | suportada | APEXlang, AI Interactive Reports, AI Agents |
| **26.2** | **06/10/2026** (re-release 09/10) | 26.2.1 | **atual — padrão da suíte** | APEXlang por arquivo, IA com reasoning effort, Deep Data Security; REST Workshop removido |

Fontes: páginas de download do APEX ([24.2](https://www.oracle.com/tools/downloads/apex-242-downloads), [26.1](https://www.oracle.com/tools/downloads/apex-261-downloads), [atual](https://www.oracle.com/tools/downloads/apex-downloads)).

> **26.2 padrão, 24.2 mínimo:** o código sai para 26.2; os padrões base valem de 24.2 em diante. Quem está na 24.2 deve estar no **patch set mais recente** — ver [Segurança](#segurança--cpu-de-outubro2026-consultado-em-06112026): a 24.2.0–24.2.20 está na faixa da CVE-2026-101521 (CVSS 9.8).

Não houve release "25.x" — a Oracle pulou de 24.2 direto para 26.1, alinhando a
numeração ao Oracle AI Database 26ai. Upgrade direto só é suportado a partir do
**APEX 18.1**; instalações anteriores devem ir antes a uma versão intermediária
(as notas da 26.2 dizem 24.1; as da 26.1 diziam 24.2).

## Requisitos por versão

| Item | 24.1 / 24.2 | 26.1 | 26.2 |
|---|---|---|---|
| Banco mínimo | 19c (19.3+) ou 23ai | 19c com **RU 19.18** (jan/2023)+; em 26ai, ao menos **23.26.0** (out/2025) | igual à 26.1 |
| ORDS | compatível com versões correntes | **26.1.1+** | **26.3.0+** (Quick SQL: 25.2+) |
| SQLcl | — | — | **26.3.0+** |
| Schema | `APEX_240100` / `APEX_240200` | `APEX_260100` (pelo padrão; a verificar) | **`APEX_260200`** |
| Ordem de instalação nova | — | ORDS antes do APEX | ORDS antes do APEX |
| Edições | EE, SE2, Free | EE, SE2, 26ai Free | EE, SE2 (19c e 26ai) |
| Memória na instalação | — | SGA ≥ 1200 MB, PGA ≥ 300 MB | a verificar (guia de instalação 26.2 não lido) |

Fonte 26.2: [release notes 26.2](https://docs.oracle.com/en/database/oracle/apex/26.2/htmrn/about-release-notes.html) e [changed behavior](https://docs.oracle.com/en/database/oracle/apex/26.2/htmrn/changed-behavior.html).

**APEX 26.x roda em 19c e em 26ai.** O RU mínimo do 19c é **19.18** (26.1 e 26.2).
Para *recursos* que dependem do banco (session state BOOLEAN, Deep Data
Security), veja [Dependências de versão de BANCO](#dependências-de-versão-de-banco).

## Exclusivo do APEX 26.2

Fonte: [New Features 26.2](https://docs.oracle.com/en/database/oracle/apex/26.2/htmrn/new-features.html) e [Desupported Features 26.2](https://docs.oracle.com/en/database/oracle/apex/26.2/htmrn/desupported-features.html).

- **APEXlang — import por arquivo:** importa um ou mais `.apx` sem importar a
  aplicação inteira, **só pelo SQLcl e pela extensão SQL Developer do VS Code**
  (não pelo App Builder) e **só para desenvolvimento**:
  `apex import -files pages/p00045-dashboard.apx shared-components/lovs/depts.apx`.
- **APEXlang — traduções:** apps com tradução *Application-Based* passam a
  exportar em APEXlang (`translations.sql` em `generated-artifacts`), e o import
  reinstala o repositório de traduções. Na 26.1 isso não era possível.
- **APEXlang — subscription mapping** no import pelo App Builder (mover apps
  entre workspaces com IDs de aplicação-mãe diferentes) e **arquivo de
  deployment JSON** (valores de aplicação, workspace, subscription e tema).
- **APIs PL/SQL de lock e Working Copy** em `APEX_APPLICATION_ADMIN`:
  `LOCK_APPLICATION`, `UNLOCK_APPLICATION` (`p_unlock_as_user`) e
  `CREATE_WORKING_COPY` (retorna o novo app id; não copia supporting objects).
  Fluxo documentado: exportar a working copy para APEXlang, editar fora e
  importar de volta.
- **REST Workshop removido:** o *RESTful Services* do SQL Workshop (deprecated
  na 26.1) está **desupported**; a definição declarativa de APIs REST segue
  pelo **SQL Developer Web**. Módulos e metadados ORDS existentes **continuam
  disponíveis**; saem o import/export legado do REST Workshop e os fluxos de
  serviço de exemplo. As views `APEX_REST_RESOURCE_*` ficam por compatibilidade,
  sem dados do REST Workshop; instalação nova não cria `APEX_LISTENER`; a
  configuração *Swagger UI URL* foi removida. Detalhe em `oracle-ords-ptbr`.
- **IA:**
  - *Reasoning Effort* em AI Agents (Default, None, Minimal, Low, Medium, High,
    Extra High, Maximum), também via `p_reasoning_effort` em
    `APEX_AI.CHAT` / `APEX_AI.GENERATE`;
  - provedores de Generative AI Service: OpenAI, Cohere, OCI Generative AI,
    Google Gemini, Anthropic Claude, Mistral AI, Ollama e Generic (compatível
    com a API da OpenAI); configuração *Provider API* (Responses como padrão;
    Chat Completions e Generate Text deprecated);
  - **colunas calculadas por linguagem natural** no Interactive Report
    ("Profit equals Revenue minus Cost" vira computed column);
  - **navigation targets** definidos no AI Request Handler da aplicação
    (`apex_ai.t_navigation_targets`) para AI Agents do *Show AI Assistant*;
  - busca no IR por frases-chave sem LLM.
- **Deep Data Security:** framework de autorização aplicado pelo banco (Data
  Roles e Data Grants) com a identidade do usuário final repassada ao banco.
  Exige **Oracle AI Database 23.26.3+** e Social Sign-In com **OCI IAM ou
  Microsoft Entra**. APIs: `APEX_APPLICATION_ADMIN.SET_DEEP_SEC` e correlatas,
  `APEX_SESSION.ENABLE_DEEP_SEC_DATA_ROLES`. Fonte: [Configuring Deep Data
  Security with APEX](https://docs.oracle.com/en/database/oracle/apex/26.2/htmdb/configuring-deep-data-security-with-apex.html).
  Recursos do banco 26ai em si: `oracle-26ai-helper-ptbr`.
- **Workflow:** *custom outcomes* em Action Tasks (`APEX_HUMAN_TASK.SET_TASK_OUTCOME`),
  evento **Fail** quando a task vai para *Errored*, atividades de rascunho
  (Draft Generic/Switch/Wait), export do diagrama em PNG/SVG e
  `APEX_WORKFLOW.MIGRATE_INSTANCE` (migra instâncias em andamento para a nova
  versão do workflow).
- **Interactive Grid:** `apex.region.multipleRefresh` aceita `interactiveGrid`
  (várias regiões numa requisição AJAX).
- **Universal Theme 26.2:** estilos Dark, Light, Pillar Dark e Pillar Light para
  cabeçalho e navegação no Theme Roller do Iris; "Redwood Light" renomeado para
  "Redwood Light [Legacy]"; novo *Utility CSS Framework* (ex.: `u-flex`,
  `u-padding-4`) e classe `u-color-subtle`. Referência viva: app *Universal
  Theme Reference* (oracleapex.com/ut).
- **IA — configurações OCI** (Model, Compartment ID, Serving Mode, Endpoint ID,
  Project ID) saem do JSON de Additional Attributes; consulta em
  `APEX_WORKSPACE_AI_SERVICES`.

## Mudanças de comportamento, deprecated e desupported no 26.2

Fontes (consultadas em 07/11/2026): [Changed Behavior](https://docs.oracle.com/en/database/oracle/apex/26.2/htmrn/changed-behavior.html), [Deprecated Features](https://docs.oracle.com/en/database/oracle/apex/26.2/htmrn/deprecated-features.html), [Desupported Features](https://docs.oracle.com/en/database/oracle/apex/26.2/htmrn/desupported-features.html).

**Mudanças que afetam código e deploy:**

| Mudança | Impacto |
|---|---|
| **OAuth:** tokens reutilizados e regra de scope respeitada | Código que define token na mão (`APEX_WEB_SERVICE.SET_OAUTH_TOKEN`) com scope diferente do da requisição pode falhar → prefira a autenticação OAuth declarativa (Web Credential) |
| **Network ACL** para e-mail, REST, LDAP e impressão | O DBA concede `connect` ao schema **`APEX_260200`** com `DBMS_NETWORK_ACL_ADMIN` (o upgrade replica a configuração da versão anterior; não se aplica ao Autonomous) — ver `oracle-ords-ptbr` |
| **Export Wizard:** sai a opção *Supporting Objects* | Os supporting objects passam a ir sempre no export pelo App Builder; para exportar sem eles use `APEX_EXPORT.GET_APPLICATION` ou `apex export` do SQLcl |
| **Static ID** não aceita caractere Tab | Valores antigos não mudam sozinhos, mas são validados ao editar o componente |
| **Barra de pesquisa do IR** redesenhada | Botão automático *Interactive Report Reset*: **Yes** em apps novas, **No** nas existentes; o upgrade desliga alguns botões de reset criados pelo desenvolvedor; atalhos de teclado mudaram |
| **Faceted Search / Smart Filters:** *Allow to Exclude* ligado por padrão | Revise facets que não devem permitir exclusão |
| **Substituições** em mais Report Settings (nome, filtro, highlight, rótulos de gráfico) | — |
| **Report Queries** passam JSON bruto (inclusive hierárquico) ao Document Generator | — |
| Instance setting **Enable RESTful Services** | Passa a controlar também o REST do schema gerenciado pelo APEX e os aliases para o SQL Developer Web |

**Deprecated no 26.2** (continuam funcionando; remoção prevista):
- **APEX Advisor** → use o **CodeScan do SQLcl 26.3.0+**, que tem regras para APEXlang (`oracle-devops-ptbr`, `codescan_gate.py`);
- autenticação **Oracle Application Server Single Sign-On** → Social Sign-In ou SAML;
- **Data Generator** do SQL Workshop e o wizard *Create Shared Component* do Page Designer;
- `APEX_AI`: membro `tool_calls` de `t_chat_message` (use entradas com `CHAT_ROLE = C_ROLE_TOOL_CALL` e `TOOL_CALL`) e membro `message` de `t_chat_response` (use `MESSAGES`);
- *Provider API* Chat Completions (OpenAI, Ollama, Generic) e Generate Text (Gemini).

**Desupported no 26.2:**
- REST Workshop do SQL Workshop (ver [Exclusivo do APEX 26.2](#exclusivo-do-apex-262));
- **Query Builder** do SQL Workshop (queries salvas viram *SQL Commands saved queries*, sem o layout);
- **Export Repository**;
- modelos OCI Generative AI `cohere.command-r-08-2024`, `cohere.command-r-plus-08-2024`, `cohere.command-latest` e `cohere.command-plus-latest` (migrados para `cohere.command-a-03-2025` no upgrade/import);
- `APEX_LISTENER` em instalação nova e a configuração *Swagger UI URL*.

**Import de apps de 24.2/26.1 no 26.2:** as notas consultadas não documentam
restrição geral; trazem as migrações automáticas acima (modelos Cohere,
serviços OpenAI/Gemini, Query Builder). O guia de instalação/upgrade da 26.2
não foi lido — requisitos de memória da instalação 26.2: **a verificar**.

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
- **Deep Data Security (APEX 26.2)** — exige **Oracle AI Database 23.26.3+** e
  Social Sign-In com OCI IAM ou Microsoft Entra. Não existe em 19c.

## Versão padrão e quando perguntar

**Padrão: APEX 26.2.** Sem versão declarada, gere para 26.2 e avise em uma
linha ("Considerei APEX 26.2"). Quando o recurso não existe em 24.2/26.1, diga
a alternativa na mesma resposta. Exemplos:

| Recurso 26.x usado no padrão | Alternativa em versão anterior |
|---|---|
| Import por arquivo (`apex import -files`), 26.2 | 26.1: importar a aplicação inteira em APEXlang; 24.2: export/import SQL (`apex export -split`) |
| `APEX_APPLICATION_ADMIN.LOCK_APPLICATION` / `CREATE_WORKING_COPY`, 26.2 | Working Copy e lock de página pelo App Builder (23.2+) |
| `p_reasoning_effort` em `APEX_AI`, 26.2 | Omitir o parâmetro (24.1+) |
| APIs REST pelo SQL Developer Web (REST Workshop removido na 26.2) | Em 24.2/26.1 o REST Workshop ainda existe, mas o caminho recomendado já é o mesmo |
| APEXlang (`.apx`), 26.1+ | 24.2: export SQL com `-split` |
| AI Interactive Reports / AI Agents, 26.1+ | 24.2: `APEX_AI.CHAT`/`GENERATE` e DA "gerar texto" |

**Pergunte (uma vez, antes de gerar) só quando:**
- houver uma **instância existente** (app de cliente, upgrade, incidente):
  versão completa com patch set — ver [Segurança](#segurança--cpu-de-outubro2026-consultado-em-06112026);
- o recurso depender do **banco 26ai** — session state BOOLEAN, Deep Data
  Security (23.26.3+), vector search — e o banco não tiver sido informado (o
  padrão é 19c, que não tem esses recursos).

Se a versão já estiver clara na conversa (ex.: "estou no 24.2"), **não
pergunte de novo** — use a versão informada e só sinalize a dependência quando
relevante.

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

