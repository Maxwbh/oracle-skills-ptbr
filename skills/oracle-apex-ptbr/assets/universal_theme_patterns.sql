--==============================================================================
-- APEX Universal Theme — classes utilitárias e CSS custom escopado
--
-- Universal Theme é o tema oficial APEX desde 5.0, baseado em CSS modular com
-- classes utilitárias prefixadas `t-` (template) e `u-` (utility). Conhecer
-- as classes evita criar CSS custom que duplica o que já existe e quebra com
-- upgrade do tema.
--
-- Em 24.2: Font APEX 2.4, Theme Roller para customização visual sem código,
-- support a CSS-only Light/Dark mode.
--==============================================================================

--==============================================================================
-- 1. Anatomia de classes do Universal Theme
--==============================================================================

/*
PREFIXOS PRINCIPAIS:

  t-*       Template — define componentes estruturais
            Ex: t-Card, t-Button, t-Region, t-Form, t-Badge

  u-*       Utility — classes atômicas para ajustes pontuais
            Ex: u-color-1, u-bg-color-2, u-mtL (margin-top large), u-pos-center

  a-*       Animation
            Ex: a-Animation--fadeIn

  icon-*    Font APEX icons
            Ex: icon-check, icon-warning, icon-edit, icon-trash

  fa-*      Font Awesome (incluído via tema)

  is-*      State modifiers (combinam com componentes)
            Ex: is-active, is-collapsed, is-disabled, is-required

  has-*     Possession modifiers
            Ex: has-error, has-warning, has-children
*/

--==============================================================================
-- 2. Componentes mais usados (referência)
--==============================================================================

/*
BUTTON
  <button class="t-Button t-Button--primary">Salvar</button>
  <button class="t-Button t-Button--danger t-Button--small">Excluir</button>
  Variantes: --primary, --hot, --warning, --danger, --success, --noUI, --link
  Tamanhos:  --small, --large
  Modifiers: t-Button--icon (com ícone), t-Button--iconOnly (só ícone)

BADGE
  <span class="t-Badge">Total</span>
  <span class="t-Badge t-Badge--accent1">12</span>
  Variantes: --accent1..--accent16 (cores diferentes)

CARD
  <div class="t-Card">
    <div class="t-Card-wrap">
      <div class="t-Card-icon">...</div>
      <div class="t-Card-titleWrap">
        <h3 class="t-Card-title">Título</h3>
        <h4 class="t-Card-subtitle">Subtítulo</h4>
      </div>
      <div class="t-Card-body">Conteúdo</div>
    </div>
  </div>

ALERT / NOTIFICATION
  <div class="t-Alert t-Alert--success">
    <div class="t-Alert-wrap">
      <div class="t-Alert-icon"><span class="icon-check"></span></div>
      <div class="t-Alert-content">
        <div class="t-Alert-title">Sucesso</div>
        <div class="t-Alert-body">Fatura salva.</div>
      </div>
    </div>
  </div>
  Variantes: --success, --warning, --danger, --info

ICON
  <span class="t-Icon icon-check"></span>
  <span class="t-Icon icon-warning u-color-warning"></span>
*/

--==============================================================================
-- 3. Utility classes (espaçamento, layout, cor)
--==============================================================================

/*
ESPAÇAMENTO  (margin / padding em "size tokens")
  u-m{T|B|L|R}{None|S|M|L}
    T=Top, B=Bottom, L=Left, R=Right
    None=0, S=small, M=medium, L=large
  Exemplos:
    u-mtL    margin-top: large
    u-mbS    margin-bottom: small
    u-pL     padding-left: medium (sem letra de tamanho = medium)
    u-ml     margin-left

COR DE TEXTO / FUNDO
  u-color-1 .. u-color-16     cor de texto (paleta theme)
  u-bg-color-1 .. u-bg-color-16  fundo
  u-color-success / warning / danger / info  ações
  u-bg-color-success / etc

DISPLAY / POSITION
  u-visibility-hidden
  u-display-none
  u-pos-center, u-pos-left, u-pos-right
  u-textCenter, u-textLeft, u-textRight
  u-noBorder
  u-flex, u-flexBasis-...

WIDTH (em grid)
  col col-1 .. col-12   (sistema de 12 colunas dentro de t-Form)
*/

--==============================================================================
-- 4. CSS custom escopado por página (pattern)
--==============================================================================

-- Local: Page Designer → Page → CSS → "Inline" section
-- Problema: CSS inline da página VAZA para outras páginas se classe colide
-- com nome usado em outro lugar.
-- Solução: escopar por seletor que use o ID da página/region.

-- Page 49, region "FATURAS_REGION":
/*
[id="report_FATURAS_REGION"] .t-Report-cell {
  font-variant-numeric: tabular-nums;
}

[id="report_FATURAS_REGION"] .t-Report-cell.coluna-valor {
  text-align: right;
  font-weight: 600;
}

[id="report_FATURAS_REGION"] tr.is-overdue {
  background: var(--ut-palette-danger, #fbe9e7);  /* token do theme + fallback */
}
*/

-- ALTERNATIVA: criar classe custom própria e aplicar via "HTML Class"
-- attribute do region/item. Evita ID-based selector (que muda se alguém
-- renomeia a region).

--==============================================================================
-- 5. Theme Roller — customização visual sem CSS
--==============================================================================

/*
Theme Roller (App Builder → Theme Roller) permite alterar variáveis CSS do
Universal Theme sem escrever CSS. Salva como Style.

Variáveis-chave (CSS custom properties do UT 24.x/26.x — prefixo --ut-*):
  --ut-palette-primary, --ut-palette-primary-contrast
  --ut-palette-success / -warning / -danger / -info
  --ut-body-text-color, --ut-body-bg-color
  --ut-component-border-radius
  Os nomes variam por versão — inspecione :root no DevTools para a lista real.

USO EM CSS CUSTOM:
  .minha-classe {
    color: var(--ut-palette-primary);
    background: var(--ut-palette-primary-shade);
  }

CRIAR UM STYLE NOVO:
  Theme Roller → Save As → "Minha Empresa Style"
  Workspace > Application Properties > User Interface > Theme Style: Minha Empresa

VANTAGEM: dark mode / light mode trocam só de Style, sem mudar CSS de páginas.
*/

--==============================================================================
-- 6. Dark mode (24.2 polishing)
--==============================================================================

/*
Universal Theme tem suporte nativo a Light/Dark Mode. Configuração:
  - Application Properties > User Interface > Theme Style: Vita-Dark / Vita
  - OU: Color Scheme Auto (segue preferência do SO via prefers-color-scheme)

EM CSS CUSTOM:
  /* Funciona em ambos os modos automaticamente: use os tokens --ut-* */
  .meu-card {
    background: var(--ut-body-bg-color);
    color: var(--ut-body-text-color);
  }

  /* Regra específica por preferência do SO (sempre válida): */
  @media (prefers-color-scheme: dark) {
    .meu-card { box-shadow: 0 0 10px rgba(255,255,255,0.1); }
  }

MARCAÇÃO NO DOM:
  O UT marca o modo ativo com classe/atributo no html/body — o NOME EXATO varia
  entre versões. Inspecione no DevTools com o Theme Style dark ativo e escreva
  o seletor conforme a sua versão (não assuma um seletor de memória).

DETECTAR EM JS:
  const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  // Para o modo do APEX (não do SO), leia a classe/atributo identificado acima.
*/

--==============================================================================
-- 7. Padrões úteis
--==============================================================================

/*
PADRÃO A: Botão de ação com ícone e estado
  <button class="t-Button t-Button--hot t-Button--icon"
          data-action="salvar"
          onclick="salvar()">
    <span class="t-Icon icon-save t-Button-icon"></span>
    <span class="t-Button-label">Salvar</span>
  </button>

  // Mostrar loading durante operação:
  apex.actions.disable('salvar');  // se usa Actions framework
  // OU manualmente:
  button.classList.add('is-disabled');
  button.querySelector('.t-Button-label').textContent = 'Salvando...';

PADRÃO B: Cell colorida em report baseada em valor
  -- Query do report:
  SELECT id,
         valor,
         CASE WHEN valor < 0 THEN 'u-color-9'    -- vermelho
              WHEN valor > 10000 THEN 'u-color-7' -- amarelo destaque
              ELSE NULL
         END AS valor_class
    FROM faturas;

  -- HTML Expression da coluna VALOR:
  <span class="&VALOR_CLASS.">&VALOR.</span>

PADRÃO C: Badge dinâmico em coluna de status
  SELECT id,
         status,
         CASE status
           WHEN 'PAGO'      THEN 't-Badge t-Badge--success'
           WHEN 'PENDENTE'  THEN 't-Badge t-Badge--warning'
           WHEN 'CANCELADO' THEN 't-Badge t-Badge--danger'
         END AS badge_class
    FROM faturas;

  -- HTML Expression na coluna STATUS:
  <span class="&BADGE_CLASS.">&STATUS.</span>
*/

--==============================================================================
-- 8. Anti-patterns
--==============================================================================

/*
ANTI-PATTERN 1: CSS inline sem escopo
  /* Inline CSS da Page 49 */
  .t-Card { background: red; }     /* ❌ vaza para TODAS as páginas */

  → use:
  [id^="P49_"] .t-Card { background: red; }
  → ou classe própria:
  .meu-card-vermelho { background: red; }

ANTI-PATTERN 2: Sobrescrever variáveis do theme em CSS custom
  /* CSS inline */
  :root { --ut-palette-primary: red; }   /* ❌ quebra todo o app */

  → use Theme Roller para mudar cores

ANTI-PATTERN 3: Criar classe paralela ao que t-Button já faz
  /* CSS custom */
  .meu-botao { padding: 8px; border-radius: 4px; ... }   /* ❌ duplicação */

  → use t-Button + variants

ANTI-PATTERN 4: !important para vencer especificidade do theme
  .meu-elemento { color: red !important; }   /* ❌ guerra de !important */

  → aumente especificidade legítima (ID-based) ou use Theme Roller

ANTI-PATTERN 5: Ignorar dark mode
  /* Funciona em light, ilegível em dark */
  .meu-card { background: #fff; color: #000; }

  → use variáveis do theme:
  .meu-card { background: var(--ut-body-bg-color); color: var(--ut-body-text-color); }

ANTI-PATTERN 6: JS manipulando DOM com classes hardcoded
  // Frágil — se theme renomear .t-Button-label, quebra
  $('.t-Button-label').text('...');

  → use apex.actions ou data-* attributes próprios
*/
