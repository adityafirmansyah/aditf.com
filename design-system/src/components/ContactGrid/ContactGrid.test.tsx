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
