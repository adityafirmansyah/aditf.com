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
