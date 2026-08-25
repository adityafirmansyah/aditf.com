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
