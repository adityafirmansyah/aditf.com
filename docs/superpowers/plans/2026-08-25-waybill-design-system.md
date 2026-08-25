# Waybill Design System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `design-system/` — a standalone, prop-driven React + TypeScript component package that reproduces aditf.com's "shipping manifest" visual language, ready to hand to the `design-sync` skill.

**Architecture:** Each of the 16 components (see spec) lives in its own `src/components/<Name>/` directory with a colocated `.tsx`, `.css`, `.test.tsx`, and `index.ts`. `src/index.ts` re-exports every component; `src/styles.css` bundles every component's CSS via `@import`, on top of `src/tokens/index.css`. esbuild bundles `src/index.ts` → `dist/index.js` and bundles (resolves `@import`s in) `src/styles.css` → `dist/styles.css`; `tsc --emitDeclarationOnly` produces `dist/*.d.ts`.

**Tech Stack:** React 18 + TypeScript 5, esbuild (bundler), Vitest + @testing-library/react + jsdom (tests).

**Spec:** `docs/superpowers/specs/2026-08-25-waybill-design-system-design.md`

## Global Constraints

- New code lives entirely under `design-system/` at repo root — never touch `index.html`, `styles.css`, `script.js`, `assets/`, or the deploy hook.
- No Storybook — this package uses `design-sync`'s "package shape."
- Fidelity target is 1:1 visual match to the live site's CSS rules (colors, spacing, type) — not a simplified reinterpretation.
- Every component takes its content via props. No component hardcodes Aditya's specific bio/projects/timeline text.
- `design-system/package.json` pins `"engines": {"node": ">=20"}`.
- Token names/values must exactly match `styles.css`'s `:root` block on the live site (see spec's token table).

---

## Task 1: Scaffold the package + design tokens

**Files:**
- Create: `design-system/package.json`
- Create: `design-system/tsconfig.json`
- Create: `design-system/vitest.config.ts`
- Create: `design-system/vitest.setup.ts`
- Create: `design-system/scripts/build.mjs`
- Create: `design-system/src/tokens/index.css`
- Create: `design-system/src/tokens/index.ts`
- Create: `design-system/src/tokens/tokens.test.ts`
- Create: `design-system/src/styles.css`
- Create: `design-system/src/index.ts`
- Create: `design-system/.gitignore`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: `colors`, `fonts`, `layout` constants from `design-system/src/tokens/index.ts`, importable as `import { colors, fonts, layout } from '../../tokens'`. `npm test`, `npm run build`, `npm run typecheck` all runnable from `design-system/`.

- [ ] **Step 1: Create `design-system/package.json`**

```json
{
  "name": "@aditf/design-system",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "engines": { "node": ">=20" },
  "main": "dist/index.js",
  "module": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "node scripts/build.mjs && tsc --emitDeclarationOnly --outDir dist",
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  },
  "peerDependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.8",
    "@testing-library/react": "^16.0.1",
    "@types/react": "^18.3.5",
    "@types/react-dom": "^18.3.0",
    "esbuild": "^0.23.1",
    "jsdom": "^25.0.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "typescript": "^5.5.4",
    "vitest": "^2.0.5"
  }
}
```

- [ ] **Step 2: Create `design-system/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "declaration": true,
    "outDir": "dist",
    "skipLibCheck": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  },
  "include": ["src", "examples"]
}
```

- [ ] **Step 3: Create `design-system/vitest.config.ts`**

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
  },
});
```

- [ ] **Step 4: Create `design-system/vitest.setup.ts`**

```typescript
import '@testing-library/jest-dom/vitest';
```

- [ ] **Step 5: Create `design-system/scripts/build.mjs`**

```javascript
import { build } from 'esbuild';

await build({
  entryPoints: ['src/index.ts'],
  bundle: true,
  outfile: 'dist/index.js',
  format: 'esm',
  platform: 'browser',
  external: ['react', 'react-dom', 'react/jsx-runtime'],
  sourcemap: true,
});

await build({
  entryPoints: ['src/styles.css'],
  bundle: true,
  outfile: 'dist/styles.css',
});

console.log('Build complete: dist/index.js, dist/styles.css');
```

- [ ] **Step 6: Create `design-system/.gitignore`**

```
node_modules/
dist/
```

- [ ] **Step 7: Create `design-system/src/tokens/index.css`**

```css
:root {
  --ink: #14181B;
  --ink-soft: #1B2023;
  --ink-line: #2B3236;
  --paper: #EDE6D6;
  --paper-dim: #9CA3A0;
  --kraft: #D9C8A8;
  --kraft-line: #B8A47D;
  --kraft-ink: #2A2116;
  --amber: #E8871E;
  --amber-soft: rgba(232, 135, 30, .14);
  --steel: #7FA9C4;
  --stamp-red: #C24B3B;

  --font-display: 'Oswald', 'Arial Narrow', sans-serif;
  --font-body: 'Inter', -apple-system, sans-serif;
  --font-mono: 'IBM Plex Mono', 'SFMono-Regular', monospace;

  --max: 1080px;
  --edge: clamp(20px, 6vw, 64px);
}
```

- [ ] **Step 8: Create `design-system/src/tokens/index.ts`**

```typescript
export const colors = {
  ink: '#14181B',
  inkSoft: '#1B2023',
  inkLine: '#2B3236',
  paper: '#EDE6D6',
  paperDim: '#9CA3A0',
  kraft: '#D9C8A8',
  kraftLine: '#B8A47D',
  kraftInk: '#2A2116',
  amber: '#E8871E',
  amberSoft: 'rgba(232, 135, 30, .14)',
  steel: '#7FA9C4',
  stampRed: '#C24B3B',
} as const;

export const fonts = {
  display: "'Oswald', 'Arial Narrow', sans-serif",
  body: "'Inter', -apple-system, sans-serif",
  mono: "'IBM Plex Mono', 'SFMono-Regular', monospace",
} as const;

export const layout = {
  max: '1080px',
  edge: 'clamp(20px, 6vw, 64px)',
} as const;
```

- [ ] **Step 9: Write the failing test — `design-system/src/tokens/tokens.test.ts`**

```typescript
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { colors, fonts, layout } from './index';

const cssPath = fileURLToPath(new URL('./index.css', import.meta.url));
const css = readFileSync(cssPath, 'utf-8');

describe('design tokens', () => {
  it('keeps every color in sync with index.css', () => {
    expect(css).toContain(`--ink: ${colors.ink};`);
    expect(css).toContain(`--ink-soft: ${colors.inkSoft};`);
    expect(css).toContain(`--ink-line: ${colors.inkLine};`);
    expect(css).toContain(`--paper: ${colors.paper};`);
    expect(css).toContain(`--paper-dim: ${colors.paperDim};`);
    expect(css).toContain(`--kraft: ${colors.kraft};`);
    expect(css).toContain(`--kraft-line: ${colors.kraftLine};`);
    expect(css).toContain(`--kraft-ink: ${colors.kraftInk};`);
    expect(css).toContain(`--amber: ${colors.amber};`);
    expect(css).toContain(`--amber-soft: ${colors.amberSoft};`);
    expect(css).toContain(`--steel: ${colors.steel};`);
    expect(css).toContain(`--stamp-red: ${colors.stampRed};`);
  });

  it('keeps font stacks in sync with index.css', () => {
    expect(css).toContain(`--font-display: ${fonts.display};`);
    expect(css).toContain(`--font-body: ${fonts.body};`);
    expect(css).toContain(`--font-mono: ${fonts.mono};`);
  });

  it('keeps layout tokens in sync with index.css', () => {
    expect(css).toContain(`--max: ${layout.max};`);
    expect(css).toContain(`--edge: ${layout.edge};`);
  });
});
```

This test is written after `index.ts`/`index.css` in this task purely because token values must be decided before there's anything to assert on both sides — treat it as the first thing you verify once both files exist, before moving on.

- [ ] **Step 10: Create `design-system/src/styles.css`**

```css
@import './tokens/index.css';

* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--ink);
  color: var(--paper);
  font-family: var(--font-body);
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
a { color: inherit; }
ul, ol { margin: 0; padding: 0; }
h1, h2, h3 { margin: 0; font-family: var(--font-display); }
::selection { background: var(--amber); color: var(--ink); }
:focus-visible { outline: 2px solid var(--amber); outline-offset: 3px; }
```

- [ ] **Step 11: Create `design-system/src/index.ts`**

```typescript
// Component exports are added here one `export * from './components/<Name>';`
// line at a time as each component lands (see later tasks).
export {};
```

- [ ] **Step 12: Install dependencies**

Run: `cd design-system && npm install`
Expected: installs cleanly, creates `package-lock.json` and `node_modules/`.

- [ ] **Step 13: Run the token test to verify it passes**

Run: `cd design-system && npm test`
Expected: PASS — 3 tests in `src/tokens/tokens.test.ts`.

- [ ] **Step 14: Run typecheck and build to verify the empty package is sound**

Run: `cd design-system && npm run typecheck && npm run build`
Expected: both succeed; `dist/index.js`, `dist/styles.css`, and `dist/index.d.ts` exist (an `export {}` module still emits a valid empty `.d.ts`).

- [ ] **Step 15: Commit**

```bash
git add design-system/
git commit -m "$(cat <<'EOF'
Scaffold design-system package with build tooling and design tokens

Sets up the React + TypeScript + esbuild + Vitest package that will
hold the Waybill design system, and extracts aditf.com's color/type/
layout tokens as the first piece.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Button

**Files:**
- Create: `design-system/src/components/Button/Button.tsx`
- Create: `design-system/src/components/Button/Button.css`
- Create: `design-system/src/components/Button/Button.test.tsx`
- Create: `design-system/src/components/Button/index.ts`
- Modify: `design-system/src/index.ts`
- Modify: `design-system/src/styles.css`

**Interfaces:**
- Consumes: `--font-mono`, `--amber`, `--ink`, `--paper`, `--ink-line` tokens (Task 1).
- Produces: `Button` component, `ButtonProps`, `ButtonVariant` — `import { Button } from '../Button'` (relative to `src/components/`) or `import { Button } from '@aditf/design-system'` once built. Signature: `<Button variant="stamp" | "ghost" href={string} download?: boolean children>`.

- [ ] **Step 1: Write the failing test — `Button.test.tsx`**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders the stamp variant with the stamp class and href', () => {
    render(<Button variant="stamp" href="/cv.pdf">Download CV</Button>);
    const link = screen.getByRole('link', { name: 'Download CV' });
    expect(link).toHaveClass('btn', 'btn--stamp');
    expect(link).toHaveAttribute('href', '/cv.pdf');
  });

  it('renders the ghost variant with the ghost class', () => {
    render(<Button variant="ghost" href="#contact">Get in touch</Button>);
    expect(screen.getByRole('link', { name: 'Get in touch' })).toHaveClass('btn', 'btn--ghost');
  });

  it('forwards native anchor attributes like download', () => {
    render(<Button variant="stamp" href="/cv.pdf" download>Download CV</Button>);
    expect(screen.getByRole('link', { name: 'Download CV' })).toHaveAttribute('download');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd design-system && npx vitest run src/components/Button`
Expected: FAIL — `Cannot find module './Button'`.

- [ ] **Step 3: Write `Button.tsx`**

```tsx
import type { AnchorHTMLAttributes, ReactNode } from 'react';

export type ButtonVariant = 'stamp' | 'ghost';

export interface ButtonProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  variant: ButtonVariant;
  children: ReactNode;
}

export function Button({ variant, children, className, ...rest }: ButtonProps) {
  const variantClass = variant === 'stamp' ? 'btn--stamp' : 'btn--ghost';
  const classes = ['btn', variantClass, className].filter(Boolean).join(' ');
  return (
    <a className={classes} {...rest}>
      {children}
    </a>
  );
}
```

- [ ] **Step 4: Write `Button.css`**

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 14px 28px;
  text-decoration: none;
  font-family: var(--font-mono);
  font-size: 13px;
  letter-spacing: .06em;
  text-transform: uppercase;
  font-weight: 500;
  border-radius: 2px;
  transition: transform .18s ease, background .18s ease, color .18s ease;
}
.btn--stamp {
  background: var(--amber);
  color: var(--ink);
  border: 1px solid var(--amber);
}
.btn--stamp:hover { transform: rotate(-1.5deg) scale(1.02); }
.btn--ghost {
  background: transparent;
  color: var(--paper);
  border: 1px solid var(--ink-line);
}
.btn--ghost:hover { border-color: var(--amber); color: var(--amber); }
```

- [ ] **Step 5: Write `index.ts`**

```typescript
export { Button } from './Button';
export type { ButtonProps, ButtonVariant } from './Button';
```

- [ ] **Step 6: Wire into the package barrel and stylesheet**

In `design-system/src/index.ts`, replace `export {};` with:

```typescript
export * from './components/Button';
```

In `design-system/src/styles.css`, add after the tokens import:

```css
@import './components/Button/Button.css';
```

- [ ] **Step 7: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/Button`
Expected: PASS — 3 tests.

- [ ] **Step 8: Run typecheck and build**

Run: `cd design-system && npm run typecheck && npm run build`
Expected: both succeed.

- [ ] **Step 9: Commit**

```bash
git add design-system/src
git commit -m "$(cat <<'EOF'
Add Button component

First component in the Waybill design system — establishes the
per-component directory pattern (.tsx/.css/.test.tsx/index.ts) the
rest of the package follows.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Simple presentational primitives — SectionHead, Waybill, Barcode, Seal, LangChip

**Files:**
- Create: `design-system/src/components/SectionHead/{SectionHead.tsx, SectionHead.css, SectionHead.test.tsx, index.ts}`
- Create: `design-system/src/components/Waybill/{Waybill.tsx, Waybill.css, Waybill.test.tsx, index.ts}`
- Create: `design-system/src/components/Barcode/{Barcode.tsx, Barcode.css, Barcode.test.tsx, index.ts}`
- Create: `design-system/src/components/Seal/{Seal.tsx, Seal.css, Seal.test.tsx, index.ts}`
- Create: `design-system/src/components/LangChip/{LangChip.tsx, LangChip.css, LangChip.test.tsx, index.ts}`
- Modify: `design-system/src/index.ts`
- Modify: `design-system/src/styles.css`

**Interfaces:**
- Consumes: tokens (Task 1).
- Produces: `SectionHead` (`eyebrow`, `title`), `Waybill` (`label`, `value`, `status?`), `Barcode` (no props), `Seal` (`label`, `sublabel`), `LangChip` (`name`, `level`). `Waybill` is consumed by `Hero` in Task 7 — its props stay `label`/`value`/`status?`.

### SectionHead

- [ ] **Step 1: Write the failing test — `SectionHead.test.tsx`**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SectionHead } from './SectionHead';

describe('SectionHead', () => {
  it('renders the eyebrow and the title as a heading', () => {
    render(<SectionHead eyebrow="Manifest — Contents Declaration" title="About" />);
    expect(screen.getByText('Manifest — Contents Declaration')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'About' })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/SectionHead`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `SectionHead.tsx`**

```tsx
export interface SectionHeadProps {
  eyebrow: string;
  title: string;
}

export function SectionHead({ eyebrow, title }: SectionHeadProps) {
  return (
    <div className="section__head">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
    </div>
  );
}
```

- [ ] **Step 4: Write `SectionHead.css`**

```css
.section__head { margin-bottom: 48px; }
.eyebrow {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--amber);
  margin: 0 0 12px;
}
.section__head h2 {
  font-size: clamp(28px, 4vw, 42px);
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: -.005em;
  color: var(--paper);
}
```

- [ ] **Step 5: Write `index.ts`**

```typescript
export { SectionHead } from './SectionHead';
export type { SectionHeadProps } from './SectionHead';
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/SectionHead`
Expected: PASS.

### Waybill

- [ ] **Step 7: Write the failing test — `Waybill.test.tsx`**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Waybill } from './Waybill';

describe('Waybill', () => {
  it('renders label and value', () => {
    render(<Waybill label="TRACKING NO." value="AF-2011–2026" />);
    expect(screen.getByText('TRACKING NO.')).toBeInTheDocument();
    expect(screen.getByText('AF-2011–2026')).toBeInTheDocument();
  });

  it('renders the status when provided', () => {
    render(<Waybill label="TRACKING NO." value="AF-2011–2026" status="IN TRANSIT" />);
    expect(screen.getByText('IN TRANSIT')).toBeInTheDocument();
  });

  it('omits the status block when not provided', () => {
    render(<Waybill label="TRACKING NO." value="AF-2011–2026" />);
    expect(screen.queryByText('IN TRANSIT')).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 8: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/Waybill`
Expected: FAIL — module not found.

- [ ] **Step 9: Write `Waybill.tsx`**

```tsx
export interface WaybillProps {
  label: string;
  value: string;
  status?: string;
}

export function Waybill({ label, value, status }: WaybillProps) {
  return (
    <div className="waybill">
      <span className="waybill__field">
        {label} <b>{value}</b>
      </span>
      {status ? (
        <>
          <span className="waybill__divider" aria-hidden="true">·</span>
          <span className="waybill__status">
            <i className="dot" aria-hidden="true" />
            {status}
          </span>
        </>
      ) : null}
    </div>
  );
}
```

- [ ] **Step 10: Write `Waybill.css`**

```css
.waybill {
  display: flex; flex-wrap: wrap; align-items: center; gap: 14px;
  font-family: var(--font-mono); font-size: 12.5px; letter-spacing: .05em;
  color: var(--paper-dim); text-transform: uppercase;
  border: 1px solid var(--ink-line); border-left: 3px solid var(--amber);
  padding: 10px 16px; width: fit-content; max-width: 100%;
}
.waybill b { color: var(--paper); font-weight: 600; }
.waybill__divider { color: var(--ink-line); }
.waybill__status { display: flex; align-items: center; gap: 8px; color: var(--amber); }
.dot {
  width: 7px; height: 7px; border-radius: 50%; background: var(--amber);
  box-shadow: 0 0 0 0 rgba(232,135,30,.6);
  animation: waybill-pulse 2.2s infinite;
}
@keyframes waybill-pulse {
  0% { box-shadow: 0 0 0 0 rgba(232,135,30,.55); }
  70% { box-shadow: 0 0 0 8px rgba(232,135,30,0); }
  100% { box-shadow: 0 0 0 0 rgba(232,135,30,0); }
}
```

- [ ] **Step 11: Write `index.ts`**

```typescript
export { Waybill } from './Waybill';
export type { WaybillProps } from './Waybill';
```

- [ ] **Step 12: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/Waybill`
Expected: PASS — 3 tests.

### Barcode

- [ ] **Step 13: Write the failing test — `Barcode.test.tsx`**

```tsx
import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import { Barcode } from './Barcode';

describe('Barcode', () => {
  it('renders a decorative, ARIA-hidden div', () => {
    const { container } = render(<Barcode />);
    const el = container.querySelector('.barcode');
    expect(el).not.toBeNull();
    expect(el).toHaveAttribute('aria-hidden', 'true');
  });
});
```

- [ ] **Step 14: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/Barcode`
Expected: FAIL — module not found.

- [ ] **Step 15: Write `Barcode.tsx`**

```tsx
export function Barcode() {
  return <div className="barcode" aria-hidden="true" />;
}
```

- [ ] **Step 16: Write `Barcode.css`**

```css
.barcode {
  height: 8px; width: 100%;
  background-image: repeating-linear-gradient(90deg,
    var(--kraft) 0 2px, transparent 2px 4px,
    var(--kraft) 4px 7px, transparent 7px 9px,
    var(--kraft) 9px 10px, transparent 10px 14px);
  opacity: .55;
}
```

- [ ] **Step 17: Write `index.ts`**

```typescript
export { Barcode } from './Barcode';
```

- [ ] **Step 18: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/Barcode`
Expected: PASS.

### Seal

- [ ] **Step 19: Write the failing test — `Seal.test.tsx`**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Seal } from './Seal';

describe('Seal', () => {
  it('renders the label and sublabel', () => {
    render(<Seal label="CSS" sublabel="Fundamentals" />);
    expect(screen.getByText('CSS')).toBeInTheDocument();
    expect(screen.getByText('Fundamentals')).toBeInTheDocument();
  });
});
```

- [ ] **Step 20: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/Seal`
Expected: FAIL — module not found.

- [ ] **Step 21: Write `Seal.tsx`**

```tsx
export interface SealProps {
  label: string;
  sublabel: string;
}

export function Seal({ label, sublabel }: SealProps) {
  return (
    <div className="seal">
      <span>{label}</span>
      <small>{sublabel}</small>
    </div>
  );
}
```

- [ ] **Step 22: Write `Seal.css`**

```css
.seal {
  width: 112px; height: 112px; border-radius: 50%;
  border: 2px dashed var(--kraft-line);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; padding: 10px;
}
.seal span {
  font-family: var(--font-display); font-size: 15px; text-transform: uppercase;
  color: var(--kraft); font-weight: 600;
}
.seal small {
  font-family: var(--font-mono); font-size: 9.5px; color: var(--paper-dim);
  text-transform: uppercase; letter-spacing: .05em; margin-top: 4px;
}
```

- [ ] **Step 23: Write `index.ts`**

```typescript
export { Seal } from './Seal';
export type { SealProps } from './Seal';
```

- [ ] **Step 24: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/Seal`
Expected: PASS.

### LangChip

- [ ] **Step 25: Write the failing test — `LangChip.test.tsx`**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LangChip } from './LangChip';

describe('LangChip', () => {
  it('renders the language name and level', () => {
    render(<LangChip name="English" level="Professional Working Proficiency" />);
    expect(screen.getByText('English')).toBeInTheDocument();
    expect(screen.getByText('Professional Working Proficiency')).toBeInTheDocument();
  });
});
```

- [ ] **Step 26: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/LangChip`
Expected: FAIL — module not found.

- [ ] **Step 27: Write `LangChip.tsx`**

```tsx
export interface LangChipProps {
  name: string;
  level: string;
}

export function LangChip({ name, level }: LangChipProps) {
  return (
    <div className="lang-chip">
      <span className="lang-chip__name">{name}</span>
      <span className="lang-chip__level">{level}</span>
    </div>
  );
}
```

- [ ] **Step 28: Write `LangChip.css`**

```css
.lang-chip {
  display: flex; align-items: center; gap: 10px;
  border: 1px solid var(--ink-line); padding: 12px 18px;
  font-family: var(--font-mono); font-size: 12.5px;
}
.lang-chip__name { color: var(--paper); text-transform: uppercase; letter-spacing: .05em; }
.lang-chip__level { color: var(--paper-dim); }
.lang-chip__level::before { content: "— "; color: var(--ink-line); }
```

- [ ] **Step 29: Write `index.ts`**

```typescript
export { LangChip } from './LangChip';
export type { LangChipProps } from './LangChip';
```

- [ ] **Step 30: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/LangChip`
Expected: PASS.

### Wire up and finish

- [ ] **Step 31: Add all five to the package barrel**

Append to `design-system/src/index.ts`:

```typescript
export * from './components/SectionHead';
export * from './components/Waybill';
export * from './components/Barcode';
export * from './components/Seal';
export * from './components/LangChip';
```

- [ ] **Step 32: Add all five imports to the stylesheet**

Append to `design-system/src/styles.css`:

```css
@import './components/SectionHead/SectionHead.css';
@import './components/Waybill/Waybill.css';
@import './components/Barcode/Barcode.css';
@import './components/Seal/Seal.css';
@import './components/LangChip/LangChip.css';
```

- [ ] **Step 33: Run the full suite, typecheck, and build**

Run: `cd design-system && npm test && npm run typecheck && npm run build`
Expected: all pass.

- [ ] **Step 34: Commit**

```bash
git add design-system/src
git commit -m "$(cat <<'EOF'
Add SectionHead, Waybill, Barcode, Seal, and LangChip components

Five leaf presentational components with no internal state — each
takes plain string props and renders one piece of the manifest motif.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: RouteProgress + Reveal

**Files:**
- Create: `design-system/src/components/RouteProgress/{RouteProgress.tsx, RouteProgress.css, RouteProgress.test.tsx, index.ts}`
- Create: `design-system/src/components/Reveal/{Reveal.tsx, Reveal.css, Reveal.test.tsx, index.ts}`
- Modify: `design-system/src/index.ts`
- Modify: `design-system/src/styles.css`

**Interfaces:**
- Consumes: tokens (Task 1).
- Produces: `RouteProgress` (no props) + `useScrollProgress(): number` hook; `Reveal` (`children: ReactNode`) — wraps content that should fade/slide in on scroll.

### RouteProgress

- [ ] **Step 1: Write the failing test — `RouteProgress.test.tsx`**

```tsx
import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render } from '@testing-library/react';
import { RouteProgress } from './RouteProgress';

afterEach(cleanup);

function mockScrollMetrics(opts: { scrollY: number; scrollHeight: number; innerHeight: number }) {
  Object.defineProperty(window, 'scrollY', { value: opts.scrollY, configurable: true });
  Object.defineProperty(document.documentElement, 'scrollHeight', { value: opts.scrollHeight, configurable: true });
  Object.defineProperty(window, 'innerHeight', { value: opts.innerHeight, configurable: true });
}

describe('RouteProgress', () => {
  it('starts at 0% width', () => {
    mockScrollMetrics({ scrollY: 0, scrollHeight: 2000, innerHeight: 800 });
    render(<RouteProgress />);
    const fill = document.querySelector('.route-progress span') as HTMLElement;
    expect(fill.style.width).toBe('0%');
  });

  it('updates width on scroll based on scroll percentage', () => {
    mockScrollMetrics({ scrollY: 600, scrollHeight: 2000, innerHeight: 800 });
    render(<RouteProgress />);
    fireEvent.scroll(window);
    const fill = document.querySelector('.route-progress span') as HTMLElement;
    expect(fill.style.width).toBe('50%');
  });

  it('renders 0% when the page is not scrollable', () => {
    mockScrollMetrics({ scrollY: 0, scrollHeight: 800, innerHeight: 800 });
    render(<RouteProgress />);
    fireEvent.scroll(window);
    const fill = document.querySelector('.route-progress span') as HTMLElement;
    expect(fill.style.width).toBe('0%');
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/RouteProgress`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `RouteProgress.tsx`**

```tsx
import { useEffect, useState } from 'react';

export function useScrollProgress(): number {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    function update() {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      setProgress(docHeight > 0 ? (scrollTop / docHeight) * 100 : 0);
    }
    update();
    window.addEventListener('scroll', update, { passive: true });
    return () => window.removeEventListener('scroll', update);
  }, []);

  return progress;
}

export function RouteProgress() {
  const progress = useScrollProgress();
  return (
    <div className="route-progress" aria-hidden="true">
      <span style={{ width: `${progress}%` }} />
    </div>
  );
}
```

- [ ] **Step 4: Write `RouteProgress.css`**

```css
.route-progress {
  position: fixed; top: 0; left: 0; right: 0; height: 3px;
  background: var(--ink-line); z-index: 200;
}
.route-progress span {
  display: block; height: 100%; width: 0%;
  background: var(--amber);
  transition: width .1s linear;
}
```

- [ ] **Step 5: Write `index.ts`**

```typescript
export { RouteProgress, useScrollProgress } from './RouteProgress';
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/RouteProgress`
Expected: PASS — 3 tests.

### Reveal

- [ ] **Step 7: Write the failing test — `Reveal.test.tsx`**

```tsx
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render } from '@testing-library/react';
import { Reveal } from './Reveal';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

class MockIntersectionObserver {
  callback: IntersectionObserverCallback;
  constructor(callback: IntersectionObserverCallback) {
    this.callback = callback;
  }
  observe(target: Element) {
    this.callback(
      [{ isIntersecting: true, target } as IntersectionObserverEntry],
      this as unknown as IntersectionObserver
    );
  }
  unobserve() {}
  disconnect() {}
}

describe('Reveal', () => {
  it('adds is-visible once IntersectionObserver reports the element intersecting', () => {
    vi.stubGlobal('IntersectionObserver', MockIntersectionObserver);
    vi.stubGlobal('matchMedia', (query: string) => ({ matches: false, media: query }) as MediaQueryList);

    const { container } = render(<Reveal><p>content</p></Reveal>);
    expect(container.querySelector('.reveal')).toHaveClass('is-visible');
  });

  it('is visible immediately when prefers-reduced-motion is set', () => {
    vi.stubGlobal('matchMedia', (query: string) => ({ matches: true, media: query }) as MediaQueryList);

    const { container } = render(<Reveal><p>content</p></Reveal>);
    expect(container.querySelector('.reveal')).toHaveClass('is-visible');
  });
});
```

- [ ] **Step 8: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/Reveal`
Expected: FAIL — module not found.

- [ ] **Step 9: Write `Reveal.tsx`**

```tsx
import { useEffect, useRef, useState, type ReactNode } from 'react';

export interface RevealProps {
  children: ReactNode;
}

export function Reveal({ children }: RevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const node = ref.current;
    if (!node) return;

    if (reduceMotion || !('IntersectionObserver' in window)) {
      setVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisible(true);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.05, rootMargin: '0px 0px -40px 0px' }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} className={`reveal${visible ? ' is-visible' : ''}`}>
      {children}
    </div>
  );
}
```

- [ ] **Step 10: Write `Reveal.css`**

```css
.reveal {
  opacity: 0; transform: translateY(18px);
  transition: opacity .6s ease, transform .6s ease;
}
.reveal.is-visible { opacity: 1; transform: translateY(0); }
@media (prefers-reduced-motion: reduce) {
  .reveal { opacity: 1; transform: none; transition: none; }
}
```

- [ ] **Step 11: Write `index.ts`**

```typescript
export { Reveal } from './Reveal';
export type { RevealProps } from './Reveal';
```

- [ ] **Step 12: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/Reveal`
Expected: PASS — 2 tests.

### Wire up and finish

- [ ] **Step 13: Add both to the package barrel**

Append to `design-system/src/index.ts`:

```typescript
export * from './components/RouteProgress';
export * from './components/Reveal';
```

- [ ] **Step 14: Add both imports to the stylesheet**

Append to `design-system/src/styles.css`:

```css
@import './components/RouteProgress/RouteProgress.css';
@import './components/Reveal/Reveal.css';
```

- [ ] **Step 15: Run the full suite, typecheck, and build**

Run: `cd design-system && npm test && npm run typecheck && npm run build`
Expected: all pass.

- [ ] **Step 16: Commit**

```bash
git add design-system/src
git commit -m "$(cat <<'EOF'
Add RouteProgress and Reveal components

Moves the site's two IntersectionObserver/scroll-driven behaviors
(scroll-progress bar, scroll-in reveal) from global script.js into
self-contained component hooks, each respecting
prefers-reduced-motion.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Nav

**Files:**
- Create: `design-system/src/components/Nav/{Nav.tsx, Nav.css, Nav.test.tsx, index.ts}`
- Modify: `design-system/src/index.ts`
- Modify: `design-system/src/styles.css`

**Interfaces:**
- Consumes: tokens (Task 1).
- Produces: `Nav` (`mark: string`, `links: NavLink[]`), `NavLink` (`{ label, href, index }`).

- [ ] **Step 1: Write the failing test — `Nav.test.tsx`**

```tsx
import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { Nav } from './Nav';

afterEach(cleanup);

const links = [
  { label: 'About', href: '#about', index: '01' },
  { label: 'Skills', href: '#skills', index: '02' },
];

describe('Nav', () => {
  it('renders the mark and every link', () => {
    render(<Nav mark="AF" links={links} />);
    expect(screen.getByRole('link', { name: 'Back to top' })).toHaveTextContent('AF');
    expect(screen.getByRole('link', { name: '01About' })).toHaveAttribute('href', '#about');
    expect(screen.getByRole('link', { name: '02Skills' })).toHaveAttribute('href', '#skills');
  });

  it('opens the mobile menu when the toggle is clicked', () => {
    render(<Nav mark="AF" links={links} />);
    const toggle = screen.getByRole('button', { name: 'Toggle navigation' });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(toggle);

    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('link', { name: '01About' }).parentElement).toHaveClass('is-open');
  });

  it('closes the mobile menu when a link is clicked', () => {
    render(<Nav mark="AF" links={links} />);
    fireEvent.click(screen.getByRole('button', { name: 'Toggle navigation' }));
    fireEvent.click(screen.getByRole('link', { name: '01About' }));
    expect(screen.getByRole('button', { name: 'Toggle navigation' })).toHaveAttribute('aria-expanded', 'false');
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/Nav`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `Nav.tsx`**

```tsx
import { useState } from 'react';

export interface NavLink {
  label: string;
  href: string;
  index: string;
}

export interface NavProps {
  mark: string;
  links: NavLink[];
}

export function Nav({ mark, links }: NavProps) {
  const [open, setOpen] = useState(false);

  return (
    <header className="nav">
      <a href="#top" className="nav__mark" aria-label="Back to top">
        {mark}
      </a>
      <button
        className="nav__toggle"
        aria-expanded={open}
        aria-controls="navLinks"
        aria-label="Toggle navigation"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span></span><span></span><span></span>
      </button>
      <nav id="navLinks" className={`nav__links${open ? ' is-open' : ''}`}>
        {links.map((link) => (
          <a key={link.href} href={link.href} onClick={() => setOpen(false)}>
            <span className="idx">{link.index}</span>
            {link.label}
          </a>
        ))}
      </nav>
    </header>
  );
}
```

- [ ] **Step 4: Write `Nav.css`**

```css
.nav {
  position: sticky; top: 3px; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px var(--edge);
  background: rgba(20,24,27,.85);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--ink-line);
}
.nav__mark {
  font-family: var(--font-mono); font-weight: 600; font-size: 15px;
  color: var(--ink); background: var(--amber);
  width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;
  text-decoration: none; transform: rotate(-3deg);
  border-radius: 2px;
}
.nav__links { display: flex; gap: 28px; list-style: none; }
.nav__links a {
  text-decoration: none; color: var(--paper-dim);
  font-family: var(--font-mono); font-size: 12.5px; letter-spacing: .06em;
  text-transform: uppercase;
  display: flex; align-items: center; gap: 6px;
  transition: color .2s ease;
}
.nav__links a:hover { color: var(--amber); }
.nav__links .idx { color: var(--ink-line); font-size: 11px; }
.nav__toggle {
  display: none; flex-direction: column; gap: 5px;
  background: none; border: none; cursor: pointer; padding: 6px;
}
.nav__toggle span { width: 22px; height: 2px; background: var(--paper); }

@media (max-width: 760px) {
  .nav__toggle { display: flex; }
  .nav__links {
    position: fixed; top: 64px; left: 0; right: 0;
    flex-direction: column; gap: 0;
    background: var(--ink-soft);
    border-bottom: 1px solid var(--ink-line);
    max-height: 0; overflow: hidden;
    transition: max-height .3s ease;
  }
  .nav__links.is-open { max-height: calc(100vh - 64px); overflow-y: auto; }
  .nav__links a { padding: 16px var(--edge); border-top: 1px solid var(--ink-line); }
}
```

- [ ] **Step 5: Write `index.ts`**

```typescript
export { Nav } from './Nav';
export type { NavProps, NavLink } from './Nav';
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/Nav`
Expected: PASS — 3 tests.

- [ ] **Step 7: Wire into the barrel and stylesheet**

Append to `design-system/src/index.ts`:

```typescript
export * from './components/Nav';
```

Append to `design-system/src/styles.css`:

```css
@import './components/Nav/Nav.css';
```

- [ ] **Step 8: Run the full suite, typecheck, and build**

Run: `cd design-system && npm test && npm run typecheck && npm run build`
Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add design-system/src
git commit -m "$(cat <<'EOF'
Add Nav component

Sticky header with logo mark, link list, and a mobile toggle whose
open/close state is now internal React state instead of the site's
manual classList.toggle wiring.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: LabelCard + StatRow/StatChip + CrateGrid/Crate

**Files:**
- Create: `design-system/src/components/LabelCard/{LabelCard.tsx, LabelCard.css, LabelCard.test.tsx, index.ts}`
- Create: `design-system/src/components/StatRow/{StatRow.tsx, StatRow.css, StatRow.test.tsx, index.ts}`
- Create: `design-system/src/components/CrateGrid/{CrateGrid.tsx, CrateGrid.css, CrateGrid.test.tsx, index.ts}`
- Modify: `design-system/src/index.ts`
- Modify: `design-system/src/styles.css`

**Interfaces:**
- Consumes: tokens (Task 1).
- Produces: `LabelCard` (`children: ReactNode`); `StatRow` (`stats: Stat[]`) + `StatChip` (`Stat = { num, label }`); `CrateGrid` (`groups: CrateGroup[]`) + `Crate` (`CrateGroup = { label, items: string[] }`).

### LabelCard

- [ ] **Step 1: Write the failing test — `LabelCard.test.tsx`**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LabelCard } from './LabelCard';

describe('LabelCard', () => {
  it('renders children inside the kraft card', () => {
    render(<LabelCard>Bio text goes here.</LabelCard>);
    const text = screen.getByText('Bio text goes here.');
    expect(text.closest('.label-card')).not.toBeNull();
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/LabelCard`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `LabelCard.tsx`**

```tsx
import type { ReactNode } from 'react';

export interface LabelCardProps {
  children: ReactNode;
}

export function LabelCard({ children }: LabelCardProps) {
  return (
    <div className="label-card">
      <span className="label-card__tape" aria-hidden="true" />
      <p>{children}</p>
    </div>
  );
}
```

- [ ] **Step 4: Write `LabelCard.css`**

```css
.label-card {
  position: relative;
  background: var(--kraft); color: var(--kraft-ink);
  padding: 36px 40px; max-width: 760px;
  border: 1px solid var(--kraft-line);
  font-size: 17px; line-height: 1.75;
}
.label-card p { margin: 0; }
.label-card__tape {
  position: absolute; top: -14px; left: 36px;
  width: 70px; height: 26px;
  background: rgba(237,230,214,.55);
  border: 1px solid rgba(184,164,125,.7);
  transform: rotate(-4deg);
}
```

- [ ] **Step 5: Write `index.ts`**

```typescript
export { LabelCard } from './LabelCard';
export type { LabelCardProps } from './LabelCard';
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/LabelCard`
Expected: PASS.

### StatRow / StatChip

- [ ] **Step 7: Write the failing test — `StatRow.test.tsx`**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatRow } from './StatRow';

describe('StatRow', () => {
  it('renders a chip per stat with its number and label', () => {
    render(
      <StatRow
        stats={[
          { num: '13+', label: 'Years Shipping Code' },
          { num: '6', label: 'Apps Built' },
        ]}
      />
    );
    expect(screen.getByText('13+')).toBeInTheDocument();
    expect(screen.getByText('Years Shipping Code')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
    expect(screen.getByText('Apps Built')).toBeInTheDocument();
  });
});
```

- [ ] **Step 8: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/StatRow`
Expected: FAIL — module not found.

- [ ] **Step 9: Write `StatRow.tsx`**

```tsx
export interface Stat {
  num: string;
  label: string;
}

export interface StatRowProps {
  stats: Stat[];
}

export function StatChip({ num, label }: Stat) {
  return (
    <div className="stat-chip">
      <span className="stat-chip__num">{num}</span>
      <span className="stat-chip__label">{label}</span>
    </div>
  );
}

export function StatRow({ stats }: StatRowProps) {
  return (
    <div className="stat-row">
      {stats.map((stat) => (
        <StatChip key={stat.label} {...stat} />
      ))}
    </div>
  );
}
```

- [ ] **Step 10: Write `StatRow.css`**

```css
.stat-row { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 28px; }
.stat-chip { border: 1px solid var(--ink-line); padding: 16px 20px; min-width: 180px; flex: 1 1 200px; }
.stat-chip__num {
  display: block; font-family: var(--font-display); font-size: 30px;
  color: var(--amber); font-weight: 600;
}
.stat-chip__label {
  display: block; font-family: var(--font-mono); font-size: 11.5px;
  color: var(--paper-dim); text-transform: uppercase; letter-spacing: .05em; margin-top: 6px;
}
```

- [ ] **Step 11: Write `index.ts`**

```typescript
export { StatRow, StatChip } from './StatRow';
export type { Stat, StatRowProps } from './StatRow';
```

- [ ] **Step 12: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/StatRow`
Expected: PASS.

### CrateGrid / Crate

- [ ] **Step 13: Write the failing test — `CrateGrid.test.tsx`**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CrateGrid } from './CrateGrid';

describe('CrateGrid', () => {
  it('renders a crate per group with its label and items', () => {
    render(
      <CrateGrid
        groups={[
          { label: 'Frontend', items: ['React', 'Next.js'] },
          { label: 'Backend', items: ['Node.js', 'gRPC'] },
        ]}
      />
    );
    expect(screen.getByText('Frontend')).toBeInTheDocument();
    expect(screen.getByText('React')).toBeInTheDocument();
    expect(screen.getByText('Backend')).toBeInTheDocument();
    expect(screen.getByText('gRPC')).toBeInTheDocument();
  });
});
```

- [ ] **Step 14: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/CrateGrid`
Expected: FAIL — module not found.

- [ ] **Step 15: Write `CrateGrid.tsx`**

```tsx
export interface CrateGroup {
  label: string;
  items: string[];
}

export interface CrateGridProps {
  groups: CrateGroup[];
}

export function Crate({ label, items }: CrateGroup) {
  return (
    <div className="crate">
      <p className="crate__label">{label}</p>
      <div className="crate__items">
        {items.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
    </div>
  );
}

export function CrateGrid({ groups }: CrateGridProps) {
  return (
    <div className="crate-grid">
      {groups.map((group) => (
        <Crate key={group.label} {...group} />
      ))}
    </div>
  );
}
```

- [ ] **Step 16: Write `CrateGrid.css`**

```css
.crate-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr));
  gap: 2px; background: var(--ink-line);
  border: 1px solid var(--ink-line);
}
.crate { background: var(--ink); padding: 26px 24px; }
.crate__label {
  font-family: var(--font-mono); font-size: 12px; letter-spacing: .08em;
  text-transform: uppercase; color: var(--steel);
  margin: 0 0 16px; padding-bottom: 12px;
  border-bottom: 1px dashed var(--ink-line);
}
.crate__items { display: flex; flex-wrap: wrap; gap: 8px; }
.crate__items span {
  font-family: var(--font-mono); font-size: 12.5px;
  color: var(--paper); background: var(--ink-soft);
  border: 1px solid var(--ink-line);
  padding: 5px 10px; border-radius: 2px;
}
```

- [ ] **Step 17: Write `index.ts`**

```typescript
export { CrateGrid, Crate } from './CrateGrid';
export type { CrateGroup, CrateGridProps } from './CrateGrid';
```

- [ ] **Step 18: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/CrateGrid`
Expected: PASS.

### Wire up and finish

- [ ] **Step 19: Add all three to the package barrel**

Append to `design-system/src/index.ts`:

```typescript
export * from './components/LabelCard';
export * from './components/StatRow';
export * from './components/CrateGrid';
```

- [ ] **Step 20: Add all three imports to the stylesheet**

Append to `design-system/src/styles.css`:

```css
@import './components/LabelCard/LabelCard.css';
@import './components/StatRow/StatRow.css';
@import './components/CrateGrid/CrateGrid.css';
```

- [ ] **Step 21: Run the full suite, typecheck, and build**

Run: `cd design-system && npm test && npm run typecheck && npm run build`
Expected: all pass.

- [ ] **Step 22: Commit**

```bash
git add design-system/src
git commit -m "$(cat <<'EOF'
Add LabelCard, StatRow, and CrateGrid components

Three composed, list-driven presentational components used by the
About and Skills sections: a kraft-paper prose card, numbered stat
chips, and a grid of freight-crate skill groups.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Hero

**Files:**
- Create: `design-system/src/components/Hero/{Hero.tsx, Hero.css, Hero.test.tsx, index.ts}`
- Modify: `design-system/src/index.ts`
- Modify: `design-system/src/styles.css`

**Interfaces:**
- Consumes: `Waybill` from `../Waybill` (Task 3) — composed directly rather than reimplemented, so the waybill markup/CSS exists in exactly one place.
- Produces: `Hero` (`trackingLabel`, `trackingValue`, `status?`, `name`, `nameAccent`, `role`, `origin`, `dest`, `lede`, `actions: ReactNode`).

- [ ] **Step 1: Write the failing test — `Hero.test.tsx`**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Hero } from './Hero';
import { Button } from '../Button';

describe('Hero', () => {
  it('renders name, accent, role, route, lede, status, and actions', () => {
    render(
      <Hero
        trackingLabel="TRACKING NO."
        trackingValue="AF-2011–2026"
        status="IN TRANSIT"
        name="Aditya"
        nameAccent="Firmansyah"
        role="Senior Software Engineer — Full-Stack Developer"
        origin="SURAKARTA, ID"
        dest="WORLDWIDE"
        lede="Thirteen-plus years shipping web, backend, and mobile software."
        actions={<Button variant="stamp" href="/cv.pdf">Download CV</Button>}
      />
    );

    expect(screen.getByText('Aditya')).toBeInTheDocument();
    expect(screen.getByText('Firmansyah')).toBeInTheDocument();
    expect(screen.getByText('Senior Software Engineer — Full-Stack Developer')).toBeInTheDocument();
    expect(screen.getByText('SURAKARTA, ID')).toBeInTheDocument();
    expect(screen.getByText('WORLDWIDE')).toBeInTheDocument();
    expect(screen.getByText('Thirteen-plus years shipping web, backend, and mobile software.')).toBeInTheDocument();
    expect(screen.getByText('IN TRANSIT')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Download CV' })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/Hero`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `Hero.tsx`**

```tsx
import type { ReactNode } from 'react';
import { Waybill } from '../Waybill';

export interface HeroProps {
  trackingLabel: string;
  trackingValue: string;
  status?: string;
  name: string;
  nameAccent: string;
  role: string;
  origin: string;
  dest: string;
  lede: string;
  actions: ReactNode;
}

export function Hero({
  trackingLabel,
  trackingValue,
  status,
  name,
  nameAccent,
  role,
  origin,
  dest,
  lede,
  actions,
}: HeroProps) {
  return (
    <section className="hero">
      <div className="hero__inner">
        <Waybill label={trackingLabel} value={trackingValue} status={status} />

        <h1 className="hero__name">
          <span>{name}</span>
          <span className="hero__name--accent">{nameAccent}</span>
        </h1>

        <p className="hero__role">{role}</p>

        <div className="route">
          <span className="route__origin">{origin}</span>
          <span className="route__line" aria-hidden="true" />
          <span className="route__dest">{dest}</span>
        </div>

        <p className="hero__lede">{lede}</p>

        <div className="hero__actions">{actions}</div>
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Write `Hero.css`**

```css
.hero { padding: min(14vh,120px) var(--edge) 90px; max-width: var(--max); margin: 0 auto; }
.hero .waybill { margin-bottom: 44px; }
.hero__name {
  font-size: clamp(48px, 10vw, 108px);
  line-height: .92; text-transform: uppercase;
  font-weight: 600; letter-spacing: -.01em;
  display: flex; flex-direction: column;
}
.hero__name--accent { color: var(--amber); }
.hero__role {
  font-family: var(--font-mono); font-size: clamp(13px,2vw,16px);
  color: var(--steel); text-transform: uppercase; letter-spacing: .08em;
  margin: 22px 0 30px;
}
.route {
  display: flex; align-items: center; gap: 14px;
  font-family: var(--font-mono); font-size: 12px; letter-spacing: .08em;
  color: var(--paper-dim); margin-bottom: 34px; max-width: 520px;
}
.route__origin { color: var(--paper); white-space: nowrap; }
.route__dest { white-space: nowrap; }
.route__line {
  flex: 1; height: 1px;
  background-image: repeating-linear-gradient(90deg, var(--kraft-line) 0 6px, transparent 6px 12px);
  position: relative;
}
.route__line::after {
  content: "▸"; position: absolute; right: -4px; top: 50%;
  transform: translateY(-50%); color: var(--amber);
}
.hero__lede { max-width: 560px; font-size: 17px; color: var(--paper-dim); margin: 0 0 40px; }
.hero__actions { display: flex; flex-wrap: wrap; gap: 16px; }
```

- [ ] **Step 5: Write `index.ts`**

```typescript
export { Hero } from './Hero';
export type { HeroProps } from './Hero';
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/Hero`
Expected: PASS.

- [ ] **Step 7: Wire into the barrel and stylesheet**

Append to `design-system/src/index.ts`:

```typescript
export * from './components/Hero';
```

Append to `design-system/src/styles.css`:

```css
@import './components/Hero/Hero.css';
```

- [ ] **Step 8: Run the full suite, typecheck, and build**

Run: `cd design-system && npm test && npm run typecheck && npm run build`
Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add design-system/src
git commit -m "$(cat <<'EOF'
Add Hero component

Composes Waybill for the tracking-number badge rather than
duplicating its markup, plus the name/role/route/lede/actions block.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: ProjectCard

**Files:**
- Create: `design-system/src/components/ProjectCard/{ProjectCard.tsx, ProjectCard.css, ProjectCard.test.tsx, index.ts}`
- Modify: `design-system/src/index.ts`
- Modify: `design-system/src/styles.css`

**Interfaces:**
- Consumes: `.btn`/`.btn--stamp` classes from `Button.css` (Task 2) and `.hero__actions` from `Hero.css` (Task 7) — reused directly for the CTA row rather than redefined.
- Produces: `ProjectCard` (`eyebrow`, `title`, `subtitle`, `badge?: ProjectBadge`, `lede`, `points: string[]`, `stack: string[]`, `cta?: ProjectCta`).

- [ ] **Step 1: Write the failing test — `ProjectCard.test.tsx`**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProjectCard } from './ProjectCard';

describe('ProjectCard', () => {
  it('renders title, subtitle, lede, points, stack and the live badge', () => {
    render(
      <ProjectCard
        eyebrow="Solo Build — Full-Stack Rust"
        title="GainForge"
        subtitle="Gamified Fitness RPG"
        badge={{ label: 'LIVE', href: 'https://gainforgeapp.com' }}
        lede="GainForge turns real workouts into RPG quests."
        points={['Full Rust stack front-to-back.', 'Designed the quest/XP/leveling system.']}
        stack={['Rust', 'Leptos (WASM)', 'Axum']}
        cta={{ label: 'Visit GainForge', href: 'https://gainforgeapp.com' }}
      />
    );

    expect(screen.getByText('GainForge')).toBeInTheDocument();
    expect(screen.getByText('Gamified Fitness RPG')).toBeInTheDocument();
    expect(screen.getByText('GainForge turns real workouts into RPG quests.')).toBeInTheDocument();
    expect(screen.getByText('Full Rust stack front-to-back.')).toBeInTheDocument();
    expect(screen.getByText('Rust')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /visit live site/i })).toHaveAttribute('href', 'https://gainforgeapp.com');
    expect(screen.getByRole('link', { name: /Visit GainForge/ })).toHaveAttribute('href', 'https://gainforgeapp.com');
  });

  it('omits the badge and CTA when not provided', () => {
    render(
      <ProjectCard
        eyebrow="Solo Build"
        title="Project"
        subtitle="Subtitle"
        lede="Lede text."
        points={['Point one.']}
        stack={['TypeScript']}
      />
    );
    expect(screen.queryByText('LIVE')).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/ProjectCard`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `ProjectCard.tsx`**

```tsx
export interface ProjectBadge {
  label: string;
  href: string;
}

export interface ProjectCta {
  label: string;
  href: string;
}

export interface ProjectCardProps {
  eyebrow: string;
  title: string;
  subtitle: string;
  badge?: ProjectBadge;
  lede: string;
  points: string[];
  stack: string[];
  cta?: ProjectCta;
}

export function ProjectCard({ eyebrow, title, subtitle, badge, lede, points, stack, cta }: ProjectCardProps) {
  return (
    <div className="project-card">
      <div className="project-card__top">
        <div>
          <p className="project-card__eyebrow">{eyebrow}</p>
          <h3>
            {title} <span>{subtitle}</span>
          </h3>
        </div>
        {badge ? (
          <a
            className="project-card__badge"
            href={badge.href}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`${title} — visit live site`}
          >
            <i className="dot" aria-hidden="true" />
            {badge.label}
          </a>
        ) : null}
      </div>

      <p className="project-card__lede">{lede}</p>

      <ul className="project-card__points">
        {points.map((point) => (
          <li key={point}>{point}</li>
        ))}
      </ul>

      <div className="project-card__stack">
        {stack.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>

      {cta ? (
        <div className="hero__actions">
          <a className="btn btn--stamp" href={cta.href} target="_blank" rel="noopener noreferrer">
            {cta.label} →
          </a>
        </div>
      ) : null}
    </div>
  );
}
```

- [ ] **Step 4: Write `ProjectCard.css`**

```css
.project-card { border: 1px solid var(--ink-line); padding: 40px; }
.project-card__top {
  display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between;
  gap: 16px; margin-bottom: 22px;
}
.project-card__eyebrow {
  font-family: var(--font-mono); font-size: 12px; letter-spacing: .08em;
  text-transform: uppercase; color: var(--steel); margin: 0 0 8px;
}
.project-card__top h3 { font-size: 22px; text-transform: none; font-weight: 600; color: var(--paper); margin: 0; }
.project-card__top h3 span {
  display: block; font-family: var(--font-mono); font-size: 13px;
  color: var(--steel); font-weight: 400; text-transform: uppercase;
  letter-spacing: .04em; margin-top: 4px;
}
.project-card__badge {
  display: flex; align-items: center; gap: 8px;
  font-family: var(--font-mono); font-size: 12px; letter-spacing: .08em;
  text-transform: uppercase; color: var(--amber);
  text-decoration: none; white-space: nowrap;
  border: 1px solid var(--amber); padding: 6px 12px; border-radius: 2px;
  transition: background .18s ease;
}
.project-card__badge:hover { background: var(--amber-soft); }
.project-card__lede { max-width: 640px; font-size: 17px; color: var(--paper-dim); margin: 0 0 24px; }
.project-card__points {
  list-style: none; display: flex; flex-direction: column; gap: 10px;
  max-width: 680px; margin: 0 0 28px; padding: 0;
}
.project-card__points li { position: relative; padding-left: 18px; color: var(--paper-dim); font-size: 15px; }
.project-card__points li::before { content: "›"; position: absolute; left: 0; color: var(--amber); }
.project-card__stack { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 28px; }
.project-card__stack span {
  font-family: var(--font-mono); font-size: 11.5px;
  color: var(--kraft); background: var(--amber-soft);
  border: 1px solid rgba(232,135,30,.35);
  padding: 4px 9px; border-radius: 2px;
}
```

- [ ] **Step 5: Write `index.ts`**

```typescript
export { ProjectCard } from './ProjectCard';
export type { ProjectCardProps, ProjectBadge, ProjectCta } from './ProjectCard';
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/ProjectCard`
Expected: PASS — 2 tests.

- [ ] **Step 7: Wire into the barrel and stylesheet**

Append to `design-system/src/index.ts`:

```typescript
export * from './components/ProjectCard';
```

Append to `design-system/src/styles.css`:

```css
@import './components/ProjectCard/ProjectCard.css';
```

- [ ] **Step 8: Run the full suite, typecheck, and build**

Run: `cd design-system && npm test && npm run typecheck && npm run build`
Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add design-system/src
git commit -m "$(cat <<'EOF'
Add ProjectCard component

Reuses .btn/.btn--stamp and .hero__actions for the CTA row instead
of redefining button styles, keeping one source of truth for the
stamp-button look.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Timeline/TimelineItem + ContactGrid/ContactRow

**Files:**
- Create: `design-system/src/components/Timeline/{Timeline.tsx, Timeline.css, Timeline.test.tsx, index.ts}`
- Create: `design-system/src/components/ContactGrid/{ContactGrid.tsx, ContactGrid.css, ContactGrid.test.tsx, index.ts}`
- Modify: `design-system/src/index.ts`
- Modify: `design-system/src/styles.css`

**Interfaces:**
- Consumes: tokens (Task 1).
- Produces: `Timeline` (`items: TimelineEntry[]`) + `TimelineItem` (`TimelineEntry = { date, status, statusVariant?, role, org, bullets: string[], stack?: string[] }`); `ContactGrid` (`rows: ContactRowData[]`) + `ContactRow` (`ContactRowData = { label, value, href? }`).

### Timeline / TimelineItem

- [ ] **Step 1: Write the failing test — `Timeline.test.tsx`**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Timeline } from './Timeline';

describe('Timeline', () => {
  it('renders one item per entry with role, org, date, status and bullets', () => {
    render(
      <Timeline
        items={[
          {
            date: 'Aug 2024 – Jul 2026',
            status: 'In Transit',
            statusVariant: 'transit',
            role: 'CTO',
            org: 'GOSG Consulting',
            bullets: ['Leads product and architecture.'],
            stack: ['AI Agents'],
          },
        ]}
      />
    );
    expect(screen.getByText('CTO')).toBeInTheDocument();
    expect(screen.getByText('— GOSG Consulting')).toBeInTheDocument();
    expect(screen.getByText('Aug 2024 – Jul 2026')).toBeInTheDocument();
    expect(screen.getByText('In Transit')).toHaveClass('timeline__badge--transit');
    expect(screen.getByText('Leads product and architecture.')).toBeInTheDocument();
    expect(screen.getByText('AI Agents')).toBeInTheDocument();
  });

  it('omits the stack row when no stack is given', () => {
    render(
      <Timeline
        items={[
          { date: '2018', status: 'Delivered', role: 'Developer', org: 'Studio', bullets: ['Shipped features.'] },
        ]}
      />
    );
    expect(screen.getByText('Delivered')).not.toHaveClass('timeline__badge--transit');
    expect(document.querySelector('.timeline__stack')).toBeNull();
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/Timeline`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `Timeline.tsx`**

```tsx
export interface TimelineEntry {
  date: string;
  status: string;
  statusVariant?: 'transit' | 'delivered';
  role: string;
  org: string;
  bullets: string[];
  stack?: string[];
}

export interface TimelineProps {
  items: TimelineEntry[];
}

export function TimelineItem({ date, status, statusVariant = 'delivered', role, org, bullets, stack }: TimelineEntry) {
  const badgeClass = statusVariant === 'transit' ? 'timeline__badge timeline__badge--transit' : 'timeline__badge';
  return (
    <li className="timeline__item">
      <div className="timeline__meta">
        <span className="timeline__date">{date}</span>
        <span className={badgeClass}>{status}</span>
      </div>
      <div className="timeline__node" aria-hidden="true" />
      <div className="timeline__card">
        <h3>
          {role} <span>— {org}</span>
        </h3>
        <ul>
          {bullets.map((bullet) => (
            <li key={bullet}>{bullet}</li>
          ))}
        </ul>
        {stack && stack.length > 0 ? (
          <div className="timeline__stack">
            {stack.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        ) : null}
      </div>
    </li>
  );
}

export function Timeline({ items }: TimelineProps) {
  return (
    <ol className="timeline">
      {items.map((item) => (
        <TimelineItem key={`${item.role}-${item.date}`} {...item} />
      ))}
    </ol>
  );
}
```

- [ ] **Step 4: Write `Timeline.css`**

```css
.timeline { list-style: none; position: relative; border-left: 1px dashed var(--kraft-line); margin-left: 6px; padding: 0; }
.timeline__item { position: relative; padding: 0 0 56px 40px; }
.timeline__item:last-child { padding-bottom: 0; }
.timeline__node {
  position: absolute; left: -6px; top: 6px;
  width: 11px; height: 11px; border-radius: 50%;
  background: var(--ink); border: 2px solid var(--amber);
}
.timeline__meta { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; margin-bottom: 14px; }
.timeline__date { font-family: var(--font-mono); font-size: 12px; color: var(--paper-dim); letter-spacing: .04em; }
.timeline__badge {
  font-family: var(--font-mono); font-size: 10.5px; letter-spacing: .08em;
  text-transform: uppercase; padding: 3px 9px;
  border: 1px solid var(--kraft-line); color: var(--kraft);
}
.timeline__badge--transit { color: var(--amber); border-color: var(--amber); }
.timeline__card h3 { font-size: 20px; text-transform: none; font-weight: 600; margin-bottom: 14px; color: var(--paper); }
.timeline__card h3 span {
  display: block; font-family: var(--font-mono); font-size: 13px;
  color: var(--steel); font-weight: 400; text-transform: uppercase;
  letter-spacing: .04em; margin-top: 4px;
}
.timeline__card ul { list-style: none; display: flex; flex-direction: column; gap: 8px; max-width: 640px; margin: 0; padding: 0; }
.timeline__card li { position: relative; padding-left: 18px; color: var(--paper-dim); font-size: 15px; }
.timeline__card li::before { content: "›"; position: absolute; left: 0; color: var(--amber); }
.timeline__stack { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
.timeline__stack span {
  font-family: var(--font-mono); font-size: 11.5px;
  color: var(--kraft); background: var(--amber-soft);
  border: 1px solid rgba(232,135,30,.35);
  padding: 4px 9px; border-radius: 2px;
}
```

- [ ] **Step 5: Write `index.ts`**

```typescript
export { Timeline, TimelineItem } from './Timeline';
export type { TimelineEntry, TimelineProps } from './Timeline';
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/Timeline`
Expected: PASS — 2 tests.

### ContactGrid / ContactRow

- [ ] **Step 7: Write the failing test — `ContactGrid.test.tsx`**

```tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ContactGrid } from './ContactGrid';

describe('ContactGrid', () => {
  it('renders linked rows as anchors and rows without href as static divs', () => {
    render(
      <ContactGrid
        rows={[
          { label: 'Email', value: 'aditf.work@gmail.com', href: 'mailto:aditf.work@gmail.com' },
          { label: 'Location', value: 'Surakarta, Central Java, Indonesia' },
        ]}
      />
    );
    const emailRow = screen.getByRole('link', { name: /Email/ });
    expect(emailRow).toHaveAttribute('href', 'mailto:aditf.work@gmail.com');
    expect(screen.getByText('Surakarta, Central Java, Indonesia').closest('div')).toHaveClass('contact-row--static');
  });
});
```

- [ ] **Step 8: Run it to verify it fails**

Run: `cd design-system && npx vitest run src/components/ContactGrid`
Expected: FAIL — module not found.

- [ ] **Step 9: Write `ContactGrid.tsx`**

```tsx
export interface ContactRowData {
  label: string;
  value: string;
  href?: string;
}

export interface ContactGridProps {
  rows: ContactRowData[];
}

export function ContactRow({ label, value, href }: ContactRowData) {
  const content = (
    <>
      <span className="contact-row__label">{label}</span>
      <span className="contact-row__value">{value}</span>
    </>
  );
  if (href) {
    const external = href.startsWith('http');
    return (
      <a
        className="contact-row"
        href={href}
        target={external ? '_blank' : undefined}
        rel={external ? 'noopener noreferrer' : undefined}
      >
        {content}
      </a>
    );
  }
  return <div className="contact-row contact-row--static">{content}</div>;
}

export function ContactGrid({ rows }: ContactGridProps) {
  return (
    <div className="contact-grid">
      {rows.map((row) => (
        <ContactRow key={row.label} {...row} />
      ))}
    </div>
  );
}
```

- [ ] **Step 10: Write `ContactGrid.css`**

```css
.contact-grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(260px,1fr)); border: 1px solid var(--ink-line); }
.contact-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px; text-decoration: none;
  border-bottom: 1px solid var(--ink-line);
  border-right: 1px solid var(--ink-line);
  transition: background .18s ease;
}
.contact-row:hover { background: var(--ink-soft); }
.contact-row--static:hover { background: none; }
.contact-row__label { font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--paper-dim); }
.contact-row__value { font-family: var(--font-mono); font-size: 13.5px; color: var(--paper); text-align: right; }
```

- [ ] **Step 11: Write `index.ts`**

```typescript
export { ContactGrid, ContactRow } from './ContactGrid';
export type { ContactGridProps, ContactRowData } from './ContactGrid';
```

- [ ] **Step 12: Run the test to verify it passes**

Run: `cd design-system && npx vitest run src/components/ContactGrid`
Expected: PASS.

### Wire up and finish

- [ ] **Step 13: Add both to the package barrel**

Append to `design-system/src/index.ts`:

```typescript
export * from './components/Timeline';
export * from './components/ContactGrid';
```

- [ ] **Step 14: Add both imports to the stylesheet**

Append to `design-system/src/styles.css`:

```css
@import './components/Timeline/Timeline.css';
@import './components/ContactGrid/ContactGrid.css';
```

- [ ] **Step 15: Run the full suite, typecheck, and build**

Run: `cd design-system && npm test && npm run typecheck && npm run build`
Expected: all pass. This is the last component task — the package now has all 16 components (Button, Nav, RouteProgress, SectionHead, Hero, Waybill, LabelCard, StatRow, StatChip, CrateGrid, Crate, ProjectCard, Timeline, TimelineItem, Seal, LangChip, ContactGrid, ContactRow, Barcode, Reveal).

- [ ] **Step 16: Commit**

```bash
git add design-system/src
git commit -m "$(cat <<'EOF'
Add Timeline and ContactGrid components

Completes the 16-component set: a dated experience log with
in-transit/delivered status badges, and a bordered contact-detail
grid whose rows render as links or static text depending on whether
an href is given.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Portfolio demo composition

**Files:**
- Create: `design-system/examples/portfolio-demo.tsx`

**Interfaces:**
- Consumes: every export from `design-system/src/index.ts` (Tasks 2–9).
- Produces: `PortfolioDemo` — a default-exported React component composing all 16 components with the real aditf.com content (the "usage reference" the `design-sync` skill's package converter later reads to generate each component's `.prompt.md`, and the fixture used for visual verification against the live site).

- [ ] **Step 1: Write `design-system/examples/portfolio-demo.tsx`**

```tsx
import {
  Barcode,
  Button,
  ContactGrid,
  CrateGrid,
  Hero,
  LabelCard,
  LangChip,
  Nav,
  ProjectCard,
  Reveal,
  RouteProgress,
  Seal,
  SectionHead,
  StatRow,
  Timeline,
} from '../src';

const navLinks = [
  { label: 'About', href: '#about', index: '01' },
  { label: 'Skills', href: '#skills', index: '02' },
  { label: 'Projects', href: '#projects', index: '03' },
  { label: 'Experience', href: '#experience', index: '04' },
  { label: 'Certs', href: '#certifications', index: '05' },
  { label: 'Contact', href: '#contact', index: '06' },
];

export default function PortfolioDemo() {
  return (
    <>
      <RouteProgress />
      <Nav mark="AF" links={navLinks} />

      <main id="top">
        <Hero
          trackingLabel="TRACKING NO."
          trackingValue="AF-2011–2026"
          status="IN TRANSIT"
          name="Aditya"
          nameAccent="Firmansyah"
          role="Senior Software Engineer — Full-Stack Developer"
          origin="SURAKARTA, ID"
          dest="WORLDWIDE"
          lede="Thirteen-plus years shipping web, backend, and mobile software — from enterprise logistics platforms moving real packages to the microservices that route them."
          actions={
            <>
              <Button variant="stamp" href="assets/Aditya_Firmansyah_CV.pdf" download>
                Download CV
              </Button>
              <Button variant="ghost" href="#contact">
                Get in touch
              </Button>
            </>
          }
        />

        <section className="section" id="about">
          <SectionHead eyebrow="Manifest — Contents Declaration" title="About" />
          <Reveal>
            <LabelCard>
              Software engineer with 13+ years designing and building scalable web, backend, and
              mobile applications, from enterprise logistics platforms to AI-integrated SaaS.
            </LabelCard>
          </Reveal>
          <Reveal>
            <StatRow
              stats={[
                { num: '13+', label: 'Years Shipping Code' },
                { num: '6', label: 'Portals & Apps Built at pickupp' },
                { num: '2', label: 'Languages — ID Native / EN Professional' },
              ]}
            />
          </Reveal>
        </section>

        <section className="section" id="skills">
          <SectionHead eyebrow="Cargo Manifest — Technical Payload" title="Skills" />
          <Reveal>
            <CrateGrid
              groups={[
                { label: 'Frontend', items: ['React', 'Next.js', 'React Native'] },
                { label: 'Backend', items: ['Node.js', 'NestJS', 'REST APIs', 'gRPC'] },
              ]}
            />
          </Reveal>
        </section>

        <section className="section" id="projects">
          <SectionHead eyebrow="Cargo Log — Personal Freight" title="Projects" />
          <div className="project-list">
            <Reveal>
              <ProjectCard
                eyebrow="Solo Build — Full-Stack Rust"
                title="GainForge"
                subtitle="Gamified Fitness RPG"
                badge={{ label: 'LIVE', href: 'https://gainforgeapp.com' }}
                lede="GainForge turns real workouts into RPG quests — users earn XP, level up a character, and grow four stats by completing daily training sessions."
                points={[
                  'Full Rust stack front-to-back — Leptos (WASM) frontend and an Axum backend share a single DTO crate.',
                  'Designed the quest/XP/leveling system and a 4-stat character model.',
                ]}
                stack={['Rust', 'Leptos (WASM)', 'Axum', 'PostgreSQL', 'Docker']}
                cta={{ label: 'Visit GainForge', href: 'https://gainforgeapp.com' }}
              />
            </Reveal>
          </div>
        </section>

        <section className="section" id="experience">
          <SectionHead eyebrow="Shipment History — Tracking Log" title="Experience" />
          <Reveal>
            <Timeline
              items={[
                {
                  date: 'Aug 2024 – Jul 2026',
                  status: 'In Transit',
                  statusVariant: 'transit',
                  role: 'CTO',
                  org: 'GOSG Consulting',
                  bullets: ['Leads product and architecture for a platform spanning website creation, e-commerce, and SEO tooling.'],
                  stack: ['Website Builder', 'E-commerce', 'AI Agents'],
                },
                {
                  date: 'Apr 2019 – Jul 2024',
                  status: 'Delivered',
                  role: 'Software Engineer',
                  org: 'pickupp, Singapore',
                  bullets: ['Developed and maintained enterprise logistics platforms using React, Next.js, Node.js, and NestJS.'],
                  stack: ['React', 'Next.js', 'Kubernetes', 'gRPC'],
                },
              ]}
            />
          </Reveal>
        </section>

        <section className="section" id="certifications">
          <SectionHead eyebrow="Quality Control — Certified Seals" title="Certifications & Languages" />
          <Reveal>
            <div className="seal-row">
              <Seal label="JavaScript" sublabel="Course" />
              <Seal label="CSS" sublabel="Fundamentals" />
            </div>
          </Reveal>
          <Reveal>
            <div className="lang-row">
              <LangChip name="Indonesian" level="Native" />
              <LangChip name="English" level="Professional Working Proficiency" />
            </div>
          </Reveal>
        </section>

        <section className="section section--contact" id="contact">
          <Barcode />
          <SectionHead eyebrow="Consignee Details — Final Destination" title="Let's ship something together." />
          <Reveal>
            <ContactGrid
              rows={[
                { label: 'Email', value: 'aditf.work@gmail.com', href: 'mailto:aditf.work@gmail.com' },
                { label: 'Location', value: 'Surakarta, Central Java, Indonesia' },
                { label: 'GitHub', value: '/adityafirmansyah', href: 'https://github.com/adityafirmansyah' },
              ]}
            />
          </Reveal>
        </section>
      </main>
    </>
  );
}
```

- [ ] **Step 2: Verify it typechecks**

Run: `cd design-system && npm run typecheck`
Expected: passes — confirms every prop shape used here matches what each component actually declares.

- [ ] **Step 3: Commit**

```bash
git add design-system/examples
git commit -m "$(cat <<'EOF'
Add portfolio-demo example composing all 16 components

Reassembles aditf.com's real content from these components, as the
visual-verification fixture and the usage reference design-sync
will read from when generating each component's prompt doc.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Final build verification

**Files:**
- None created or modified — this task only runs and confirms the existing build/test/typecheck pipeline end to end.

**Interfaces:**
- Consumes: the complete package from Tasks 1–10.
- Produces: a verified `design-system/dist/` (`index.js`, `index.d.ts`, `styles.css`) ready for `design-sync` to convert.

- [ ] **Step 1: Run the full test suite**

Run: `cd design-system && npm test`
Expected: PASS — every `*.test.tsx`/`*.test.ts` file across all 16 components plus the tokens test, no failures.

- [ ] **Step 2: Run typecheck**

Run: `cd design-system && npm run typecheck`
Expected: PASS — no type errors across `src/` and `examples/`.

- [ ] **Step 3: Run a clean build**

Run: `cd design-system && rm -rf dist && npm run build`
Expected: PASS — `dist/index.js`, `dist/index.js.map`, `dist/styles.css`, and `dist/index.d.ts` (plus per-component `.d.ts` files) are all created with no esbuild or tsc errors.

- [ ] **Step 4: Spot-check the bundled stylesheet resolved every `@import`**

Run: `grep -c "@import" design-system/dist/styles.css`
Expected: `0` — esbuild's CSS bundling inlines every `@import`, so the compiled stylesheet has none left; each component's actual CSS rules (e.g. `grep '.btn--stamp' design-system/dist/styles.css`) should be present instead.

- [ ] **Step 5: Confirm nothing outside `design-system/` changed**

Run: `git status --porcelain -- index.html styles.css script.js assets`
Expected: empty output — the live site is untouched.

- [ ] **Step 6: Commit (if step 3's `dist/` regeneration surfaced anything to commit — it shouldn't, since `dist/` is gitignored)**

Run: `git status --porcelain design-system/`
Expected: empty (all real changes were already committed in Tasks 1–10; this task is verification-only). If anything unexpected shows up, inspect it before deciding whether it belongs in a commit — don't commit blindly.

---

## After this plan

Once Task 11 passes clean, `design-system/` is a complete, verified, prop-driven React package matching the reviewed component catalog. The next step — invoking the `design-sync` skill (package shape) against `design-system/` to sync it into a new Claude Design project — is explicitly out of scope for this plan (see the spec's "Follow-on" section) and should be picked up as its own pass.
