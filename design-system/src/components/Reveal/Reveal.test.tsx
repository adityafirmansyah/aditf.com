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
