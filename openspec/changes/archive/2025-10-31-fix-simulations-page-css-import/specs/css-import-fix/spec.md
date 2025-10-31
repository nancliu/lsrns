# Spec: CSS Import Fix for Simulations Page

**Capability ID**: css-import-fix
**Related Change**: fix-simulations-page-css-import
**Version**: 1.0

---

## ADDED Requirements

### Requirement: HTML pages MUST import CSS variables file first

All HTML pages in the control frontend MUST import `css/variables.css` as the first stylesheet, before any other CSS files that reference CSS custom properties.

**Priority**: P0
**Status**: New

#### Scenario: Simulations page imports CSS files in correct order

**Given**:
- The simulations page uses styles that reference CSS custom properties (e.g., `var(--color-primary)`)
- CSS custom properties are defined in `css/variables.css`
- Base layout styles are in `css/templates-base.css` and `css/templates-layout.css`

**When**:
- User opens `http://localhost:8000/control/simulations.html`

**Then**:
- The HTML `<head>` contains CSS imports in this exact order:
  ```html
  <link rel="stylesheet" href="css/variables.css">
  <link rel="stylesheet" href="css/templates-base.css">
  <link rel="stylesheet" href="css/templates-layout.css">
  <link rel="stylesheet" href="css/simulations.css">
  ```
- All CSS custom properties resolve correctly
- The page displays with full styling (colors, spacing, fonts)
- No console errors related to undefined CSS properties

---

#### Scenario: Page displays with correct visual styling

**Given**:
- CSS files are imported in correct order
- API server is running

**When**:
- User loads `http://localhost:8000/control/simulations.html`

**Then**:
- **Top bar** displays with:
  - Gradient background (`linear-gradient(135deg, #667eea 0%, #764ba2 100%)`)
  - White text
  - Proper padding and layout
- **Sidebar** displays with:
  - Dark background (`#2c3e50`)
  - White/light text for links
  - Hover effects on navigation items
  - Active state styling
- **Content area** displays with:
  - Light background (`#f5f7fa`)
  - Proper padding (30px)
  - Scrollable overflow
- **Buttons** display with:
  - Primary: Blue background (`#3498db`)
  - Secondary: Gray background (`#95a5a6`)
  - Proper padding, border-radius, hover effects
- **Config sections** display with:
  - White background
  - Box shadows
  - Proper spacing between sections
- **Form inputs** display with:
  - Borders (`#ddd`)
  - Proper padding and sizing
  - Correct font styles

---

### Requirement: CSS import order MUST follow dependency hierarchy

When a page uses modular CSS files, imports MUST follow the dependency hierarchy: variables → base → layout → page-specific.

**Priority**: P0
**Status**: New

#### Scenario: CSS files loaded in dependency order

**Given**:
- `variables.css` defines CSS custom properties
- `templates-base.css` uses variables for common styles (reset, buttons, badges)
- `templates-layout.css` uses variables for layout (top-bar, sidebar, containers)
- `simulations.css` uses variables and depends on base/layout classes

**When**:
- Browser loads `simulations.html`

**Then**:
- CSS files load in this order:
  1. `variables.css` (no dependencies)
  2. `templates-base.css` (depends on variables)
  3. `templates-layout.css` (depends on variables)
  4. `simulations.css` (depends on variables, base, layout)
- No FOUC (Flash of Unstyled Content)
- All styles apply correctly on first render

---

### Requirement: Missing CSS imports MUST cause visual verification to fail

Any HTML page missing required CSS imports MUST be detected through visual verification testing.

**Priority**: P1
**Status**: New

#### Scenario: Detect missing variables.css import

**Given**:
- An HTML page imports `simulations.css` but NOT `variables.css`
- `simulations.css` uses CSS custom properties like `var(--color-primary)`

**When**:
- Developer opens the page in browser
- Developer inspects computed styles

**Then**:
- CSS custom properties are undefined (fallback to initial values)
- Elements appear unstyled:
  - Buttons have no background color
  - Text has default browser font and size
  - No spacing or padding applied
  - No box shadows visible
- Browser console MAY show warnings (browser-dependent)
- Visual verification immediately reveals the issue

---

#### Scenario: Verify CSS load order in DevTools

**Given**:
- Developer opens browser DevTools (F12)
- Developer navigates to Network tab

**When**:
- Page loads `simulations.html`
- Developer filters for CSS files

**Then**:
- Network tab shows CSS files loaded in correct order:
  1. `variables.css`
  2. `templates-base.css`
  3. `templates-layout.css`
  4. `simulations.css`
- All files return HTTP 200 status
- No 404 errors for missing CSS files

---

## MODIFIED Requirements

(None - This is a new fix)

---

## REMOVED Requirements

(None)

---

## Non-Functional Requirements

### Performance

- CSS files SHOULD load quickly (<100ms each)
- Total CSS load time SHOULD be <500ms
- No blocking JavaScript that delays CSS application

### Compatibility

- CSS custom properties MUST be supported (IE 11 excluded)
- Supported browsers: Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+
- Fallback strategy: Not required (IE 11 not supported)

### Maintainability

- CSS import order MUST be documented in HTML comments
- Example:
  ```html
  <!-- CSS Import Order: variables → base → layout → page-specific -->
  <link rel="stylesheet" href="css/variables.css">
  <link rel="stylesheet" href="css/templates-base.css">
  <link rel="stylesheet" href="css/templates-layout.css">
  <link rel="stylesheet" href="css/simulations.css">
  ```

---

## Testing Strategy

### Unit Tests

Not applicable (HTML/CSS only)

### Integration Tests

Not applicable (no API changes)

### E2E Tests

**Recommended** (Optional for this change):
- Create Playwright test: `tests/e2e/test_simulations_page_styling.spec.js`
- Verify computed styles of key elements:
  ```javascript
  test('simulations page has correct styling', async ({ page }) => {
    await page.goto('http://localhost:8000/control/simulations.html');

    // Verify top bar gradient
    const topBar = page.locator('.top-bar');
    const bgColor = await topBar.evaluate(el => getComputedStyle(el).background);
    expect(bgColor).toContain('linear-gradient');

    // Verify button colors
    const primaryBtn = page.locator('.btn-primary').first();
    const btnBg = await primaryBtn.evaluate(el => getComputedStyle(el).backgroundColor);
    expect(btnBg).toBe('rgb(52, 152, 219)'); // #3498db
  });
  ```

### Manual Testing

**Required**:
1. Visual verification in at least one browser
2. Check browser console for CSS errors
3. Compare with `templates.html` for consistency

---

## Dependencies

**No external dependencies**

**Related files**:
- `frontend/control/css/variables.css` (defines variables)
- `frontend/control/css/templates-base.css` (base styles)
- `frontend/control/css/templates-layout.css` (layout styles)
- `frontend/control/css/simulations.css` (page-specific styles)
- `frontend/control/templates.html` (reference implementation)

---

## Migration

**No migration required** - This is a purely additive change (adding missing imports).

**Rollback**: Remove the three added `<link>` tags.

---

## Documentation Updates

**CLAUDE.md**:
- Add CSS import order requirements under "Frontend Development Standards → CSS 文件"
- Document the dependency hierarchy: variables → base → layout → page-specific
- Provide example HTML head structure

**Example addition**:
```markdown
**CSS Import Order Requirements**:

All HTML pages MUST import CSS files in the following order:

1. **variables.css** - Defines CSS custom properties (--color-*, --spacing-*, etc.)
2. **templates-base.css** - Base styles (reset, common elements)
3. **templates-layout.css** - Layout structure (top-bar, sidebar, containers)
4. **Page-specific CSS** - Page-specific styles that build on base/layout

**Example**:
```html
<link rel="stylesheet" href="css/variables.css">
<link rel="stylesheet" href="css/templates-base.css">
<link rel="stylesheet" href="css/templates-layout.css">
<link rel="stylesheet" href="css/your-page.css">
```

**Rationale**: CSS custom properties must be defined before they are referenced. Incorrect order results in unstyled pages.
```
