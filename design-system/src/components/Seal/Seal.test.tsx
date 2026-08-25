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
