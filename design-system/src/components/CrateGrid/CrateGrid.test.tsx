import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CrateGrid } from './CrateGrid';

describe('CrateGrid', () => {
  it('renders a crate per group with its label and items', () => {
    render(
      <CrateGrid
        groups={[
          { label: 'Frontend', items: ['React', 'Next.js'] },
          { label: 'Backend', items: ['Node.js', 'gRPC'] },
        ]}
      />
    );
    expect(screen.getByText('Frontend')).toBeInTheDocument();
    expect(screen.getByText('React')).toBeInTheDocument();
    expect(screen.getByText('Backend')).toBeInTheDocument();
    expect(screen.getByText('gRPC')).toBeInTheDocument();
  });
});
