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
