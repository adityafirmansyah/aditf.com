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
