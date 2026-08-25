// @vitest-environment node
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
