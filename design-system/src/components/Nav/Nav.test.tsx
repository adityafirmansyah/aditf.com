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
