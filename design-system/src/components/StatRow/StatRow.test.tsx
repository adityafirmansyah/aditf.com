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
